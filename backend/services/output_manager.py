"""Manage the directory used for generated files.

The output directory is selected in this order: a one-shot override, the
persisted user preference, ``OUTPUT_DIR``, then ``outputs`` below the current
working directory.  The user preference lives in the platform's conventional
configuration directory unless ``AGENT_WORLD_CONFIG_FILE`` overrides it.
"""

from __future__ import annotations

import json
import os
import stat
import sys
import tempfile
from collections.abc import Mapping
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any

PathInput = str | os.PathLike[str]


class OutputConfigurationError(RuntimeError):
    """Raised when output configuration or a requested output path is unsafe."""


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

    def resolve_output_path(
        self,
        filename: PathInput,
        output_dir: PathInput | None = None,
    ) -> Path:
        """Resolve ``filename`` below the selected directory without escapes.

        Absolute filenames and every explicit ``..`` component are rejected.
        Resolution follows existing symlinks before containment is checked, so
        a symlink cannot redirect a generated file outside the output tree.
        """

        relative_path = self._safe_relative_filename(filename)
        directory = self.get_output_directory(output_dir)

        try:
            target = (directory / relative_path).resolve(strict=False)
            target.relative_to(directory)
        except (OSError, RuntimeError, ValueError) as exc:
            raise OutputConfigurationError(
                f"Output path escapes the configured directory: {filename!s}"
            ) from exc

        if target == directory:
            raise OutputConfigurationError("An output filename is required")
        if target.exists() and not target.is_file():
            raise OutputConfigurationError(
                f"Output path is not a regular file: {target}"
            )

        return target

    def write_json(
        self,
        filename: PathInput,
        data: Any,
        output_dir: PathInput | None = None,
    ) -> Path:
        """Atomically write UTF-8 JSON and return its absolute path."""

        target = self.resolve_output_path(filename, output_dir)
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise OutputConfigurationError(
                f"Cannot create output subdirectory '{target.parent}': {exc}"
            ) from exc

        # Re-resolve after creating parents to catch a concurrently introduced
        # or pre-existing symlink before opening a temporary file there.
        target = self.resolve_output_path(filename, output_dir)
        self._write_json_atomically(target, data, "output file")
        return target

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

    @staticmethod
    def _write_json_atomically(path: Path, data: Any, description: str) -> None:
        temporary_path: Path | None = None
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            descriptor, temporary_name = tempfile.mkstemp(
                prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
            )
            temporary_path = Path(temporary_name)
            with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
                json.dump(
                    data,
                    handle,
                    ensure_ascii=False,
                    allow_nan=False,
                    indent=2,
                    sort_keys=True,
                )
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary_path, path)
        except (OSError, TypeError, ValueError) as exc:
            if temporary_path is not None:
                try:
                    temporary_path.unlink(missing_ok=True)
                except OSError:
                    pass
            raise OutputConfigurationError(
                f"Cannot write {description} '{path}': {exc}"
            ) from exc

    @staticmethod
    def _safe_relative_filename(filename: PathInput) -> Path:
        try:
            raw_filename = os.fspath(filename)
        except TypeError as exc:
            raise OutputConfigurationError("Output filename must be path-like") from exc

        if not isinstance(raw_filename, str) or not raw_filename.strip():
            raise OutputConfigurationError("Output filename must be a non-empty string")
        if "\x00" in raw_filename:
            raise OutputConfigurationError("Output filename contains a null byte")

        posix_path = PurePosixPath(raw_filename)
        windows_path = PureWindowsPath(raw_filename)
        if posix_path.is_absolute() or windows_path.is_absolute():
            raise OutputConfigurationError("Absolute output filenames are not allowed")
        if ".." in posix_path.parts or ".." in windows_path.parts:
            raise OutputConfigurationError("Output path traversal is not allowed")

        return Path(raw_filename)

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
