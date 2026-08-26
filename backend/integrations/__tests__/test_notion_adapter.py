# Tests for Notion Integration Adapter
# Version: 0.5.0 (Épic 7 - US-050)

"""
Unit tests for the NotionIntegrationAdapter class.
"""

import pytest
from unittest.mock import MagicMock, patch
from urllib.parse import quote

from ..integration_types import (
    IntegrationAction,
    IntegrationConfig,
    IntegrationCredentials,
    IntegrationResult,
    IntegrationType,
)
from ..adapters.notion_adapter import NotionIntegrationAdapter
from ..base_adapter import ActionNotSupportedError, AuthenticationError


@pytest.fixture
def notion_adapter():
    """Create a test NotionIntegrationAdapter instance."""
    config = IntegrationConfig(
        id=1,
        integration_type=IntegrationType.NOTION,
        name="Test Notion",
        credentials=IntegrationCredentials(
            access_token="test_token",
        ),
    )
    return NotionIntegrationAdapter(config)


@pytest.fixture
def notion_adapter_no_creds():
    """Create a NotionIntegrationAdapter without credentials."""
    config = IntegrationConfig(
        id=1,
        integration_type=IntegrationType.NOTION,
        name="Test Notion",
        credentials=IntegrationCredentials(),
    )
    return NotionIntegrationAdapter(config)


@pytest.fixture
def notion_adapter_api_key():
    """Create a NotionIntegrationAdapter with API key."""
    config = IntegrationConfig(
        id=1,
        integration_type=IntegrationType.NOTION,
        name="Test Notion",
        credentials=IntegrationCredentials(
            api_key="test_api_key",
        ),
    )
    return NotionIntegrationAdapter(config)


class TestNotionIntegrationAdapter:
    """Tests for NotionIntegrationAdapter."""

    def test_adapter_properties(self, notion_adapter):
        """Test adapter properties."""
        assert notion_adapter.type == IntegrationType.NOTION
        assert notion_adapter.name == "Notion"
        assert notion_adapter.description == "Intégration avec Notion pour synchroniser des bases de données et créer des pages"
        assert notion_adapter.auth_type.value == "oauth2"
        assert "create_page" in notion_adapter.supported_actions
        assert "query_database" in notion_adapter.supported_actions
        assert "sync_database" in notion_adapter.supported_actions
        assert "get_current_user" in notion_adapter.supported_actions

    def test_is_action_supported(self, notion_adapter):
        """Test checking if action is supported."""
        assert notion_adapter.is_action_supported("create_page") is True
        assert notion_adapter.is_action_supported("query_database") is True
        assert notion_adapter.is_action_supported("sync_database") is True
        assert notion_adapter.is_action_supported("unknown_action") is False

    def test_get_metadata(self, notion_adapter):
        """Test getting adapter metadata."""
        metadata = notion_adapter.get_metadata()
        
        assert metadata["type"] == "notion"
        assert metadata["name"] == "Notion"
        assert metadata["auth_type"] == "oauth2"
        assert "create_page" in metadata["supported_actions"]
        assert metadata["icon"] == "notion"
        assert metadata["color"] == "#000000"

    def test_get_oauth_scopes(self, notion_adapter):
        """Test getting OAuth scopes."""
        scopes = notion_adapter.get_oauth_scopes()
        
        assert isinstance(scopes, list)
        assert len(scopes) > 0
        assert "read:user" in scopes
        assert "read:page" in scopes
        assert "write:page" in scopes
        assert "read:database" in scopes
        assert "write:database" in scopes

    def test_get_configuration_schema(self, notion_adapter):
        """Test getting configuration schema."""
        schema = notion_adapter.get_configuration_schema()
        
        assert isinstance(schema, dict)
        assert "properties" in schema
        assert "name" in schema["properties"]
        assert "settings" in schema["properties"]
        assert "default_database_id" in schema["properties"]["settings"]["properties"]
        assert "auto_sync" in schema["properties"]["settings"]["properties"]

    def test_get_action_schema(self, notion_adapter):
        """Test getting action schema."""
        schema = notion_adapter.get_action_schema("create_page")
        
        assert isinstance(schema, dict)
        
        # Test with unsupported action
        with pytest.raises(ValueError):
            notion_adapter.get_action_schema("unknown_action")

    def test_authentication_with_access_token(self, notion_adapter):
        """Test authentication with access token."""
        headers = notion_adapter._get_auth_headers()
        
        assert "Authorization" in headers
        assert headers["Authorization"] == "Bearer test_token"

    def test_authentication_with_api_key(self, notion_adapter_api_key):
        """Test authentication with API key."""
        headers = notion_adapter_api_key._get_auth_headers()
        
        assert "Authorization" in headers
        assert headers["Authorization"] == "Bearer test_api_key"

    def test_authentication_without_credentials(self, notion_adapter_no_creds):
        """Test authentication without credentials."""
        with pytest.raises(AuthenticationError):
            notion_adapter_no_creds._get_auth_headers()

    def test_format_notion_id_with_dashes(self, notion_adapter):
        """Test formatting ID that already has dashes."""
        result = notion_adapter._format_notion_id("123e4567-e89b-12d3-a456-426614174000")
        assert result == "123e4567-e89b-12d3-a456-426614174000"

    def test_format_notion_id_without_dashes(self, notion_adapter):
        """Test formatting ID without dashes (32 characters)."""
        result = notion_adapter._format_notion_id("123e4567e89b12d3a456426614174000")
        assert result == "123e4567-e89b-12d3-a456-426614174000"

    def test_format_notion_id_short(self, notion_adapter):
        """Test formatting short ID."""
        result = notion_adapter._format_notion_id("short")
        assert result == "short"

    def test_format_notion_id_empty(self, notion_adapter):
        """Test formatting empty ID."""
        result = notion_adapter._format_notion_id("")
        assert result == ""

    def test_format_notion_id_none(self, notion_adapter):
        """Test formatting None ID."""
        result = notion_adapter._format_notion_id(None)
        assert result is None

    @patch.object(NotionIntegrationAdapter, '_make_request')
    def test_test_connection_success(self, mock_make_request, notion_adapter):
        """Test successful connection test."""
        mock_make_request.return_value = {
            "object": "user",
            "id": "user-123",
            "name": "Test User",
            "type": "person",
        }
        
        result = notion_adapter.test_connection()
        
        assert result.success is True
        assert "user" in result.data
        assert result.data["user"]["id"] == "user-123"
        assert result.data["user"]["name"] == "Test User"

    @patch.object(NotionIntegrationAdapter, '_make_request')
    def test_test_connection_failure(self, mock_make_request, notion_adapter):
        """Test failed connection test."""
        mock_make_request.side_effect = Exception("Connection failed")
        
        result = notion_adapter.test_connection()
        
        assert result.success is False
        assert "Connection failed" in result.error

    @patch.object(NotionIntegrationAdapter, '_make_request')
    def test_get_current_user(self, mock_make_request, notion_adapter):
        """Test getting current user."""
        mock_make_request.return_value = {
            "object": "user",
            "id": "user-123",
            "name": "Test User",
            "email": "test@example.com",
        }
        
        result = notion_adapter._get_current_user({})
        
        assert result.success is True
        assert result.data["user"]["id"] == "user-123"
        assert result.data["user"]["name"] == "Test User"

    @patch.object(NotionIntegrationAdapter, '_make_request')
    def test_list_databases(self, mock_make_request, notion_adapter):
        """Test listing databases."""
        mock_make_request.return_value = {
            "results": [
                {"object": "database", "id": "db-1", "title": [{"text": {"content": "Test DB"}}]},
                {"object": "page", "id": "page-1", "title": "Not a database"},
                {"object": "database", "id": "db-2", "title": [{"text": {"content": "Another DB"}}]},
            ]
        }
        
        result = notion_adapter._list_databases({"query": "test"})
        
        assert result.success is True
        assert len(result.data["databases"]) == 2
        assert result.data["count"] == 2

    @patch.object(NotionIntegrationAdapter, '_make_request')
    def test_get_database(self, mock_make_request, notion_adapter):
        """Test getting a database."""
        mock_make_request.return_value = {
            "object": "database",
            "id": "db-123",
            "title": [{"text": {"content": "Test Database"}}],
        }
        
        result = notion_adapter._get_database({"database_id": "db-123"})
        
        assert result.success is True
        assert result.data["database"]["id"] == "db-123"

    @patch.object(NotionIntegrationAdapter, '_make_request')
    def test_query_database(self, mock_make_request, notion_adapter):
        """Test querying a database."""
        mock_make_request.return_value = {
            "results": [
                {"id": "page-1", "properties": {"Name": {"title": [{"text": {"content": "Item 1"}}]}}},
                {"id": "page-2", "properties": {"Name": {"title": [{"text": {"content": "Item 2"}}]}}},
            ],
            "has_more": False,
            "next_cursor": None,
        }
        
        result = notion_adapter._query_database({
            "database_id": "db-123",
            "filter": {"property": "Status", "select": {"equals": "Done"}},
        })
        
        assert result.success is True
        assert len(result.data["results"]) == 2
        assert result.data["has_more"] is False
        assert result.data["count"] == 2

    @patch.object(NotionIntegrationAdapter, '_make_request')
    def test_create_page(self, mock_make_request, notion_adapter):
        """Test creating a page."""
        mock_make_request.return_value = {
            "object": "page",
            "id": "page-123",
            "parent": {"type": "database_id", "database_id": "db-123"},
            "properties": {"Name": {"title": [{"text": {"content": "Test Page"}}]}},
        }
        
        result = notion_adapter._create_page({
            "database_id": "db-123",
            "properties": {"Name": {"title": [{"text": {"content": "Test Page"}}]}},
        })
        
        assert result.success is True
        assert result.data["page"]["id"] == "page-123"

    @patch.object(NotionIntegrationAdapter, '_make_request')
    def test_get_page(self, mock_make_request, notion_adapter):
        """Test getting a page."""
        mock_make_request.return_value = {
            "object": "page",
            "id": "page-123",
            "properties": {"Name": {"title": [{"text": {"content": "Test Page"}}]}},
        }
        
        result = notion_adapter._get_page({"page_id": "page-123"})
        
        assert result.success is True
        assert result.data["page"]["id"] == "page-123"

    @patch.object(NotionIntegrationAdapter, '_make_request')
    def test_update_page(self, mock_make_request, notion_adapter):
        """Test updating a page."""
        mock_make_request.return_value = {
            "object": "page",
            "id": "page-123",
            "properties": {"Name": {"title": [{"text": {"content": "Updated Page"}}]}},
        }
        
        result = notion_adapter._update_page({
            "page_id": "page-123",
            "properties": {"Name": {"title": [{"text": {"content": "Updated Page"}}]}},
        })
        
        assert result.success is True
        assert result.data["page"]["id"] == "page-123"

    @patch.object(NotionIntegrationAdapter, '_make_request')
    def test_delete_page(self, mock_make_request, notion_adapter):
        """Test deleting (archiving) a page."""
        mock_make_request.return_value = {
            "object": "page",
            "id": "page-123",
            "archived": True,
        }
        
        result = notion_adapter._delete_page({"page_id": "page-123"})
        
        assert result.success is True
        assert result.data["archived"] is True

    @patch.object(NotionIntegrationAdapter, '_make_request')
    def test_search(self, mock_make_request, notion_adapter):
        """Test searching."""
        mock_make_request.return_value = {
            "results": [
                {"object": "page", "id": "page-1", "title": "Test Page"},
                {"object": "database", "id": "db-1", "title": "Test Database"},
            ]
        }
        
        result = notion_adapter._search({"query": "test"})
        
        assert result.success is True
        assert len(result.data["results"]) == 2

    @patch.object(NotionIntegrationAdapter, '_make_request')
    def test_sync_database_from_notion(self, mock_make_request, notion_adapter):
        """Test syncing database from Notion."""
        mock_make_request.return_value = {
            "results": [
                {"id": "page-1", "properties": {"Name": {"title": [{"text": {"content": "Item 1"}}]}}},
            ],
            "has_more": False,
        }
        
        result = notion_adapter._sync_database({
            "database_id": "db-123",
            "direction": "from_notion",
        })
        
        assert result.success is True
        assert result.data["direction"] == "from_notion"
        assert result.data["count"] == 1

    def test_execute_supported_action(self, notion_adapter):
        """Test executing a supported action."""
        with patch.object(notion_adapter, '_create_page') as mock_create_page:
            mock_create_page.return_value = IntegrationResult(
                success=True,
                data={"page": {"id": "test"}},
            )
            
            action = IntegrationAction(
                action_type="create_page",
                payload={"database_id": "db-123"},
            )
            
            result = notion_adapter.execute(action)
            
            assert result.success is True
            mock_create_page.assert_called_once()

    def test_execute_unsupported_action(self, notion_adapter):
        """Test executing an unsupported action."""
        action = IntegrationAction(
            action_type="unknown_action",
            payload={},
        )
        
        with pytest.raises(ActionNotSupportedError):
            notion_adapter.execute(action)

    def test_get_authentication_url(self, notion_adapter):
        """Test getting authentication URL."""
        # Mock OAuth config
        notion_adapter.oauth_config = MagicMock()
        notion_adapter.oauth_config.client_id = "test_client_id"
        notion_adapter.oauth_config.redirect_uri = "https://callback.com"
        notion_adapter.oauth_config.scope = ["read:user", "write:page"]
        notion_adapter.oauth_config.authorization_url = "https://api.notion.com/v1/oauth/authorize"
        
        url = notion_adapter.get_authentication_url()
        
        assert "https://api.notion.com/v1/oauth/authorize" in url
        assert "client_id=test_client_id" in url
        # L'URL est encodée, donc on vérifie la version encodée
        assert quote("redirect_uri=https://callback.com", safe='') in url or "redirect_uri=" in url
        assert "read%3Auser" in url or "read:user" in url
        assert "write%3Apage" in url or "write:page" in url

    @patch('requests.post')
    def test_exchange_code_for_token(self, mock_post, notion_adapter):
        """Test exchanging code for token."""
        # Mock OAuth config
        notion_adapter.oauth_config = MagicMock()
        notion_adapter.oauth_config.client_id = "test_client_id"
        notion_adapter.oauth_config.client_secret = "test_client_secret"
        notion_adapter.oauth_config.redirect_uri = "https://callback.com"
        notion_adapter.oauth_config.token_url = "https://api.notion.com/v1/oauth/token"
        
        # Mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "access_token": "test_access_token",
            "refresh_token": "test_refresh_token",
            "expires_in": 3600,
        }
        mock_post.return_value = mock_response
        
        credentials = notion_adapter.exchange_code_for_token("test_code")
        
        assert credentials.access_token == "test_access_token"
        assert credentials.refresh_token == "test_refresh_token"
        assert credentials.token_expiry is not None

    @patch('requests.post')
    def test_refresh_token(self, mock_post, notion_adapter):
        """Test refreshing token."""
        # Mock OAuth config
        notion_adapter.oauth_config = MagicMock()
        notion_adapter.oauth_config.client_id = "test_client_id"
        notion_adapter.oauth_config.client_secret = "test_client_secret"
        notion_adapter.oauth_config.token_url = "https://api.notion.com/v1/oauth/token"
        
        # Mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "access_token": "new_access_token",
            "expires_in": 3600,
        }
        mock_post.return_value = mock_response
        
        credentials = notion_adapter.refresh_token("test_refresh_token")
        
        assert credentials.access_token == "new_access_token"
        assert credentials.refresh_token == "test_refresh_token"  # Conservé car non fourni

    def test_authenticate_success(self, notion_adapter):
        """Test successful authentication."""
        credentials = IntegrationCredentials(
            access_token="valid_token",
        )
        
        with patch.object(notion_adapter, 'test_connection') as mock_test:
            mock_test.return_value = IntegrationResult(success=True)
            
            result = notion_adapter.authenticate(credentials)
            
            assert result is True

    def test_authenticate_failure(self, notion_adapter):
        """Test failed authentication."""
        credentials = IntegrationCredentials(
            access_token="invalid_token",
        )
        
        with patch.object(notion_adapter, 'test_connection') as mock_test:
            mock_test.return_value = IntegrationResult(success=False)
            
            result = notion_adapter.authenticate(credentials)
            
            assert result is False
