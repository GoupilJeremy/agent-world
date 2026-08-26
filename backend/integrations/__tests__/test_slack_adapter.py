# Tests for Slack Integration Adapter
# Version: 0.5.0 (Épic 7 - US-048)

"""
Unit tests for the SlackIntegrationAdapter class.
"""

from unittest.mock import MagicMock, PropertyMock, patch

import pytest

from ..adapters.slack_adapter import SlackIntegrationAdapter
from ..base_adapter import ActionNotSupportedError, AuthenticationError
from ..integration_types import (
    IntegrationAction,
    IntegrationConfig,
    IntegrationCredentials,
    IntegrationType,
)


@pytest.fixture
def slack_adapter():
    """Create a test SlackIntegrationAdapter instance."""
    config = IntegrationConfig(
        id=1,
        integration_type=IntegrationType.SLACK,
        name="Test Slack",
        credentials=IntegrationCredentials(
            access_token="fake-slack-token",
        ),
    )
    adapter = SlackIntegrationAdapter(config)
    # Mock the session to avoid actual API calls
    adapter.session = MagicMock()
    return adapter


@pytest.fixture
def slack_adapter_no_creds():
    """Create a SlackIntegrationAdapter without credentials."""
    config = IntegrationConfig(
        id=1,
        integration_type=IntegrationType.SLACK,
        name="Test Slack",
        credentials=IntegrationCredentials(),
    )
    adapter = SlackIntegrationAdapter(config)
    adapter.session = MagicMock()
    return adapter


@pytest.fixture
def slack_adapter_with_bot_token():
    """Create a SlackIntegrationAdapter with bot token."""
    config = IntegrationConfig(
        id=1,
        integration_type=IntegrationType.SLACK,
        name="Test Slack",
        credentials=IntegrationCredentials(
            api_key="fake-slack-bot-token",
        ),
    )
    adapter = SlackIntegrationAdapter(config)
    adapter.session = MagicMock()
    return adapter


class TestSlackIntegrationAdapter:
    """Tests for SlackIntegrationAdapter."""

    def test_adapter_properties(self, slack_adapter):
        """Test adapter properties."""
        assert slack_adapter.type == IntegrationType.SLACK
        assert slack_adapter.name == "Slack"
        assert (
            slack_adapter.description
            == "Intégration avec Slack pour envoyer des messages, notifications et interagir avec les équipes"
        )
        assert slack_adapter.auth_type.value == "oauth2"
        assert slack_adapter.color == "#4A154B"
        assert slack_adapter.icon == "slack"
        assert "send_message" in slack_adapter.supported_actions
        assert "list_channels" in slack_adapter.supported_actions
        assert "get_user_info" in slack_adapter.supported_actions
        assert "create_channel" in slack_adapter.supported_actions
        assert "add_reaction" in slack_adapter.supported_actions

    def test_is_action_supported(self, slack_adapter):
        """Test checking if action is supported."""
        assert slack_adapter.is_action_supported("send_message") is True
        assert slack_adapter.is_action_supported("list_channels") is True
        assert slack_adapter.is_action_supported("create_channel") is True
        assert slack_adapter.is_action_supported("unknown_action") is False

    def test_get_metadata(self, slack_adapter):
        """Test getting adapter metadata."""
        metadata = slack_adapter.get_metadata()

        assert metadata["type"] == "slack"
        assert metadata["name"] == "Slack"
        assert metadata["auth_type"] == "oauth2"
        assert "send_message" in metadata["supported_actions"]
        assert "list_channels" in metadata["supported_actions"]

    def test_get_oauth_scopes(self, slack_adapter):
        """Test getting OAuth scopes."""
        scopes = slack_adapter.get_oauth_scopes()

        assert isinstance(scopes, list)
        assert len(scopes) > 0
        assert "chat:write" in scopes
        assert "channels:read" in scopes
        assert "users:read" in scopes

    def test_get_configuration_schema(self, slack_adapter):
        """Test getting configuration schema."""
        schema = slack_adapter.get_configuration_schema()

        assert isinstance(schema, dict)
        assert "properties" in schema
        assert "name" in schema["properties"]
        assert "settings" in schema["properties"]
        assert schema["required"] == ["name"]

    def test_get_action_schema(self, slack_adapter):
        """Test getting action schema."""
        schema = slack_adapter.get_action_schema("send_message")

        assert isinstance(schema, dict)

        # Test with unsupported action
        with pytest.raises(ValueError):
            slack_adapter.get_action_schema("unknown_action")

    def test_authenticate_with_valid_credentials(self, slack_adapter):
        """Test authentication with valid credentials."""
        with patch.object(slack_adapter, "test_connection") as mock_test:
            mock_test.return_value.success = True

            result = slack_adapter.authenticate(
                IntegrationCredentials(access_token="valid-token")
            )

            assert result is True

    def test_authenticate_with_invalid_credentials(self, slack_adapter):
        """Test authentication with invalid credentials."""
        with patch.object(slack_adapter, "test_connection") as mock_test:
            mock_test.return_value.success = False

            result = slack_adapter.authenticate(
                IntegrationCredentials(access_token="invalid-token")
            )

            assert result is False

    def test_get_auth_headers_with_access_token(self, slack_adapter):
        """Test getting auth headers with access token."""
        headers = slack_adapter._get_auth_headers()

        assert "Authorization" in headers
        assert headers["Authorization"].startswith("Bearer ")
        assert headers["Authorization"] == "Bearer fake-slack-token"

    def test_get_auth_headers_with_bot_token(self, slack_adapter_with_bot_token):
        """Test getting auth headers with bot token."""
        headers = slack_adapter_with_bot_token._get_auth_headers()

        assert "Authorization" in headers
        assert headers["Authorization"].startswith("Bearer ")

    def test_get_auth_headers_no_credentials(self, slack_adapter_no_creds):
        """Test getting auth headers without credentials."""
        with pytest.raises(AuthenticationError):
            slack_adapter_no_creds._get_auth_headers()

    def test_authentication_url_generation(self, slack_adapter):
        """Test OAuth2 authentication URL generation."""
        # Set up OAuth config
        slack_adapter.oauth_config.client_id = "test_client_id"
        slack_adapter.oauth_config.redirect_uri = "http://test.com/callback"
        slack_adapter.oauth_config.scope = ["chat:write", "users:read"]

        url = slack_adapter.get_authentication_url(state="test_state")

        assert "client_id=test_client_id" in url
        # redirect_uri is URL-encoded in the query string
        assert (
            "redirect_uri=http%3A%2F%2Ftest.com%2Fcallback" in url
            or "redirect_uri=http://test.com/callback" in url
        )
        # user_scope is URL-encoded (comma and colon)
        assert (
            "user_scope=chat%3Awrite%2Cusers%3Aread" in url
            or "user_scope=chat:write,users:read" in url
            or "user_scope=chat%3Awrite,users%3Aread" in url
        )
        assert "state=test_state" in url
        assert "slack.com/oauth/v2/authorize" in url

    def test_authentication_url_without_state(self, slack_adapter):
        """Test OAuth2 authentication URL generation without state."""
        slack_adapter.oauth_config.client_id = "test_client_id"
        slack_adapter.oauth_config.redirect_uri = "http://test.com/callback"

        url = slack_adapter.get_authentication_url()

        assert "client_id=test_client_id" in url
        assert "state=" in url
        # State should be a random string
        assert len(url.split("state=")[1].split("&")[0]) > 10

    def test_execute_supported_action(self, slack_adapter):
        """Test executing a supported action."""
        with patch.object(slack_adapter, "_send_message") as mock_send:
            mock_send.return_value.success = True

            action = IntegrationAction(
                action_type="send_message", payload={"channel": "C123", "text": "Hello"}
            )

            result = slack_adapter.execute(action)

            mock_send.assert_called_once_with({"channel": "C123", "text": "Hello"})
            assert result.success is True

    def test_execute_unsupported_action(self, slack_adapter):
        """Test executing an unsupported action."""
        action = IntegrationAction(action_type="unsupported_action", payload={})

        with pytest.raises(ActionNotSupportedError):
            slack_adapter.execute(action)

    def test_send_message(self, slack_adapter):
        """Test sending a message."""
        with patch.object(slack_adapter, "_make_request") as mock_request:
            mock_request.return_value = {
                "ok": True,
                "ts": "12345.678",
                "channel": "C123",
            }

            payload = {
                "channel": "C123",
                "text": "Hello World",
            }

            result = slack_adapter._send_message(payload)

            assert result.success is True
            mock_request.assert_called_once()
            call_args = mock_request.call_args
            assert call_args[0][0] == "POST"
            assert call_args[0][1] == "chat.postMessage"
            assert call_args[1]["json"]["channel"] == "C123"
            assert call_args[1]["json"]["text"] == "Hello World"

    def test_send_message_with_blocks(self, slack_adapter):
        """Test sending a message with blocks."""
        with patch.object(slack_adapter, "_make_request") as mock_request:
            mock_request.return_value = {"ok": True, "ts": "12345.678"}

            payload = {
                "channel": "C123",
                "text": "Hello",
                "blocks": [
                    {"type": "section", "text": {"type": "mrkdwn", "text": "test"}}
                ],
            }

            result = slack_adapter._send_message(payload)

            assert result.success is True
            call_args = mock_request.call_args
            assert "blocks" in call_args[1]["json"]

    def test_send_message_missing_required_fields(self, slack_adapter):
        """Test sending a message with missing required fields."""
        # Missing channel
        payload = {"text": "Hello"}
        result = slack_adapter._send_message(payload)
        assert result.success is False
        assert "channel" in result.error

        # Missing text
        payload = {"channel": "C123"}
        result = slack_adapter._send_message(payload)
        assert result.success is False
        assert "text" in result.error

    def test_send_ephemeral_message(self, slack_adapter):
        """Test sending an ephemeral message."""
        with patch.object(slack_adapter, "_make_request") as mock_request:
            mock_request.return_value = {"ok": True}

            payload = {
                "channel": "C123",
                "text": "Only you can see this",
                "user": "U123",
            }

            result = slack_adapter._send_ephemeral_message(payload)

            assert result.success is True
            call_args = mock_request.call_args
            assert call_args[0][0] == "POST"
            assert call_args[0][1] == "chat.postEphemeral"

    def test_send_ephemeral_message_missing_fields(self, slack_adapter):
        """Test sending an ephemeral message with missing fields."""
        payload = {"channel": "C123", "text": "Hello"}  # Missing user
        result = slack_adapter._send_ephemeral_message(payload)
        assert result.success is False

    def test_list_channels(self, slack_adapter):
        """Test listing channels."""
        with patch.object(slack_adapter, "_make_request") as mock_request:
            mock_request.return_value = {
                "ok": True,
                "channels": [
                    {"id": "C123", "name": "general"},
                    {"id": "C456", "name": "random"},
                ],
                "response_metadata": {"next_cursor": ""},
            }

            payload = {"limit": 50}

            result = slack_adapter._list_channels(payload)

            assert result.success is True
            assert len(result.data["channels"]) == 2
            assert result.data["count"] == 2

    def test_get_channel_info(self, slack_adapter):
        """Test getting channel info."""
        with patch.object(slack_adapter, "_make_request") as mock_request:
            mock_request.return_value = {
                "ok": True,
                "channel": {"id": "C123", "name": "general", "topic": "Test"},
            }

            payload = {"channel": "C123"}

            result = slack_adapter._get_channel_info(payload)

            assert result.success is True
            assert result.data["channel"]["name"] == "general"

    def test_create_channel(self, slack_adapter):
        """Test creating a channel."""
        with patch.object(slack_adapter, "_make_request") as mock_request:
            mock_request.return_value = {
                "ok": True,
                "channel": {"id": "C123", "name": "new-channel"},
            }

            payload = {"name": "new-channel", "is_private": False}

            result = slack_adapter._create_channel(payload)

            assert result.success is True
            assert result.data["channel"]["name"] == "new-channel"

    def test_join_channel(self, slack_adapter):
        """Test joining a channel."""
        with patch.object(slack_adapter, "_make_request") as mock_request:
            mock_request.return_value = {"ok": True, "channel": {"id": "C123"}}

            payload = {"channel": "C123"}

            result = slack_adapter._join_channel(payload)

            assert result.success is True

    def test_leave_channel(self, slack_adapter):
        """Test leaving a channel."""
        with patch.object(slack_adapter, "_make_request") as mock_request:
            mock_request.return_value = {"ok": True}

            payload = {"channel": "C123"}

            result = slack_adapter._leave_channel(payload)

            assert result.success is True

    def test_get_user_info(self, slack_adapter):
        """Test getting user info."""
        with patch.object(slack_adapter, "_make_request") as mock_request:
            mock_request.return_value = {
                "ok": True,
                "user": {"id": "U123", "name": "testuser", "real_name": "Test User"},
            }

            payload = {"user": "U123"}

            result = slack_adapter._get_user_info(payload)

            assert result.success is True
            assert result.data["user"]["name"] == "testuser"

    def test_list_users(self, slack_adapter):
        """Test listing users."""
        with patch.object(slack_adapter, "_make_request") as mock_request:
            mock_request.return_value = {
                "ok": True,
                "members": [
                    {"id": "U123", "name": "user1"},
                    {"id": "U456", "name": "user2"},
                ],
                "response_metadata": {"next_cursor": ""},
            }

            payload = {"limit": 100}

            result = slack_adapter._list_users(payload)

            assert result.success is True
            assert len(result.data["users"]) == 2

    def test_add_reaction(self, slack_adapter):
        """Test adding a reaction."""
        with patch.object(slack_adapter, "_make_request") as mock_request:
            mock_request.return_value = {"ok": True}

            payload = {
                "channel": "C123",
                "timestamp": "12345.678",
                "name": ":smile:",
            }

            result = slack_adapter._add_reaction(payload)

            assert result.success is True

    def test_remove_reaction(self, slack_adapter):
        """Test removing a reaction."""
        with patch.object(slack_adapter, "_make_request") as mock_request:
            mock_request.return_value = {"ok": True}

            payload = {
                "channel": "C123",
                "timestamp": "12345.678",
                "name": ":smile:",
            }

            result = slack_adapter._remove_reaction(payload)

            assert result.success is True

    def test_open_conversation(self, slack_adapter):
        """Test opening a conversation."""
        with patch.object(slack_adapter, "_make_request") as mock_request:
            mock_request.return_value = {
                "ok": True,
                "channel": {"id": "D123", "user": "U456"},
            }

            payload = {"users": ["U456"]}

            result = slack_adapter._open_conversation(payload)

            assert result.success is True
            assert result.data["conversation"]["id"] == "D123"

    def test_open_conversation_missing_users(self, slack_adapter):
        """Test opening a conversation without users."""
        payload = {}  # Missing users
        result = slack_adapter._open_conversation(payload)
        assert result.success is False
        assert "users" in result.error

    def test_test_connection_success(self, slack_adapter):
        """Test successful connection test."""
        with patch.object(slack_adapter, "_make_request") as mock_request:
            mock_request.return_value = {
                "ok": True,
                "user_id": "U123",
                "team_id": "T456",
            }

            result = slack_adapter.test_connection()

            assert result.success is True
            assert result.data["user_id"] == "U123"
            assert result.data["team_id"] == "T456"

    def test_test_connection_failure(self, slack_adapter):
        """Test failed connection test."""
        with patch.object(slack_adapter, "_make_request") as mock_request:
            mock_request.return_value = {"ok": False, "error": "invalid_auth"}

            result = slack_adapter.test_connection()

            assert result.success is False

    def test_exchange_code_for_token_success(self, slack_adapter):
        """Test successful token exchange."""
        slack_adapter.oauth_config.client_id = "test_client"
        slack_adapter.oauth_config.client_secret = "test_secret"
        slack_adapter.oauth_config.redirect_uri = "http://test.com/callback"

        with patch("requests.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "ok": True,
                "access_token": "fake-slack-token",
                "refresh_token": "test-refresh-token",
                "expires_in": 3600,
                "authed_user": {"access_token": "fake-slack-token"},
            }
            mock_post.return_value = mock_response

            result = slack_adapter.exchange_code_for_token("test_code")

            assert result.access_token == "fake-slack-token"
            assert result.refresh_token == "test-refresh-token"
            assert result.token_expiry is not None

    def test_exchange_code_for_token_failure(self, slack_adapter):
        """Test failed token exchange."""
        slack_adapter.oauth_config.client_id = "test_client"
        slack_adapter.oauth_config.client_secret = "test_secret"
        slack_adapter.oauth_config.redirect_uri = "http://test.com/callback"

        with patch("requests.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 400
            mock_response.json.return_value = {"ok": False, "error": "invalid_grant"}
            mock_post.return_value = mock_response

            with pytest.raises(ValueError):
                slack_adapter.exchange_code_for_token("invalid_code")


class TestSlackIntegrationAdapterInitialization:
    """Test SlackIntegrationAdapter initialization."""

    def test_init_with_config(self):
        """Test initialization with config."""
        config = IntegrationConfig(
            id=1,
            integration_type=IntegrationType.SLACK,
            name="Test",
            credentials=IntegrationCredentials(access_token="test-token"),
        )

        adapter = SlackIntegrationAdapter(config)

        assert adapter.config == config
        assert adapter.type == IntegrationType.SLACK

    def test_init_without_config(self):
        """Test initialization without config."""
        adapter = SlackIntegrationAdapter()

        assert adapter.config is None
        assert adapter.type == IntegrationType.SLACK

    def test_init_with_oauth_config(self):
        """Test initialization with OAuth config."""
        from ..integration_types import OAuthConfig

        oauth_config = OAuthConfig(
            client_id="test_client",
            client_secret="test_secret",
            redirect_uri="http://test.com/callback",
            scope=["chat:write"],
        )

        config = IntegrationConfig(
            id=1,
            integration_type=IntegrationType.SLACK,
            oauth_config=oauth_config,
        )

        adapter = SlackIntegrationAdapter(config)

        assert adapter.oauth_config == oauth_config
