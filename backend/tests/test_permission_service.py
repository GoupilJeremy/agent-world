# 🧪 Agent World - Permission Service Tests
# Version: 1.0.0 (EPIC 10 - US-066)
# Description: Tests unitaires pour le service PermissionService

"""
Unit tests for PermissionService.

Ces tests couvrent:
- Création et gestion des permissions
- Création et gestion des rôles
- Assignation des permissions aux rôles
- Assignation des rôles aux utilisateurs
- Vérification des permissions des utilisateurs
- Initialisation des valeurs par défaut
"""

import unittest
from unittest.mock import MagicMock, patch

from backend.app import create_app
from backend.models.base import db
from backend.models.user import User
from backend.services.permission_service import (
    PermissionDeniedError,
    PermissionError,
    PermissionNotFoundError,
    PermissionService,
    RoleNotFoundError,
)


class TestPermissionService(unittest.TestCase):
    """Test cases for PermissionService."""

    def setUp(self):
        """Set up test fixtures."""
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
        self.app.config["AUTO_CREATE_DB"] = True
        
        self.client = self.app.test_client()
        
        with self.app.app_context():
            db.create_all()
            self.permission_service = PermissionService()
            
            # Create a test user
            self.user = User(
                email="test@example.com",
                username="testuser",
                password="testpassword123",
            )
            db.session.add(self.user)
            db.session.commit()

    def tearDown(self):
        """Clean up test fixtures."""
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_create_permission(self):
        """Test creating a new permission."""
        with self.app.app_context():
            permission = self.permission_service.create_permission(
                name="test_permission",
                description="A test permission",
                category="test",
            )
            
            self.assertIsNotNone(permission)
            self.assertEqual(permission.name, "test_permission")
            self.assertEqual(permission.description, "A test permission")
            self.assertEqual(permission.category, "test")

    def test_create_duplicate_permission(self):
        """Test creating a duplicate permission raises error."""
        with self.app.app_context():
            self.permission_service.create_permission(
                name="test_permission",
                description="A test permission",
            )
            
            with self.assertRaises(PermissionError):
                self.permission_service.create_permission(
                    name="test_permission",
                    description="Duplicate",
                )

    def test_get_permission(self):
        """Test getting a permission by ID."""
        with self.app.app_context():
            permission = self.permission_service.create_permission(
                name="test_permission",
            )
            
            fetched = self.permission_service.get_permission(permission.id)
            self.assertEqual(fetched.id, permission.id)

    def test_get_permission_not_found(self):
        """Test getting a non-existent permission raises error."""
        with self.app.app_context():
            with self.assertRaises(PermissionNotFoundError):
                self.permission_service.get_permission(9999)

    def test_get_permission_by_name(self):
        """Test getting a permission by name."""
        with self.app.app_context():
            permission = self.permission_service.create_permission(
                name="test_permission",
            )
            
            fetched = self.permission_service.get_permission_by_name("test_permission")
            self.assertEqual(fetched.id, permission.id)

    def test_list_permissions(self):
        """Test listing all permissions."""
        with self.app.app_context():
            self.permission_service.create_permission(name="perm1", category="cat1")
            self.permission_service.create_permission(name="perm2", category="cat2")
            
            permissions = self.permission_service.list_permissions()
            self.assertGreaterEqual(len(permissions), 2)

    def test_list_permissions_by_category(self):
        """Test listing permissions by category."""
        with self.app.app_context():
            self.permission_service.create_permission(name="perm1", category="cat1")
            self.permission_service.create_permission(name="perm2", category="cat2")
            
            permissions = self.permission_service.list_permissions(category="cat1")
            self.assertEqual(len(permissions), 1)
            self.assertEqual(permissions[0].name, "perm1")

    def test_delete_permission(self):
        """Test deleting a permission."""
        with self.app.app_context():
            permission = self.permission_service.create_permission(name="test_perm")
            
            result = self.permission_service.delete_permission(permission.id)
            self.assertTrue(result)
            
            # Verify it's deleted
            with self.assertRaises(PermissionNotFoundError):
                self.permission_service.get_permission(permission.id)

    def test_create_role(self):
        """Test creating a new role."""
        with self.app.app_context():
            role = self.permission_service.create_role(
                name="test_role",
                description="A test role",
            )
            
            self.assertIsNotNone(role)
            self.assertEqual(role.name, "test_role")
            self.assertEqual(role.description, "A test role")
            self.assertFalse(role.is_default)
            self.assertFalse(role.is_system)

    def test_create_duplicate_role(self):
        """Test creating a duplicate role raises error."""
        with self.app.app_context():
            self.permission_service.create_role(name="test_role")
            
            with self.assertRaises(PermissionError):
                self.permission_service.create_role(name="test_role")

    def test_get_role(self):
        """Test getting a role by ID."""
        with self.app.app_context():
            role = self.permission_service.create_role(name="test_role")
            
            fetched = self.permission_service.get_role(role.id)
            self.assertEqual(fetched.id, role.id)

    def test_get_role_not_found(self):
        """Test getting a non-existent role raises error."""
        with self.app.app_context():
            with self.assertRaises(RoleNotFoundError):
                self.permission_service.get_role(9999)

    def test_get_role_by_name(self):
        """Test getting a role by name."""
        with self.app.app_context():
            role = self.permission_service.create_role(name="test_role")
            
            fetched = self.permission_service.get_role_by_name("test_role")
            self.assertEqual(fetched.id, role.id)

    def test_list_roles(self):
        """Test listing all roles."""
        with self.app.app_context():
            self.permission_service.create_role(name="role1")
            self.permission_service.create_role(name="role2")
            
            roles = self.permission_service.list_roles()
            self.assertGreaterEqual(len(roles), 2)

    def test_delete_role(self):
        """Test deleting a role."""
        with self.app.app_context():
            role = self.permission_service.create_role(name="test_role")
            
            result = self.permission_service.delete_role(role.id)
            self.assertTrue(result)
            
            # Verify it's deleted
            with self.assertRaises(RoleNotFoundError):
                self.permission_service.get_role(role.id)

    def test_assign_permission_to_role(self):
        """Test assigning a permission to a role."""
        with self.app.app_context():
            permission = self.permission_service.create_permission(name="test_perm")
            role = self.permission_service.create_role(name="test_role")
            
            result = self.permission_service.assign_permission_to_role(
                role.id, permission.id
            )
            self.assertTrue(result)
            
            # Verify assignment
            role = self.permission_service.get_role(role.id)
            self.assertIn(permission, role.permissions)

    def test_remove_permission_from_role(self):
        """Test removing a permission from a role."""
        with self.app.app_context():
            permission = self.permission_service.create_permission(name="test_perm")
            role = self.permission_service.create_role(name="test_role")
            self.permission_service.assign_permission_to_role(role.id, permission.id)
            
            result = self.permission_service.remove_permission_from_role(
                role.id, permission.id
            )
            self.assertTrue(result)
            
            # Verify removal
            role = self.permission_service.get_role(role.id)
            self.assertNotIn(permission, role.permissions)

    def test_assign_role_to_user(self):
        """Test assigning a role to a user."""
        with self.app.app_context():
            role = self.permission_service.create_role(name="test_role")
            
            result = self.permission_service.assign_role_to_user(
                self.user.id, role.id
            )
            self.assertTrue(result)
            
            # Verify assignment
            roles = self.permission_service.get_user_roles(self.user.id)
            self.assertEqual(len(roles), 1)
            self.assertEqual(roles[0].id, role.id)

    def test_remove_role_from_user(self):
        """Test removing a role from a user."""
        with self.app.app_context():
            role = self.permission_service.create_role(name="test_role")
            self.permission_service.assign_role_to_user(self.user.id, role.id)
            
            result = self.permission_service.remove_role_from_user(
                self.user.id, role.id
            )
            self.assertTrue(result)
            
            # Verify removal
            roles = self.permission_service.get_user_roles(self.user.id)
            self.assertEqual(len(roles), 0)

    def test_get_user_roles(self):
        """Test getting roles assigned to a user."""
        with self.app.app_context():
            role1 = self.permission_service.create_role(name="role1")
            role2 = self.permission_service.create_role(name="role2")
            
            self.permission_service.assign_role_to_user(self.user.id, role1.id)
            self.permission_service.assign_role_to_user(self.user.id, role2.id)
            
            roles = self.permission_service.get_user_roles(self.user.id)
            self.assertEqual(len(roles), 2)

    def test_get_user_permissions(self):
        """Test getting all permissions for a user."""
        with self.app.app_context():
            # Create permissions
            perm1 = self.permission_service.create_permission(name="perm1")
            perm2 = self.permission_service.create_permission(name="perm2")
            
            # Create role and assign permissions
            role = self.permission_service.create_role(name="test_role")
            self.permission_service.assign_permission_to_role(role.id, perm1.id)
            self.permission_service.assign_permission_to_role(role.id, perm2.id)
            
            # Assign role to user
            self.permission_service.assign_role_to_user(self.user.id, role.id)
            
            permissions = self.permission_service.get_user_permissions(self.user.id)
            self.assertIn("perm1", permissions)
            self.assertIn("perm2", permissions)

    def test_has_permission(self):
        """Test checking if a user has a permission."""
        with self.app.app_context():
            # Create permission and role
            perm = self.permission_service.create_permission(name="test_perm")
            role = self.permission_service.create_role(name="test_role")
            self.permission_service.assign_permission_to_role(role.id, perm.id)
            
            # User without the role should not have permission
            has_perm = self.permission_service.has_permission(self.user.id, "test_perm")
            self.assertFalse(has_perm)
            
            # Assign role to user
            self.permission_service.assign_role_to_user(self.user.id, role.id)
            
            # User should now have permission
            has_perm = self.permission_service.has_permission(self.user.id, "test_perm")
            self.assertTrue(has_perm)

    def test_check_permission(self):
        """Test check_permission raises error if user doesn't have permission."""
        with self.app.app_context():
            with self.assertRaises(PermissionDeniedError):
                self.permission_service.check_permission(
                    self.user.id, "nonexistent_permission"
                )

    def test_is_admin(self):
        """Test checking if a user is admin."""
        with self.app.app_context():
            # User is not admin by default
            self.assertFalse(self.permission_service.is_admin(self.user.id))
            
            # Create admin role and assign to user
            admin_role = self.permission_service.create_role(
                name="admin",
                description="Admin role",
            )
            self.permission_service.assign_role_to_user(self.user.id, admin_role.id)
            
            self.assertTrue(self.permission_service.is_admin(self.user.id))


class TestDefaultInitialization(unittest.TestCase):
    """Test cases for default RBAC initialization."""

    def setUp(self):
        """Set up test fixtures."""
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
        self.app.config["AUTO_CREATE_DB"] = True
        
        self.client = self.app.test_client()
        
        with self.app.app_context():
            db.create_all()
            self.permission_service = PermissionService()

    def tearDown(self):
        """Clean up test fixtures."""
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_initialize_defaults(self):
        """Test initializing default roles and permissions."""
        with self.app.app_context():
            self.permission_service.initialize_defaults()
            
            # Check that default roles are created
            from backend.models.role import Role
            admin_role = Role.get_by_name("admin")
            member_role = Role.get_by_name("member")
            guest_role = Role.get_by_name("guest")
            
            self.assertIsNotNone(admin_role)
            self.assertIsNotNone(member_role)
            self.assertIsNotNone(guest_role)
            
            # Check that admin role has all permissions
            from backend.models.permission import Permission
            all_permissions = Permission.query.count()
            self.assertEqual(len(admin_role.permissions), all_permissions)

    def test_role_permissions_after_init(self):
        """Test that roles have correct permissions after initialization."""
        with self.app.app_context():
            self.permission_service.initialize_defaults()
            
            from backend.models.role import Role
            
            # Get roles
            admin_role = Role.get_by_name("admin")
            member_role = Role.get_by_name("member")
            guest_role = Role.get_by_name("guest")
            
            # Admin should have all permissions
            self.assertTrue(admin_role.has_permission("manage_roles"))
            self.assertTrue(admin_role.has_permission("delete_user"))
            
            # Member should not have system permissions
            self.assertFalse(member_role.has_permission("manage_roles"))
            self.assertFalse(member_role.has_permission("manage_permissions"))
            
            # Guest should only have read permissions
            self.assertTrue(guest_role.has_permission("read_agent"))
            self.assertFalse(guest_role.has_permission("create_agent"))


class TestRoleModel(unittest.TestCase):
    """Test cases for Role model."""

    def setUp(self):
        """Set up test fixtures."""
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
        self.app.config["AUTO_CREATE_DB"] = True
        
        self.client = self.app.test_client()
        
        with self.app.app_context():
            db.create_all()

    def tearDown(self):
        """Clean up test fixtures."""
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_role_creation(self):
        """Test creating a role."""
        from backend.models.role import Role
        
        with self.app.app_context():
            role = Role(
                name="test_role",
                description="A test role",
                is_default=False,
                is_system=False,
            )
            db.session.add(role)
            db.session.commit()
            
            self.assertIsNotNone(role.id)
            self.assertEqual(role.name, "test_role")

    def test_role_has_permission(self):
        """Test checking if a role has a permission."""
        from backend.models.role import Role
        from backend.models.permission import Permission
        
        with self.app.app_context():
            role = Role(name="test_role")
            permission = Permission(name="test_perm", category="test")
            
            db.session.add(role)
            db.session.add(permission)
            db.session.commit()
            
            # Initially, role should not have permission
            self.assertFalse(role.has_permission("test_perm"))
            
            # Add permission to role
            role.permissions.append(permission)
            db.session.commit()
            
            # Now role should have permission
            self.assertTrue(role.has_permission("test_perm"))

    def test_role_get_permission_names(self):
        """Test getting permission names from a role."""
        from backend.models.role import Role
        from backend.models.permission import Permission
        
        with self.app.app_context():
            role = Role(name="test_role")
            perm1 = Permission(name="perm1", category="test")
            perm2 = Permission(name="perm2", category="test")
            
            db.session.add(role)
            db.session.add(perm1)
            db.session.add(perm2)
            db.session.commit()
            
            role.permissions.extend([perm1, perm2])
            db.session.commit()
            
            names = role.get_permission_names()
            self.assertIn("perm1", names)
            self.assertIn("perm2", names)


class TestPermissionModel(unittest.TestCase):
    """Test cases for Permission model."""

    def setUp(self):
        """Set up test fixtures."""
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
        self.app.config["AUTO_CREATE_DB"] = True
        
        self.client = self.app.test_client()
        
        with self.app.app_context():
            db.create_all()

    def tearDown(self):
        """Clean up test fixtures."""
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_permission_creation(self):
        """Test creating a permission."""
        from backend.models.permission import Permission
        
        with self.app.app_context():
            permission = Permission(
                name="test_permission",
                description="A test permission",
                category="test",
            )
            db.session.add(permission)
            db.session.commit()
            
            self.assertIsNotNone(permission.id)
            self.assertEqual(permission.name, "test_permission")

    def test_get_permission_by_name(self):
        """Test getting permission by name."""
        from backend.models.permission import Permission
        
        with self.app.app_context():
            permission = Permission(name="test_perm", category="test")
            db.session.add(permission)
            db.session.commit()
            
            fetched = Permission.get_by_name("test_perm")
            self.assertIsNotNone(fetched)
            self.assertEqual(fetched.id, permission.id)

    def test_get_all_by_category(self):
        """Test getting all permissions by category."""
        from backend.models.permission import Permission
        
        with self.app.app_context():
            Permission(name="perm1", category="cat1")
            Permission(name="perm2", category="cat1")
            Permission(name="perm3", category="cat2")
            
            db.session.add_all([Permission(name="perm1", category="cat1"),
                               Permission(name="perm2", category="cat1"),
                               Permission(name="perm3", category="cat2")])
            db.session.commit()
            
            cat1_perms = Permission.get_all_by_category("cat1")
            self.assertEqual(len(cat1_perms), 2)


if __name__ == "__main__":
    unittest.main()
