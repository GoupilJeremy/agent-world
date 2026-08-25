"""REST resources for catalogued generated files."""

from __future__ import annotations

import hashlib
import html
import json
import secrets
from functools import wraps
from typing import Any, Callable

from flask import Response, current_app, request, send_file
from flask_restful import Resource
from werkzeug.exceptions import HTTPException

from ..models.base import db
from ..services.file_service import FileService, FileServiceError, FileValidationError

NO_STORE_HEADERS = {
    "Cache-Control": "no-store, max-age=0",
    "Pragma": "no-cache",
    "Referrer-Policy": "no-referrer",
    "X-Content-Type-Options": "nosniff",
    "Content-Security-Policy": "default-src 'none'; frame-ancestors 'none'",
}


def _service() -> FileService:
    return current_app.extensions["file_service"]


def _management_token() -> str | None:
    return request.headers.get("X-Management-Token")


def _json_response(data: Any, status: int = 200) -> tuple[Any, int, dict[str, str]]:
    return data, status, dict(NO_STORE_HEADERS)


def _secure_response(response: Response) -> Response:
    for name, value in NO_STORE_HEADERS.items():
        response.headers[name] = value
    return response


def _preview_response(preview: dict[str, Any]) -> Any:
    """Return JSON by default or a script-free browser preview on request."""

    if request.args.get("view") != "html":
        return _json_response(preview)

    metadata = preview["file"]
    title = html.escape(str(metadata["name"]), quote=True)
    if preview["format"] == "md":
        rendered = preview["html"]
    elif preview["format"] == "json":
        formatted = json.dumps(
            preview["content"], ensure_ascii=False, indent=2, sort_keys=True
        )
        rendered = f"<pre>{html.escape(formatted, quote=True)}</pre>"
    else:
        rendered = f"<pre>{html.escape(preview['content'], quote=True)}</pre>"

    document = (
        '<!doctype html><html lang="fr"><head><meta charset="utf-8">'
        f"<title>Aperçu — {title}</title></head><body>"
        f"<main><h1>{title}</h1>{rendered}</main></body></html>"
    )
    return _secure_response(Response(document, mimetype="text/html"))


def _payload() -> dict[str, Any]:
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise FileValidationError("A JSON object is required")
    return data


def _required(data: dict[str, Any], name: str) -> Any:
    if name not in data:
        raise FileValidationError(f"{name} is required")
    return data[name]


def _version_argument() -> int | None:
    raw = request.args.get("version")
    if raw is None:
        return None
    try:
        version = int(raw)
    except ValueError as exc:
        raise FileValidationError("version must be a positive integer") from exc
    if version < 1:
        raise FileValidationError("version must be a positive integer")
    return version


def _require_cleanup_authority() -> None:
    configured = current_app.config.get("FILE_CLEANUP_TOKEN")
    if not isinstance(configured, str) or not configured:
        error = FileServiceError("Manual cleanup endpoint is disabled")
        error.status_code = 503
        error.error_code = "cleanup_disabled"
        raise error
    supplied = request.headers.get("X-Cleanup-Token", "")
    expected_hash = hashlib.sha256(configured.encode("utf-8")).digest()
    supplied_hash = hashlib.sha256(supplied.encode("utf-8")).digest()
    if not secrets.compare_digest(expected_hash, supplied_hash):
        error = FileServiceError("A valid cleanup token is required")
        error.status_code = 403
        error.error_code = "forbidden"
        raise error


def file_errors(function: Callable[..., Any]) -> Callable[..., Any]:
    """Map known service errors without leaking filesystem details."""

    @wraps(function)
    def wrapped(*args: Any, **kwargs: Any) -> Any:
        try:
            return function(*args, **kwargs)
        except FileServiceError as exc:
            db.session.rollback()
            return _json_response(
                {"error": exc.message, "code": exc.error_code}, exc.status_code
            )
        except HTTPException:
            db.session.rollback()
            raise
        except Exception:
            db.session.rollback()
            current_app.logger.exception("Unexpected generated-file API failure")
            return _json_response(
                {"error": "The file operation failed", "code": "internal_error"},
                500,
            )

    return wrapped


class FileCollectionResource(Resource):
    """List capability-scoped metadata or create a logical file."""

    @file_errors
    def get(self) -> tuple[Any, int, dict[str, str]]:
        raw_agent_id = request.args.get("agent_id")
        if raw_agent_id is None:
            raise FileValidationError("agent_id is required")
        try:
            agent_id = int(raw_agent_id)
        except ValueError as exc:
            raise FileValidationError("agent_id must be a positive integer") from exc
        generated_files = _service().list_files(agent_id, _management_token())
        return _json_response([item.to_dict() for item in generated_files])

    @file_errors
    def post(self) -> tuple[Any, int, dict[str, str]]:
        data = _payload()
        is_temporary = data.get("is_temporary", False)
        if not isinstance(is_temporary, bool):
            raise FileValidationError("is_temporary must be a boolean")
        generated_file, management_token = _service().create_file(
            agent_id=_required(data, "agent_id"),
            logical_name=_required(data, "name"),
            file_format=_required(data, "format"),
            content=_required(data, "content"),
            execution_id=data.get("execution_id"),
            is_temporary=is_temporary,
        )
        response = generated_file.to_dict()
        response["management_token"] = management_token
        return _json_response(response, 201)


class FileResource(Resource):
    """Return protected metadata for one managed file."""

    @file_errors
    def get(self, file_id: int) -> tuple[Any, int, dict[str, str]]:
        generated_file = _service().get_file(file_id, _management_token() or "")
        return _json_response(generated_file.to_dict())


class FileVersionCollectionResource(Resource):
    """List or append immutable versions."""

    @file_errors
    def get(self, file_id: int) -> tuple[Any, int, dict[str, str]]:
        versions = _service().list_versions(file_id, _management_token() or "")
        return _json_response([version.to_dict() for version in versions])

    @file_errors
    def post(self, file_id: int) -> tuple[Any, int, dict[str, str]]:
        data = _payload()
        version = _service().append_version(
            file_id,
            _required(data, "content"),
            management_token=_management_token(),
            execution_id=data.get("execution_id"),
        )
        return _json_response(version.to_dict(), 201)


class FileRestoreResource(Resource):
    """Restore an old snapshot by creating a new version."""

    @file_errors
    def post(self, file_id: int, version: int) -> tuple[Any, int, dict[str, str]]:
        restored = _service().restore_version(
            file_id, version, _management_token() or ""
        )
        return _json_response(restored.to_dict(), 201)


class FilePreviewResource(Resource):
    """Preview a managed file without exposing its path."""

    @file_errors
    def get(self, file_id: int) -> Any:
        preview = _service().preview_file(
            file_id, _management_token() or "", _version_argument()
        )
        return _preview_response(preview)


class FileDownloadResource(Resource):
    """Download an integrity-checked managed version."""

    @file_errors
    def get(self, file_id: int) -> Response:
        stream, generated_file, version = _service().download_file_stream(
            file_id, _management_token() or "", _version_argument()
        )
        response = send_file(
            stream,
            mimetype=generated_file.mime_type,
            as_attachment=True,
            download_name=_service().download_name(generated_file),
            conditional=False,
            etag=version.sha256,
            max_age=0,
        )
        return _secure_response(response)


class FileShareCollectionResource(Resource):
    """Create and list revocable share links."""

    @file_errors
    def get(self, file_id: int) -> tuple[Any, int, dict[str, str]]:
        shares = _service().list_shares(file_id, _management_token() or "")
        return _json_response([share.to_dict() for share in shares])

    @file_errors
    def post(self, file_id: int) -> tuple[Any, int, dict[str, str]]:
        data = _payload()
        share, raw_token = _service().create_share(
            file_id,
            _management_token() or "",
            permission=data.get("permission", "read"),
            expires_in_seconds=data.get("expires_in_seconds"),
            recipient_user_id=data.get("recipient_user_id"),
        )
        response = share.to_dict()
        response.update(
            {
                "token": raw_token,
                "preview_url": f"/api/shares/{raw_token}/preview",
                "preview_page_url": (f"/api/shares/{raw_token}/preview?view=html"),
                "download_url": f"/api/shares/{raw_token}/download",
                "content_url": f"/api/shares/{raw_token}/content",
            }
        )
        return _json_response(response, 201)


class FileShareResource(Resource):
    """Revoke a share link."""

    @file_errors
    def delete(self, file_id: int, share_id: int) -> tuple[Any, int, dict[str, str]]:
        _service().revoke_share(file_id, share_id, _management_token() or "")
        return _json_response({}, 204)


class SharedPreviewResource(Resource):
    """Preview the current version through a share capability."""

    @file_errors
    def get(self, token: str) -> Any:
        return _preview_response(_service().preview_share(token))


class SharedDownloadResource(Resource):
    """Download the current version through a share capability."""

    @file_errors
    def get(self, token: str) -> Response:
        stream, generated_file, version = _service().download_share_stream(token)
        response = send_file(
            stream,
            mimetype=generated_file.mime_type,
            as_attachment=True,
            download_name=_service().download_name(generated_file),
            conditional=False,
            etag=version.sha256,
            max_age=0,
        )
        return _secure_response(response)


class SharedContentResource(Resource):
    """Append the current file through a write capability."""

    @file_errors
    def put(self, token: str) -> tuple[Any, int, dict[str, str]]:
        share = _service().resolve_share(token, require_write=True)
        payload = request.get_data(cache=False)
        version = _service().append_version(
            share.generated_file_id, payload, share_token=token
        )
        return _json_response(version.to_dict(), 201)


class FileCleanupPolicyResource(Resource):
    """Inspect or update the cleanup policy with an administrative token."""

    @file_errors
    def get(self) -> tuple[Any, int, dict[str, str]]:
        _require_cleanup_authority()
        return _json_response(_service().cleanup_policy())

    @file_errors
    def put(self) -> tuple[Any, int, dict[str, str]]:
        _require_cleanup_authority()
        return _json_response(_service().update_cleanup_policy(_payload()))


class FileCleanupResource(Resource):
    """Run a safe catalogue-only cleanup, dry-run by default."""

    @file_errors
    def post(self) -> tuple[Any, int, dict[str, str]]:
        _require_cleanup_authority()
        data = request.get_json(silent=True)
        if data is None:
            data = {}
        if not isinstance(data, dict):
            raise FileValidationError("A JSON object is required")
        unknown = set(data) - {"dry_run"}
        if unknown:
            raise FileValidationError(f"Unknown cleanup option: {sorted(unknown)[0]}")
        dry_run = data.get("dry_run", True)
        if not isinstance(dry_run, bool):
            raise FileValidationError("dry_run must be a boolean")
        return _json_response(_service().cleanup(dry_run=dry_run))


def register_resources(api: Any) -> None:
    """Register file resources on the shared Flask-RESTful API."""

    api.add_resource(FileCollectionResource, "/files")
    api.add_resource(FileResource, "/files/<int:file_id>")
    api.add_resource(FileVersionCollectionResource, "/files/<int:file_id>/versions")
    api.add_resource(
        FileRestoreResource,
        "/files/<int:file_id>/versions/<int:version>/restore",
    )
    api.add_resource(FilePreviewResource, "/files/<int:file_id>/preview")
    api.add_resource(FileDownloadResource, "/files/<int:file_id>/download")
    api.add_resource(FileShareCollectionResource, "/files/<int:file_id>/shares")
    api.add_resource(FileShareResource, "/files/<int:file_id>/shares/<int:share_id>")
    api.add_resource(FileCleanupPolicyResource, "/files/cleanup-policy")
    api.add_resource(FileCleanupResource, "/files/cleanup")
    api.add_resource(SharedPreviewResource, "/shares/<string:token>/preview")
    api.add_resource(SharedDownloadResource, "/shares/<string:token>/download")
    api.add_resource(SharedContentResource, "/shares/<string:token>/content")
