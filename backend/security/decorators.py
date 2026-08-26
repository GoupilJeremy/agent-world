"""Security decorators for route protection."""

from __future__ import annotations

from functools import wraps
from typing import Any, Callable

from flask import current_app, request

from ..services.auth_service import AuthenticationError, AuthService
from ..services.permission_service import PermissionDeniedError


def require_auth(function: Callable[..., Any]) -> Callable[..., Any]:
    """Require a valid bearer token. Injects `user` into kwargs."""

    @wraps(function)
    def wrapped(*args: Any, **kwargs: Any) -> Any:
        if not current_app.config.get("AUTH_ENFORCE_ALL", False):
            return function(*args, **kwargs)
        auth_service: AuthService = current_app.extensions["auth_service"]
        user = auth_service.authenticate_authorization_header(
            request.headers.get("Authorization")
        )
        if user is None:
            raise AuthenticationError("A bearer access token is required")
        return function(*args, user=user, **kwargs)

    return wrapped


def require_permission(permission: str) -> Callable[..., Any]:
    """Require both authentication and a specific permission."""

    def decorator(function: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(function)
        def wrapped(*args: Any, **kwargs: Any) -> Any:
            if not current_app.config.get("AUTH_ENFORCE_ALL", False):
                return function(*args, **kwargs)
            from ..services.permission_service import has_permission
            user = kwargs.get("user")
            if user is None:
                auth_service: AuthService = current_app.extensions["auth_service"]
                user = auth_service.authenticate_authorization_header(
                    request.headers.get("Authorization")
                )
            if user is None:
                raise AuthenticationError("A bearer access token is required")
            if not has_permission(user, permission):
                raise PermissionDeniedError("Permission denied")
            return function(*args, user=user, **kwargs)

        return wrapped

    return decorator
