# 🔐 Agent World - Permission and Role Routes
# Version: 1.0.0 (EPIC 10 - US-066)
# Description: Endpoints API pour gérer les permissions et rôles

"""
Permission and Role Routes for Agent World.

Ces endpoints permettent aux administrateurs de :
- Créer, lire, mettre à jour et supprimer des permissions
- Créer, lire, mettre à jour et supprimer des rôles
- Assigner des permissions aux rôles
- Assigner des rôles aux utilisateurs
- Vérifier les permissions des utilisateurs
"""

from __future__ import annotations

from functools import wraps
from typing import Any, Callable

from flask import current_app, request
from flask_restful import Resource

from ..models.base import db
from ..models.user import User
from ..services.auth_service import AuthenticationError, AuthService
from ..services.permission_service import (
    PermissionDeniedError,
    PermissionError,
    PermissionNotFoundError,
    PermissionService,
    RoleNotFoundError,
)

NO_STORE_HEADERS = {
    "Cache-Control": "no-store, max-age=0",
    "Pragma": "no-cache",
    "X-Content-Type-Options": "nosniff",
}


def _auth_service() -> AuthService:
    return current_app.extensions["auth_service"]


def _permission_service() -> PermissionService:
    return current_app.extensions["permission_service"]


def _response(
    data: Any,
    status: int = 200,
    headers: dict[str, str] | None = None,
) -> tuple[Any, int, dict[str, str]]:
    return data, status, headers or dict(NO_STORE_HEADERS)


def permission_errors(function: Callable[..., Any]) -> Callable[..., Any]:
    """Handle permission-related errors and return appropriate responses."""

    @wraps(function)
    def wrapped(*args: Any, **kwargs: Any) -> Any:
        try:
            return function(*args, **kwargs)
        except (PermissionError, PermissionDeniedError, RoleNotFoundError, PermissionNotFoundError) as exc:
            db.session.rollback()
            headers = dict(NO_STORE_HEADERS)
            if exc.status_code == 401:
                headers["WWW-Authenticate"] = "Bearer"
            return _response(
                {"error": exc.args[0] if exc.args else "Permission error", "code": exc.error_code},
                exc.status_code,
                headers,
            )
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


def get_current_user() -> User:
    """Get the current authenticated user from the request headers."""
    auth_header = request.headers.get("Authorization")
    user = _auth_service().authenticate_authorization_header(auth_header)
    if user is None:
        raise AuthenticationError("A bearer access token is required")
    return user


def require_admin(f: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator to require admin privileges."""

    @wraps(f)
    def wrapped(*args: Any, **kwargs: Any) -> Any:
        user = get_current_user()
        if not _permission_service().is_admin(user.id):
            raise PermissionDeniedError("Admin privileges required")
        return f(*args, **kwargs)

    return wrapped


# ==================== Permission Resources ====================

class PermissionListResource(Resource):
    """List all permissions."""

    @permission_errors
    def get(self) -> tuple[Any, int, dict[str, str]]:
        """Get list of all permissions."""
        category = request.args.get("category", None)
        
        permissions = _permission_service().list_permissions(category)
        
        return _response({
            "permissions": [p.to_dict() for p in permissions],
            "count": len(permissions),
        })


class PermissionResource(Resource):
    """Create or get a specific permission."""

    @permission_errors
    @require_admin
    def post(self) -> tuple[Any, int, dict[str, str]]:
        """Create a new permission."""
        data = request.get_json(silent=True)
        
        if not isinstance(data, dict):
            return _response(
                {"error": "A JSON object is required", "code": "invalid_request"},
                400,
            )
        
        name = data.get("name")
        description = data.get("description", "")
        category = data.get("category", "general")
        
        if not isinstance(name, str) or not name.strip():
            return _response(
                {"error": "Permission name is required", "code": "invalid_request"},
                400,
            )
        
        permission = _permission_service().create_permission(
            name=name.strip(),
            description=description,
            category=category,
        )
        
        return _response({
            "message": "Permission created successfully",
            "permission": permission.to_dict(),
        }, 201)

    @permission_errors
    def get(self, permission_id: int) -> tuple[Any, int, dict[str, str]]:
        """Get a specific permission by ID."""
        permission = _permission_service().get_permission(permission_id)
        return _response(permission.to_dict())

    @permission_errors
    @require_admin
    def delete(self, permission_id: int) -> tuple[Any, int, dict[str, str]]:
        """Delete a permission."""
        _permission_service().delete_permission(permission_id)
        return _response({
            "message": "Permission deleted successfully",
            "permission_id": permission_id,
        })


# ==================== Role Resources ====================

class RoleListResource(Resource):
    """List all roles."""

    @permission_errors
    def get(self) -> tuple[Any, int, dict[str, str]]:
        """Get list of all roles."""
        roles = _permission_service().list_roles()
        
        return _response({
            "roles": [r.to_dict() for r in roles],
            "count": len(roles),
        })


class RoleResource(Resource):
    """Create or get a specific role."""

    @permission_errors
    @require_admin
    def post(self) -> tuple[Any, int, dict[str, str]]:
        """Create a new role."""
        data = request.get_json(silent=True)
        
        if not isinstance(data, dict):
            return _response(
                {"error": "A JSON object is required", "code": "invalid_request"},
                400,
            )
        
        name = data.get("name")
        description = data.get("description", "")
        is_default = data.get("is_default", False)
        
        if not isinstance(name, str) or not name.strip():
            return _response(
                {"error": "Role name is required", "code": "invalid_request"},
                400,
            )
        
        role = _permission_service().create_role(
            name=name.strip(),
            description=description,
            is_default=is_default,
        )
        
        return _response({
            "message": "Role created successfully",
            "role": role.to_dict(),
        }, 201)

    @permission_errors
    def get(self, role_id: int) -> tuple[Any, int, dict[str, str]]:
        """Get a specific role by ID."""
        role = _permission_service().get_role(role_id)
        return _response(role.to_dict())

    @permission_errors
    @require_admin
    def delete(self, role_id: int) -> tuple[Any, int, dict[str, str]]:
        """Delete a role."""
        _permission_service().delete_role(role_id)
        return _response({
            "message": "Role deleted successfully",
            "role_id": role_id,
        })


# ==================== Role-Permission Assignment Resources ====================

class RolePermissionAssignResource(Resource):
    """Assign or remove permissions from roles."""

    @permission_errors
    @require_admin
    def post(self, role_id: int) -> tuple[Any, int, dict[str, str]]:
        """Assign a permission to a role."""
        data = request.get_json(silent=True)
        
        if not isinstance(data, dict):
            return _response(
                {"error": "A JSON object is required", "code": "invalid_request"},
                400,
            )
        
        permission_id = data.get("permission_id")
        
        if not isinstance(permission_id, int) or permission_id < 1:
            return _response(
                {"error": "Valid permission_id is required", "code": "invalid_request"},
                400,
            )
        
        _permission_service().assign_permission_to_role(role_id, permission_id)
        
        return _response({
            "message": "Permission assigned to role successfully",
            "role_id": role_id,
            "permission_id": permission_id,
        })

    @permission_errors
    @require_admin
    def delete(self, role_id: int, permission_id: int) -> tuple[Any, int, dict[str, str]]:
        """Remove a permission from a role."""
        _permission_service().remove_permission_from_role(role_id, permission_id)
        return _response({
            "message": "Permission removed from role successfully",
            "role_id": role_id,
            "permission_id": permission_id,
        })


# ==================== User-Role Assignment Resources ====================

class UserRoleAssignResource(Resource):
    """Assign or remove roles from users."""

    @permission_errors
    @require_admin
    def post(self, user_id: int) -> tuple[Any, int, dict[str, str]]:
        """Assign a role to a user."""
        data = request.get_json(silent=True)
        
        if not isinstance(data, dict):
            return _response(
                {"error": "A JSON object is required", "code": "invalid_request"},
                400,
            )
        
        role_id = data.get("role_id")
        
        if not isinstance(role_id, int) or role_id < 1:
            return _response(
                {"error": "Valid role_id is required", "code": "invalid_request"},
                400,
            )
        
        _permission_service().assign_role_to_user(user_id, role_id)
        
        return _response({
            "message": "Role assigned to user successfully",
            "user_id": user_id,
            "role_id": role_id,
        })

    @permission_errors
    @require_admin
    def delete(self, user_id: int, role_id: int) -> tuple[Any, int, dict[str, str]]:
        """Remove a role from a user."""
        _permission_service().remove_role_from_user(user_id, role_id)
        return _response({
            "message": "Role removed from user successfully",
            "user_id": user_id,
            "role_id": role_id,
        })


class UserRolesResource(Resource):
    """Get roles assigned to a user."""

    @permission_errors
    def get(self, user_id: int) -> tuple[Any, int, dict[str, str]]:
        """Get all roles assigned to a user."""
        current_user = get_current_user()
        
        # Users can view their own roles, admins can view any user's roles
        if not _permission_service().is_admin(current_user.id) and current_user.id != user_id:
            raise PermissionDeniedError("You can only view your own roles")
        
        roles = _permission_service().get_user_roles(user_id)
        
        return _response({
            "user_id": user_id,
            "roles": [r.to_dict() for r in roles],
            "count": len(roles),
        })


class UserPermissionsResource(Resource):
    """Get all permissions for a user."""

    @permission_errors
    def get(self, user_id: int) -> tuple[Any, int, dict[str, str]]:
        """Get all permissions for a user."""
        current_user = get_current_user()
        
        # Users can view their own permissions, admins can view any user's permissions
        if not _permission_service().is_admin(current_user.id) and current_user.id != user_id:
            raise PermissionDeniedError("You can only view your own permissions")
        
        permissions = _permission_service().get_user_permissions(user_id)
        
        return _response({
            "user_id": user_id,
            "permissions": sorted(list(permissions)),
            "count": len(permissions),
        })


class CheckPermissionResource(Resource):
    """Check if a user has a specific permission."""

    @permission_errors
    def get(self, user_id: int, permission_name: str) -> tuple[Any, int, dict[str, str]]:
        """Check if a user has a specific permission."""
        current_user = get_current_user()
        
        # Users can check their own permissions, admins can check any user's permissions
        if not _permission_service().is_admin(current_user.id) and current_user.id != user_id:
            raise PermissionDeniedError("You can only check your own permissions")
        
        has_permission = _permission_service().has_permission(user_id, permission_name)
        
        return _response({
            "user_id": user_id,
            "permission": permission_name,
            "has_permission": has_permission,
        })


class CurrentUserRolesResource(Resource):
    """Get roles for the current user."""

    @permission_errors
    def get(self) -> tuple[Any, int, dict[str, str]]:
        """Get all roles for the current user."""
        user = get_current_user()
        roles = _permission_service().get_user_roles(user.id)
        
        return _response({
            "user_id": user.id,
            "roles": [r.to_dict() for r in roles],
            "count": len(roles),
        })


class CurrentUserPermissionsResource(Resource):
    """Get all permissions for the current user."""

    @permission_errors
    def get(self) -> tuple[Any, int, dict[str, str]]:
        """Get all permissions for the current user."""
        user = get_current_user()
        permissions = _permission_service().get_user_permissions(user.id)
        
        return _response({
            "user_id": user.id,
            "permissions": sorted(list(permissions)),
            "count": len(permissions),
        })


class InitializeDefaultsResource(Resource):
    """Initialize default roles and permissions."""

    @permission_errors
    @require_admin
    def post(self) -> tuple[Any, int, dict[str, str]]:
        """Reinitialize default roles and permissions."""
        _permission_service().initialize_defaults()
        
        return _response({
            "message": "Default roles and permissions initialized successfully",
        })


def register_permission_resources(api: Any) -> None:
    """Register the permission and role API resources."""
    
    # Permission resources
    api.add_resource(
        PermissionListResource,
        "/permissions",
        endpoint="permission_list",
    )
    api.add_resource(
        PermissionResource,
        "/permissions/<int:permission_id>",
        endpoint="permission",
    )
    
    # Role resources
    api.add_resource(
        RoleListResource,
        "/roles",
        endpoint="role_list",
    )
    api.add_resource(
        RoleResource,
        "/roles/<int:role_id>",
        endpoint="role",
    )
    
    # Role-Permission assignment
    api.add_resource(
        RolePermissionAssignResource,
        "/roles/<int:role_id>/permissions",
        "/roles/<int:role_id>/permissions/<int:permission_id>",
        endpoint="role_permission",
    )
    
    # User-Role assignment
    api.add_resource(
        UserRoleAssignResource,
        "/users/<int:user_id>/roles",
        "/users/<int:user_id>/roles/<int:role_id>",
        endpoint="user_role",
    )
    
    # User roles and permissions
    api.add_resource(
        UserRolesResource,
        "/users/<int:user_id>/roles",
        endpoint="user_roles",
    )
    api.add_resource(
        UserPermissionsResource,
        "/users/<int:user_id>/permissions",
        endpoint="user_permissions",
    )
    api.add_resource(
        CheckPermissionResource,
        "/users/<int:user_id>/permissions/<string:permission_name>",
        endpoint="check_permission",
    )
    
    # Current user resources
    api.add_resource(
        CurrentUserRolesResource,
        "/me/roles",
        endpoint="current_user_roles",
    )
    api.add_resource(
        CurrentUserPermissionsResource,
        "/me/permissions",
        endpoint="current_user_permissions",
    )
    
    # Initialize defaults
    api.add_resource(
        InitializeDefaultsResource,
        "/permissions/initialize",
        endpoint="initialize_defaults",
    )
