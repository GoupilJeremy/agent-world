"""Authentication endpoints used by recipient-constrained file shares."""

from __future__ import annotations

from functools import wraps
from typing import Any, Callable

from flask import current_app, request
from flask_restful import Resource

from ..models.base import db
from ..services.auth_service import (
    AuthenticationError,
    AuthenticationValidationError,
    AuthService,
    InvalidCredentialsError,
)

NO_STORE_HEADERS = {
    "Cache-Control": "no-store, max-age=0",
    "Pragma": "no-cache",
    "X-Content-Type-Options": "nosniff",
}


def _service() -> AuthService:
    return current_app.extensions["auth_service"]


def _response(
    data: Any,
    status: int = 200,
    headers: dict[str, str] | None = None,
) -> tuple[Any, int, dict[str, str]]:
    return data, status, headers or dict(NO_STORE_HEADERS)


def auth_errors(function: Callable[..., Any]) -> Callable[..., Any]:
    """Return stable authentication failures without leaking user existence."""

    @wraps(function)
    def wrapped(*args: Any, **kwargs: Any) -> Any:
        try:
            return function(*args, **kwargs)
        except AuthenticationError as exc:
            db.session.rollback()
            headers = dict(NO_STORE_HEADERS)
            if exc.status_code == 401:
                headers["WWW-Authenticate"] = "Bearer"
            return _response(
                {"error": exc.message, "code": exc.error_code},
                exc.status_code,
                headers,
            )

    return wrapped


class LoginResource(Resource):
    """Exchange existing user credentials for a short-lived access token."""

    @auth_errors
    def post(self) -> tuple[Any, int, dict[str, str]]:
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            raise AuthenticationValidationError("A JSON object is required")
        identifier = data.get("identifier")
        password = data.get("password")
        if not isinstance(identifier, str) or not isinstance(password, str):
            raise InvalidCredentialsError("Invalid username/email or password")
        user, access_token = _service().login(identifier, password)
        return _response(
            {
                "access_token": access_token,
                "token_type": "Bearer",
                "expires_in": _service().access_token_ttl_seconds,
                "user": user.to_dict(),
            }
        )


class CurrentUserResource(Resource):
    """Return the active identity represented by a bearer token."""

    @auth_errors
    def get(self) -> tuple[Any, int, dict[str, str]]:
        user = _service().authenticate_authorization_header(
            request.headers.get("Authorization")
        )
        assert user is not None
        return _response(user.to_dict())


def register_resources(api: Any) -> None:
    """Register the minimal authentication API."""

    api.add_resource(LoginResource, "/auth/login")
    api.add_resource(CurrentUserResource, "/auth/me")
