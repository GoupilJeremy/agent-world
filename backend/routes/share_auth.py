"""Request hook enforcing identities on recipient-constrained share links."""

from __future__ import annotations

from typing import Any

from flask import Flask, current_app, request

from ..services.auth_service import AuthenticationError, AuthService
from ..services.file_service import FileService, FileServiceError

NO_STORE_HEADERS = {
    "Cache-Control": "no-store, max-age=0",
    "Pragma": "no-cache",
    "X-Content-Type-Options": "nosniff",
}


def _error_response(error: Any) -> tuple[dict[str, str], int, dict[str, str]]:
    headers = dict(NO_STORE_HEADERS)
    if error.status_code == 401:
        headers["WWW-Authenticate"] = "Bearer"
    return (
        {"error": error.message, "code": error.error_code},
        error.status_code,
        headers,
    )


def register_share_recipient_auth(app: Flask) -> None:
    """Require a matching JWT only when a share names a recipient user."""

    @app.before_request
    def enforce_share_recipient() -> Any:
        if request.method == "OPTIONS" or not request.path.startswith("/api/shares/"):
            return None
        view_args = request.view_args or {}
        raw_token = view_args.get("token")
        if not isinstance(raw_token, str):
            return None

        file_service: FileService = current_app.extensions["file_service"]
        try:
            share = file_service.resolve_share(raw_token)
            if share.recipient_user_id is None:
                return None
            auth_service: AuthService = current_app.extensions["auth_service"]
            user = auth_service.authenticate_authorization_header(
                request.headers.get("Authorization")
            )
            assert user is not None
            file_service.require_share_recipient(share, user.id)
        except (AuthenticationError, FileServiceError) as exc:
            return _error_response(exc)
        return None
