# Tests for Google Drive Integration Adapter
# Version: 0.5.0 (Épic 7 - US-051)

"""
Unit tests for the GoogleDriveIntegrationAdapter class.
"""

import base64
from unittest.mock import MagicMock, patch

import pytest

from ..adapters.google_drive_adapter import GoogleDriveIntegrationAdapter
from ..base_adapter import ActionNotSupportedError, AuthenticationError
from ..integration_types import (
    IntegrationAction,
    IntegrationConfig,
    IntegrationCredentials,
    IntegrationResult,
    IntegrationType,
)


@pytest.fixture
def google_drive_adapter():
    """Create a test GoogleDriveIntegrationAdapter instance."""
    config = IntegrationConfig(
        id=1,
        integration_type=IntegrationType.GOOGLE_DRIVE,
        name="Test Google Drive",
        credentials=IntegrationCredentials(
            access_token="test_token",
        ),
    )
    return GoogleDriveIntegrationAdapter(config)


@pytest.fixture
def google_drive_adapter_no_creds():
    """Create a GoogleDriveIntegrationAdapter without credentials."""
    config = IntegrationConfig(
        id=1,
        integration_type=IntegrationType.GOOGLE_DRIVE,
        name="Test Google Drive",
        credentials=IntegrationCredentials(),
    )
    return GoogleDriveIntegrationAdapter(config)


@pytest.fixture
def google_drive_adapter_api_key():
    """Create a GoogleDriveIntegrationAdapter with API key."""
    config = IntegrationConfig(
        id=1,
        integration_type=IntegrationType.GOOGLE_DRIVE,
        name="Test Google Drive",
        credentials=IntegrationCredentials(
            api_key="test_api_key",
        ),
    )
    return GoogleDriveIntegrationAdapter(config)


class TestGoogleDriveIntegrationAdapter:
    """Tests for GoogleDriveIntegrationAdapter."""

    def test_adapter_properties(self, google_drive_adapter):
        """Test adapter properties."""
        assert google_drive_adapter.type == IntegrationType.GOOGLE_DRIVE
        assert google_drive_adapter.name == "Google Drive"
        assert (
            google_drive_adapter.description
            == "Intégration avec Google Drive pour stocker et gérer des fichiers"
        )
        assert google_drive_adapter.auth_type.value == "oauth2"
        assert "list_files" in google_drive_adapter.supported_actions
        assert "upload_file" in google_drive_adapter.supported_actions
        assert "download_file" in google_drive_adapter.supported_actions
        assert "create_folder" in google_drive_adapter.supported_actions
        assert "get_quota" in google_drive_adapter.supported_actions

    def test_is_action_supported(self, google_drive_adapter):
        """Test checking if action is supported."""
        assert google_drive_adapter.is_action_supported("list_files") is True
        assert google_drive_adapter.is_action_supported("upload_file") is True
        assert google_drive_adapter.is_action_supported("get_quota") is True
        assert google_drive_adapter.is_action_supported("unknown_action") is False

    def test_get_metadata(self, google_drive_adapter):
        """Test getting adapter metadata."""
        metadata = google_drive_adapter.get_metadata()

        assert metadata["type"] == "google_drive"
        assert metadata["name"] == "Google Drive"
        assert metadata["auth_type"] == "oauth2"
        assert "list_files" in metadata["supported_actions"]
        assert metadata["icon"] == "google-drive"
        assert metadata["color"] == "#4285F4"

    def test_get_oauth_scopes(self, google_drive_adapter):
        """Test getting OAuth scopes."""
        scopes = google_drive_adapter.get_oauth_scopes()

        assert isinstance(scopes, list)
        assert len(scopes) > 0
        assert "https://www.googleapis.com/auth/drive" in scopes
        assert "https://www.googleapis.com/auth/drive.file" in scopes
        assert "https://www.googleapis.com/auth/drive.metadata" in scopes

    def test_get_configuration_schema(self, google_drive_adapter):
        """Test getting configuration schema."""
        schema = google_drive_adapter.get_configuration_schema()

        assert isinstance(schema, dict)
        assert "properties" in schema
        assert "name" in schema["properties"]
        assert "settings" in schema["properties"]
        assert "root_folder_id" in schema["properties"]["settings"]["properties"]
        assert "auto_organize" in schema["properties"]["settings"]["properties"]

    def test_get_action_schema(self, google_drive_adapter):
        """Test getting action schema."""
        schema = google_drive_adapter.get_action_schema("upload_file")

        assert isinstance(schema, dict)

        # Test with unsupported action
        with pytest.raises(ValueError):
            google_drive_adapter.get_action_schema("unknown_action")

    def test_authentication_with_access_token(self, google_drive_adapter):
        """Test authentication with access token."""
        headers = google_drive_adapter._get_auth_headers()

        assert "Authorization" in headers
        assert headers["Authorization"] == "Bearer test_token"

    def test_authentication_with_api_key(self, google_drive_adapter_api_key):
        """Test authentication with API key."""
        headers = google_drive_adapter_api_key._get_auth_headers()

        assert "Authorization" in headers
        assert headers["Authorization"] == "Bearer test_api_key"

    def test_authentication_without_credentials(self, google_drive_adapter_no_creds):
        """Test authentication without credentials."""
        with pytest.raises(AuthenticationError):
            google_drive_adapter_no_creds._get_auth_headers()

    def test_build_search_query_root(self, google_drive_adapter):
        """Test building search query for root folder."""
        result = google_drive_adapter._build_search_query("root", "")
        assert result == "trashed = false"

    def test_build_search_query_with_folder(self, google_drive_adapter):
        """Test building search query with folder ID."""
        result = google_drive_adapter._build_search_query("folder-123", "")
        assert "'folder-123' in parents" in result
        assert "trashed = false" in result

    def test_build_search_query_with_custom(self, google_drive_adapter):
        """Test building search query with custom query."""
        result = google_drive_adapter._build_search_query("root", "name = 'test.txt'")
        assert "name = 'test.txt'" in result
        assert "trashed = false" in result

    @patch.object(GoogleDriveIntegrationAdapter, "_make_request")
    def test_test_connection_success(self, mock_make_request, google_drive_adapter):
        """Test successful connection test."""
        mock_make_request.return_value = {
            "sub": "1234567890",
            "email": "test@example.com",
            "name": "Test User",
            "picture": "https://picture.url",
        }

        result = google_drive_adapter.test_connection()

        assert result.success is True
        assert "user" in result.data
        assert result.data["user"]["id"] == "1234567890"
        assert result.data["user"]["email"] == "test@example.com"

    @patch.object(GoogleDriveIntegrationAdapter, "_make_request")
    def test_test_connection_failure(self, mock_make_request, google_drive_adapter):
        """Test failed connection test."""
        mock_make_request.side_effect = Exception("Connection failed")

        result = google_drive_adapter.test_connection()

        assert result.success is False
        assert "Connection failed" in result.error

    @patch.object(GoogleDriveIntegrationAdapter, "_make_request")
    def test_get_quota(self, mock_make_request, google_drive_adapter):
        """Test getting quota information."""
        mock_make_request.return_value = {
            "storageQuota": {
                "limit": 10737418240,  # 10 Go
                "usage": 1073741824,  # 1 Go
                "usageInDrive": 1073741824,
                "usageInDriveTrash": 0,
            }
        }

        result = google_drive_adapter._get_quota({})

        assert result.success is True
        assert result.data["quota"]["limit"] == 10737418240
        assert result.data["quota"]["usage"] == 1073741824
        assert result.data["percentage_used"] == pytest.approx(10.0)

    @patch.object(GoogleDriveIntegrationAdapter, "_make_request")
    def test_list_files(self, mock_make_request, google_drive_adapter):
        """Test listing files."""
        mock_make_request.return_value = {
            "files": [
                {
                    "id": "file-1",
                    "name": "document.txt",
                    "mimeType": "text/plain",
                    "size": "1024",
                    "createdTime": "2023-01-01T00:00:00Z",
                    "modifiedTime": "2023-01-02T00:00:00Z",
                    "parents": ["folder-1"],
                    "webViewLink": "https://drive.google.com/file/d/file-1",
                },
                {
                    "id": "file-2",
                    "name": "image.png",
                    "mimeType": "image/png",
                    "size": "2048",
                    "parents": ["folder-1"],
                },
            ],
            "nextPageToken": "token-123",
        }

        result = google_drive_adapter._list_files(
            {
                "folder_id": "folder-1",
                "page_size": 100,
            }
        )

        assert result.success is True
        assert len(result.data["files"]) == 2
        assert result.data["count"] == 2
        assert result.data["next_page_token"] == "token-123"

    @patch.object(GoogleDriveIntegrationAdapter, "_make_request")
    def test_search_files(self, mock_make_request, google_drive_adapter):
        """Test searching files."""
        mock_make_request.return_value = {
            "files": [
                {
                    "id": "file-1",
                    "name": "test.txt",
                    "mimeType": "text/plain",
                    "size": "1024",
                },
            ],
            "nextPageToken": None,
        }

        result = google_drive_adapter._search_files(
            {
                "query": "name = 'test.txt'",
                "page_size": 100,
            }
        )

        assert result.success is True
        assert len(result.data["files"]) == 1
        assert result.data["query"] == "name = 'test.txt'"

    @patch.object(GoogleDriveIntegrationAdapter, "_make_request")
    def test_get_file_metadata(self, mock_make_request, google_drive_adapter):
        """Test getting file metadata."""
        mock_make_request.return_value = {
            "id": "file-123",
            "name": "test.txt",
            "mimeType": "text/plain",
            "size": "1024",
            "createdTime": "2023-01-01T00:00:00Z",
            "modifiedTime": "2023-01-02T00:00:00Z",
            "parents": ["folder-1"],
            "webViewLink": "https://drive.google.com/file/d/file-123",
            "webContentLink": "https://drive.google.com/uc?id=file-123",
        }

        result = google_drive_adapter._get_file_metadata(
            {
                "file_id": "file-123",
            }
        )

        assert result.success is True
        assert result.data["metadata"]["id"] == "file-123"
        assert result.data["metadata"]["name"] == "test.txt"

    @patch.object(GoogleDriveIntegrationAdapter, "_make_request")
    def test_list_folders(self, mock_make_request, google_drive_adapter):
        """Test listing folders."""
        mock_make_request.return_value = {
            "files": [
                {
                    "id": "folder-1",
                    "name": "Documents",
                    "mimeType": "application/vnd.google-apps.folder",
                    "createdTime": "2023-01-01T00:00:00Z",
                    "modifiedTime": "2023-01-02T00:00:00Z",
                },
                {
                    "id": "folder-2",
                    "name": "Images",
                    "mimeType": "application/vnd.google-apps.folder",
                },
            ],
            "nextPageToken": None,
        }

        result = google_drive_adapter._list_folders(
            {
                "parent_id": "root",
                "page_size": 100,
            }
        )

        assert result.success is True
        assert len(result.data["folders"]) == 2
        assert result.data["count"] == 2

    @patch.object(GoogleDriveIntegrationAdapter, "_make_request")
    def test_get_folder(self, mock_make_request, google_drive_adapter):
        """Test getting a folder."""
        mock_make_request.return_value = {
            "id": "folder-123",
            "name": "Documents",
            "mimeType": "application/vnd.google-apps.folder",
            "createdTime": "2023-01-01T00:00:00Z",
            "modifiedTime": "2023-01-02T00:00:00Z",
            "parents": ["root"],
            "size": "100",
        }

        result = google_drive_adapter._get_folder(
            {
                "folder_id": "folder-123",
            }
        )

        assert result.success is True
        assert result.data["folder"]["id"] == "folder-123"
        assert result.data["folder"]["name"] == "Documents"

    @patch.object(GoogleDriveIntegrationAdapter, "_make_request")
    def test_create_folder(self, mock_make_request, google_drive_adapter):
        """Test creating a folder."""
        mock_make_request.return_value = {
            "id": "folder-new",
            "name": "New Folder",
            "mimeType": "application/vnd.google-apps.folder",
            "parents": ["folder-1"],
            "webViewLink": "https://drive.google.com/folders/folder-new",
        }

        result = google_drive_adapter._create_folder(
            {
                "name": "New Folder",
                "parent_id": "folder-1",
            }
        )

        assert result.success is True
        assert result.data["folder"]["id"] == "folder-new"
        assert result.data["folder"]["name"] == "New Folder"

    @patch.object(GoogleDriveIntegrationAdapter, "_make_request")
    def test_upload_file(self, mock_make_request, google_drive_adapter):
        """Test uploading a file."""
        mock_make_request.return_value = {
            "id": "file-new",
            "name": "test.txt",
            "mimeType": "text/plain",
            "parents": ["folder-1"],
            "webViewLink": "https://drive.google.com/file/d/file-new",
        }

        result = google_drive_adapter._upload_file(
            {
                "name": "test.txt",
                "content": "Test content",
                "content_type": "text/plain",
                "parent_id": "folder-1",
            }
        )

        assert result.success is True
        assert result.data["file"]["id"] == "file-new"
        assert result.data["uploaded"] is True
        assert result.data["size"] == 12  # len("Test content")

    @patch.object(GoogleDriveIntegrationAdapter, "_make_request")
    def test_get_file(self, mock_make_request, google_drive_adapter):
        """Test downloading a file."""
        # Mock metadata request
        with patch.object(google_drive_adapter, "_get_file_metadata") as mock_metadata:
            mock_metadata.return_value = IntegrationResult(
                success=True,
                data={
                    "metadata": {
                        "id": "file-123",
                        "name": "test.txt",
                        "mimeType": "text/plain",
                    }
                },
            )

            # Mock file content request
            mock_make_request.return_value = b"Test file content"

            result = google_drive_adapter._get_file({"file_id": "file-123"})

            assert result.success is True
            assert "content" in result.data
            # Le contenu doit être encodé en base64
            assert (
                result.data["content"]
                == base64.b64encode(b"Test file content").decode()
            )

    @patch.object(GoogleDriveIntegrationAdapter, "_make_request")
    def test_delete_file(self, mock_make_request, google_drive_adapter):
        """Test deleting a file."""
        # _make_request retourne None pour une réponse 204
        mock_make_request.return_value = None

        result = google_drive_adapter._delete_file({"file_id": "file-123"})

        assert result.success is True
        assert result.data["deleted"] is True
        assert result.data["file_id"] == "file-123"

    @patch.object(GoogleDriveIntegrationAdapter, "_make_request")
    def test_copy_file(self, mock_make_request, google_drive_adapter):
        """Test copying a file."""
        mock_make_request.return_value = {
            "id": "file-copy",
            "name": "test_copy.txt",
            "mimeType": "text/plain",
            "parents": ["folder-2"],
        }

        result = google_drive_adapter._copy_file(
            {
                "file_id": "file-123",
                "name": "test_copy.txt",
                "parent_id": "folder-2",
            }
        )

        assert result.success is True
        assert result.data["file"]["id"] == "file-copy"
        assert result.data["copied_from"] == "file-123"

    @patch.object(GoogleDriveIntegrationAdapter, "_make_request")
    def test_move_file(self, mock_make_request, google_drive_adapter):
        """Test moving a file."""
        # Mock get_file_metadata
        with patch.object(google_drive_adapter, "_get_file_metadata") as mock_metadata:
            mock_metadata.return_value = IntegrationResult(
                success=True,
                data={
                    "metadata": {
                        "id": "file-123",
                        "parents": ["folder-1"],
                    }
                },
            )

            mock_make_request.return_value = {
                "id": "file-123",
                "name": "test.txt",
                "parents": ["folder-2"],
            }

            result = google_drive_adapter._move_file(
                {
                    "file_id": "file-123",
                    "new_parent_id": "folder-2",
                    "remove_old_parents": True,
                }
            )

            assert result.success is True
            assert result.data["moved_to"] == "folder-2"

    @patch.object(GoogleDriveIntegrationAdapter, "_make_request")
    def test_update_file_metadata(self, mock_make_request, google_drive_adapter):
        """Test updating file metadata."""
        mock_make_request.return_value = {
            "id": "file-123",
            "name": "renamed.txt",
            "description": "Updated description",
            "mimeType": "text/plain",
        }

        result = google_drive_adapter._update_file_metadata(
            {
                "file_id": "file-123",
                "metadata": {
                    "name": "renamed.txt",
                    "description": "Updated description",
                },
            }
        )

        assert result.success is True
        assert result.data["file"]["name"] == "renamed.txt"
        assert "name" in result.data["updated_fields"]
        assert "description" in result.data["updated_fields"]

    @patch.object(GoogleDriveIntegrationAdapter, "_make_request")
    def test_get_permissions(self, mock_make_request, google_drive_adapter):
        """Test getting file permissions."""
        mock_make_request.return_value = {
            "permissions": [
                {
                    "id": "perm-1",
                    "type": "user",
                    "role": "owner",
                    "emailAddress": "owner@example.com",
                    "displayName": "Owner",
                },
                {
                    "id": "perm-2",
                    "type": "user",
                    "role": "reader",
                    "emailAddress": "reader@example.com",
                    "displayName": "Reader",
                },
            ],
        }

        result = google_drive_adapter._get_permissions({"file_id": "file-123"})

        assert result.success is True
        assert len(result.data["permissions"]) == 2
        assert result.data["count"] == 2

    @patch.object(GoogleDriveIntegrationAdapter, "_make_request")
    def test_add_permission(self, mock_make_request, google_drive_adapter):
        """Test adding a permission."""
        mock_make_request.return_value = {
            "id": "perm-new",
            "type": "user",
            "role": "reader",
            "emailAddress": "new@example.com",
        }

        result = google_drive_adapter._add_permission(
            {
                "file_id": "file-123",
                "email": "new@example.com",
                "role": "reader",
                "type": "user",
            }
        )

        assert result.success is True
        assert result.data["permission"]["id"] == "perm-new"

    @patch.object(GoogleDriveIntegrationAdapter, "_make_request")
    def test_remove_permission(self, mock_make_request, google_drive_adapter):
        """Test removing a permission."""
        # _make_request retourne None pour une réponse 204
        mock_make_request.return_value = None

        result = google_drive_adapter._remove_permission(
            {
                "file_id": "file-123",
                "permission_id": "perm-1",
            }
        )

        assert result.success is True
        assert result.data["removed"] is True
        assert result.data["permission_id"] == "perm-1"

    def test_execute_supported_action(self, google_drive_adapter):
        """Test executing a supported action."""
        with patch.object(google_drive_adapter, "_list_files") as mock_list_files:
            mock_list_files.return_value = IntegrationResult(
                success=True,
                data={"files": [], "count": 0},
            )

            action = IntegrationAction(
                action_type="list_files",
                payload={"folder_id": "root"},
            )

            result = google_drive_adapter.execute(action)

            assert result.success is True
            mock_list_files.assert_called_once()

    def test_execute_unsupported_action(self, google_drive_adapter):
        """Test executing an unsupported action."""
        action = IntegrationAction(
            action_type="unknown_action",
            payload={},
        )

        with pytest.raises(ActionNotSupportedError):
            google_drive_adapter.execute(action)

    def test_get_authentication_url(self, google_drive_adapter):
        """Test getting authentication URL."""
        # Mock OAuth config
        google_drive_adapter.oauth_config = MagicMock()
        google_drive_adapter.oauth_config.client_id = "test_client_id"
        google_drive_adapter.oauth_config.redirect_uri = "https://callback.com"
        google_drive_adapter.oauth_config.scope = [
            "https://www.googleapis.com/auth/drive",
            "https://www.googleapis.com/auth/drive.file",
        ]
        google_drive_adapter.oauth_config.authorization_url = (
            "https://accounts.google.com/o/oauth2/v2/auth"
        )

        url = google_drive_adapter.get_authentication_url()

        assert "https://accounts.google.com/o/oauth2/v2/auth" in url
        assert "client_id=test_client_id" in url
        # L'URL est encodée
        assert "redirect_uri=" in url
        assert "response_type=code" in url
        assert "access_type=offline" in url
        assert "scope=" in url

    @patch("requests.post")
    def test_exchange_code_for_token(self, mock_post, google_drive_adapter):
        """Test exchanging code for token."""
        # Mock OAuth config
        google_drive_adapter.oauth_config = MagicMock()
        google_drive_adapter.oauth_config.client_id = "test_client_id"
        google_drive_adapter.oauth_config.client_secret = "test_client_secret"
        google_drive_adapter.oauth_config.redirect_uri = "https://callback.com"
        google_drive_adapter.oauth_config.token_url = (
            "https://oauth2.googleapis.com/token"
        )

        # Mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "access_token": "test_access_token",
            "refresh_token": "test_refresh_token",
            "expires_in": 3600,
        }
        mock_post.return_value = mock_response

        credentials = google_drive_adapter.exchange_code_for_token("test_code")

        assert credentials.access_token == "test_access_token"
        assert credentials.refresh_token == "test_refresh_token"
        assert credentials.token_expiry is not None

    @patch("requests.post")
    def test_refresh_token(self, mock_post, google_drive_adapter):
        """Test refreshing token."""
        # Mock OAuth config
        google_drive_adapter.oauth_config = MagicMock()
        google_drive_adapter.oauth_config.client_id = "test_client_id"
        google_drive_adapter.oauth_config.client_secret = "test_client_secret"
        google_drive_adapter.oauth_config.token_url = (
            "https://oauth2.googleapis.com/token"
        )

        # Mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "access_token": "new_access_token",
            "expires_in": 3600,
        }
        mock_post.return_value = mock_response

        credentials = google_drive_adapter.refresh_token("test_refresh_token")

        assert credentials.access_token == "new_access_token"
        assert credentials.refresh_token == "test_refresh_token"

    def test_authenticate_success(self, google_drive_adapter):
        """Test successful authentication."""
        credentials = IntegrationCredentials(
            access_token="valid_token",
        )

        with patch.object(google_drive_adapter, "test_connection") as mock_test:
            mock_test.return_value = IntegrationResult(success=True)

            result = google_drive_adapter.authenticate(credentials)

            assert result is True

    def test_authenticate_failure(self, google_drive_adapter):
        """Test failed authentication."""
        credentials = IntegrationCredentials(
            access_token="invalid_token",
        )

        with patch.object(google_drive_adapter, "test_connection") as mock_test:
            mock_test.return_value = IntegrationResult(success=False)

            result = google_drive_adapter.authenticate(credentials)

            assert result is False
