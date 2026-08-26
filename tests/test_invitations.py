# 🧪 Agent World - Invitation Tests
# Version: 0.4.0 (Collaboration)
# Description: Tests pour les fonctionnalités d'invitation (US-040)

"""
Tests for Invitation functionality (US-040).

Ces tests couvrent :
- Création d'invitations
- Récupération d'invitations
- Acceptation d'invitations
- Révocation d'invitations
- Expiration des invitations
"""

from datetime import datetime, timedelta

import pytest

from backend.app import create_app
from backend.models.base import db
from backend.models.invitation import Invitation, InvitationStatus
from backend.models.project import Project
from backend.models.user import User
from backend.services.invitation_service import InvitationError, InvitationService


@pytest.fixture
def app():
    """Create and configure a new app instance for each test."""
    app = create_app()
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.config["AUTO_CREATE_DB"] = True
    app.config["WTF_CSRF_ENABLED"] = False

    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def client(app):
    """Create a test client."""
    return app.test_client()


@pytest.fixture
def invitation_service(app):
    """Create an InvitationService instance for testing."""
    return InvitationService()


@pytest.fixture
def test_user(app):
    """Create a test user."""
    with app.app_context():
        user = User.create(
            email="test@example.com",
            username="testuser",
            password="testpass123",
            first_name="Test",
            last_name="User",
        )
        return user


@pytest.fixture
def test_project(app, test_user):
    """Create a test project."""
    with app.app_context():
        project = Project.create(
            name="Test Project",
            description="A test project for invitations",
            created_by=test_user.id,
        )
        return project


# ============================================================================
# Tests for Invitation Model
# ============================================================================


class TestInvitationModel:
    """Tests for the Invitation model."""

    def test_create_invitation(self, app, test_user, test_project):
        """Test creating a new invitation."""
        with app.app_context():
            token = "test-token-123456789"
            invitation = Invitation.create(
                project_id=test_project.id,
                email="invited@example.com",
                token=token,
                role="member",
                created_by=test_user.id,
            )

            assert invitation.id is not None
            assert invitation.project_id == test_project.id
            assert invitation.email == "invited@example.com"
            assert invitation.token == token
            assert invitation.role == "member"
            assert invitation.created_by == test_user.id
            assert invitation.status == InvitationStatus.PENDING
            assert invitation.expires_at is not None
            assert invitation.is_pending is True

    def test_get_by_token(self, app, test_user, test_project):
        """Test retrieving an invitation by token."""
        with app.app_context():
            token = "test-token-get-by-token"
            invitation = Invitation.create(
                project_id=test_project.id,
                email="invited@example.com",
                token=token,
                created_by=test_user.id,
            )

            retrieved = Invitation.get_by_token(token)
            assert retrieved is not None
            assert retrieved.id == invitation.id
            assert retrieved.email == invitation.email

    def test_get_by_token_not_found(self, app):
        """Test retrieving a non-existent invitation by token."""
        with app.app_context():
            result = Invitation.get_by_token("non-existent-token")
            assert result is None

    def test_get_by_project(self, app, test_user, test_project):
        """Test retrieving invitations by project."""
        with app.app_context():
            # Create multiple invitations for the same project
            Invitation.create(
                project_id=test_project.id,
                email="user1@example.com",
                token="token-1",
                created_by=test_user.id,
            )
            Invitation.create(
                project_id=test_project.id,
                email="user2@example.com",
                token="token-2",
                created_by=test_user.id,
            )

            # Create an invitation for a different project
            other_project = Project.create(
                name="Other Project",
                created_by=test_user.id,
            )
            Invitation.create(
                project_id=other_project.id,
                email="user3@example.com",
                token="token-3",
                created_by=test_user.id,
            )

            invitations = Invitation.get_by_project(test_project.id)
            assert len(invitations) == 2
            assert all(inv.project_id == test_project.id for inv in invitations)

    def test_accept_invitation(self, app, test_user, test_project):
        """Test accepting an invitation."""
        with app.app_context():
            token = "test-token-accept"
            invitation = Invitation.create(
                project_id=test_project.id,
                email="invited@example.com",
                token=token,
                created_by=test_user.id,
            )

            assert invitation.status == InvitationStatus.PENDING
            assert invitation.accepted_at is None

            invitation.accept()

            assert invitation.status == InvitationStatus.ACCEPTED
            assert invitation.accepted_at is not None
            assert invitation.is_accepted is True

    def test_revoke_invitation(self, app, test_user, test_project):
        """Test revoking an invitation."""
        with app.app_context():
            token = "test-token-revoke"
            invitation = Invitation.create(
                project_id=test_project.id,
                email="invited@example.com",
                token=token,
                created_by=test_user.id,
            )

            assert invitation.status == InvitationStatus.PENDING

            invitation.revoke()

            assert invitation.status == InvitationStatus.REVOKED

    def test_expired_invitation(self, app, test_user, test_project):
        """Test invitation expiration."""
        with app.app_context():
            # Create an invitation that expired yesterday
            expires_at = datetime.utcnow() - timedelta(days=1)
            invitation = Invitation.create(
                project_id=test_project.id,
                email="invited@example.com",
                token="expired-token",
                created_by=test_user.id,
                expires_at=expires_at,
            )

            assert invitation.is_expired is True
            assert invitation.is_pending is False

    def test_to_dict(self, app, test_user, test_project):
        """Test converting invitation to dictionary."""
        with app.app_context():
            token = "test-token-to-dict"
            invitation = Invitation.create(
                project_id=test_project.id,
                email="invited@example.com",
                token=token,
                role="admin",
                created_by=test_user.id,
            )

            result = invitation.to_dict()

            assert result["id"] == invitation.id
            assert result["project_id"] == test_project.id
            assert result["email"] == "invited@example.com"
            assert result["token"] == token
            assert result["role"] == "admin"
            assert result["status"] == "PENDING"
            assert result["created_by"] == test_user.id
            assert result["created_at"] is not None
            assert result["expires_at"] is not None


# ============================================================================
# Tests for Invitation Service
# ============================================================================


class TestInvitationService:
    """Tests for the InvitationService."""

    def test_generate_token(self, invitation_service):
        """Test generating a unique token."""
        token1 = invitation_service.generate_token()
        token2 = invitation_service.generate_token()

        assert token1 != token2
        assert len(token1) == 32  # Default length

    def test_generate_token_custom_length(self, invitation_service):
        """Test generating a token with custom length."""
        token = invitation_service.generate_token(length=64)
        assert len(token) == 64

    def test_create_invitation(self, app, invitation_service, test_user, test_project):
        """Test creating an invitation via the service."""
        with app.app_context():
            invitation = invitation_service.create_invitation(
                project_id=test_project.id,
                email="newuser@example.com",
                role="member",
                created_by=test_user.id,
                expires_in_days=7,
            )

            assert invitation is not None
            assert invitation.project_id == test_project.id
            assert invitation.email == "newuser@example.com"
            assert invitation.role == "member"
            assert invitation.created_by == test_user.id
            assert invitation.status == InvitationStatus.PENDING

    def test_create_invitation_invalid_project(
        self, app, invitation_service, test_user
    ):
        """Test creating an invitation with invalid project ID."""
        with app.app_context():
            with pytest.raises(InvitationError) as exc_info:
                invitation_service.create_invitation(
                    project_id=99999,  # Non-existent project
                    email="newuser@example.com",
                    created_by=test_user.id,
                )

            assert "Projet 99999 introuvable" in str(exc_info.value)

    def test_create_invitation_duplicate(
        self, app, invitation_service, test_user, test_project
    ):
        """Test creating a duplicate invitation for the same email and project."""
        with app.app_context():
            # Create first invitation
            invitation_service.create_invitation(
                project_id=test_project.id,
                email="duplicate@example.com",
                created_by=test_user.id,
            )

            # Try to create another invitation for the same email and project
            with pytest.raises(InvitationError) as exc_info:
                invitation_service.create_invitation(
                    project_id=test_project.id,
                    email="duplicate@example.com",
                    created_by=test_user.id,
                )

            assert "invitation pendante existe déjà" in str(exc_info.value)

    def test_accept_invitation(self, app, invitation_service, test_user, test_project):
        """Test accepting an invitation via the service."""
        with app.app_context():
            # Create an invitation
            invitation = invitation_service.create_invitation(
                project_id=test_project.id,
                email="toaccept@example.com",
                created_by=test_user.id,
            )

            # Accept the invitation
            accepted = invitation_service.accept_invitation(
                token=invitation.token,
                user_id=test_user.id,
            )

            assert accepted.status == InvitationStatus.ACCEPTED
            assert accepted.accepted_at is not None

    def test_accept_invitation_invalid_token(self, app, invitation_service):
        """Test accepting an invitation with invalid token."""
        with app.app_context():
            with pytest.raises(InvitationError) as exc_info:
                invitation_service.accept_invitation(
                    token="invalid-token",
                    user_id=1,
                )

            assert "Invitation introuvable" in str(exc_info.value)

    def test_accept_invitation_already_accepted(
        self, app, invitation_service, test_user, test_project
    ):
        """Test accepting an already accepted invitation."""
        with app.app_context():
            # Create and accept an invitation
            invitation = invitation_service.create_invitation(
                project_id=test_project.id,
                email="alreadyaccepted@example.com",
                created_by=test_user.id,
            )
            invitation_service.accept_invitation(
                token=invitation.token,
                user_id=test_user.id,
            )

            # Try to accept again
            with pytest.raises(InvitationError) as exc_info:
                invitation_service.accept_invitation(
                    token=invitation.token,
                    user_id=test_user.id,
                )

            assert "Invitation non valide" in str(exc_info.value)

    def test_revoke_invitation(self, app, invitation_service, test_user, test_project):
        """Test revoking an invitation via the service."""
        with app.app_context():
            # Create an invitation
            invitation = invitation_service.create_invitation(
                project_id=test_project.id,
                email="torevoke@example.com",
                created_by=test_user.id,
            )

            # Revoke the invitation
            revoked = invitation_service.revoke_invitation(
                invitation_id=invitation.id,
                revoked_by=test_user.id,
            )

            assert revoked.status == InvitationStatus.REVOKED

    def test_revoke_invitation_not_creator(
        self, app, invitation_service, test_user, test_project
    ):
        """Test that only the creator or admin can revoke an invitation."""
        with app.app_context():
            # Create another user
            other_user = User.create(
                email="other@example.com",
                username="otheruser",
                password="otherpass123",
            )

            # Create an invitation
            invitation = invitation_service.create_invitation(
                project_id=test_project.id,
                email="torevoke@example.com",
                created_by=test_user.id,
            )

            # Try to revoke with the other user
            with pytest.raises(InvitationError) as exc_info:
                invitation_service.revoke_invitation(
                    invitation_id=invitation.id,
                    revoked_by=other_user.id,
                )

            assert "Seul le créateur" in str(exc_info.value)

    def test_get_invitations_by_project(
        self, app, invitation_service, test_user, test_project
    ):
        """Test getting invitations by project."""
        with app.app_context():
            # Create invitations for the project
            invitation_service.create_invitation(
                project_id=test_project.id,
                email="user1@example.com",
                created_by=test_user.id,
            )
            invitation_service.create_invitation(
                project_id=test_project.id,
                email="user2@example.com",
                created_by=test_user.id,
            )

            invitations = invitation_service.get_invitations_by_project(test_project.id)

            assert len(invitations) == 2
            assert all(inv.project_id == test_project.id for inv in invitations)

    def test_get_pending_invitations_by_email(
        self, app, invitation_service, test_user, test_project
    ):
        """Test getting pending invitations by email."""
        with app.app_context():
            # Create pending invitation
            invitation_service.create_invitation(
                project_id=test_project.id,
                email="pending@example.com",
                created_by=test_user.id,
            )

            # Create an accepted invitation (should not be returned)
            accepted_inv = invitation_service.create_invitation(
                project_id=test_project.id,
                email="accepted@example.com",
                created_by=test_user.id,
            )
            accepted_inv.accept()

            pending = invitation_service.get_pending_invitations_by_email(
                "pending@example.com"
            )
            accepted = invitation_service.get_pending_invitations_by_email(
                "accepted@example.com"
            )

            assert len(pending) == 1
            assert len(accepted) == 0

    def test_cleanup_expired_invitations(
        self, app, invitation_service, test_user, test_project
    ):
        """Test cleaning up expired invitations."""
        with app.app_context():
            # Create a pending invitation that will expire
            expires_at = datetime.utcnow() - timedelta(days=1)
            invitation = Invitation.create(
                project_id=test_project.id,
                email="expired@example.com",
                token="expired-token",
                created_by=test_user.id,
                expires_at=expires_at,
            )

            # Run cleanup
            count = invitation_service.cleanup_expired_invitations()

            assert count >= 1

            # Refresh the invitation from DB
            invitation.refresh()
            assert invitation.status == InvitationStatus.EXPIRED


# ============================================================================
# Tests for Invitation API Endpoints
# ============================================================================


class TestInvitationAPI:
    """Tests for the Invitation API endpoints."""

    def test_create_invitation_endpoint(self, client, app, test_user, test_project):
        """Test the POST /api/invitations endpoint."""
        with app.app_context():
            response = client.post(
                "/api/invitations",
                json={
                    "project_id": test_project.id,
                    "email": "apiuser@example.com",
                    "role": "member",
                },
            )

            assert response.status_code == 201
            data = response.get_json()
            assert data["email"] == "apiuser@example.com"
            assert data["project_id"] == test_project.id
            assert data["role"] == "member"
            assert data["status"] == "PENDING"

    def test_get_invitation_by_token_endpoint(
        self, client, app, test_user, test_project
    ):
        """Test the GET /api/invitations/<token> endpoint."""
        with app.app_context():
            # Create an invitation
            invitation = Invitation.create(
                project_id=test_project.id,
                email="getbytoken@example.com",
                token="api-test-token",
                created_by=test_user.id,
            )

            response = client.get(f"/api/invitations/{invitation.token}")

            assert response.status_code == 200
            data = response.get_json()
            assert data["email"] == "getbytoken@example.com"
            assert data["token"] == "api-test-token"

    def test_get_invitation_by_token_not_found(self, client):
        """Test the GET /api/invitations/<token> endpoint with non-existent token."""
        response = client.get("/api/invitations/non-existent-token")

        assert response.status_code == 404

    def test_accept_invitation_endpoint(self, client, app, test_user, test_project):
        """Test the POST /api/invitations/<token>/accept endpoint."""
        with app.app_context():
            # Create an invitation
            invitation = Invitation.create(
                project_id=test_project.id,
                email="acceptapi@example.com",
                token="api-accept-token",
                created_by=test_user.id,
            )

            response = client.post(
                f"/api/invitations/{invitation.token}/accept",
                json={"user_id": test_user.id},
            )

            assert response.status_code == 200
            data = response.get_json()
            assert data["status"] == "ACCEPTED"

    def test_accept_invitation_missing_user_id(
        self, client, app, test_user, test_project
    ):
        """Test the POST /api/invitations/<token>/accept endpoint without user_id."""
        with app.app_context():
            invitation = Invitation.create(
                project_id=test_project.id,
                email="acceptapi@example.com",
                token="api-accept-token-2",
                created_by=test_user.id,
            )

            response = client.post(
                f"/api/invitations/{invitation.token}/accept",
                json={},
            )

            assert response.status_code == 400

    def test_list_invitations_endpoint(self, client, app, test_user, test_project):
        """Test the GET /api/invitations endpoint."""
        with app.app_context():
            # Create some invitations
            Invitation.create(
                project_id=test_project.id,
                email="list1@example.com",
                token="list-token-1",
                created_by=test_user.id,
            )
            Invitation.create(
                project_id=test_project.id,
                email="list2@example.com",
                token="list-token-2",
                created_by=test_user.id,
            )

            response = client.get("/api/invitations")

            assert response.status_code == 200
            data = response.get_json()
            assert isinstance(data, list)
            assert len(data) >= 2

    def test_get_project_invitations_endpoint(
        self, client, app, test_user, test_project
    ):
        """Test the GET /api/projects/<project_id>/invitations endpoint."""
        with app.app_context():
            # Create invitations for the project
            Invitation.create(
                project_id=test_project.id,
                email="project1@example.com",
                token="project-token-1",
                created_by=test_user.id,
            )
            Invitation.create(
                project_id=test_project.id,
                email="project2@example.com",
                token="project-token-2",
                created_by=test_user.id,
            )

            response = client.get(f"/api/projects/{test_project.id}/invitations")

            assert response.status_code == 200
            data = response.get_json()
            assert isinstance(data, list)
            assert len(data) == 2

    def test_get_project_invitations_not_found(self, client):
        """Test the GET /api/projects/<project_id>/invitations endpoint with non-existent project."""
        response = client.get("/api/projects/99999/invitations")

        assert response.status_code == 404
