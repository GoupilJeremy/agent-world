# 🧪 Agent World - User Model Tests
# Version: 0.1.0 (MVP)
# Description: Tests unitaires pour le modèle User

"""
Unit tests for the User model.

Ces tests vérifient le bon fonctionnement du modèle User
et de ses méthodes.
"""

import pytest

from backend.app import create_app
from backend.models.base import db
from backend.models.user import User


@pytest.fixture
def app():
    """Create and configure a new app instance for each test."""
    app = create_app()
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


class TestUserModel:
    """Test cases for the User model."""

    def test_create_user(self, app):
        """Test creating a new user."""
        with app.app_context():
            user = User.create(
                email="test@example.com",
                username="testuser",
                password="securepassword123",
            )

            assert user.id is not None
            assert user.email == "test@example.com"
            assert user.username == "testuser"
            assert user.password_hash is not None
            assert user.is_active is True
            assert user.is_admin is False

    def test_user_password_hashing(self, app):
        """Test that passwords are properly hashed."""
        with app.app_context():
            password = "testpassword123"
            user = User.create(
                email="hash@example.com", username="hashuser", password=password
            )

            # Password should be hashed, not stored in plain text
            assert user.password_hash != password
            assert user.password_hash is not None

            # Check password verification
            assert user.check_password(password) is True
            assert user.check_password("wrongpassword") is False

    def test_set_password(self, app):
        """Test setting a new password."""
        with app.app_context():
            user = User.create(
                email="setpass@example.com",
                username="setpassuser",
                password="oldpassword",
            )

            old_hash = user.password_hash
            user.set_password("newpassword")

            assert user.password_hash != old_hash
            assert user.check_password("newpassword") is True
            assert user.check_password("oldpassword") is False

    def test_get_user_by_id(self, app):
        """Test getting a user by ID."""
        with app.app_context():
            user = User.create(
                email="byid@example.com", username="byiduser", password="password123"
            )

            retrieved_user = User.get_by_id(user.id)

            assert retrieved_user is not None
            assert retrieved_user.id == user.id
            assert retrieved_user.email == "byid@example.com"

    def test_get_user_by_email(self, app):
        """Test getting a user by email."""
        with app.app_context():
            User.create(
                email="byemail@example.com",
                username="byemailuser",
                password="password123",
            )

            retrieved_user = User.get_by_email("byemail@example.com")

            assert retrieved_user is not None
            assert retrieved_user.email == "byemail@example.com"

    def test_get_user_by_username(self, app):
        """Test getting a user by username."""
        with app.app_context():
            User.create(
                email="byusername@example.com",
                username="uniqueusername",
                password="password123",
            )

            retrieved_user = User.get_by_username("uniqueusername")

            assert retrieved_user is not None
            assert retrieved_user.username == "uniqueusername"

    def test_get_all_users(self, app):
        """Test getting all users."""
        with app.app_context():
            # Create multiple users
            for i in range(3):
                User.create(
                    email=f"user{i}@example.com",
                    username=f"user{i}",
                    password="password123",
                )

            users = User.get_all()
            assert len(users) == 3

    def test_get_active_users(self, app):
        """Test getting only active users."""
        with app.app_context():
            # Create active and inactive users
            User.create(
                email="active1@example.com",
                username="active1",
                password="password123",
                is_active=True,
            )
            User.create(
                email="inactive@example.com",
                username="inactive",
                password="password123",
                is_active=False,
            )
            User.create(
                email="active2@example.com",
                username="active2",
                password="password123",
                is_active=True,
            )

            active_users = User.get_active()
            assert len(active_users) == 2
            for user in active_users:
                assert user.is_active is True

    def test_user_full_name(self, app):
        """Test user full name property."""
        with app.app_context():
            user1 = User.create(
                email="fullname@example.com",
                username="fullnameuser",
                password="password123",
                first_name="John",
                last_name="Doe",
            )

            user2 = User.create(
                email="noname@example.com",
                username="nonameuser",
                password="password123",
            )

            assert user1.full_name == "John Doe"
            assert user2.full_name == ""

    def test_update_user(self, app):
        """Test updating a user."""
        with app.app_context():
            user = User.create(
                email="update@example.com",
                username="updateuser",
                password="oldpassword",
                first_name="Old",
                last_name="Name",
            )

            user.update(first_name="New", last_name="Name", password="newpassword")

            updated_user = User.get_by_id(user.id)
            assert updated_user.first_name == "New"
            assert updated_user.last_name == "Name"
            assert updated_user.check_password("newpassword") is True

    def test_delete_user(self, app):
        """Test deleting a user."""
        with app.app_context():
            user = User.create(
                email="delete@example.com",
                username="deleteuser",
                password="password123",
            )
            user_id = user.id

            user.delete()

            deleted_user = User.get_by_id(user_id)
            assert deleted_user is None

    def test_user_to_dict(self, app):
        """Test converting user to dictionary."""
        with app.app_context():
            user = User.create(
                email="dict@example.com",
                username="dictuser",
                password="password123",
                first_name="Test",
                last_name="User",
            )

            user_dict = user.to_dict()

            assert user_dict["id"] == user.id
            assert user_dict["email"] == "dict@example.com"
            assert user_dict["username"] == "dictuser"
            assert user_dict["full_name"] == "Test User"
            assert "password_hash" not in user_dict

    def test_user_to_dict_with_password(self, app):
        """Test converting user to dictionary with password."""
        with app.app_context():
            user = User.create(
                email="pass@example.com", username="passuser", password="password123"
            )

            user_dict = user.to_dict(include_password=True)

            assert "password_hash" in user_dict

    def test_duplicate_email(self, app):
        """Test that duplicate emails are not allowed."""
        with app.app_context():
            User.create(
                email="duplicate@example.com", username="user1", password="password123"
            )

            from sqlalchemy.exc import IntegrityError

            with pytest.raises(IntegrityError):
                User.create(
                    email="duplicate@example.com",
                    username="user2",
                    password="password456",
                )
                db.session.commit()

    def test_duplicate_username(self, app):
        """Test that duplicate usernames are not allowed."""
        with app.app_context():
            User.create(
                email="email1@example.com",
                username="duplicateuser",
                password="password123",
            )

            from sqlalchemy.exc import IntegrityError

            with pytest.raises(IntegrityError):
                User.create(
                    email="email2@example.com",
                    username="duplicateuser",
                    password="password456",
                )
                db.session.commit()

    def test_admin_user(self, app):
        """Test creating an admin user."""
        with app.app_context():
            user = User.create(
                email="admin@example.com",
                username="admin",
                password="adminpassword",
                is_admin=True,
            )

            assert user.is_admin is True
