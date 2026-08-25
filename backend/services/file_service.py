"""Secure catalogue, sharing, cleanup, and preview operations for files."""

from __future__ import annotations

import hashlib
import html
import io
import json
import os
import re
import secrets
import tempfile
import threading
import unicodedata
import uuid
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any, BinaryIO, Callable, ClassVar, Iterator, cast

from ..models.agent import Agent
from ..models.base import db
from ..models.execution import Execution
from ..models.generated_file import (
    FileShare,
    FileVersion,
    GeneratedFile,
    SharePermission,
)
from ..models.user import User
from .output_manager import OutputConfigurationError, OutputManager


class FileServiceError(RuntimeError):
    """Base class for errors that can safely be returned by the file API."""

    status_code = 400
    error_code = "file_error"

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class FileValidationError(FileServiceError):
    """A supplied file value is invalid."""

    error_code = "invalid_file"


class ManagedFileNotFoundError(FileServiceError):
    """A managed file, version, or share was not found."""

    status_code = 404
    error_code = "not_found"


class FileAccessDeniedError(FileServiceError):
    """A valid capability does not grant the requested operation."""

    status_code = 403
    error_code = "forbidden"


class FileAuthenticationRequiredError(FileServiceError):
    """A recipient-constrained share requires an authenticated identity."""

    status_code = 401
    error_code = "authentication_required"


class FileConflictError(FileServiceError):
    """The catalogue and physical storage no longer agree."""

    status_code = 409
    error_code = "file_conflict"


class UnsupportedPreviewError(FileServiceError):
    """The requested file cannot be safely previewed."""

    status_code = 415
    error_code = "unsupported_preview"


class InvalidJsonPreviewError(FileServiceError):
    """A catalogued JSON file contains invalid JSON."""

    status_code = 422
    error_code = "invalid_json"


class PreviewTooLargeError(FileServiceError):
    """A file is larger than the configured preview limit."""

    status_code = 413
    error_code = "preview_too_large"


class FileService:
    """Manage generated files without accepting physical paths from callers."""

    FORMATS = {
        "json": ("json", "application/json"),
        "md": ("md", "text/markdown"),
        "markdown": ("md", "text/markdown"),
        "txt": ("txt", "text/plain"),
        "text": ("txt", "text/plain"),
    }
    TOKEN_PATTERN = re.compile(r"^[A-Za-z0-9_-]{43}$")
    CLEANUP_POLICY_FILENAME = ".agent-world-cleanup-policy.json"
    CLEANUP_LOCK_FILENAME = ".agent-world-cleanup.lock"
    _named_locks: ClassVar[dict[str, threading.RLock]] = {}
    _named_locks_guard: ClassVar[threading.Lock] = threading.Lock()

    def __init__(
        self,
        output_manager: OutputManager | None = None,
        output_dir: str | os.PathLike[str] | None = None,
        preview_max_bytes: int = 1024 * 1024,
        write_max_bytes: int = 1024 * 1024,
        share_default_ttl_seconds: int = 7 * 24 * 60 * 60,
        share_max_ttl_seconds: int = 30 * 24 * 60 * 60,
        cleanup_enabled: bool = False,
        cleanup_interval_seconds: int = 24 * 60 * 60,
        temporary_ttl_hours: int = 24,
        obsolete_ttl_days: int = 30,
        keep_latest_versions: int = 3,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self.output_manager = output_manager or OutputManager()
        self.output_dir = output_dir
        self.preview_max_bytes = self._positive_int(
            preview_max_bytes, "preview_max_bytes"
        )
        self.write_max_bytes = self._positive_int(write_max_bytes, "write_max_bytes")
        self.share_default_ttl_seconds = self._positive_int(
            share_default_ttl_seconds, "share_default_ttl_seconds"
        )
        self.share_max_ttl_seconds = self._positive_int(
            share_max_ttl_seconds, "share_max_ttl_seconds"
        )
        if self.share_default_ttl_seconds > self.share_max_ttl_seconds:
            raise ValueError("Default share lifetime exceeds its maximum")
        self.cleanup_enabled = bool(cleanup_enabled)
        self.cleanup_interval_seconds = self._positive_int(
            cleanup_interval_seconds, "cleanup_interval_seconds"
        )
        self.temporary_ttl_hours = self._positive_int(
            temporary_ttl_hours, "temporary_ttl_hours"
        )
        self.obsolete_ttl_days = self._positive_int(
            obsolete_ttl_days, "obsolete_ttl_days"
        )
        self.keep_latest_versions = self._positive_int(
            keep_latest_versions, "keep_latest_versions"
        )
        self._clock = clock or datetime.utcnow
        self._last_cleanup_at: datetime | None = None
        self._cleanup_lock = threading.Lock()
        policy_root = self.output_manager.get_output_directory(override=self.output_dir)
        self._cleanup_policy_path = policy_root / self.CLEANUP_POLICY_FILENAME
        self._cleanup_lock_path = policy_root / self.CLEANUP_LOCK_FILENAME
        try:
            self._refresh_cleanup_policy_unlocked()
        except FileServiceError:
            # A malformed optional preference must not prevent the application
            # from starting. Administrative policy reads still report it and a
            # subsequent valid update repairs it atomically.
            pass

    @staticmethod
    def _positive_int(value: Any, label: str) -> int:
        if isinstance(value, bool) or not isinstance(value, int) or value < 1:
            raise ValueError(f"{label} must be a positive integer")
        return value

    @classmethod
    def _identifier(cls, value: Any, label: str) -> int:
        try:
            return cls._positive_int(value, label)
        except ValueError as exc:
            raise FileValidationError(str(exc)) from exc

    @staticmethod
    def hash_token(token: str) -> str:
        """Hash a high-entropy capability token for persistent storage."""

        return hashlib.sha256(token.encode("utf-8")).hexdigest()

    def cleanup_policy(self) -> dict[str, Any]:
        """Return the active cleanup policy."""

        with self._advisory_guard(self._cleanup_lock_path, blocking=True) as acquired:
            if not acquired:  # pragma: no cover - blocking locks always acquire
                raise FileConflictError("Cleanup policy is currently locked")
            self._refresh_cleanup_policy_unlocked()
            return self._cleanup_policy_snapshot()

    def _cleanup_policy_snapshot(self) -> dict[str, Any]:
        return {
            "enabled": self.cleanup_enabled,
            "interval_seconds": self.cleanup_interval_seconds,
            "temporary_ttl_hours": self.temporary_ttl_hours,
            "obsolete_ttl_days": self.obsolete_ttl_days,
            "keep_latest_versions": self.keep_latest_versions,
            "last_run_at": (
                self._last_cleanup_at.isoformat() if self._last_cleanup_at else None
            ),
        }

    def update_cleanup_policy(self, values: dict[str, Any]) -> dict[str, Any]:
        """Validate and durably update the cleanup policy as one operation."""

        if not isinstance(values, dict):
            raise FileValidationError("Cleanup policy must be a JSON object")
        allowed = {
            "enabled",
            "interval_seconds",
            "temporary_ttl_hours",
            "obsolete_ttl_days",
            "keep_latest_versions",
        }
        unknown = set(values) - allowed
        if unknown:
            raise FileValidationError(f"Unknown cleanup setting: {sorted(unknown)[0]}")

        validated: dict[str, Any] = {}
        if "enabled" in values:
            if not isinstance(values["enabled"], bool):
                raise FileValidationError("enabled must be a boolean")
            validated["enabled"] = values["enabled"]
        for key in allowed - {"enabled"}:
            if key in values:
                try:
                    validated[key] = self._positive_int(values[key], key)
                except ValueError as exc:
                    raise FileValidationError(str(exc)) from exc

        with self._advisory_guard(self._cleanup_lock_path, blocking=True) as acquired:
            if not acquired:  # pragma: no cover - blocking locks always acquire
                raise FileConflictError("Cleanup policy is currently locked")
            try:
                self._refresh_cleanup_policy_unlocked()
            except FileConflictError:
                # A valid full write is the recovery path for corrupted policy
                # state. Keep the validated constructor defaults for omitted
                # settings instead of partially applying corrupt data.
                pass
            state = self._cleanup_policy_snapshot()
            state.update(validated)
            self._write_cleanup_policy_unlocked(state)
            self._apply_cleanup_policy_state(state)
            return self._cleanup_policy_snapshot()

    def create_file(
        self,
        *,
        agent_id: int,
        logical_name: str,
        file_format: str,
        content: Any,
        execution_id: int | None = None,
        created_by: int | None = None,
        is_temporary: bool = False,
        expires_at: datetime | None = None,
        output_dir: str | os.PathLike[str] | None = None,
        agent_name: str | None = None,
        output_layout: str | None = None,
    ) -> tuple[GeneratedFile, str]:
        """Create a catalogued file and its first immutable version."""

        agent_id = self._identifier(agent_id, "agent_id")
        agent = db.session.get(Agent, agent_id)
        if agent is None:
            raise FileValidationError("Agent does not exist")
        self._validate_execution(execution_id, agent_id)
        self._validate_user(created_by, "Creator")
        name = self._validate_logical_name(logical_name)
        normalized_format, mime_type = self._normalize_format(file_format)
        self._validate_current_filename(name, normalized_format)
        payload = self._serialize_content(normalized_format, content)
        if (
            GeneratedFile.query.filter_by(agent_id=agent_id, logical_name=name).first()
            is not None
        ):
            raise FileConflictError(
                "A file with this name already exists for the agent"
            )

        management_token = secrets.token_urlsafe(32)
        selected_output_dir = self.output_dir if output_dir is None else output_dir
        try:
            root = self.output_manager.get_agent_output_directory(
                agent_id,
                agent.name if agent_name is None else agent_name,
                output_dir=selected_output_dir,
                output_layout=output_layout,
            )
        except OutputConfigurationError as exc:
            raise FileValidationError("Output directory is invalid") from exc
        generated_file = GeneratedFile(
            agent_id=agent_id,
            execution_id=execution_id,
            created_by=created_by,
            logical_name=name,
            file_format=normalized_format,
            mime_type=mime_type,
            storage_key=str(uuid.uuid4()),
            storage_root=str(root),
            current_version=0,
            size_bytes=0,
            sha256="",
            management_token_hash=self.hash_token(management_token),
            is_temporary=bool(is_temporary),
            expires_at=expires_at,
        )
        db.session.add(generated_file)
        try:
            db.session.flush()
            self._append_bytes(
                generated_file,
                payload,
                created_by=created_by,
                execution_id=execution_id,
            )
        except Exception:
            db.session.rollback()
            raise
        self._run_cleanup_after_write()
        return generated_file, management_token

    def save_execution_output(
        self,
        *,
        agent_id: int,
        execution_id: int,
        logical_name: str,
        file_format: str,
        content: Any,
        created_by: int | None = None,
        is_temporary: bool = False,
        output_dir: str | os.PathLike[str] | None = None,
        output_layout: str | None = None,
    ) -> tuple[GeneratedFile, str | None]:
        """Create or append one trusted execution output.

        The physical root uses the same stable per-agent layout as the CLI.
        A raw management capability is returned only for the first creation;
        subsequent trusted appends return ``None`` because raw tokens are never
        persisted.
        """

        normalized_agent_id = self._identifier(agent_id, "agent_id")
        agent = db.session.get(Agent, normalized_agent_id)
        if agent is None:
            raise FileValidationError("Agent does not exist")
        name = self._validate_logical_name(logical_name)
        normalized_format, _ = self._normalize_format(file_format)
        self._validate_current_filename(name, normalized_format)
        selected_output_dir = self.output_dir if output_dir is None else output_dir
        try:
            expected_root = self.output_manager.get_agent_output_directory(
                normalized_agent_id,
                agent.name,
                output_dir=selected_output_dir,
                output_layout=output_layout,
            )
        except OutputConfigurationError as exc:
            raise FileValidationError("Output directory is invalid") from exc

        existing = GeneratedFile.query.filter_by(
            agent_id=normalized_agent_id, logical_name=name
        ).first()
        if existing is None:
            return self.create_file(
                agent_id=normalized_agent_id,
                execution_id=execution_id,
                logical_name=name,
                file_format=normalized_format,
                content=content,
                created_by=created_by,
                is_temporary=is_temporary,
                output_dir=selected_output_dir,
                agent_name=agent.name,
                output_layout=output_layout,
            )

        if existing.file_format != normalized_format:
            raise FileConflictError("Existing file format does not match")
        try:
            actual_root = Path(existing.storage_root).resolve(strict=True)
        except OSError as exc:
            raise FileConflictError("Managed storage is unavailable") from exc
        if actual_root != expected_root.resolve(strict=True):
            raise FileConflictError("Existing file uses a different output layout")
        self._validate_execution(execution_id, normalized_agent_id)
        self._validate_user(created_by, "Creator")
        payload = self._serialize_content(normalized_format, content)
        self._append_bytes(
            existing,
            payload,
            created_by=created_by,
            execution_id=execution_id,
        )
        self._run_cleanup_after_write()
        return existing, None

    def get_file_by_agent_name(
        self, agent_id: int, logical_name: str
    ) -> GeneratedFile:
        """Trusted lookup used by non-HTTP integrations such as the CLI."""

        normalized_agent_id = self._identifier(agent_id, "agent_id")
        name = self._validate_logical_name(logical_name)
        generated_file = GeneratedFile.query.filter_by(
            agent_id=normalized_agent_id, logical_name=name
        ).first()
        if generated_file is None:
            raise ManagedFileNotFoundError("File not found")
        return generated_file

    def list_versions_trusted(
        self, agent_id: int, logical_name: str
    ) -> list[FileVersion]:
        """List versions for a trusted backend caller without a capability."""

        generated_file = self.get_file_by_agent_name(agent_id, logical_name)
        return sorted(
            generated_file.versions, key=lambda item: item.version, reverse=True
        )

    def restore_version_trusted(
        self, agent_id: int, logical_name: str, version: int
    ) -> FileVersion:
        """Restore a version for a trusted backend caller."""

        generated_file = self.get_file_by_agent_name(agent_id, logical_name)
        restored = self._restore_generated_file(generated_file, version)
        self._run_cleanup_after_write()
        return restored

    def list_files(
        self, agent_id: int, management_token: str | None
    ) -> list[GeneratedFile]:
        """List catalogue entries covered by a capability for one agent.

        Management tokens are file-scoped, so this deliberately returns only
        the matching entry rather than treating one token as agent-wide access.
        """

        normalized_agent_id = self._identifier(agent_id, "agent_id")
        supplied_hash = (
            self.hash_token(management_token)
            if isinstance(management_token, str) and management_token
            else ""
        )
        generated_file = GeneratedFile.query.filter_by(
            agent_id=normalized_agent_id,
            management_token_hash=supplied_hash,
        ).first()
        if generated_file is None:
            raise FileAccessDeniedError("A valid management token is required")
        return [generated_file]

    def get_file(
        self, file_id: int, management_token: str | None = None
    ) -> GeneratedFile:
        """Load a file and optionally enforce its management capability."""

        file_id = self._identifier(file_id, "file_id")
        generated_file = GeneratedFile.get_by_id(file_id)
        if generated_file is None:
            raise ManagedFileNotFoundError("File not found")
        if management_token is not None:
            self.require_management_token(generated_file, management_token)
        return generated_file

    def require_management_token(
        self, generated_file: GeneratedFile, token: str | None
    ) -> None:
        """Require the unguessable token issued when the file was created."""

        supplied_hash = self.hash_token(token) if isinstance(token, str) else ""
        if not supplied_hash or not secrets.compare_digest(
            supplied_hash, generated_file.management_token_hash
        ):
            raise FileAccessDeniedError("A valid management token is required")

    def list_versions(self, file_id: int, management_token: str) -> list[FileVersion]:
        """List immutable versions, newest first."""

        generated_file = self.get_file(file_id, management_token)
        return sorted(
            generated_file.versions, key=lambda item: item.version, reverse=True
        )

    def append_version(
        self,
        file_id: int,
        content: Any,
        *,
        management_token: str | None = None,
        share_token: str | None = None,
        created_by: int | None = None,
        execution_id: int | None = None,
    ) -> FileVersion:
        """Append content using either management or write-share authority."""

        if share_token is not None:
            share = self.resolve_share(share_token, require_write=True)
            if share.generated_file_id != file_id:
                raise ManagedFileNotFoundError("Share not found")
            generated_file = cast(GeneratedFile, share.generated_file)
        else:
            generated_file = self.get_file(file_id)
            self.require_management_token(generated_file, management_token)
            share = None

        self._validate_execution(execution_id, generated_file.agent_id)
        self._validate_user(created_by, "Creator")
        payload = self._serialize_content(generated_file.file_format, content)
        version = self._append_bytes(
            generated_file,
            payload,
            created_by=created_by,
            execution_id=execution_id,
        )
        if share is not None:
            self._touch(generated_file, share)
        self._run_cleanup_after_write()
        return version

    def restore_version(
        self, file_id: int, version: int, management_token: str
    ) -> FileVersion:
        """Restore by appending a snapshot; historical rows remain immutable."""

        generated_file = self.get_file(file_id, management_token)
        restored = self._restore_generated_file(generated_file, version)
        self._run_cleanup_after_write()
        return restored

    def _restore_generated_file(
        self, generated_file: GeneratedFile, version: int
    ) -> FileVersion:
        with self._file_operation_guard(generated_file) as acquired:
            if not acquired:  # pragma: no cover - blocking locks always acquire
                raise FileConflictError("File is currently being modified")
            db.session.refresh(generated_file)
            source = self._get_version(generated_file, version)
            payload = self._read_version_bytes(generated_file, source)
            restored = self._append_bytes_locked(
                generated_file,
                payload,
                created_by=generated_file.created_by,
                execution_id=None,
                restored_from_version_id=source.id,
            )
        return restored

    def create_share(
        self,
        file_id: int,
        management_token: str,
        *,
        permission: str = SharePermission.READ.value,
        expires_in_seconds: int | None = None,
        recipient_user_id: int | None = None,
        created_by: int | None = None,
    ) -> tuple[FileShare, str]:
        """Create an expiring capability and return its raw token once."""

        generated_file = self.get_file(file_id, management_token)
        try:
            normalized_permission = SharePermission(permission).value
        except (TypeError, ValueError) as exc:
            raise FileValidationError("permission must be read or write") from exc
        ttl = (
            self.share_default_ttl_seconds
            if expires_in_seconds is None
            else expires_in_seconds
        )
        try:
            ttl = self._positive_int(ttl, "expires_in_seconds")
        except ValueError as exc:
            raise FileValidationError(str(exc)) from exc
        if ttl > self.share_max_ttl_seconds:
            raise FileValidationError("Share lifetime exceeds the configured maximum")
        self._validate_user(recipient_user_id, "Recipient")
        self._validate_user(created_by, "Creator")

        raw_token = secrets.token_urlsafe(32)
        share = FileShare(
            generated_file_id=generated_file.id,
            created_by=created_by,
            recipient_user_id=recipient_user_id,
            permission=normalized_permission,
            token_hash=self.hash_token(raw_token),
            expires_at=self._clock() + timedelta(seconds=ttl),
        )
        db.session.add(share)
        db.session.commit()
        return share, raw_token

    def list_shares(self, file_id: int, management_token: str) -> list[FileShare]:
        """Return all shares without ever returning their token hashes."""

        generated_file = self.get_file(file_id, management_token)
        return sorted(generated_file.shares, key=lambda item: item.created_at)

    def revoke_share(
        self, file_id: int, share_id: int, management_token: str
    ) -> FileShare:
        """Revoke a share while retaining its audit metadata."""

        generated_file = self.get_file(file_id, management_token)
        share_id = self._identifier(share_id, "share_id")
        share = db.session.get(FileShare, share_id)
        if share is None or share.generated_file_id != generated_file.id:
            raise ManagedFileNotFoundError("Share not found")
        if share.revoked_at is None:
            share.revoked_at = self._clock()
            db.session.commit()
        return share

    def resolve_share(self, raw_token: str, require_write: bool = False) -> FileShare:
        """Resolve a non-revoked, unexpired share without leaking its state."""

        if not isinstance(raw_token, str) or not self.TOKEN_PATTERN.fullmatch(
            raw_token
        ):
            # Perform the same local digest work as a well-formed token.
            self.hash_token(str(raw_token))
            raise ManagedFileNotFoundError("Share not found")
        share = FileShare.query.filter_by(token_hash=self.hash_token(raw_token)).first()
        now = self._clock()
        if share is None or share.revoked_at is not None or share.expires_at <= now:
            raise ManagedFileNotFoundError("Share not found")
        if require_write and share.permission != SharePermission.WRITE.value:
            raise FileAccessDeniedError("This share is read-only")
        return share

    @classmethod
    def require_share_recipient(
        cls, share: FileShare, authenticated_user_id: int | None
    ) -> None:
        """Enforce the optional recipient attached to a capability link."""

        if share.recipient_user_id is None:
            return
        if authenticated_user_id is None:
            raise FileAuthenticationRequiredError(
                "This share requires an authenticated recipient"
            )
        user_id = cls._identifier(authenticated_user_id, "authenticated_user_id")
        if user_id != share.recipient_user_id:
            raise FileAccessDeniedError(
                "This share is restricted to a different recipient"
            )

    def preview_file(
        self,
        file_id: int,
        management_token: str,
        version: int | None = None,
    ) -> dict[str, Any]:
        """Return a bounded, safe preview using management authority."""

        generated_file = self.get_file(file_id, management_token)
        preview = self._preview(generated_file, version)
        self._touch(generated_file)
        return preview

    def preview_share(
        self, raw_token: str, version: int | None = None
    ) -> dict[str, Any]:
        """Return a preview using a read or write share capability."""

        share = self.resolve_share(raw_token)
        generated_file = cast(GeneratedFile, share.generated_file)
        preview = self._preview(generated_file, version)
        self._touch(generated_file, share)
        return preview

    def download_file(
        self,
        file_id: int,
        management_token: str,
        version: int | None = None,
    ) -> tuple[Path, GeneratedFile, FileVersion]:
        """Resolve and integrity-check a managed download."""

        generated_file = self.get_file(file_id, management_token)
        result = self._download(generated_file, version)
        self._touch(generated_file)
        return result

    def download_share(
        self, raw_token: str, version: int | None = None
    ) -> tuple[Path, GeneratedFile, FileVersion]:
        """Resolve and integrity-check a shared download."""

        share = self.resolve_share(raw_token)
        generated_file = cast(GeneratedFile, share.generated_file)
        result = self._download(generated_file, version)
        self._touch(generated_file, share)
        return result

    def download_file_stream(
        self,
        file_id: int,
        management_token: str,
        version: int | None = None,
    ) -> tuple[io.BytesIO, GeneratedFile, FileVersion]:
        """Return one integrity-checked in-memory snapshot for an HTTP response."""

        generated_file = self.get_file(file_id, management_token)
        selected = self._get_version(generated_file, version)
        payload = self._read_version_bytes(generated_file, selected)
        self._touch(generated_file)
        return io.BytesIO(payload), generated_file, selected

    def download_share_stream(
        self, raw_token: str
    ) -> tuple[io.BytesIO, GeneratedFile, FileVersion]:
        """Return a shared current snapshot without reopening a verified path."""

        share = self.resolve_share(raw_token)
        generated_file = cast(GeneratedFile, share.generated_file)
        selected = self._get_version(generated_file, None)
        payload = self._read_version_bytes(generated_file, selected)
        self._touch(generated_file, share)
        return io.BytesIO(payload), generated_file, selected

    @staticmethod
    def download_name(generated_file: GeneratedFile) -> str:
        """Return a display-only filename with the catalogued extension."""

        return FileService._current_filename(
            generated_file.logical_name, generated_file.file_format
        )

    def cleanup(
        self, *, dry_run: bool = True, now: datetime | None = None
    ) -> dict[str, Any]:
        """Clean only catalogued temporary files and obsolete versions."""

        current_time = now or self._clock()
        self._cleanup_lock.acquire()
        try:
            with self._advisory_guard(
                self._cleanup_lock_path, blocking=True
            ) as acquired:
                if not acquired:  # pragma: no cover - blocking locks always acquire
                    raise FileConflictError("Cleanup is currently running")
                self._refresh_cleanup_policy_unlocked()
                report = self._cleanup_catalogue(
                    dry_run=bool(dry_run), current_time=current_time
                )
                if not dry_run:
                    state = self._cleanup_policy_snapshot()
                    state["last_run_at"] = current_time.isoformat()
                    self._write_cleanup_policy_unlocked(state)
                    self._apply_cleanup_policy_state(state)
                return report
        finally:
            self._cleanup_lock.release()

    def _cleanup_catalogue(
        self, *, dry_run: bool, current_time: datetime
    ) -> dict[str, Any]:
        """Run one cleanup pass while the global cleanup lease is held."""

        temp_cutoff = current_time - timedelta(hours=self.temporary_ttl_hours)
        obsolete_cutoff = current_time - timedelta(days=self.obsolete_ttl_days)
        report: dict[str, Any] = {
            "dry_run": dry_run,
            "candidates": 0,
            "deleted": 0,
            "bytes_reclaimed": 0,
            "skipped": 0,
            "errors": [],
        }

        file_ids = [item.id for item in GeneratedFile.query.all()]
        for file_id in file_ids:
            generated_file = db.session.get(GeneratedFile, file_id)
            if generated_file is None:
                continue
            with self._file_operation_guard(generated_file) as acquired:
                if not acquired:  # pragma: no cover - blocking locks always acquire
                    report["skipped"] += 1
                    continue
                db.session.refresh(generated_file)
                versions = sorted(
                    generated_file.versions,
                    key=lambda item: item.version,
                    reverse=True,
                )
                has_active_share = any(
                    share.revoked_at is None and share.expires_at > current_time
                    for share in generated_file.shares
                )
                temporary_expired = generated_file.is_temporary and (
                    (
                        generated_file.expires_at is not None
                        and generated_file.expires_at <= current_time
                    )
                    or generated_file.created_at <= temp_cutoff
                )
                if temporary_expired:
                    if generated_file.pinned or has_active_share:
                        report["skipped"] += len(versions)
                        continue
                    self._cleanup_versions(
                        generated_file,
                        versions,
                        report,
                        dry_run=dry_run,
                        delete_file_record=True,
                    )
                    continue

                if generated_file.pinned:
                    continue
                protected = {item.id for item in versions[: self.keep_latest_versions]}
                current = next(
                    (
                        item
                        for item in versions
                        if item.version == generated_file.current_version
                    ),
                    None,
                )
                if current is not None:
                    protected.add(current.id)
                obsolete = [
                    item
                    for item in versions
                    if item.id not in protected and item.created_at <= obsolete_cutoff
                ]
                self._cleanup_versions(
                    generated_file,
                    obsolete,
                    report,
                    dry_run=dry_run,
                    delete_file_record=False,
                )

        return report

    def run_if_due(self, now: datetime | None = None) -> dict[str, Any]:
        """Claim and run automatic cleanup at most once across workers."""

        current_time = now or self._clock()
        if not self._cleanup_lock.acquire(blocking=False):
            return {"ran": False, "reason": "already_running"}
        try:
            with self._advisory_guard(
                self._cleanup_lock_path, blocking=False
            ) as acquired:
                if not acquired:
                    return {"ran": False, "reason": "already_running"}
                self._refresh_cleanup_policy_unlocked()
                if not self.cleanup_enabled:
                    return {"ran": False, "reason": "disabled"}
                if self._last_cleanup_at is not None:
                    due_at = self._last_cleanup_at + timedelta(
                        seconds=self.cleanup_interval_seconds
                    )
                    if current_time < due_at:
                        return {"ran": False, "reason": "not_due"}
                report = self._cleanup_catalogue(
                    dry_run=False, current_time=current_time
                )
                state = self._cleanup_policy_snapshot()
                state["last_run_at"] = current_time.isoformat()
                self._write_cleanup_policy_unlocked(state)
                self._apply_cleanup_policy_state(state)
                return {"ran": True, **report}
        finally:
            self._cleanup_lock.release()

    def _run_cleanup_after_write(self) -> None:
        try:
            self.run_if_due()
        except Exception:
            # A committed user write must not be reported as failed because a
            # best-effort retention pass encountered an unrelated file.
            db.session.rollback()

    def _append_bytes(
        self,
        generated_file: GeneratedFile,
        payload: bytes,
        *,
        created_by: int | None,
        execution_id: int | None,
        restored_from_version_id: int | None = None,
    ) -> FileVersion:
        with self._file_operation_guard(generated_file) as acquired:
            if not acquired:  # pragma: no cover - blocking locks always acquire
                raise FileConflictError("File is currently being modified")
            if generated_file.id is not None:
                db.session.refresh(generated_file)
            return self._append_bytes_locked(
                generated_file,
                payload,
                created_by=created_by,
                execution_id=execution_id,
                restored_from_version_id=restored_from_version_id,
            )

    def _append_bytes_locked(
        self,
        generated_file: GeneratedFile,
        payload: bytes,
        *,
        created_by: int | None,
        execution_id: int | None,
        restored_from_version_id: int | None = None,
    ) -> FileVersion:
        """Append while the logical file's process and filesystem lock is held."""

        current_target = self._resolve_current_target(generated_file)
        previous_current: bytes | None = None
        if current_target.exists():
            try:
                previous_current = current_target.read_bytes()
            except OSError as exc:
                raise FileConflictError("Current output cannot be read") from exc
            if generated_file.current_version < 1:
                raise FileConflictError("Current output path is already occupied")
            self._verify_payload(previous_current, generated_file.sha256)

        next_version = generated_file.current_version + 1
        relative_path = self._version_relative_path(generated_file, next_version)
        target = self._resolve_target_for_write(generated_file, relative_path)
        self._atomic_write_new(target, payload)
        try:
            self._atomic_replace_file(current_target, payload)
        except Exception:
            target.unlink(missing_ok=True)
            raise
        digest = hashlib.sha256(payload).hexdigest()
        version = FileVersion(
            generated_file_id=generated_file.id,
            version=next_version,
            relative_path=relative_path,
            size_bytes=len(payload),
            sha256=digest,
            created_by=created_by,
            execution_id=execution_id,
            restored_from_version_id=restored_from_version_id,
        )
        generated_file.current_version = next_version
        generated_file.size_bytes = len(payload)
        generated_file.sha256 = digest
        generated_file.updated_at = self._clock()
        db.session.add(version)
        try:
            db.session.commit()
        except Exception as commit_error:
            db.session.rollback()
            try:
                target.unlink(missing_ok=True)
            except OSError:
                pass
            try:
                if previous_current is None:
                    current_target.unlink(missing_ok=True)
                else:
                    self._atomic_replace_file(current_target, previous_current)
            except (OSError, FileServiceError) as restore_error:
                raise FileConflictError(
                    "Append transaction failed and current output could not be restored"
                ) from restore_error
            raise commit_error
        return version

    def _cleanup_versions(
        self,
        generated_file: GeneratedFile,
        versions: list[FileVersion],
        report: dict[str, Any],
        *,
        dry_run: bool,
        delete_file_record: bool,
    ) -> None:
        if not versions:
            return
        validated: list[tuple[FileVersion, Path]] = []
        for version in versions:
            report["candidates"] += 1
            try:
                path = self._resolve_version_path(generated_file, version)
                self._verify_checksum(path, version.sha256)
                validated.append((version, path))
            except FileServiceError as exc:
                report["skipped"] += 1
                report["errors"].append(
                    {
                        "file_id": generated_file.id,
                        "version": version.version,
                        "error": exc.error_code,
                    }
                )
        if dry_run:
            return
        if delete_file_record and len(validated) != len(versions):
            return

        current_path: Path | None = None
        if delete_file_record:
            try:
                candidate = self._resolve_current_target(generated_file)
                if candidate.exists():
                    self._verify_checksum(candidate, generated_file.sha256)
                    current_path = candidate
            except FileServiceError as exc:
                report["skipped"] += len(versions)
                report["errors"].append(
                    {
                        "file_id": generated_file.id,
                        "version": "current",
                        "error": exc.error_code,
                    }
                )
                return

        staged: list[tuple[FileVersion, Path, Path]] = []
        for version, path in validated:
            quarantine = path.with_name(f".{path.name}.cleanup-{secrets.token_hex(12)}")
            try:
                path.replace(quarantine)
            except OSError:
                restored = self._restore_staged_paths(
                    [(original, staged_path) for _, original, staged_path in staged]
                )
                report["skipped"] += len(validated)
                report["errors"].append(
                    {
                        "file_id": generated_file.id,
                        "version": version.version,
                        "error": "stage_failed",
                    }
                )
                if not restored:
                    raise FileConflictError("Cleanup staging could not be compensated")
                return
            staged.append((version, path, quarantine))

        staged_current: tuple[Path, Path] | None = None
        if current_path is not None:
            quarantine = current_path.with_name(
                f".{current_path.name}.cleanup-{secrets.token_hex(12)}"
            )
            try:
                current_path.replace(quarantine)
            except OSError:
                restored = self._restore_staged_paths(
                    [(original, staged_path) for _, original, staged_path in staged]
                )
                report["skipped"] += len(validated)
                report["errors"].append(
                    {
                        "file_id": generated_file.id,
                        "version": "current",
                        "error": "stage_failed",
                    }
                )
                if not restored:
                    raise FileConflictError(
                        "Cleanup staging could not be compensated"
                    )
                return
            staged_current = (current_path, quarantine)

        for version, _, _ in staged:
            if not delete_file_record:
                db.session.delete(version)
        if delete_file_record:
            db.session.delete(generated_file)

        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            staged_paths = [
                (original, staged_path) for _, original, staged_path in staged
            ]
            if staged_current is not None:
                staged_paths.append(staged_current)
            if not self._restore_staged_paths(staged_paths):
                raise FileConflictError(
                    "Cleanup transaction failed and files could not be restored"
                )
            raise

        for version, _, quarantine in staged:
            try:
                quarantine.unlink()
            except OSError:
                report["skipped"] += 1
                report["errors"].append(
                    {
                        "file_id": generated_file.id,
                        "version": version.version,
                        "error": "purge_failed",
                    }
                )
                continue
            report["deleted"] += 1
            report["bytes_reclaimed"] += version.size_bytes

        if staged_current is not None:
            _, quarantine = staged_current
            try:
                quarantine.unlink()
            except OSError:
                report["skipped"] += 1
                report["errors"].append(
                    {
                        "file_id": generated_file.id,
                        "version": "current",
                        "error": "purge_failed",
                    }
                )
            else:
                report["bytes_reclaimed"] += generated_file.size_bytes

    @staticmethod
    def _restore_staged_paths(staged: list[tuple[Path, Path]]) -> bool:
        restored_all = True
        for original, quarantine in reversed(staged):
            try:
                if original.exists() or not quarantine.exists():
                    restored_all = False
                    continue
                quarantine.replace(original)
            except OSError:
                restored_all = False
        return restored_all

    def _preview(
        self, generated_file: GeneratedFile, version_number: int | None
    ) -> dict[str, Any]:
        version = self._get_version(generated_file, version_number)
        payload = self._read_version_bytes(
            generated_file, version, limit=self.preview_max_bytes
        )
        try:
            source = payload.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise UnsupportedPreviewError("Preview requires valid UTF-8 text") from exc
        if "\x00" in source:
            raise UnsupportedPreviewError("Binary files cannot be previewed")

        result: dict[str, Any] = {
            "file": generated_file.to_dict(),
            "version": version.to_dict(),
            "format": generated_file.file_format,
        }
        if generated_file.file_format == "json":
            try:
                result["content"] = json.loads(source)
            except json.JSONDecodeError as exc:
                raise InvalidJsonPreviewError(
                    "The file does not contain valid JSON"
                ) from exc
        elif generated_file.file_format == "md":
            result["html"] = self._render_safe_markdown(source)
        elif generated_file.file_format == "txt":
            result["content"] = source
        else:
            raise UnsupportedPreviewError("This file format cannot be previewed")
        return result

    def _download(
        self, generated_file: GeneratedFile, version_number: int | None
    ) -> tuple[Path, GeneratedFile, FileVersion]:
        version = self._get_version(generated_file, version_number)
        path = self._resolve_version_path(generated_file, version)
        self._verify_checksum(path, version.sha256)
        return path, generated_file, version

    def _get_version(
        self, generated_file: GeneratedFile, version_number: int | None
    ) -> FileVersion:
        target_version = (
            generated_file.current_version if version_number is None else version_number
        )
        target_version = self._identifier(target_version, "version")
        version = FileVersion.query.filter_by(
            generated_file_id=generated_file.id, version=target_version
        ).first()
        if version is None:
            raise ManagedFileNotFoundError("File version not found")
        return version

    def _read_version_bytes(
        self,
        generated_file: GeneratedFile,
        version: FileVersion,
        limit: int | None = None,
    ) -> bytes:
        path = self._resolve_version_path(generated_file, version)
        try:
            with path.open("rb") as handle:
                payload = handle.read() if limit is None else handle.read(limit + 1)
        except OSError as exc:
            raise FileConflictError("Managed file cannot be read") from exc
        if limit is not None and len(payload) > limit:
            raise PreviewTooLargeError("File exceeds the preview size limit")
        self._verify_payload(payload, version.sha256)
        return payload

    def _resolve_version_path(
        self, generated_file: GeneratedFile, version: FileVersion
    ) -> Path:
        root = Path(generated_file.storage_root)
        if not root.is_absolute() or not root.exists() or not root.is_dir():
            raise FileConflictError("Managed storage is unavailable")
        relative = self._validate_relative_path(version.relative_path)
        try:
            target = self.output_manager.resolve_existing_output_path(
                relative, output_dir=root
            )
        except OutputConfigurationError as exc:
            raise FileConflictError("Managed path is unsafe") from exc
        return target

    def _resolve_target_for_write(
        self, generated_file: GeneratedFile, relative_path: str
    ) -> Path:
        root = Path(generated_file.storage_root)
        relative = self._validate_relative_path(relative_path)
        try:
            target = self.output_manager.resolve_output_path(relative, output_dir=root)
            target.parent.mkdir(parents=True, exist_ok=True)
            target = self.output_manager.resolve_output_path(relative, output_dir=root)
        except (OSError, OutputConfigurationError) as exc:
            raise FileConflictError("Managed path is unsafe") from exc
        if target.exists():
            raise FileConflictError("Immutable file version already exists")
        return target

    def _resolve_current_target(self, generated_file: GeneratedFile) -> Path:
        root = Path(generated_file.storage_root)
        filename = self._current_filename(
            generated_file.logical_name, generated_file.file_format
        )
        try:
            target = self.output_manager.resolve_output_path(filename, output_dir=root)
        except OutputConfigurationError as exc:
            raise FileConflictError("Current output path is unsafe") from exc
        return target

    @staticmethod
    def _validate_relative_path(value: str) -> str:
        if not isinstance(value, str) or not value or "\x00" in value:
            raise FileConflictError("Managed path is invalid")
        posix = PurePosixPath(value)
        windows = PureWindowsPath(value)
        if (
            posix.is_absolute()
            or windows.is_absolute()
            or ".." in posix.parts
            or ".." in windows.parts
        ):
            raise FileConflictError("Managed path is unsafe")
        return value

    @staticmethod
    def _atomic_write_new(target: Path, payload: bytes) -> None:
        temporary: Path | None = None
        try:
            descriptor, temporary_name = tempfile.mkstemp(
                prefix=f".{target.name}.", suffix=".tmp", dir=target.parent
            )
            temporary = Path(temporary_name)
            with os.fdopen(descriptor, "wb") as handle:
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
            # A hard link publishes the completed temporary inode atomically
            # and, unlike os.replace(), refuses to overwrite an existing
            # immutable version.
            os.link(temporary, target)
            temporary.unlink()
        except FileServiceError:
            if temporary is not None:
                temporary.unlink(missing_ok=True)
            raise
        except OSError as exc:
            if temporary is not None:
                try:
                    temporary.unlink(missing_ok=True)
                except OSError:
                    pass
            raise FileConflictError("Managed file cannot be written") from exc

    @staticmethod
    def _atomic_replace_file(target: Path, payload: bytes) -> None:
        temporary: Path | None = None
        try:
            descriptor, temporary_name = tempfile.mkstemp(
                prefix=f".{target.name}.", suffix=".tmp", dir=target.parent
            )
            temporary = Path(temporary_name)
            with os.fdopen(descriptor, "wb") as handle:
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, target)
        except OSError as exc:
            if temporary is not None:
                try:
                    temporary.unlink(missing_ok=True)
                except OSError:
                    pass
            raise FileConflictError("Current output cannot be published") from exc

    @classmethod
    def _named_lock(cls, path: Path) -> threading.RLock:
        key = os.path.normcase(str(path.resolve(strict=False)))
        with cls._named_locks_guard:
            return cls._named_locks.setdefault(key, threading.RLock())

    @classmethod
    @contextmanager
    def _advisory_guard(cls, path: Path, *, blocking: bool) -> Iterator[bool]:
        """Combine a process-local lock with an OS-released advisory lock."""

        thread_lock = cls._named_lock(path)
        acquired_thread = thread_lock.acquire(blocking=blocking)
        if not acquired_thread:
            yield False
            return

        handle: BinaryIO | None = None
        advisory_locked = False
        try:
            try:
                path.parent.mkdir(parents=True, exist_ok=True)
                handle = path.open("a+b")
                handle.seek(0, os.SEEK_END)
                if handle.tell() == 0:
                    handle.write(b"\0")
                    handle.flush()
                handle.seek(0)
                if os.name == "nt":
                    import msvcrt

                    mode = msvcrt.LK_LOCK if blocking else msvcrt.LK_NBLCK
                    msvcrt.locking(handle.fileno(), mode, 1)
                else:
                    import fcntl

                    mode = fcntl.LOCK_EX
                    if not blocking:
                        mode |= fcntl.LOCK_NB
                    fcntl.flock(handle.fileno(), mode)
                advisory_locked = True
            except OSError:
                if blocking:
                    raise FileConflictError("File operation lock is unavailable")
                yield False
                return
            yield True
        finally:
            if advisory_locked and handle is not None:
                try:
                    if os.name == "nt":
                        import msvcrt

                        handle.seek(0)
                        msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
                    else:
                        import fcntl

                        fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
                except OSError:
                    pass
            if handle is not None:
                handle.close()
            thread_lock.release()

    @contextmanager
    def _file_operation_guard(
        self, generated_file: GeneratedFile, *, blocking: bool = True
    ) -> Iterator[bool]:
        """Serialize append and cleanup for one catalogued logical file."""

        try:
            storage_key = str(uuid.UUID(generated_file.storage_key))
            root = Path(generated_file.storage_root).resolve(strict=True)
            if not root.is_dir():
                raise OSError("storage root is not a directory")
        except (OSError, ValueError) as exc:
            raise FileConflictError("Managed storage is unavailable") from exc
        lock_path = root / "managed" / ".locks" / f"{storage_key}.lock"
        with self._advisory_guard(lock_path, blocking=blocking) as acquired:
            yield acquired

    def _refresh_cleanup_policy_unlocked(self) -> None:
        if not self._cleanup_policy_path.exists():
            return
        try:
            with self._cleanup_policy_path.open("r", encoding="utf-8") as handle:
                state = json.load(handle)
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise FileConflictError("Cleanup policy storage is invalid") from exc
        if not isinstance(state, dict):
            raise FileConflictError("Cleanup policy storage is invalid")
        self._apply_cleanup_policy_state(state)

    def _apply_cleanup_policy_state(self, state: dict[str, Any]) -> None:
        try:
            enabled = state["enabled"]
            if not isinstance(enabled, bool):
                raise ValueError("enabled")
            interval = self._positive_int(state["interval_seconds"], "interval_seconds")
            temporary_ttl = self._positive_int(
                state["temporary_ttl_hours"], "temporary_ttl_hours"
            )
            obsolete_ttl = self._positive_int(
                state["obsolete_ttl_days"], "obsolete_ttl_days"
            )
            keep_latest = self._positive_int(
                state["keep_latest_versions"], "keep_latest_versions"
            )
            raw_last_run = state.get("last_run_at")
            if raw_last_run is None:
                last_run = None
            elif isinstance(raw_last_run, str):
                last_run = datetime.fromisoformat(raw_last_run)
                if last_run.tzinfo is not None:
                    last_run = last_run.astimezone(timezone.utc).replace(tzinfo=None)
            else:
                raise ValueError("last_run_at")
        except (KeyError, TypeError, ValueError) as exc:
            raise FileConflictError("Cleanup policy storage is invalid") from exc

        self.cleanup_enabled = enabled
        self.cleanup_interval_seconds = interval
        self.temporary_ttl_hours = temporary_ttl
        self.obsolete_ttl_days = obsolete_ttl
        self.keep_latest_versions = keep_latest
        self._last_cleanup_at = last_run

    def _write_cleanup_policy_unlocked(self, state: dict[str, Any]) -> None:
        temporary: Path | None = None
        try:
            serialized = (
                json.dumps(
                    state,
                    ensure_ascii=False,
                    allow_nan=False,
                    indent=2,
                    sort_keys=True,
                ).encode("utf-8")
                + b"\n"
            )
            self._cleanup_policy_path.parent.mkdir(parents=True, exist_ok=True)
            descriptor, temporary_name = tempfile.mkstemp(
                prefix=f".{self._cleanup_policy_path.name}.",
                suffix=".tmp",
                dir=self._cleanup_policy_path.parent,
            )
            temporary = Path(temporary_name)
            with os.fdopen(descriptor, "wb") as handle:
                handle.write(serialized)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, self._cleanup_policy_path)
        except (OSError, TypeError, ValueError) as exc:
            if temporary is not None:
                try:
                    temporary.unlink(missing_ok=True)
                except OSError:
                    pass
            raise FileConflictError("Cleanup policy cannot be persisted") from exc

    @staticmethod
    def _verify_payload(payload: bytes, expected_hash: str) -> None:
        if not secrets.compare_digest(
            hashlib.sha256(payload).hexdigest(), expected_hash
        ):
            raise FileConflictError("Managed file failed its integrity check")

    @classmethod
    def _verify_checksum(cls, path: Path, expected_hash: str) -> None:
        try:
            payload = path.read_bytes()
        except OSError as exc:
            raise FileConflictError("Managed file cannot be read") from exc
        cls._verify_payload(payload, expected_hash)

    def _serialize_content(self, file_format: str, content: Any) -> bytes:
        try:
            if file_format == "json":
                value = content
                if isinstance(value, bytes):
                    value = value.decode("utf-8")
                if isinstance(value, str):
                    value = json.loads(value)
                serialized = json.dumps(
                    value,
                    ensure_ascii=False,
                    allow_nan=False,
                    indent=2,
                    sort_keys=True,
                )
                payload = f"{serialized}\n".encode("utf-8")
            elif file_format in {"md", "txt"}:
                if isinstance(content, bytes):
                    content.decode("utf-8")
                    payload = content
                elif isinstance(content, str):
                    payload = content.encode("utf-8")
                else:
                    raise FileValidationError("Text content must be a string")
            else:
                raise UnsupportedPreviewError("Unsupported generated file format")
        except (UnicodeDecodeError, json.JSONDecodeError, TypeError, ValueError) as exc:
            if isinstance(exc, FileServiceError):
                raise
            raise FileValidationError(
                "Content is invalid for the selected format"
            ) from exc
        if len(payload) > self.write_max_bytes:
            raise FileValidationError("Content exceeds the file size limit")
        return payload

    @classmethod
    def _normalize_format(cls, value: str) -> tuple[str, str]:
        if not isinstance(value, str):
            raise FileValidationError("format must be json, md, or txt")
        normalized = value.strip().lower().lstrip(".")
        if normalized not in cls.FORMATS:
            raise FileValidationError("format must be json, md, or txt")
        return cls.FORMATS[normalized]

    @staticmethod
    def _validate_logical_name(value: str) -> str:
        if not isinstance(value, str):
            raise FileValidationError("name must be a string")
        name = value.strip()
        if (
            not name
            or len(name) > 255
            or name in {".", ".."}
            or "/" in name
            or "\\" in name
            or any(
                unicodedata.category(character) in {"Cc", "Cf"} for character in name
            )
        ):
            raise FileValidationError(
                "name must be a safe filename without directories"
            )
        return name

    @classmethod
    def _validate_current_filename(cls, logical_name: str, file_format: str) -> None:
        filename = cls._current_filename(logical_name, file_format)
        reserved = {
            cls.CLEANUP_POLICY_FILENAME.casefold(),
            cls.CLEANUP_LOCK_FILENAME.casefold(),
        }
        if (
            len(filename) > 255
            or filename.casefold() in reserved
            or any(character in '<>:"/\\|?*' for character in filename)
            or filename.endswith((" ", "."))
            or PureWindowsPath(filename).is_reserved()
        ):
            raise FileValidationError("name is not a portable output filename")

    @staticmethod
    def _current_filename(logical_name: str, file_format: str) -> str:
        suffix = f".{file_format}"
        if logical_name.lower().endswith(suffix):
            return logical_name
        return f"{logical_name}{suffix}"

    def _validate_execution(self, execution_id: int | None, agent_id: int) -> None:
        if execution_id is None:
            return
        execution_id = self._identifier(execution_id, "execution_id")
        execution = db.session.get(Execution, execution_id)
        if execution is None or execution.agent_id != agent_id:
            raise FileValidationError("Execution does not belong to the agent")

    @classmethod
    def _validate_user(cls, user_id: int | None, label: str) -> None:
        if user_id is None:
            return
        user_id = cls._identifier(user_id, f"{label.lower()}_user_id")
        if db.session.get(User, user_id) is None:
            raise FileValidationError(f"{label} does not exist")

    @staticmethod
    def _version_relative_path(generated_file: GeneratedFile, version: int) -> str:
        return (
            Path("managed")
            .joinpath(
                generated_file.storage_key,
                f"v{version:04d}.{generated_file.file_format}",
            )
            .as_posix()
        )

    @staticmethod
    def _render_safe_markdown(source: str) -> str:
        """Render a deliberately small Markdown subset after HTML escaping."""

        blocks: list[str] = []
        paragraph: list[str] = []
        list_items: list[str] = []
        code_lines: list[str] = []
        in_code = False

        def flush_paragraph() -> None:
            if paragraph:
                blocks.append(f"<p>{' '.join(paragraph)}</p>")
                paragraph.clear()

        def flush_list() -> None:
            if list_items:
                blocks.append(
                    "<ul>"
                    + "".join(f"<li>{item}</li>" for item in list_items)
                    + "</ul>"
                )
                list_items.clear()

        for raw_line in source.splitlines():
            if raw_line.strip().startswith("```"):
                if in_code:
                    blocks.append(
                        "<pre><code>" + "\n".join(code_lines) + "</code></pre>"
                    )
                    code_lines.clear()
                    in_code = False
                else:
                    flush_paragraph()
                    flush_list()
                    in_code = True
                continue
            escaped = html.escape(raw_line, quote=True)
            if in_code:
                code_lines.append(escaped)
                continue
            if not raw_line.strip():
                flush_paragraph()
                flush_list()
                continue
            heading = re.match(r"^(#{1,6})\s+(.+)$", raw_line)
            if heading:
                flush_paragraph()
                flush_list()
                level = len(heading.group(1))
                blocks.append(f"<h{level}>{html.escape(heading.group(2))}</h{level}>")
                continue
            item = re.match(r"^\s*[-*+]\s+(.+)$", raw_line)
            if item:
                flush_paragraph()
                list_items.append(html.escape(item.group(1)))
                continue
            if raw_line.lstrip().startswith(">"):
                flush_paragraph()
                flush_list()
                quote = raw_line.lstrip()[1:].lstrip()
                blocks.append(f"<blockquote>{html.escape(quote)}</blockquote>")
                continue
            flush_list()
            paragraph.append(escaped)

        if in_code:
            blocks.append("<pre><code>" + "\n".join(code_lines) + "</code></pre>")
        flush_paragraph()
        flush_list()
        return "\n".join(blocks)

    def _touch(
        self, generated_file: GeneratedFile, share: FileShare | None = None
    ) -> None:
        now = self._clock()
        generated_file.last_accessed_at = now
        if share is not None:
            share.last_accessed_at = now
        db.session.commit()
