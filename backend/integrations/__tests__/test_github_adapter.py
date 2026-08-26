# Tests for GitHub Integration Adapter
# Version: 0.5.0 (Épic 7 - US-047)

"""
Unit tests for the GitHubIntegrationAdapter class.
"""

import pytest
from unittest.mock import MagicMock, patch

from ..integration_types import (
    IntegrationAction,
    IntegrationConfig,
    IntegrationCredentials,
    IntegrationType,
)
from ..adapters.github_adapter import GitHubIntegrationAdapter
from ..base_adapter import ActionNotSupportedError, AuthenticationError


@pytest.fixture
def github_adapter():
    """Create a test GitHubIntegrationAdapter instance."""
    config = IntegrationConfig(
        id=1,
        integration_type=IntegrationType.GITHUB,
        name="Test GitHub",
        credentials=IntegrationCredentials(
            access_token="test_token",
        ),
    )
    return GitHubIntegrationAdapter(config)


@pytest.fixture
def github_adapter_no_creds():
    """Create a GitHubIntegrationAdapter without credentials."""
    config = IntegrationConfig(
        id=1,
        integration_type=IntegrationType.GITHUB,
        name="Test GitHub",
        credentials=IntegrationCredentials(),
    )
    return GitHubIntegrationAdapter(config)


class TestGitHubIntegrationAdapter:
    """Tests for GitHubIntegrationAdapter."""

    def test_adapter_properties(self, github_adapter):
        """Test adapter properties."""
        assert github_adapter.type == IntegrationType.GITHUB
        assert github_adapter.name == "GitHub"
        assert github_adapter.description == "Intégration avec GitHub pour gérer des repositories, PR et issues"
        assert github_adapter.auth_type.value == "oauth2"
        assert "create_pull_request" in github_adapter.supported_actions
        assert "create_issue" in github_adapter.supported_actions
        assert "list_repositories" in github_adapter.supported_actions

    def test_is_action_supported(self, github_adapter):
        """Test checking if action is supported."""
        assert github_adapter.is_action_supported("create_pull_request") is True
        assert github_adapter.is_action_supported("create_issue") is True
        assert github_adapter.is_action_supported("unknown_action") is False

    def test_get_metadata(self, github_adapter):
        """Test getting adapter metadata."""
        metadata = github_adapter.get_metadata()
        
        assert metadata["type"] == "github"
        assert metadata["name"] == "GitHub"
        assert metadata["auth_type"] == "oauth2"
        assert "create_pull_request" in metadata["supported_actions"]

    def test_get_oauth_scopes(self, github_adapter):
        """Test getting OAuth scopes."""
        scopes = github_adapter.get_oauth_scopes()
        
        assert isinstance(scopes, list)
        assert len(scopes) > 0
        assert "repo" in scopes

    def test_get_configuration_schema(self, github_adapter):
        """Test getting configuration schema."""
        schema = github_adapter.get_configuration_schema()
        
        assert isinstance(schema, dict)
        assert "properties" in schema
        assert "name" in schema["properties"]

    def test_get_action_schema(self, github_adapter):
        """Test getting action schema."""
        schema = github_adapter.get_action_schema("create_pull_request")
        
        assert isinstance(schema, dict)
        
        # Test with unsupported action
        with pytest.raises(ValueError):
            github_adapter.get_action_schema("unknown_action")

    def test_authenticate_with_valid_credentials(self, github_adapter_no_creds):
        """Test authentication with valid credentials."""
        credentials = IntegrationCredentials(access_token="valid_token")
        
        with patch.object(github_adapter_no_creds, 'test_connection') as mock_test:
            mock_test.return_value.success = True
            result = github_adapter_no_creds.authenticate(credentials)
            assert result is True

    def test_authenticate_with_invalid_credentials(self, github_adapter_no_creds):
        """Test authentication with invalid credentials."""
        credentials = IntegrationCredentials(access_token="invalid_token")
        
        with patch.object(github_adapter_no_creds, 'test_connection') as mock_test:
            mock_test.return_value.success = False
            result = github_adapter_no_creds.authenticate(credentials)
            assert result is False

    @patch('requests.Session.get')
    def test_test_connection_success(self, mock_get, github_adapter):
        """Test connection test with valid credentials."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"login": "test_user"}
        mock_get.return_value = mock_response
        
        result = github_adapter.test_connection()
        
        assert result.success is True
        assert result.data["user"] == "test_user"

    @patch('requests.Session.get')
    def test_test_connection_failure(self, mock_get, github_adapter):
        """Test connection test with invalid credentials."""
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_get.return_value = mock_response
        
        result = github_adapter.test_connection()
        
        assert result.success is False

    @patch('requests.Session.get')
    def test_execute_list_repositories(self, mock_get, github_adapter):
        """Test executing list_repositories action."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {"name": "repo1", "full_name": "user/repo1"},
            {"name": "repo2", "full_name": "user/repo2"},
        ]
        mock_get.return_value = mock_response
        
        action = IntegrationAction(
            action_type="list_repositories",
            payload={"visibility": "all"},
        )
        
        result = github_adapter.execute(action)
        
        assert result.success is True
        assert "repositories" in result.data
        assert len(result.data["repositories"]) == 2

    def test_execute_unsupported_action(self, github_adapter):
        """Test executing unsupported action."""
        action = IntegrationAction(action_type="unsupported_action")
        
        with pytest.raises(ActionNotSupportedError):
            github_adapter.execute(action)

    def test_execute_missing_required_fields(self, github_adapter):
        """Test executing action with missing required fields."""
        # Test create_pull_request without required fields
        action = IntegrationAction(
            action_type="create_pull_request",
            payload={},  # Missing owner, repo, title, head, base
        )
        
        result = github_adapter.execute(action)
        
        assert result.success is False
        assert "required" in result.error.lower()

    def test_get_authentication_url(self, github_adapter):
        """Test generating authentication URL."""
        url, state = github_adapter.get_authentication_url()
        
        assert isinstance(url, str)
        assert "github.com/login/oauth/authorize" in url
        assert "client_id" in url
        assert "scope" in url
        assert "state" in url
        assert isinstance(state, str)
        assert len(state) > 0

    def test_exchange_code_for_token(self, github_adapter):
        """Test exchanging code for token."""
        with patch('requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "access_token": "test_access_token",
                "token_type": "bearer",
                "scope": "repo user",
            }
            mock_post.return_value = mock_response
            
            credentials = github_adapter.exchange_code_for_token("test_code")
            
            assert credentials.access_token == "test_access_token"
            assert credentials.token_type == "bearer"

    def test_refresh_token_not_supported(self, github_adapter):
        """Test that GitHub doesn't support token refresh."""
        with pytest.raises(NotImplementedError):
            github_adapter.refresh_token("refresh_token")


class TestGitHubActionHandlers:
    """Tests for GitHub action handlers."""

    @patch('requests.Session.get')
    def test_get_repository(self, mock_get, github_adapter):
        """Test getting repository info."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "name": "test-repo",
            "full_name": "user/test-repo",
            "private": False,
        }
        mock_get.return_value = mock_response
        
        action = IntegrationAction(
            action_type="get_repository",
            payload={
                "owner": "user",
                "repo": "test-repo",
            },
        )
        
        result = github_adapter.execute(action)
        
        assert result.success is True
        assert result.data["repository"]["name"] == "test-repo"

    @patch('requests.Session.post')
    def test_create_issue(self, mock_post, github_adapter):
        """Test creating an issue."""
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            "number": 1,
            "title": "Test Issue",
            "body": "This is a test issue",
        }
        mock_post.return_value = mock_response
        
        action = IntegrationAction(
            action_type="create_issue",
            payload={
                "owner": "user",
                "repo": "test-repo",
                "title": "Test Issue",
                "body": "This is a test issue",
            },
        )
        
        result = github_adapter.execute(action)
        
        assert result.success is True
        assert result.data["issue"]["title"] == "Test Issue"

    @patch('requests.Session.post')
    def test_comment_issue(self, mock_post, github_adapter):
        """Test commenting on an issue."""
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            "id": 1,
            "body": "Test comment",
        }
        mock_post.return_value = mock_response
        
        action = IntegrationAction(
            action_type="comment_issue",
            payload={
                "owner": "user",
                "repo": "test-repo",
                "issue_number": 1,
                "body": "Test comment",
            },
        )
        
        result = github_adapter.execute(action)
        
        assert result.success is True
        assert result.data["comment"]["body"] == "Test comment"

    @patch('requests.Session.put')
    def test_create_file(self, mock_put, github_adapter):
        """Test creating a file."""
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            "path": "test.txt",
            "content": {"name": "test.txt"},
        }
        mock_put.return_value = mock_response
        
        action = IntegrationAction(
            action_type="create_file",
            payload={
                "owner": "user",
                "repo": "test-repo",
                "path": "test.txt",
                "content": "Test content",
                "message": "Add test file",
                "branch": "main",
            },
        )
        
        result = github_adapter.execute(action)
        
        assert result.success is True
        assert result.data["file"]["path"] == "test.txt"

    @patch('requests.Session.get')
    def test_get_file(self, mock_get, github_adapter):
        """Test getting file content."""
        import base64
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "path": "test.txt",
            "content": base64.b64encode(b"Test content").decode(),
            "encoding": "base64",
        }
        mock_get.return_value = mock_response
        
        action = IntegrationAction(
            action_type="get_file",
            payload={
                "owner": "user",
                "repo": "test-repo",
                "path": "test.txt",
            },
        )
        
        result = github_adapter.execute(action)
        
        assert result.success is True
        assert result.data["file"]["path"] == "test.txt"
        assert "content_decoded" in result.data["file"]
        assert result.data["file"]["content_decoded"] == "Test content"
