"""Manage the directory used for generated files.

The output directory is selected in this order: a one-shot override, the
persisted user preference, ``OUTPUT_DIR``, then ``outputs`` below the current
working directory.  The user preference lives in the platform's conventional
configuration directory unless ``AGENT_WORLD_CONFIG_FILE`` overrides it.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import stat
import sys
import tempfile
import threading
from collections.abc import Mapping
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath, PureWindowsPath
from string import Formatter
from typing import Any, BinaryIO, ClassVar, Iterator

from .file_naming import slugify_component

PathInput = str | os.PathLike[str]


class OutputConfigurationError(RuntimeError):
    """Raised when output configuration or a requested output path is unsafe."""


@dataclass(frozen=True)
class OutputVersion:
    """Metadata for one immutable version of a generated file."""

    version: int
    path: Path
    snapshot_path: Path
    created_at: str
    size_bytes: int
    sha256: str
    restored_from: int | None = None

    def to_dict(self) -> dict[str, Any]:
        """Return public metadata without exposing local absolute paths."""

        data = asdict(self)
        data.pop("path")
        data.pop("snapshot_path")
        return data


@dataclass(frozen=True)
class _StagedOutputVersion:
    """A complete snapshot that has not entered the visible history yet."""

    version: int
    target: Path
    staging_directory: Path
    final_directory: Path
    created_at: str
    size_bytes: int
    sha256: str
    restored_from: int | None = None

    @property
    def snapshot_path(self) -> Path:
        return self.staging_directory / f"content{self.target.suffix}"


class OutputManager:
    """Resolve, persist, and safely write to the configured output directory.

    Args:
        config_path: Explicit preference file. It takes precedence over
            ``AGENT_WORLD_CONFIG_FILE`` and is mainly useful to isolate a
            particular installation or test.
        environ: Environment mapping to read. A snapshot of ``os.environ`` is
            used when this argument is omitted.
        cwd: Base directory for relative paths. Defaults to the process current
            working directory at construction time.

    The default preference file is ``%APPDATA%/Agent World/config.json`` on
    Windows, ``~/Library/Application Support/Agent World/config.json`` on
    macOS, and ``$XDG_CONFIG_HOME/agent-world/config.json`` (falling back to
    ``~/.config/agent-world/config.json``) on other platforms. It can be
    overridden on every platform with ``AGENT_WORLD_CONFIG_FILE``.
    """

    CONFIG_FILE_ENV = "AGENT_WORLD_CONFIG_FILE"
    OUTPUT_DIRECTORY_ENV = "OUTPUT_DIR"
    OUTPUT_DIRECTORY_KEY = "output_directory"
    DEFAULT_OUTPUT_DIRECTORY = "outputs"
    OUTPUT_LAYOUT_ENV = "OUTPUT_LAYOUT"
    OUTPUT_LAYOUT_KEY = "output_layout"
    DEFAULT_OUTPUT_LAYOUT = "agents/{agent_id}/outputs"
    VERSION_DIRECTORY = ".versions"
    _VERSION_PATTERN = re.compile(r"^v(?P<version>[0-9]{6})$")
    _PENDING_VERSION_PATTERN = re.compile(
        r"^\.v(?P<version>[0-9]{6})\.[A-Za-z0-9_-]+\.pending$"
    )
    _LAYOUT_FIELDS = frozenset({"agent_id", "agent_name"})
    _WINDOWS_INVALID_CHARACTERS = frozenset('<>:"|?*')
    _WINDOWS_RESERVED_NAMES = frozenset(
        {"con", "prn", "aux", "nul"}
        | {f"com{number}" for number in range(1, 10)}
        | {f"lpt{number}" for number in range(1, 10)}
        | {f"com{number}" for number in "¹²³"}
        | {f"lpt{number}" for number in "¹²³"}
    )
    _version_locks: ClassVar[dict[str, threading.RLock]] = {}
    _version_locks_guard: ClassVar[threading.Lock] = threading.Lock()

    def __init__(
        self,
        config_path: PathInput | None = None,
        environ: Mapping[str, str] | None = None,
        cwd: PathInput | None = None,
    ) -> None:
        self._environ = dict(os.environ if environ is None else environ)
        raw_cwd: PathInput = Path.cwd() if cwd is None else cwd
        self._cwd = self._absolute_path(raw_cwd, "working directory", Path.cwd())

        configured_path: PathInput | None = config_path
        if configured_path is None:
            configured_path = self._environ.get(self.CONFIG_FILE_ENV)

        if configured_path is None:
            self.config_path = self._default_config_path()
        else:
            self.config_path = self._absolute_path(
                configured_path, "configuration file", self._cwd
            )

    def get_output_directory(self, override: PathInput | None = None) -> Path:
        """Return a created and writable output directory.

        ``override`` applies only to this call and has priority over both the
        persisted preference and environment. Relative directory paths are
        interpreted from the manager's ``cwd``.
        """

        if override is not None:
            return self._prepare_output_directory(override)

        config = self._read_config()
        if self.OUTPUT_DIRECTORY_KEY in config:
            preference = config[self.OUTPUT_DIRECTORY_KEY]
            if not isinstance(preference, str) or not preference.strip():
                raise OutputConfigurationError(
                    f"'{self.OUTPUT_DIRECTORY_KEY}' must be a non-empty string"
                )
            return self._prepare_output_directory(preference)

        environment_value = self._environ.get(self.OUTPUT_DIRECTORY_ENV)
        if environment_value is not None:
            return self._prepare_output_directory(environment_value)

        return self._prepare_output_directory(self.DEFAULT_OUTPUT_DIRECTORY)

    def set_output_directory(self, path: PathInput) -> Path:
        """Validate and persist ``path``, preserving unrelated preferences."""

        config = self._read_config()
        directory = self._prepare_output_directory(path)
        config[self.OUTPUT_DIRECTORY_KEY] = str(directory)
        self._write_config(config)
        return directory

    def reset_output_directory(self) -> Path:
        """Forget the persisted preference and return the active fallback."""

        config_exists = self.config_path.exists()
        config = self._read_config()
        preference_existed = self.OUTPUT_DIRECTORY_KEY in config
        config.pop(self.OUTPUT_DIRECTORY_KEY, None)

        if config_exists and preference_existed:
            self._write_config(config)

        return self.get_output_directory()

    def get_output_layout(self, override: str | None = None) -> str:
        """Return a validated relative layout for agent output directories."""

        if override is not None:
            return self._validate_output_layout(override)

        config = self._read_config()
        if self.OUTPUT_LAYOUT_KEY in config:
            preference = config[self.OUTPUT_LAYOUT_KEY]
            if not isinstance(preference, str) or not preference.strip():
                raise OutputConfigurationError(
                    f"'{self.OUTPUT_LAYOUT_KEY}' must be a non-empty string"
                )
            return self._validate_output_layout(preference)

        environment_value = self._environ.get(self.OUTPUT_LAYOUT_ENV)
        if environment_value is not None:
            return self._validate_output_layout(environment_value)

        return self._validate_output_layout(self.DEFAULT_OUTPUT_LAYOUT)

    def set_output_layout(self, layout: str) -> str:
        """Validate and persist the automatic agent-directory layout."""

        config = self._read_config()
        validated = self._validate_output_layout(layout)
        config[self.OUTPUT_LAYOUT_KEY] = validated
        self._write_config(config)
        return validated

    def reset_output_layout(self) -> str:
        """Forget the persisted layout and return the active fallback."""

        config_exists = self.config_path.exists()
        config = self._read_config()
        preference_existed = self.OUTPUT_LAYOUT_KEY in config
        config.pop(self.OUTPUT_LAYOUT_KEY, None)
        if config_exists and preference_existed:
            self._write_config(config)
        return self.get_output_layout()

    def get_agent_output_directory(
        self,
        agent_id: int,
        agent_name: str,
        output_dir: PathInput | None = None,
        output_layout: str | None = None,
    ) -> Path:
        """Return the confined, automatically created directory for an agent."""

        if isinstance(agent_id, bool) or not isinstance(agent_id, int) or agent_id < 1:
            raise OutputConfigurationError("Agent ID must be a positive integer")
        if not isinstance(agent_name, str) or not agent_name.strip():
            raise OutputConfigurationError("Agent name must be a non-empty string")

        root = self.get_output_directory(output_dir)
        layout = self.get_output_layout(output_layout)
        safe_agent_name = slugify_component(agent_name, fallback=f"agent-{agent_id}")
        try:
            relative_directory = layout.format(
                agent_id=agent_id,
                agent_name=safe_agent_name,
            )
        except (KeyError, ValueError) as exc:
            raise OutputConfigurationError(f"Invalid output layout: {layout}") from exc

        relative_path = self._safe_relative_path(relative_directory, "output layout")
        try:
            directory = (root / relative_path).resolve(strict=False)
            self._assert_within(directory, root)
            directory.mkdir(parents=True, exist_ok=True)
            directory = directory.resolve(strict=True)
            self._assert_within(directory, root)
        except (OSError, RuntimeError, ValueError) as exc:
            raise OutputConfigurationError(
                f"Cannot create agent output directory from layout '{layout}': {exc}"
            ) from exc

        if not directory.is_dir():
            raise OutputConfigurationError(
                f"Agent output path is not a directory: {directory}"
            )
        self._validate_writable_directory(directory)
        return directory

    def resolve_output_path(
        self,
        filename: PathInput,
        output_dir: PathInput | None = None,
        *,
        agent_id: int | None = None,
        agent_name: str | None = None,
        output_layout: str | None = None,
    ) -> Path:
        """Resolve ``filename`` below the selected directory without escapes.

        Absolute filenames and every explicit ``..`` component are rejected.
        Resolution follows existing symlinks before containment is checked, so
        a symlink cannot redirect a generated file outside the output tree.
        """

        relative_path = self._safe_relative_filename(filename)
        directory = self._get_context_directory(
            output_dir=output_dir,
            agent_id=agent_id,
            agent_name=agent_name,
            output_layout=output_layout,
        )

        try:
            target = (directory / relative_path).resolve(strict=False)
            self._assert_within(target, directory)
        except (OSError, RuntimeError, ValueError) as exc:
            raise OutputConfigurationError(
                f"Output path escapes the configured directory: {filename!s}"
            ) from exc

        if self._same_path(target, directory):
            raise OutputConfigurationError("An output filename is required")
        if target.exists() and not target.is_file():
            raise OutputConfigurationError(
                f"Output path is not a regular file: {target}"
            )

        return target

    def resolve_existing_output_path(
        self,
        filename: PathInput,
        *,
        output_dir: PathInput,
    ) -> Path:
        """Resolve an existing regular file without requiring write access."""

        relative_path = self._safe_relative_filename(filename)
        try:
            directory = self._absolute_path(
                output_dir, "existing output directory", self._cwd
            ).resolve(strict=True)
            if not directory.is_dir():
                raise OSError("root is not a directory")
            target = (directory / relative_path).resolve(strict=True)
            self._assert_within(target, directory)
            if self._same_path(target, directory) or not target.is_file():
                raise OSError("target is not a regular file")
        except (OSError, RuntimeError, ValueError) as exc:
            raise OutputConfigurationError(
                "Existing output file is unavailable"
            ) from exc
        return target

    def write_json(
        self,
        filename: PathInput,
        data: Any,
        output_dir: PathInput | None = None,
        *,
        agent_id: int | None = None,
        agent_name: str | None = None,
        output_layout: str | None = None,
    ) -> Path:
        """Atomically write UTF-8 JSON and return its absolute path."""

        serialized = self._serialize_json(data, "output file")
        return self.write_bytes(
            filename,
            serialized,
            output_dir,
            agent_id=agent_id,
            agent_name=agent_name,
            output_layout=output_layout,
        )

    def write_text(
        self,
        filename: PathInput,
        data: str,
        output_dir: PathInput | None = None,
        *,
        agent_id: int | None = None,
        agent_name: str | None = None,
        output_layout: str | None = None,
    ) -> Path:
        """Atomically write UTF-8 text and return its absolute path."""

        if not isinstance(data, str):
            raise OutputConfigurationError("Output text must be a string")
        return self.write_bytes(
            filename,
            data.encode("utf-8"),
            output_dir,
            agent_id=agent_id,
            agent_name=agent_name,
            output_layout=output_layout,
        )

    def write_bytes(
        self,
        filename: PathInput,
        data: bytes | bytearray | memoryview,
        output_dir: PathInput | None = None,
        *,
        agent_id: int | None = None,
        agent_name: str | None = None,
        output_layout: str | None = None,
    ) -> Path:
        """Atomically write bytes and return the confined absolute path."""

        if not isinstance(data, (bytes, bytearray, memoryview)):
            raise OutputConfigurationError("Output data must be bytes-like")
        target = self._prepare_output_target(
            filename,
            output_dir=output_dir,
            agent_id=agent_id,
            agent_name=agent_name,
            output_layout=output_layout,
        )
        self._write_bytes_atomically(target, bytes(data), "output file")
        return target

    def write_versioned_json(
        self,
        filename: PathInput,
        data: Any,
        *,
        agent_id: int,
        agent_name: str,
        output_dir: PathInput | None = None,
        output_layout: str | None = None,
    ) -> OutputVersion:
        """Serialize JSON and append it as a new immutable output version."""

        serialized = self._serialize_json(data, "output file")
        return self.write_versioned_bytes(
            filename,
            serialized,
            agent_id=agent_id,
            agent_name=agent_name,
            output_dir=output_dir,
            output_layout=output_layout,
        )

    def write_versioned_text(
        self,
        filename: PathInput,
        data: str,
        *,
        agent_id: int,
        agent_name: str,
        output_dir: PathInput | None = None,
        output_layout: str | None = None,
    ) -> OutputVersion:
        """Encode UTF-8 text and append it as a new immutable version."""

        if not isinstance(data, str):
            raise OutputConfigurationError("Output text must be a string")
        return self.write_versioned_bytes(
            filename,
            data.encode("utf-8"),
            agent_id=agent_id,
            agent_name=agent_name,
            output_dir=output_dir,
            output_layout=output_layout,
        )

    def write_versioned_bytes(
        self,
        filename: PathInput,
        data: bytes | bytearray | memoryview,
        *,
        agent_id: int,
        agent_name: str,
        output_dir: PathInput | None = None,
        output_layout: str | None = None,
        restored_from: int | None = None,
    ) -> OutputVersion:
        """Append bytes to a file's history and update its current copy.

        Existing current files that predate versioning are imported before the
        new version. External edits to the current copy are also captured, so
        enabling versioning never silently discards prior content.
        """

        if not isinstance(data, (bytes, bytearray, memoryview)):
            raise OutputConfigurationError("Output data must be bytes-like")
        if restored_from is not None and (
            isinstance(restored_from, bool)
            or not isinstance(restored_from, int)
            or restored_from < 1
        ):
            raise OutputConfigurationError("Restored version must be positive")

        target = self._prepare_output_target(
            filename,
            output_dir=output_dir,
            agent_id=agent_id,
            agent_name=agent_name,
            output_layout=output_layout,
        )
        directory = self.get_agent_output_directory(
            agent_id,
            agent_name,
            output_dir=output_dir,
            output_layout=output_layout,
        )
        payload = bytes(data)
        with self._version_transaction(target, directory):
            return self._append_version_locked(
                target,
                directory,
                payload,
                restored_from=restored_from,
            )

    def list_versions(
        self,
        filename: PathInput,
        *,
        agent_id: int,
        agent_name: str,
        output_dir: PathInput | None = None,
        output_layout: str | None = None,
    ) -> list[OutputVersion]:
        """Return the immutable history for a generated file, oldest first."""

        target = self.resolve_output_path(
            filename,
            output_dir,
            agent_id=agent_id,
            agent_name=agent_name,
            output_layout=output_layout,
        )
        directory = self.get_agent_output_directory(
            agent_id,
            agent_name,
            output_dir=output_dir,
            output_layout=output_layout,
        )
        with self._version_transaction(target, directory):
            return self._read_version_history(target, directory)

    def restore_version(
        self,
        filename: PathInput,
        version: int,
        *,
        agent_id: int,
        agent_name: str,
        output_dir: PathInput | None = None,
        output_layout: str | None = None,
    ) -> OutputVersion:
        """Restore an immutable snapshot by creating a new current version."""

        if isinstance(version, bool) or not isinstance(version, int) or version < 1:
            raise OutputConfigurationError("Version must be a positive integer")

        target = self.resolve_output_path(
            filename,
            output_dir,
            agent_id=agent_id,
            agent_name=agent_name,
            output_layout=output_layout,
        )
        directory = self.get_agent_output_directory(
            agent_id,
            agent_name,
            output_dir=output_dir,
            output_layout=output_layout,
        )
        with self._version_transaction(target, directory):
            versions = self._read_version_history(target, directory)
            selected = next(
                (item for item in versions if item.version == version), None
            )
            if selected is None:
                raise OutputConfigurationError(
                    f"Version {version} does not exist for '{filename!s}'"
                )
            payload = self._read_confined_bytes(selected.snapshot_path, directory)
            if self._sha256(payload) != selected.sha256:
                raise OutputConfigurationError(
                    f"Version {version} failed its integrity check"
                )

            return self._append_version_locked(
                target,
                directory,
                payload,
                restored_from=version,
            )

    def _append_version_locked(
        self,
        target: Path,
        directory: Path,
        payload: bytes,
        *,
        restored_from: int | None = None,
    ) -> OutputVersion:
        """Append a version while the thread and process locks are held."""

        versions = self._read_version_history(target, directory)
        target_existed = target.exists()
        previous_data: bytes | None = None
        if target_existed:
            previous_data = self._read_confined_bytes(target, directory)
            current_hash = self._sha256(previous_data)
            if not versions or versions[-1].sha256 != current_hash:
                imported_number = versions[-1].version + 1 if versions else 1
                imported = self._create_version_snapshot(
                    target,
                    directory,
                    previous_data,
                    imported_number,
                )
                versions.append(imported)

        version_number = versions[-1].version + 1 if versions else 1
        staged = self._stage_version_snapshot(
            target,
            directory,
            payload,
            version_number,
            restored_from=restored_from,
        )
        try:
            self._write_bytes_atomically(target, payload, "output file")
        except OutputConfigurationError:
            self._discard_staged_snapshot(staged, directory)
            raise

        try:
            return self._publish_staged_snapshot(staged, directory)
        except OutputConfigurationError:
            rolled_back = self._rollback_current_file(
                target,
                previous_data,
                existed=target_existed,
            )
            if rolled_back:
                self._discard_staged_snapshot(staged, directory)
            # If rollback also failed, retain the complete pending snapshot.
            # The next locked operation can finish publishing it when its hash
            # matches the current copy.
            raise

    def _get_context_directory(
        self,
        *,
        output_dir: PathInput | None,
        agent_id: int | None,
        agent_name: str | None,
        output_layout: str | None,
    ) -> Path:
        if agent_id is None and agent_name is None:
            if output_layout is not None:
                raise OutputConfigurationError(
                    "An output layout requires an agent ID and name"
                )
            return self.get_output_directory(output_dir)
        if agent_id is None or agent_name is None:
            raise OutputConfigurationError(
                "Agent ID and name must be provided together"
            )
        return self.get_agent_output_directory(
            agent_id,
            agent_name,
            output_dir=output_dir,
            output_layout=output_layout,
        )

    def _prepare_output_target(
        self,
        filename: PathInput,
        *,
        output_dir: PathInput | None,
        agent_id: int | None,
        agent_name: str | None,
        output_layout: str | None,
    ) -> Path:
        target = self.resolve_output_path(
            filename,
            output_dir,
            agent_id=agent_id,
            agent_name=agent_name,
            output_layout=output_layout,
        )
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise OutputConfigurationError(
                f"Cannot create output subdirectory '{target.parent}': {exc}"
            ) from exc

        # Re-resolve after creating parents to catch a pre-existing symlink.
        return self.resolve_output_path(
            filename,
            output_dir,
            agent_id=agent_id,
            agent_name=agent_name,
            output_layout=output_layout,
        )

    @classmethod
    def _validate_output_layout(cls, layout: str) -> str:
        if not isinstance(layout, str) or not layout.strip():
            raise OutputConfigurationError("Output layout must be a non-empty string")
        if "\x00" in layout:
            raise OutputConfigurationError("Output layout contains a null byte")

        normalized = layout.strip().replace("\\", "/")
        try:
            parsed = list(Formatter().parse(normalized))
        except ValueError as exc:
            raise OutputConfigurationError(f"Invalid output layout: {layout}") from exc

        fields: set[str] = set()
        for _, field_name, format_spec, conversion in parsed:
            if field_name is None:
                continue
            if field_name not in cls._LAYOUT_FIELDS:
                raise OutputConfigurationError(
                    f"Unsupported output layout placeholder: {field_name}"
                )
            if format_spec or conversion:
                raise OutputConfigurationError(
                    "Output layout placeholders cannot use formatting or conversion"
                )
            fields.add(field_name)

        if "agent_id" not in fields:
            raise OutputConfigurationError(
                "Output layout must include the {agent_id} placeholder"
            )

        try:
            rendered = normalized.format(agent_id=1, agent_name="agent")
        except (KeyError, ValueError) as exc:
            raise OutputConfigurationError(f"Invalid output layout: {layout}") from exc
        relative = cls._safe_relative_path(rendered, "output layout")
        if relative == Path("."):
            raise OutputConfigurationError("Output layout must create a subdirectory")
        return normalized

    @classmethod
    def _version_lock(cls, target: Path) -> threading.RLock:
        try:
            canonical_target = target.resolve(strict=False)
        except (OSError, RuntimeError, ValueError):
            canonical_target = target
        key = cls._comparison_path(canonical_target)
        with cls._version_locks_guard:
            return cls._version_locks.setdefault(key, threading.RLock())

    @contextmanager
    def _version_transaction(self, target: Path, directory: Path) -> Iterator[None]:
        """Serialize one history mutation across threads and processes."""

        with self._version_lock(target):
            root = self._version_root(target, directory, create=True)
            with self._interprocess_lock(root / ".lock", directory):
                self._recover_version_entries(target, directory, root)
                yield

    @classmethod
    @contextmanager
    def _interprocess_lock(cls, lock_path: Path, directory: Path) -> Iterator[None]:
        """Hold an advisory OS lock backed by a confined persistent file."""

        handle: BinaryIO | None = None
        locked = False
        try:
            root = lock_path.parent.resolve(strict=True)
            cls._assert_within(root, directory)
            if lock_path.is_symlink():
                raise OSError("lock path is a symbolic link")

            flags = os.O_RDWR | os.O_CREAT
            flags |= getattr(os, "O_BINARY", 0)
            flags |= getattr(os, "O_CLOEXEC", 0)
            flags |= getattr(os, "O_NOFOLLOW", 0)
            descriptor = os.open(lock_path, flags, 0o600)
            handle = os.fdopen(descriptor, "r+b", buffering=0)
            if not stat.S_ISREG(os.fstat(handle.fileno()).st_mode):
                raise OSError("lock path is not a regular file")

            handle.seek(0, os.SEEK_END)
            if handle.tell() == 0:
                handle.write(b"\0")
                handle.flush()
                os.fsync(handle.fileno())
            handle.seek(0)
            cls._lock_file_handle(handle)
            locked = True
            yield
        except OutputConfigurationError:
            raise
        except OSError as exc:
            raise OutputConfigurationError(
                f"Cannot lock output history for '{lock_path.parent.name}': {exc}"
            ) from exc
        finally:
            if handle is not None:
                if locked:
                    try:
                        cls._unlock_file_handle(handle)
                    except OSError:
                        pass
                handle.close()

    @staticmethod
    def _lock_file_handle(handle: BinaryIO) -> None:
        handle.seek(0)
        if os.name == "nt":
            import msvcrt

            msvcrt.locking(handle.fileno(), msvcrt.LK_LOCK, 1)
            return

        import fcntl

        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)

    @staticmethod
    def _unlock_file_handle(handle: BinaryIO) -> None:
        handle.seek(0)
        if os.name == "nt":
            import msvcrt

            msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            return

        import fcntl

        fcntl.flock(handle.fileno(), fcntl.LOCK_UN)

    def _version_root(self, target: Path, directory: Path, create: bool) -> Path:
        candidate = target.parent / self.VERSION_DIRECTORY / target.name
        try:
            root = candidate.resolve(strict=False)
            self._assert_within(root, directory)
            if create:
                root.mkdir(parents=True, exist_ok=True)
                root = root.resolve(strict=True)
                self._assert_within(root, directory)
        except (OSError, RuntimeError, ValueError) as exc:
            raise OutputConfigurationError(
                f"Unsafe version history path for '{target.name}'"
            ) from exc
        if root.exists() and not root.is_dir():
            raise OutputConfigurationError(
                f"Version history path is not a directory: {root}"
            )
        return root

    def _recover_version_entries(
        self, target: Path, directory: Path, root: Path
    ) -> None:
        """Remove legacy partial entries and finish a committed pending write."""

        try:
            entries = sorted(root.iterdir(), key=lambda item: item.name)
        except OSError as exc:
            raise OutputConfigurationError(
                f"Cannot recover version history for '{target.name}': {exc}"
            ) from exc

        published_numbers: set[int] = set()
        pending_entries: list[tuple[int, Path]] = []
        for entry in entries:
            version_match = self._VERSION_PATTERN.fullmatch(entry.name)
            if version_match is not None:
                version_number = int(version_match.group("version"))
                self._recover_incomplete_published_entry(
                    target,
                    directory,
                    root,
                    entry,
                )
                if entry.exists():
                    published_numbers.add(version_number)
                continue

            pending_match = self._PENDING_VERSION_PATTERN.fullmatch(entry.name)
            if pending_match is not None:
                pending_entries.append((int(pending_match.group("version")), entry))

        for version_number, entry in pending_entries:
            final_directory = root / f"v{version_number:06d}"
            if final_directory.exists():
                self._remove_version_directory(entry, root, directory)
                continue
            try:
                pending = self._load_staged_snapshot(
                    target,
                    directory,
                    entry,
                    final_directory,
                    version_number,
                )
                expected_version = max(published_numbers, default=0) + 1
                current_payload = (
                    self._read_confined_bytes(target, directory)
                    if target.exists()
                    else None
                )
                if (
                    version_number == expected_version
                    and current_payload is not None
                    and self._sha256(current_payload) == pending.sha256
                ):
                    self._publish_staged_snapshot(pending, directory)
                    published_numbers.add(version_number)
                    continue
            except OutputConfigurationError:
                # Pending directories are unpublished transaction state. A
                # malformed or incomplete one is safe to discard below.
                pass
            self._remove_version_directory(entry, root, directory)

    def _recover_incomplete_published_entry(
        self,
        target: Path,
        directory: Path,
        root: Path,
        entry: Path,
    ) -> None:
        """Remove directories exposed by the legacy non-atomic publisher."""

        if entry.is_symlink():
            raise OutputConfigurationError(
                f"Unsafe version directory for '{target.name}'"
            )
        try:
            resolved = entry.resolve(strict=True)
            self._assert_within(resolved, root)
            self._assert_within(resolved, directory)
        except (OSError, RuntimeError, ValueError) as exc:
            raise OutputConfigurationError(
                f"Unsafe version directory for '{target.name}'"
            ) from exc
        if not resolved.is_dir():
            raise OutputConfigurationError(
                f"Version entry is not a directory: {resolved}"
            )

        metadata_path = resolved / "metadata.json"
        snapshot_path = resolved / f"content{target.suffix}"
        for expected in (metadata_path, snapshot_path):
            if expected.is_symlink():
                raise OutputConfigurationError(
                    f"Unsafe version entry for '{target.name}'"
                )
        if metadata_path.is_file() and snapshot_path.is_file():
            return
        self._remove_version_directory(entry, root, directory)

    def _load_staged_snapshot(
        self,
        target: Path,
        directory: Path,
        staging_directory: Path,
        final_directory: Path,
        version: int,
    ) -> _StagedOutputVersion:
        if staging_directory.is_symlink() or not staging_directory.is_dir():
            raise OutputConfigurationError("Pending version entry is unsafe")
        metadata = self._read_version_metadata(
            staging_directory / "metadata.json", directory
        )
        snapshot_path = staging_directory / f"content{target.suffix}"
        payload = self._read_confined_bytes(snapshot_path, directory)
        size_bytes, digest, created_at, restored_from = self._version_metadata_values(
            metadata,
            version,
            target.name,
        )
        if len(payload) != size_bytes or self._sha256(payload) != digest:
            raise OutputConfigurationError(
                f"Pending version {version} failed its integrity check"
            )
        return _StagedOutputVersion(
            version=version,
            target=target,
            staging_directory=staging_directory,
            final_directory=final_directory,
            created_at=created_at,
            size_bytes=size_bytes,
            sha256=digest,
            restored_from=restored_from,
        )

    @classmethod
    def _remove_version_directory(
        cls, entry: Path, root: Path, directory: Path
    ) -> None:
        """Remove one confined unpublished or incomplete version directory."""

        try:
            resolved_root = root.resolve(strict=True)
            if entry.is_symlink():
                raise OSError("version entry is a symbolic link")
            resolved = entry.resolve(strict=True)
            cls._assert_within(resolved, resolved_root)
            cls._assert_within(resolved, directory)
            if cls._comparison_path(resolved.parent) != cls._comparison_path(
                resolved_root
            ):
                raise OSError("version entry is not a direct child")
            if not resolved.is_dir():
                raise OSError("version entry is not a directory")
            for child in resolved.iterdir():
                if child.is_dir() and not child.is_symlink():
                    raise OSError("version entry contains a nested directory")
                child.unlink()
            resolved.rmdir()
        except (OSError, RuntimeError, ValueError) as exc:
            raise OutputConfigurationError(
                f"Cannot recover incomplete version entry '{entry.name}': {exc}"
            ) from exc

    def _read_version_history(
        self, target: Path, directory: Path
    ) -> list[OutputVersion]:
        root = self._version_root(target, directory, create=False)
        if not root.exists():
            return []

        versions: list[OutputVersion] = []
        try:
            entries = sorted(root.iterdir(), key=lambda item: item.name)
        except OSError as exc:
            raise OutputConfigurationError(
                f"Cannot read version history for '{target.name}': {exc}"
            ) from exc

        for entry in entries:
            match = self._VERSION_PATTERN.fullmatch(entry.name)
            if match is None:
                continue
            version_number = int(match.group("version"))
            if version_number < 1:
                raise OutputConfigurationError(
                    f"Invalid version directory for '{target.name}'"
                )
            try:
                version_directory = entry.resolve(strict=True)
                self._assert_within(version_directory, directory)
            except (OSError, RuntimeError, ValueError) as exc:
                raise OutputConfigurationError(
                    f"Unsafe version directory for '{target.name}'"
                ) from exc
            if not version_directory.is_dir():
                raise OutputConfigurationError(
                    f"Version entry is not a directory: {version_directory}"
                )

            metadata_path = version_directory / "metadata.json"
            snapshot_path = version_directory / f"content{target.suffix}"
            metadata = self._read_version_metadata(metadata_path, directory)
            payload = self._read_confined_bytes(snapshot_path, directory)
            size_bytes, digest, created_at, restored_from = (
                self._version_metadata_values(
                    metadata,
                    version_number,
                    target.name,
                )
            )
            if len(payload) != size_bytes or self._sha256(payload) != digest:
                raise OutputConfigurationError(
                    f"Version {version_number} failed its integrity check"
                )
            versions.append(
                OutputVersion(
                    version=version_number,
                    path=target,
                    snapshot_path=snapshot_path.resolve(strict=True),
                    created_at=created_at,
                    size_bytes=size_bytes,
                    sha256=digest,
                    restored_from=restored_from,
                )
            )
        return versions

    def _create_version_snapshot(
        self,
        target: Path,
        directory: Path,
        payload: bytes,
        version: int,
        restored_from: int | None = None,
    ) -> OutputVersion:
        staged = self._stage_version_snapshot(
            target,
            directory,
            payload,
            version,
            restored_from=restored_from,
        )
        try:
            return self._publish_staged_snapshot(staged, directory)
        except OutputConfigurationError:
            self._discard_staged_snapshot(staged, directory)
            raise

    def _stage_version_snapshot(
        self,
        target: Path,
        directory: Path,
        payload: bytes,
        version: int,
        restored_from: int | None = None,
    ) -> _StagedOutputVersion:
        """Build a complete snapshot outside the visible ``vNNNNNN`` name."""

        if version > 999999:
            raise OutputConfigurationError("Maximum output version reached")
        root = self._version_root(target, directory, create=True)
        final_directory = root / f"v{version:06d}"
        if final_directory.exists():
            raise OutputConfigurationError(f"Output version {version} already exists")
        try:
            staging_directory = Path(
                tempfile.mkdtemp(
                    prefix=f".v{version:06d}.",
                    suffix=".pending",
                    dir=root,
                )
            ).resolve(strict=True)
            self._assert_within(staging_directory, root)
            self._assert_within(staging_directory, directory)
        except (OSError, RuntimeError, ValueError) as exc:
            raise OutputConfigurationError(
                f"Cannot stage output version {version}: {exc}"
            ) from exc

        created_at = datetime.now(timezone.utc).isoformat()
        digest = self._sha256(payload)
        snapshot_path = staging_directory / f"content{target.suffix}"
        metadata = {
            "created_at": created_at,
            "restored_from": restored_from,
            "sha256": digest,
            "size_bytes": len(payload),
            "version": version,
        }
        try:
            self._write_bytes_atomically(snapshot_path, payload, "version snapshot")
            self._write_json_atomically(
                staging_directory / "metadata.json",
                metadata,
                "version metadata",
            )
        except OutputConfigurationError:
            provisional = _StagedOutputVersion(
                version=version,
                target=target,
                staging_directory=staging_directory,
                final_directory=final_directory,
                created_at=created_at,
                size_bytes=len(payload),
                sha256=digest,
                restored_from=restored_from,
            )
            self._discard_staged_snapshot(provisional, directory)
            raise

        return _StagedOutputVersion(
            version=version,
            target=target,
            staging_directory=staging_directory,
            final_directory=final_directory,
            created_at=created_at,
            size_bytes=len(payload),
            sha256=digest,
            restored_from=restored_from,
        )

    def _publish_staged_snapshot(
        self, staged: _StagedOutputVersion, directory: Path
    ) -> OutputVersion:
        """Atomically expose a complete staged directory as one immutable version."""

        try:
            root = staged.final_directory.parent.resolve(strict=True)
            staging_directory = staged.staging_directory.resolve(strict=True)
            final_directory = staged.final_directory.resolve(strict=False)
            self._assert_within(root, directory)
            self._assert_within(staging_directory, root)
            self._assert_within(final_directory, root)
            if staged.final_directory.exists():
                raise FileExistsError(staged.final_directory)
            os.rename(staging_directory, staged.final_directory)
        except (OSError, RuntimeError, ValueError) as exc:
            raise OutputConfigurationError(
                f"Cannot publish output version {staged.version}: {exc}"
            ) from exc

        snapshot_path = staged.final_directory / f"content{staged.target.suffix}"
        return OutputVersion(
            version=staged.version,
            path=staged.target,
            snapshot_path=snapshot_path,
            created_at=staged.created_at,
            size_bytes=staged.size_bytes,
            sha256=staged.sha256,
            restored_from=staged.restored_from,
        )

    @staticmethod
    def _version_metadata_values(
        metadata: dict[str, Any], version: int, target_name: str
    ) -> tuple[int, str, str, int | None]:
        if metadata.get("version") != version:
            raise OutputConfigurationError(
                f"Version metadata mismatch for '{target_name}'"
            )
        size_bytes = metadata.get("size_bytes")
        digest = metadata.get("sha256")
        created_at = metadata.get("created_at")
        restored_from = metadata.get("restored_from")
        if (
            not isinstance(size_bytes, int)
            or isinstance(size_bytes, bool)
            or size_bytes < 0
            or not isinstance(digest, str)
            or not re.fullmatch(r"[0-9a-f]{64}", digest)
            or not isinstance(created_at, str)
            or (
                restored_from is not None
                and (
                    isinstance(restored_from, bool)
                    or not isinstance(restored_from, int)
                    or restored_from < 1
                )
            )
        ):
            raise OutputConfigurationError(
                f"Invalid version metadata for '{target_name}'"
            )
        return size_bytes, digest, created_at, restored_from

    def _read_version_metadata(
        self, metadata_path: Path, directory: Path
    ) -> dict[str, Any]:
        try:
            resolved = metadata_path.resolve(strict=True)
            self._assert_within(resolved, directory)
            if not resolved.is_file():
                raise OSError("metadata is not a regular file")
            with resolved.open("r", encoding="utf-8") as handle:
                metadata = json.load(handle)
        except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
            raise OutputConfigurationError(
                f"Cannot read version metadata '{metadata_path.name}': {exc}"
            ) from exc
        if not isinstance(metadata, dict):
            raise OutputConfigurationError(
                f"Version metadata must be a JSON object: {metadata_path}"
            )
        return metadata

    @staticmethod
    def _read_confined_bytes(path: Path, directory: Path) -> bytes:
        try:
            resolved = path.resolve(strict=True)
            OutputManager._assert_within(resolved, directory)
            if not resolved.is_file():
                raise OSError("path is not a regular file")
            return resolved.read_bytes()
        except (OSError, RuntimeError, ValueError) as exc:
            raise OutputConfigurationError(
                f"Cannot read confined output file '{path.name}': {exc}"
            ) from exc

    @classmethod
    def _discard_staged_snapshot(
        cls, staged: _StagedOutputVersion, directory: Path
    ) -> None:
        try:
            root = staged.final_directory.parent.resolve(strict=True)
            if staged.staging_directory.exists():
                cls._remove_version_directory(
                    staged.staging_directory,
                    root,
                    directory,
                )
        except OutputConfigurationError:
            # The original write error is more useful than a cleanup failure.
            pass

    def _rollback_current_file(
        self,
        target: Path,
        previous_data: bytes | None,
        *,
        existed: bool,
    ) -> bool:
        try:
            if existed:
                if previous_data is None:
                    return False
                self._write_bytes_atomically(target, previous_data, "output rollback")
            else:
                target.unlink(missing_ok=True)
            return True
        except (OSError, OutputConfigurationError):
            return False

    @staticmethod
    def _sha256(payload: bytes) -> str:
        return hashlib.sha256(payload).hexdigest()

    def _default_config_path(self) -> Path:
        """Return the conventional per-user configuration file for this OS."""

        home = self._home_directory()
        if sys.platform.startswith("win"):
            base_value = self._environ.get("APPDATA")
            base = (
                self._absolute_path(base_value, "APPDATA", self._cwd)
                if base_value
                else home / "AppData" / "Roaming"
            )
            return (base / "Agent World" / "config.json").resolve(strict=False)

        if sys.platform == "darwin":
            return (
                home / "Library" / "Application Support" / "Agent World" / "config.json"
            ).resolve(strict=False)

        base_value = self._environ.get("XDG_CONFIG_HOME")
        base = (
            self._absolute_path(base_value, "XDG_CONFIG_HOME", self._cwd)
            if base_value
            else home / ".config"
        )
        return (base / "agent-world" / "config.json").resolve(strict=False)

    def _home_directory(self) -> Path:
        """Resolve a home directory while respecting an injected environment."""

        keys = ("USERPROFILE", "HOME") if sys.platform.startswith("win") else ("HOME",)
        for key in keys:
            value = self._environ.get(key)
            if value:
                return self._absolute_path(value, key, self._cwd)
        return Path.home().resolve(strict=False)

    def _prepare_output_directory(self, value: PathInput) -> Path:
        directory = self._absolute_path(value, "output directory", self._cwd)
        try:
            directory.mkdir(parents=True, exist_ok=True)
            directory = directory.resolve(strict=True)
        except (OSError, RuntimeError) as exc:
            raise OutputConfigurationError(
                f"Cannot create output directory '{directory}': {exc}"
            ) from exc

        if not directory.is_dir():
            raise OutputConfigurationError(
                f"Output path is not a directory: {directory}"
            )

        self._validate_writable_directory(directory)
        return directory

    @staticmethod
    def _validate_writable_directory(directory: Path) -> None:
        """Probe directory writability without leaving a generated file behind."""

        try:
            mode = directory.stat().st_mode
            if os.name != "nt" and not mode & (
                stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH
            ):
                raise PermissionError("no write permission bits are set")

            descriptor, probe_name = tempfile.mkstemp(
                prefix=".agent-world-write-test-", dir=directory
            )
            os.close(descriptor)
            Path(probe_name).unlink()
        except OSError as exc:
            raise OutputConfigurationError(
                f"Output directory is not writable: {directory}: {exc}"
            ) from exc

    def _read_config(self) -> dict[str, Any]:
        if not self.config_path.exists():
            return {}

        try:
            with self.config_path.open("r", encoding="utf-8") as config_file:
                config = json.load(config_file)
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise OutputConfigurationError(
                f"Cannot read configuration file '{self.config_path}': {exc}"
            ) from exc

        if not isinstance(config, dict):
            raise OutputConfigurationError(
                f"Configuration file must contain a JSON object: {self.config_path}"
            )
        return config

    def _write_config(self, config: dict[str, Any]) -> None:
        self._write_json_atomically(self.config_path, config, "configuration file")

    @classmethod
    def _write_json_atomically(cls, path: Path, data: Any, description: str) -> None:
        serialized = cls._serialize_json(data, description)
        cls._write_bytes_atomically(path, serialized, description)

    @staticmethod
    def _serialize_json(data: Any, description: str) -> bytes:
        try:
            serialized = json.dumps(
                data,
                ensure_ascii=False,
                allow_nan=False,
                indent=2,
                sort_keys=True,
            )
        except (TypeError, ValueError) as exc:
            raise OutputConfigurationError(
                f"Cannot write {description}: {exc}"
            ) from exc
        return f"{serialized}\n".encode("utf-8")

    @staticmethod
    def _write_bytes_atomically(path: Path, data: bytes, description: str) -> None:
        temporary_path: Path | None = None
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            descriptor, temporary_name = tempfile.mkstemp(
                prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
            )
            temporary_path = Path(temporary_name)
            with os.fdopen(descriptor, "wb") as handle:
                handle.write(data)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary_path, path)
        except OSError as exc:
            if temporary_path is not None:
                try:
                    temporary_path.unlink(missing_ok=True)
                except OSError:
                    pass
            raise OutputConfigurationError(
                f"Cannot write {description} '{path}': {exc}"
            ) from exc

    @classmethod
    def _safe_relative_filename(cls, filename: PathInput) -> Path:
        return cls._safe_relative_path(filename, "output filename")

    @classmethod
    def _safe_relative_path(cls, value: PathInput, label: str) -> Path:
        try:
            raw_value = os.fspath(value)
        except TypeError as exc:
            raise OutputConfigurationError(
                f"{label.capitalize()} must be path-like"
            ) from exc

        if not isinstance(raw_value, str) or not raw_value.strip():
            raise OutputConfigurationError(
                f"{label.capitalize()} must be a non-empty string"
            )
        if "\x00" in raw_value:
            raise OutputConfigurationError(f"{label.capitalize()} contains a null byte")

        posix_path = PurePosixPath(raw_value)
        windows_path = PureWindowsPath(raw_value)
        if posix_path.is_absolute() or windows_path.is_absolute():
            raise OutputConfigurationError(f"Absolute {label.lower()}s are not allowed")
        if windows_path.drive:
            raise OutputConfigurationError(
                f"Drive-relative {label.lower()}s are not allowed"
            )
        if ".." in posix_path.parts or ".." in windows_path.parts:
            raise OutputConfigurationError("Output path traversal is not allowed")
        parts = {
            part
            for part in (*posix_path.parts, *windows_path.parts)
            if part not in {"", "."}
        }
        for part in parts:
            cls._validate_portable_path_component(part, label)

        return Path(raw_value)

    @classmethod
    def _validate_portable_path_component(cls, part: str, label: str) -> None:
        """Reject aliases and device names interpreted specially by Windows."""

        if part.endswith((" ", ".")):
            raise OutputConfigurationError(
                f"{label.capitalize()} components cannot end with a dot or space"
            )
        if any(
            ord(character) < 32 or character in cls._WINDOWS_INVALID_CHARACTERS
            for character in part
        ):
            raise OutputConfigurationError(
                f"{label.capitalize()} contains Windows-unsafe characters"
            )

        folded = part.casefold()
        if folded == cls.VERSION_DIRECTORY.casefold():
            raise OutputConfigurationError(
                f"'{cls.VERSION_DIRECTORY}' is reserved for output history"
            )
        device_stem = folded.split(".", 1)[0]
        if device_stem in cls._WINDOWS_RESERVED_NAMES:
            raise OutputConfigurationError(
                f"{label.capitalize()} contains a reserved Windows name"
            )

    @staticmethod
    def _comparison_path(path: Path) -> str:
        """Normalize a resolved path for stable cross-platform comparisons."""

        normalized = os.path.normcase(os.path.abspath(os.fspath(path)))
        if os.name == "nt":
            # Concurrent Windows resolutions may inconsistently add the
            # extended-length namespace. It does not change path identity.
            if normalized.startswith("\\\\?\\unc\\"):
                normalized = "\\\\" + normalized[8:]
            elif normalized.startswith("\\\\?\\"):
                normalized = normalized[4:]
            normalized = normalized.casefold()
        return os.path.normpath(normalized)

    @classmethod
    def _assert_within(cls, path: Path, directory: Path) -> None:
        candidate = cls._comparison_path(path)
        root = cls._comparison_path(directory)
        if os.path.commonpath((root, candidate)) != root:
            raise ValueError(f"{path} is outside {directory}")

    @classmethod
    def _same_path(cls, first: Path, second: Path) -> bool:
        return cls._comparison_path(first) == cls._comparison_path(second)

    @staticmethod
    def _absolute_path(value: PathInput, label: str, base: Path) -> Path:
        try:
            raw_value = os.fspath(value)
        except TypeError as exc:
            message = f"{label.capitalize()} must be path-like"
            raise OutputConfigurationError(message) from exc

        if not isinstance(raw_value, str) or not raw_value.strip():
            raise OutputConfigurationError(
                f"{label.capitalize()} must be a non-empty path"
            )

        try:
            path = Path(raw_value).expanduser()
            if not path.is_absolute():
                path = base / path
            return path.resolve(strict=False)
        except (OSError, RuntimeError, ValueError) as exc:
            raise OutputConfigurationError(
                f"Cannot resolve {label} '{raw_value}': {exc}"
            ) from exc
