"""Permission service for role-based access control."""

from __future__ import annotations

from typing import List, Optional

from ..models.user import User


class PermissionDeniedError(RuntimeError):
    status_code = 403
    error_code = "permission_denied"


# Default permission sets aligned with existing role vocabulary
# from models/invitation.py: member, admin (viewer mentioned in backlog).
ROLE_PERMISSIONS: dict[str, List[str]] = {
    "viewer": [
        "agent:read",
        "template:read",
        "file:read",
        "project:read",
        "history:read",
    ],
    "member": [
        "agent:read",
        "agent:write",
        "template:read",
        "template:write",
        "file:read",
        "file:write",
        "project:read",
        "project:write",
        "history:read",
        "invitation:read",
        "invitation:write",
    ],
    "admin": [
        "agent:read",
        "agent:write",
        "agent:delete",
        "template:read",
        "template:write",
        "template:delete",
        "file:read",
        "file:write",
        "file:delete",
        "project:read",
        "project:write",
        "project:delete",
        "history:read",
        "history:delete",
        "invitation:read",
        "invitation:write",
        "invitation:delete",
        "user:read",
        "user:write",
        "user:delete",
        "audit:read",
        "security:manage",
    ],
}


def _role_names(user: User) -> set[str]:
    names = {role.name for role in getattr(user, "roles", [])}
    if getattr(user, "is_admin", False):
        names.add("admin")
    return names


def has_permission(user: User, permission: str) -> bool:
    allowed: set[str] = set()
    for role_name in _role_names(user):
        allowed.update(ROLE_PERMISSIONS.get(role_name, []))
    return permission in allowed


def role_permissions(role_name: str) -> List[str]:
    return list(ROLE_PERMISSIONS.get(role_name, []))


def required_permission(permission: str):
    def decorator(function):
        def wrapper(*args, **kwargs):
            from ..services.auth_service import AuthenticationError
            from flask import current_app, request

            auth_service = current_app.extensions["auth_service"]
            user = auth_service.authenticate_authorization_header(
                request.headers.get("Authorization")
            )
            if user is None:
                raise AuthenticationError("A bearer access token is required")
            if not has_permission(user, permission):
                raise PermissionDeniedError("Permission denied")
            return function(*args, user=user, **kwargs)
        return wrapper
    return decorator
