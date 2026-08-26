# Tests for Trello Integration Adapter
# Version: 0.5.0 (Épic 7 - US-052)

"""
Unit tests for the TrelloIntegrationAdapter class.
"""

import pytest
from unittest.mock import MagicMock, patch

from ..integration_types import (
    IntegrationAction,
    IntegrationConfig,
    IntegrationCredentials,
    IntegrationResult,
    IntegrationType,
)
from ..adapters.trello_adapter import TrelloIntegrationAdapter
from ..base_adapter import ActionNotSupportedError, AuthenticationError


@pytest.fixture
def trello_adapter():
    """Create a test TrelloIntegrationAdapter instance."""
    config = IntegrationConfig(
        id=1,
        integration_type=IntegrationType.TRELLO,
        name="Test Trello",
        credentials=IntegrationCredentials(
            api_key="test_api_key",
            client_secret="test_token",
        ),
    )
    return TrelloIntegrationAdapter(config)


@pytest.fixture
def trello_adapter_oauth():
    """Create a TrelloIntegrationAdapter with OAuth."""
    config = IntegrationConfig(
        id=1,
        integration_type=IntegrationType.TRELLO,
        name="Test Trello",
        credentials=IntegrationCredentials(
            access_token="test_oauth_token",
            client_id="test_client_id",
        ),
    )
    return TrelloIntegrationAdapter(config)


@pytest.fixture
def trello_adapter_no_creds():
    """Create a TrelloIntegrationAdapter without credentials."""
    config = IntegrationConfig(
        id=1,
        integration_type=IntegrationType.TRELLO,
        name="Test Trello",
        credentials=IntegrationCredentials(),
    )
    return TrelloIntegrationAdapter(config)


class TestTrelloIntegrationAdapter:
    """Tests for TrelloIntegrationAdapter."""

    def test_adapter_properties(self, trello_adapter):
        """Test adapter properties."""
        assert trello_adapter.type == IntegrationType.TRELLO
        assert trello_adapter.name == "Trello"
        assert trello_adapter.description == "Intégration avec Trello pour créer et gérer des cartes de tâches"
        assert trello_adapter.auth_type.value == "oauth2"
        assert "create_card" in trello_adapter.supported_actions
        assert "create_board" in trello_adapter.supported_actions
        assert "list_cards" in trello_adapter.supported_actions
        assert "move_card" in trello_adapter.supported_actions
        assert "add_comment" in trello_adapter.supported_actions

    def test_is_action_supported(self, trello_adapter):
        """Test checking if action is supported."""
        assert trello_adapter.is_action_supported("create_card") is True
        assert trello_adapter.is_action_supported("create_board") is True
        assert trello_adapter.is_action_supported("list_boards") is True
        assert trello_adapter.is_action_supported("unknown_action") is False

    def test_get_metadata(self, trello_adapter):
        """Test getting adapter metadata."""
        metadata = trello_adapter.get_metadata()
        
        assert metadata["type"] == "trello"
        assert metadata["name"] == "Trello"
        assert metadata["auth_type"] == "oauth2"
        assert "create_card" in metadata["supported_actions"]
        assert metadata["icon"] == "trello"
        assert metadata["color"] == "#0079BF"

    def test_get_oauth_scopes(self, trello_adapter):
        """Test getting OAuth scopes."""
        scopes = trello_adapter.get_oauth_scopes()
        
        assert isinstance(scopes, list)
        assert len(scopes) > 0
        assert "read" in scopes
        assert "write" in scopes
        assert "account" in scopes

    def test_get_configuration_schema(self, trello_adapter):
        """Test getting configuration schema."""
        schema = trello_adapter.get_configuration_schema()
        
        assert isinstance(schema, dict)
        assert "properties" in schema
        assert "name" in schema["properties"]
        assert "settings" in schema["properties"]
        assert "default_board_id" in schema["properties"]["settings"]["properties"]
        assert "auto_create_cards" in schema["properties"]["settings"]["properties"]

    def test_get_action_schema(self, trello_adapter):
        """Test getting action schema."""
        schema = trello_adapter.get_action_schema("create_card")
        
        assert isinstance(schema, dict)
        
        # Test with unsupported action
        with pytest.raises(ValueError):
            trello_adapter.get_action_schema("unknown_action")

    def test_authentication_with_api_key(self, trello_adapter):
        """Test authentication with API key and token."""
        params = trello_adapter._get_auth_params()
        
        assert "key" in params
        assert "token" in params
        assert params["key"] == "test_api_key"
        assert params["token"] == "test_token"

    def test_authentication_with_oauth(self, trello_adapter_oauth):
        """Test authentication with OAuth token."""
        params = trello_adapter_oauth._get_auth_params()
        
        assert "key" in params
        assert "token" in params
        assert params["key"] == "test_client_id"
        assert params["token"] == "test_oauth_token"

    def test_authentication_without_credentials(self, trello_adapter_no_creds):
        """Test authentication without credentials."""
        with pytest.raises(AuthenticationError):
            trello_adapter_no_creds._get_auth_params()

    @patch.object(TrelloIntegrationAdapter, '_make_request')
    def test_test_connection_success(self, mock_make_request, trello_adapter):
        """Test successful connection test."""
        mock_make_request.return_value = {
            "id": "member-123",
            "username": "testuser",
            "fullName": "Test User",
            "email": "test@example.com",
            "avatarUrl": "https://avatar.url",
        }
        
        result = trello_adapter.test_connection()
        
        assert result.success is True
        assert "user" in result.data
        assert result.data["user"]["id"] == "member-123"
        assert result.data["user"]["username"] == "testuser"
        assert result.data["user"]["full_name"] == "Test User"

    @patch.object(TrelloIntegrationAdapter, '_make_request')
    def test_test_connection_failure(self, mock_make_request, trello_adapter):
        """Test failed connection test."""
        mock_make_request.side_effect = Exception("Connection failed")
        
        result = trello_adapter.test_connection()
        
        assert result.success is False
        assert "Connection failed" in result.error

    @patch.object(TrelloIntegrationAdapter, '_make_request')
    def test_list_boards(self, mock_make_request, trello_adapter):
        """Test listing boards."""
        mock_make_request.return_value = [
            {
                "id": "board-1",
                "name": "Project Board",
                "desc": "Project description",
                "closed": False,
            },
            {
                "id": "board-2",
                "name": "Personal Board",
                "closed": False,
            },
        ]
        
        result = trello_adapter._list_boards({"member_id": "me"})
        
        assert result.success is True
        assert len(result.data["boards"]) == 2
        assert result.data["count"] == 2

    @patch.object(TrelloIntegrationAdapter, '_make_request')
    def test_get_board(self, mock_make_request, trello_adapter):
        """Test getting a board."""
        mock_make_request.return_value = {
            "id": "board-123",
            "name": "Test Board",
            "desc": "Test description",
            "closed": False,
            "members": [],
            "lists": [],
        }
        
        result = trello_adapter._get_board({"board_id": "board-123"})
        
        assert result.success is True
        assert result.data["board"]["id"] == "board-123"
        assert result.data["board"]["name"] == "Test Board"

    @patch.object(TrelloIntegrationAdapter, '_make_request')
    def test_create_board(self, mock_make_request, trello_adapter):
        """Test creating a board."""
        mock_make_request.return_value = {
            "id": "board-new",
            "name": "New Board",
            "desc": "Board description",
            "closed": False,
        }
        
        result = trello_adapter._create_board({
            "name": "New Board",
            "description": "Board description",
            "default_lists": True,
        })
        
        assert result.success is True
        assert result.data["board"]["id"] == "board-new"
        assert result.data["board"]["name"] == "New Board"

    @patch.object(TrelloIntegrationAdapter, '_make_request')
    def test_list_lists(self, mock_make_request, trello_adapter):
        """Test listing lists on a board."""
        mock_make_request.return_value = [
            {
                "id": "list-1",
                "name": "To Do",
                "closed": False,
                "pos": 1,
            },
            {
                "id": "list-2",
                "name": "In Progress",
                "closed": False,
                "pos": 2,
            },
            {
                "id": "list-3",
                "name": "Done",
                "closed": False,
                "pos": 3,
            },
        ]
        
        result = trello_adapter._list_lists({"board_id": "board-123"})
        
        assert result.success is True
        assert len(result.data["lists"]) == 3
        assert result.data["count"] == 3

    @patch.object(TrelloIntegrationAdapter, '_make_request')
    def test_get_list(self, mock_make_request, trello_adapter):
        """Test getting a list."""
        mock_make_request.return_value = {
            "id": "list-123",
            "name": "To Do",
            "closed": False,
            "pos": 1,
            "idBoard": "board-123",
        }
        
        result = trello_adapter._get_list({"list_id": "list-123"})
        
        assert result.success is True
        assert result.data["list"]["id"] == "list-123"
        assert result.data["list"]["name"] == "To Do"

    @patch.object(TrelloIntegrationAdapter, '_make_request')
    def test_create_list(self, mock_make_request, trello_adapter):
        """Test creating a list."""
        mock_make_request.return_value = {
            "id": "list-new",
            "name": "New List",
            "closed": False,
            "pos": 3,
            "idBoard": "board-123",
        }
        
        result = trello_adapter._create_list({
            "board_id": "board-123",
            "name": "New List",
            "position": "bottom",
        })
        
        assert result.success is True
        assert result.data["list"]["id"] == "list-new"
        assert result.data["list"]["name"] == "New List"

    @patch.object(TrelloIntegrationAdapter, '_make_request')
    def test_list_cards(self, mock_make_request, trello_adapter):
        """Test listing cards from a list."""
        mock_make_request.return_value = [
            {
                "id": "card-1",
                "name": "Task 1",
                "desc": "Description 1",
                "closed": False,
                "idList": "list-1",
            },
            {
                "id": "card-2",
                "name": "Task 2",
                "desc": "Description 2",
                "closed": False,
                "idList": "list-1",
            },
        ]
        
        result = trello_adapter._list_cards({"list_id": "list-1"})
        
        assert result.success is True
        assert len(result.data["cards"]) == 2
        assert result.data["count"] == 2

    @patch.object(TrelloIntegrationAdapter, '_make_request')
    def test_get_card(self, mock_make_request, trello_adapter):
        """Test getting a card."""
        mock_make_request.return_value = {
            "id": "card-123",
            "name": "Test Card",
            "desc": "Test description",
            "closed": False,
            "idList": "list-1",
            "idBoard": "board-1",
            "idMembers": [],
            "idLabels": [],
        }
        
        result = trello_adapter._get_card({"card_id": "card-123"})
        
        assert result.success is True
        assert result.data["card"]["id"] == "card-123"
        assert result.data["card"]["name"] == "Test Card"

    @patch.object(TrelloIntegrationAdapter, '_make_request')
    def test_create_card(self, mock_make_request, trello_adapter):
        """Test creating a card."""
        mock_make_request.return_value = {
            "id": "card-new",
            "name": "New Task",
            "desc": "Task description",
            "closed": False,
            "idList": "list-1",
            "idBoard": "board-1",
        }
        
        result = trello_adapter._create_card({
            "list_id": "list-1",
            "name": "New Task",
            "description": "Task description",
        })
        
        assert result.success is True
        assert result.data["card"]["id"] == "card-new"
        assert result.data["card"]["name"] == "New Task"

    @patch.object(TrelloIntegrationAdapter, '_make_request')
    def test_update_card(self, mock_make_request, trello_adapter):
        """Test updating a card."""
        mock_make_request.return_value = {
            "id": "card-123",
            "name": "Updated Task",
            "desc": "Updated description",
            "closed": False,
            "idList": "list-2",
        }
        
        result = trello_adapter._update_card({
            "card_id": "card-123",
            "name": "Updated Task",
            "description": "Updated description",
            "list_id": "list-2",
        })
        
        assert result.success is True
        assert result.data["card"]["id"] == "card-123"
        assert result.data["card"]["name"] == "Updated Task"

    @patch.object(TrelloIntegrationAdapter, '_make_request')
    def test_delete_card(self, mock_make_request, trello_adapter):
        """Test deleting (archiving) a card."""
        mock_make_request.return_value = {
            "id": "card-123",
            "name": "Archived Task",
            "closed": True,
        }
        
        result = trello_adapter._delete_card({"card_id": "card-123"})
        
        assert result.success is True
        assert result.data["archived"] is True

    @patch.object(TrelloIntegrationAdapter, '_make_request')
    def test_move_card_to_list(self, mock_make_request, trello_adapter):
        """Test moving a card to another list."""
        mock_make_request.return_value = {
            "_value": "list-2",
        }
        
        result = trello_adapter._move_card({
            "card_id": "card-123",
            "list_id": "list-2",
        })
        
        assert result.success is True
        assert result.data["card_id"] == "card-123"
        assert result.data["moved_to"] == "list-2"

    @patch.object(TrelloIntegrationAdapter, '_make_request')
    def test_move_card_to_position(self, mock_make_request, trello_adapter):
        """Test moving a card to a position."""
        mock_make_request.return_value = {
            "_value": "top",
        }
        
        result = trello_adapter._move_card({
            "card_id": "card-123",
            "position": "top",
        })
        
        assert result.success is True
        assert result.data["card_id"] == "card-123"
        assert result.data["moved_to"] == "top"

    @patch.object(TrelloIntegrationAdapter, '_make_request')
    def test_add_comment(self, mock_make_request, trello_adapter):
        """Test adding a comment to a card."""
        mock_make_request.return_value = {
            "id": "comment-1",
            "text": "Test comment",
            "type": "commentCard",
            "idCard": "card-123",
            "idMember": "member-1",
        }
        
        result = trello_adapter._add_comment({
            "card_id": "card-123",
            "text": "Test comment",
        })
        
        assert result.success is True
        assert result.data["comment"]["id"] == "comment-1"
        assert result.data["comment"]["text"] == "Test comment"

    @patch.object(TrelloIntegrationAdapter, '_make_request')
    def test_list_comments(self, mock_make_request, trello_adapter):
        """Test listing comments on a card."""
        mock_make_request.return_value = [
            {
                "id": "comment-1",
                "text": "Comment 1",
                "type": "commentCard",
                "idCard": "card-123",
            },
            {
                "id": "comment-2",
                "text": "Comment 2",
                "type": "commentCard",
                "idCard": "card-123",
            },
            {
                "id": "action-1",
                "text": "Not a comment",
                "type": "createCard",
            },
        ]
        
        result = trello_adapter._list_comments({"card_id": "card-123"})
        
        assert result.success is True
        assert len(result.data["comments"]) == 2
        assert result.data["count"] == 2

    @patch.object(TrelloIntegrationAdapter, '_make_request')
    def test_list_labels(self, mock_make_request, trello_adapter):
        """Test listing labels."""
        mock_make_request.return_value = [
            {
                "id": "label-1",
                "name": "Bug",
                "color": "red",
            },
            {
                "id": "label-2",
                "name": "Feature",
                "color": "green",
            },
        ]
        
        result = trello_adapter._list_labels({"board_id": "board-123"})
        
        assert result.success is True
        assert len(result.data["labels"]) == 2
        assert result.data["count"] == 2

    @patch.object(TrelloIntegrationAdapter, '_make_request')
    def test_add_label_to_card_existing(self, mock_make_request, trello_adapter):
        """Test adding an existing label to a card."""
        mock_make_request.return_value = {
            "_value": "label-1",
        }
        
        result = trello_adapter._add_label_to_card({
            "card_id": "card-123",
            "label_id": "label-1",
        })
        
        assert result.success is True
        assert result.data["label_added"] == "label-1"

    @patch.object(TrelloIntegrationAdapter, '_make_request')
    @patch.object(TrelloIntegrationAdapter, '_list_labels')
    def test_add_label_to_card_new(self, mock_list_labels, mock_make_request, trello_adapter):
        """Test creating and adding a new label to a card."""
        # Mock list_labels to return no existing label
        mock_list_labels.return_value = IntegrationResult(
            success=True,
            data={"labels": [], "count": 0},
        )
        
        # First call: create label
        # Second call: add label to card
        mock_make_request.side_effect = [
            {"id": "label-new", "name": "Priority", "color": "red"},
            {"_value": "label-new"},
        ]
        
        result = trello_adapter._add_label_to_card({
            "card_id": "card-123",
            "board_id": "board-123",
            "label_name": "Priority",
            "label_color": "red",
        })
        
        assert result.success is True
        # Le label_id est retourné, pas le label_name
        assert result.data["label_added"] == "label-new"

    @patch.object(TrelloIntegrationAdapter, '_make_request')
    def test_remove_label_from_card(self, mock_make_request, trello_adapter):
        """Test removing a label from a card."""
        mock_make_request.return_value = ""  # Empty response for DELETE
        
        result = trello_adapter._remove_label_from_card({
            "card_id": "card-123",
            "label_id": "label-1",
        })
        
        assert result.success is True
        assert result.data["removed"] is True
        assert result.data["label_id"] == "label-1"

    @patch.object(TrelloIntegrationAdapter, '_make_request')
    def test_add_checklist(self, mock_make_request, trello_adapter):
        """Test adding a checklist to a card."""
        mock_make_request.return_value = {
            "id": "checklist-1",
            "name": "Tasks",
            "checkItems": [],
            "idCard": "card-123",
        }
        
        result = trello_adapter._add_checklist({
            "card_id": "card-123",
            "name": "Tasks",
        })
        
        assert result.success is True
        assert result.data["checklist"]["id"] == "checklist-1"
        assert result.data["checklist"]["name"] == "Tasks"

    @patch.object(TrelloIntegrationAdapter, '_make_request')
    def test_add_checklist_item(self, mock_make_request, trello_adapter):
        """Test adding an item to a checklist."""
        mock_make_request.return_value = {
            "id": "item-1",
            "name": "Task 1",
            "checked": False,
            "idChecklist": "checklist-1",
        }
        
        result = trello_adapter._add_checklist_item({
            "checklist_id": "checklist-1",
            "name": "Task 1",
            "checked": False,
        })
        
        assert result.success is True
        assert result.data["checklist_item"]["id"] == "item-1"
        assert result.data["checklist_item"]["name"] == "Task 1"

    @patch.object(TrelloIntegrationAdapter, '_make_request')
    def test_update_checklist_item(self, mock_make_request, trello_adapter):
        """Test updating a checklist item."""
        mock_make_request.return_value = {
            "id": "item-1",
            "name": "Updated Task",
            "checked": True,
            "idChecklist": "checklist-1",
        }
        
        result = trello_adapter._update_checklist_item({
            "item_id": "item-1",
            "name": "Updated Task",
            "checked": True,
        })
        
        assert result.success is True
        assert result.data["checklist_item"]["id"] == "item-1"
        assert result.data["checklist_item"]["checked"] is True

    @patch.object(TrelloIntegrationAdapter, '_make_request')
    def test_add_attachment(self, mock_make_request, trello_adapter):
        """Test adding an attachment to a card."""
        mock_make_request.return_value = {
            "id": "attachment-1",
            "name": "document.pdf",
            "url": "https://example.com/document.pdf",
            "idCard": "card-123",
        }
        
        result = trello_adapter._add_attachment({
            "card_id": "card-123",
            "url": "https://example.com/document.pdf",
            "name": "document.pdf",
        })
        
        assert result.success is True
        assert result.data["attachment"]["id"] == "attachment-1"
        assert result.data["attachment"]["url"] == "https://example.com/document.pdf"

    @patch.object(TrelloIntegrationAdapter, '_make_request')
    def test_list_attachments(self, mock_make_request, trello_adapter):
        """Test listing attachments on a card."""
        mock_make_request.return_value = [
            {
                "id": "attachment-1",
                "name": "file1.pdf",
                "url": "https://example.com/file1.pdf",
            },
            {
                "id": "attachment-2",
                "name": "file2.jpg",
                "url": "https://example.com/file2.jpg",
            },
        ]
        
        result = trello_adapter._list_attachments({"card_id": "card-123"})
        
        assert result.success is True
        assert len(result.data["attachments"]) == 2
        assert result.data["count"] == 2

    @patch.object(TrelloIntegrationAdapter, '_make_request')
    def test_list_members(self, mock_make_request, trello_adapter):
        """Test listing members."""
        mock_make_request.return_value = [
            {
                "id": "member-1",
                "username": "user1",
                "fullName": "User One",
            },
            {
                "id": "member-2",
                "username": "user2",
                "fullName": "User Two",
            },
        ]
        
        result = trello_adapter._list_members({"board_id": "board-123"})
        
        assert result.success is True
        assert len(result.data["members"]) == 2
        assert result.data["count"] == 2

    @patch.object(TrelloIntegrationAdapter, '_make_request')
    def test_add_member_to_card(self, mock_make_request, trello_adapter):
        """Test adding a member to a card."""
        mock_make_request.return_value = {
            "_value": "member-1",
        }
        
        result = trello_adapter._add_member_to_card({
            "card_id": "card-123",
            "member_id": "member-1",
        })
        
        assert result.success is True
        assert result.data["member_added"] == "member-1"
        assert result.data["card_id"] == "card-123"

    @patch.object(TrelloIntegrationAdapter, '_make_request')
    def test_remove_member_from_card(self, mock_make_request, trello_adapter):
        """Test removing a member from a card."""
        mock_make_request.return_value = ""  # Empty response for DELETE
        
        result = trello_adapter._remove_member_from_card({
            "card_id": "card-123",
            "member_id": "member-1",
        })
        
        assert result.success is True
        assert result.data["removed"] is True
        assert result.data["member_id"] == "member-1"

    @patch.object(TrelloIntegrationAdapter, '_make_request')
    def test_create_webhook(self, mock_make_request, trello_adapter):
        """Test creating a webhook."""
        mock_make_request.return_value = {
            "id": "webhook-1",
            "description": "Agent World Webhook",
            "callbackURL": "https://callback.com",
            "active": True,
            "idModel": "board-123",
        }
        
        result = trello_adapter._create_webhook({
            "board_id": "board-123",
            "callback_url": "https://callback.com",
            "description": "Agent World Webhook",
        })
        
        assert result.success is True
        assert result.data["webhook"]["id"] == "webhook-1"

    @patch.object(TrelloIntegrationAdapter, '_make_request')
    def test_delete_webhook(self, mock_make_request, trello_adapter):
        """Test deleting a webhook."""
        mock_make_request.return_value = ""  # Empty response for DELETE
        
        result = trello_adapter._delete_webhook({"webhook_id": "webhook-1"})
        
        assert result.success is True
        assert result.data["deleted"] is True
        assert result.data["webhook_id"] == "webhook-1"

    def test_execute_supported_action(self, trello_adapter):
        """Test executing a supported action."""
        with patch.object(trello_adapter, '_list_boards') as mock_list_boards:
            mock_list_boards.return_value = IntegrationResult(
                success=True,
                data={"boards": [], "count": 0},
            )
            
            action = IntegrationAction(
                action_type="list_boards",
                payload={},
            )
            
            result = trello_adapter.execute(action)
            
            assert result.success is True
            mock_list_boards.assert_called_once()

    def test_execute_unsupported_action(self, trello_adapter):
        """Test executing an unsupported action."""
        action = IntegrationAction(
            action_type="unknown_action",
            payload={},
        )
        
        with pytest.raises(ActionNotSupportedError):
            trello_adapter.execute(action)

    def test_get_authentication_url(self, trello_adapter):
        """Test getting authentication URL."""
        # Mock OAuth config
        trello_adapter.oauth_config = MagicMock()
        trello_adapter.oauth_config.client_id = "test_client_id"
        trello_adapter.oauth_config.redirect_uri = "https://callback.com"
        trello_adapter.oauth_config.scope = ["read", "write"]
        trello_adapter.oauth_config.authorization_url = "https://trello.com/1/OAuthAuthorizeToken"
        
        url = trello_adapter.get_authentication_url()
        
        assert "https://trello.com/1/OAuthAuthorizeToken" in url
        assert "key=test_client_id" in url
        # L'URL est encodée
        assert "return_url=" in url
        # Trello utilise + comme séparateur pour les scopes
        assert "scope=read+write" in url or "scope=read write" in url
        assert "response_type=token" in url

    def test_exchange_code_for_token(self, trello_adapter):
        """Test exchanging code for token (OAuth1)."""
        # With OAuth1, the code IS the token
        credentials = trello_adapter.exchange_code_for_token("oauth_token_123")
        
        assert credentials.access_token == "oauth_token_123"
        assert credentials.token_expiry is None  # OAuth1 tokens don't expire

    def test_refresh_token_not_implemented(self, trello_adapter):
        """Test that refresh token raises NotImplementedError."""
        with pytest.raises(NotImplementedError):
            trello_adapter.refresh_token("refresh_token")

    def test_authenticate_success(self, trello_adapter):
        """Test successful authentication."""
        credentials = IntegrationCredentials(
            api_key="valid_key",
            client_secret="valid_token",
        )
        
        with patch.object(trello_adapter, 'test_connection') as mock_test:
            mock_test.return_value = IntegrationResult(success=True)
            
            result = trello_adapter.authenticate(credentials)
            
            assert result is True

    def test_authenticate_failure(self, trello_adapter):
        """Test failed authentication."""
        credentials = IntegrationCredentials(
            api_key="invalid_key",
            client_secret="invalid_token",
        )
        
        with patch.object(trello_adapter, 'test_connection') as mock_test:
            mock_test.return_value = IntegrationResult(success=False)
            
            result = trello_adapter.authenticate(credentials)
            
            assert result is False
