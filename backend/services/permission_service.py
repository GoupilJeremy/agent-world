# 🔐 Agent World - Permission Service
# Version: 1.0.0 (EPIC 10 - US-066)
# Description: Service pour gérer les permissions et rôles RBAC

"""
Permission Service for Agent World.

Ce service gère:
- La création et gestion des permissions
- La création et gestion des rôles
- L'assignation des permissions aux rôles
- L'assignation des rôles aux utilisateurs
- La vérification des permissions des utilisateurs
"""

from typing import List, Optional, Set

from ..models.base import db
from ..models.permission import Permission
from ..models.role import Role, user_roles
from ..models.user import User


class PermissionError(Exception):
    """Base exception for permission-related errors."""

    status_code = 400
    error_code = "permission_error"


class PermissionDeniedError(PermissionError):
    """User does not have the required permission."""

    status_code = 403
    error_code = "permission_denied"


class RoleNotFoundError(PermissionError):
    """Role not found."""

    status_code = 404
    error_code = "role_not_found"


class PermissionNotFoundError(PermissionError):
    """Permission not found."""

    status_code = 404
    error_code = "permission_not_found"


class PermissionService:
    """
    Service for managing RBAC (Role-Based Access Control).

    This service provides functionality for:
    - Managing permissions
    - Managing roles
    - Assigning permissions to roles
    - Assigning roles to users
    - Checking user permissions
    """

    # Default roles
    DEFAULT_ROLES = {
        "admin": {
            "description": "Administrator with full access",
            "is_default": False,
            "is_system": True,
        },
        "member": {
            "description": "Regular member with standard access",
            "is_default": True,
            "is_system": True,
        },
        "guest": {
            "description": "Guest with limited read-only access",
            "is_default": False,
            "is_system": True,
        },
    }

    # Default permissions by category
    DEFAULT_PERMISSIONS = {
        "agent": [
            ("create_agent", "Create new agents"),
            ("read_agent", "View agents"),
            ("update_agent", "Update existing agents"),
            ("delete_agent", "Delete agents"),
            ("execute_agent", "Execute agents"),
        ],
        "project": [
            ("create_project", "Create new projects"),
            ("read_project", "View projects"),
            ("update_project", "Update existing projects"),
            ("delete_project", "Delete projects"),
        ],
        "user": [
            ("create_user", "Create new users"),
            ("read_user", "View users"),
            ("update_user", "Update existing users"),
            ("delete_user", "Delete users"),
            ("manage_roles", "Manage user roles"),
        ],
        "template": [
            ("create_template", "Create new templates"),
            ("read_template", "View templates"),
            ("update_template", "Update existing templates"),
            ("delete_template", "Delete templates"),
        ],
        "workflow": [
            ("create_workflow", "Create new workflows"),
            ("read_workflow", "View workflows"),
            ("update_workflow", "Update existing workflows"),
            ("delete_workflow", "Delete workflows"),
        ],
        "system": [
            ("manage_permissions", "Manage system permissions"),
            ("manage_roles", "Manage system roles"),
            ("view_audit_logs", "View audit logs"),
            ("manage_settings", "Manage system settings"),
        ],
        "file": [
            ("read_file", "Read files"),
            ("write_file", "Write files"),
            ("delete_file", "Delete files"),
            ("share_file", "Share files"),
        ],
    }

    def __init__(self):
        """Initialize the PermissionService."""
        pass

    def initialize_defaults(self) -> None:
        """
        Initialize default roles and permissions.
        Should be called during application startup.
        """
        # Create default permissions
        for category, permissions in self.DEFAULT_PERMISSIONS.items():
            for name, description in permissions:
                if not Permission.get_by_name(name):
                    permission = Permission(
                        name=name,
                        description=description,
                        category=category,
                    )
                    db.session.add(permission)

        db.session.commit()

        # Create default roles
        for role_name, role_config in self.DEFAULT_ROLES.items():
            if not Role.get_by_name(role_name):
                role = Role(
                    name=role_name,
                    description=role_config["description"],
                    is_default=role_config["is_default"],
                    is_system=role_config["is_system"],
                )
                db.session.add(role)
                db.session.commit()

        # Assign permissions to roles
        self._assign_default_role_permissions()

    def _assign_default_role_permissions(self) -> None:
        """Assign default permissions to roles."""
        admin_role = Role.get_by_name("admin")
        member_role = Role.get_by_name("member")
        guest_role = Role.get_by_name("guest")

        if not admin_role or not member_role or not guest_role:
            return

        # Admin gets all permissions
        all_permissions = Permission.query.all()
        admin_role.permissions = all_permissions

        # Member gets most permissions except user management and system settings
        member_permissions = []
        restricted_categories = ["system"]
        restricted_permission_names = ["manage_roles", "manage_permissions", "create_user", "delete_user"]

        for permission in all_permissions:
            if (
                permission.category not in restricted_categories
                and permission.name not in restricted_permission_names
            ):
                member_permissions.append(permission)

        member_role.permissions = member_permissions

        # Guest gets read-only permissions
        guest_permissions = []
        read_permission_names = [
            "read_agent",
            "read_project",
            "read_user",  # Only self
            "read_template",
            "read_workflow",
            "read_file",
        ]

        for permission in all_permissions:
            if permission.name in read_permission_names:
                guest_permissions.append(permission)

        guest_role.permissions = guest_permissions

        db.session.commit()

    def create_permission(self, name: str, description: str = "", category: str = "general") -> Permission:
        """
        Create a new permission.

        Args:
            name: Unique name of the permission
            description: Description of the permission
            category: Category of the permission

        Returns:
            The created permission
        """
        if Permission.get_by_name(name):
            raise PermissionError(f"Permission '{name}' already exists")

        permission = Permission(
            name=name,
            description=description,
            category=category,
        )
        db.session.add(permission)
        db.session.commit()

        return permission

    def get_permission(self, permission_id: int) -> Permission:
        """Get a permission by ID."""
        permission = db.session.get(Permission, permission_id)
        if not permission:
            raise PermissionNotFoundError(f"Permission with ID {permission_id} not found")
        return permission

    def get_permission_by_name(self, name: str) -> Permission:
        """Get a permission by name."""
        permission = Permission.get_by_name(name)
        if not permission:
            raise PermissionNotFoundError(f"Permission '{name}' not found")
        return permission

    def list_permissions(self, category: Optional[str] = None) -> List[Permission]:
        """List all permissions, optionally filtered by category."""
        if category:
            return Permission.get_all_by_category(category)
        return Permission.query.all()

    def delete_permission(self, permission_id: int) -> bool:
        """Delete a permission."""
        permission = db.session.get(Permission, permission_id)
        if not permission:
            raise PermissionNotFoundError(f"Permission with ID {permission_id} not found")

        # Check if permission is used by any role
        if permission.roles:
            raise PermissionError(
                f"Cannot delete permission '{permission.name}' as it is used by roles"
            )

        db.session.delete(permission)
        db.session.commit()
        return True

    def create_role(
        self, name: str, description: str = "", is_default: bool = False
    ) -> Role:
        """
        Create a new role.

        Args:
            name: Unique name of the role
            description: Description of the role
            is_default: Whether this should be the default role

        Returns:
            The created role
        """
        if Role.get_by_name(name):
            raise PermissionError(f"Role '{name}' already exists")

        # If setting as default, unset any existing default
        if is_default:
            default_role = Role.get_default()
            if default_role:
                default_role.is_default = False

        role = Role(
            name=name,
            description=description,
            is_default=is_default,
            is_system=False,
        )
        db.session.add(role)
        db.session.commit()

        return role

    def get_role(self, role_id: int) -> Role:
        """Get a role by ID."""
        role = db.session.get(Role, role_id)
        if not role:
            raise RoleNotFoundError(f"Role with ID {role_id} not found")
        return role

    def get_role_by_name(self, name: str) -> Role:
        """Get a role by name."""
        role = Role.get_by_name(name)
        if not role:
            raise RoleNotFoundError(f"Role '{name}' not found")
        return role

    def list_roles(self) -> List[Role]:
        """List all roles."""
        return Role.query.all()

    def delete_role(self, role_id: int) -> bool:
        """Delete a role."""
        role = db.session.get(Role, role_id)
        if not role:
            raise RoleNotFoundError(f"Role with ID {role_id} not found")

        if role.is_system:
            raise PermissionError(f"Cannot delete system role '{role.name}'")

        # Check if role is assigned to any user
        if role.users:
            raise PermissionError(
                f"Cannot delete role '{role.name}' as it is assigned to users"
            )

        db.session.delete(role)
        db.session.commit()
        return True

    def assign_permission_to_role(self, role_id: int, permission_id: int) -> bool:
        """
        Assign a permission to a role.

        Args:
            role_id: ID of the role
            permission_id: ID of the permission

        Returns:
            True if successful
        """
        role = self.get_role(role_id)
        permission = self.get_permission(permission_id)

        if permission in role.permissions:
            return True  # Already assigned

        role.permissions.append(permission)
        db.session.commit()
        return True

    def remove_permission_from_role(self, role_id: int, permission_id: int) -> bool:
        """
        Remove a permission from a role.

        Args:
            role_id: ID of the role
            permission_id: ID of the permission

        Returns:
            True if successful
        """
        role = self.get_role(role_id)
        permission = self.get_permission(permission_id)

        if permission not in role.permissions:
            return True  # Not assigned

        role.permissions.remove(permission)
        db.session.commit()
        return True

    def assign_role_to_user(self, user_id: int, role_id: int) -> bool:
        """
        Assign a role to a user.

        Args:
            user_id: ID of the user
            role_id: ID of the role

        Returns:
            True if successful
        """
        user = db.session.get(User, user_id)
        if not user:
            raise PermissionError(f"User with ID {user_id} not found")

        role = self.get_role(role_id)

        # Check if already assigned
        for existing_role in user.roles:
            if existing_role.id == role.id:
                return True

        user.roles.append(role)
        db.session.commit()
        return True

    def remove_role_from_user(self, user_id: int, role_id: int) -> bool:
        """
        Remove a role from a user.

        Args:
            user_id: ID of the user
            role_id: ID of the role

        Returns:
            True if successful
        """
        user = db.session.get(User, user_id)
        if not user:
            raise PermissionError(f"User with ID {user_id} not found")

        role = self.get_role(role_id)

        # Check if assigned
        found = False
        for existing_role in user.roles:
            if existing_role.id == role.id:
                found = True
                break

        if not found:
            return True

        user.roles.remove(role)
        db.session.commit()
        return True

    def get_user_roles(self, user_id: int) -> List[Role]:
        """Get all roles assigned to a user."""
        user = db.session.get(User, user_id)
        if not user:
            raise PermissionError(f"User with ID {user_id} not found")
        return list(user.roles)

    def get_user_permissions(self, user_id: int) -> Set[str]:
        """
        Get all permission names for a user.

        Args:
            user_id: ID of the user

        Returns:
            Set of permission names
        """
        user = db.session.get(User, user_id)
        if not user:
            raise PermissionError(f"User with ID {user_id} not found")

        permissions = set()
        for role in user.roles:
            permissions.update(role.get_permission_names())

        return permissions

    def has_permission(self, user_id: int, permission_name: str) -> bool:
        """
        Check if a user has a specific permission.

        Args:
            user_id: ID of the user
            permission_name: Name of the permission to check

        Returns:
            True if the user has the permission
        """
        user = db.session.get(User, user_id)
        if not user:
            raise PermissionError(f"User with ID {user_id} not found")

        for role in user.roles:
            if role.has_permission(permission_name):
                return True

        return False

    def check_permission(self, user_id: int, permission_name: str) -> None:
        """
        Check if a user has a specific permission, raise error if not.

        Args:
            user_id: ID of the user
            permission_name: Name of the permission to check

        Raises:
            PermissionDeniedError: If the user does not have the permission
        """
        if not self.has_permission(user_id, permission_name):
            raise PermissionDeniedError(
                f"User with ID {user_id} does not have permission '{permission_name}'"
            )

    def is_admin(self, user_id: int) -> bool:
        """Check if a user has the admin role."""
        user = db.session.get(User, user_id)
        if not user:
            return False

        for role in user.roles:
            if role.name == "admin":
                return True

        return False

    def create_default_setup(self) -> None:
        """
        Create the default RBAC setup with roles and permissions.
        This is a convenience method for initializing a new system.
        """
        self.initialize_defaults()
