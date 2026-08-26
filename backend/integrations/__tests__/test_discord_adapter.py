# Tests for Discord Integration Adapter
# Version: 0.5.0 (Épic 7 - US-049)

"""
Unit tests for the DiscordIntegrationAdapter class.
"""

import pytest
from unittest.mock import MagicMock, patch

from ..integration_types import (
    IntegrationAction,
    IntegrationConfig,
    IntegrationCredentials,
    IntegrationType,
)
from ..adapters.discord_adapter import DiscordIntegrationAdapter
from ..base_adapter import ActionNotSupportedError, AuthenticationError


@pytest.fixture
def discord_adapter():
    """Create a test DiscordIntegrationAdapter instance."""
    config = IntegrationConfig(
        id=1,
        integration_type=IntegrationType.DISCORD,
        name="Test Discord",
        credentials=IntegrationCredentials(
            access_token="test_bot_token",
        ),
    )
    adapter = DiscordIntegrationAdapter(config)
    # Mock the session to avoid actual API calls
    adapter.session = MagicMock()
    return adapter


@pytest.fixture
def discord_adapter_no_creds():
    """Create a DiscordIntegrationAdapter without credentials."""
    config = IntegrationConfig(
        id=1,
        integration_type=IntegrationType.DISCORD,
        name="Test Discord",
        credentials=IntegrationCredentials(),
    )
    adapter = DiscordIntegrationAdapter(config)
    adapter.session = MagicMock()
    return adapter


@pytest.fixture
def discord_adapter_with_bot_token():
    """Create a DiscordIntegrationAdapter with bot token."""
    config = IntegrationConfig(
        id=1,
        integration_type=IntegrationType.DISCORD,
        name="Test Discord",
        credentials=IntegrationCredentials(
            api_key="fake-discord-bot-token",  # Bot token format
        ),
    )
    adapter = DiscordIntegrationAdapter(config)
    adapter.session = MagicMock()
    return adapter


class TestDiscordIntegrationAdapter:
    """Tests for DiscordIntegrationAdapter."""

    def test_adapter_properties(self, discord_adapter):
        """Test adapter properties."""
        assert discord_adapter.type == IntegrationType.DISCORD
        assert discord_adapter.name == "Discord"
        assert discord_adapter.description == "Intégration avec Discord pour envoyer des messages, notifications et interagir avec les serveurs"
        assert discord_adapter.auth_type.value == "oauth2"
        assert discord_adapter.color == "#5865F2"
        assert discord_adapter.icon == "discord"
        assert "send_message" in discord_adapter.supported_actions
        assert "list_channels" in discord_adapter.supported_actions
        assert "get_user_info" in discord_adapter.supported_actions
        assert "create_channel" in discord_adapter.supported_actions
        assert "send_embed" in discord_adapter.supported_actions
        assert "add_reaction" in discord_adapter.supported_actions

    def test_is_action_supported(self, discord_adapter):
        """Test checking if action is supported."""
        assert discord_adapter.is_action_supported("send_message") is True
        assert discord_adapter.is_action_supported("list_channels") is True
        assert discord_adapter.is_action_supported("send_embed") is True
        assert discord_adapter.is_action_supported("create_slash_command") is True
        assert discord_adapter.is_action_supported("execute_webhook") is True
        assert discord_adapter.is_action_supported("unknown_action") is False

    def test_get_metadata(self, discord_adapter):
        """Test getting adapter metadata."""
        metadata = discord_adapter.get_metadata()
        
        assert metadata["type"] == "discord"
        assert metadata["name"] == "Discord"
        assert metadata["auth_type"] == "oauth2"
        assert "send_message" in metadata["supported_actions"]
        assert "send_embed" in metadata["supported_actions"]
        assert "create_slash_command" in metadata["supported_actions"]

    def test_get_oauth_scopes(self, discord_adapter):
        """Test getting OAuth scopes."""
        scopes = discord_adapter.get_oauth_scopes()
        
        assert isinstance(scopes, list)
        assert len(scopes) > 0
        assert "identify" in scopes
        assert "guilds" in scopes
        assert "bot" in scopes
        assert "messages.read" in scopes

    def test_get_configuration_schema(self, discord_adapter):
        """Test getting configuration schema."""
        schema = discord_adapter.get_configuration_schema()
        
        assert isinstance(schema, dict)
        assert "properties" in schema
        assert "name" in schema["properties"]
        assert "settings" in schema["properties"]
        assert schema["required"] == ["name"]
        # Check for Discord-specific settings
        assert "application_id" in schema["properties"]["settings"]["properties"]
        assert "command_prefix" in schema["properties"]["settings"]["properties"]

    def test_get_action_schema(self, discord_adapter):
        """Test getting action schema."""
        schema = discord_adapter.get_action_schema("send_message")
        
        assert isinstance(schema, dict)
        
        # Test with unsupported action
        with pytest.raises(ValueError):
            discord_adapter.get_action_schema("unknown_action")

    def test_authenticate_with_valid_credentials(self, discord_adapter):
        """Test authentication with valid credentials."""
        with patch.object(discord_adapter, 'test_connection') as mock_test:
            mock_test.return_value.success = True
            
            result = discord_adapter.authenticate(IntegrationCredentials(
                access_token="valid-token"
            ))
            
            assert result is True

    def test_authenticate_with_invalid_credentials(self, discord_adapter):
        """Test authentication with invalid credentials."""
        with patch.object(discord_adapter, 'test_connection') as mock_test:
            mock_test.return_value.success = False
            
            result = discord_adapter.authenticate(IntegrationCredentials(
                access_token="invalid-token"
            ))
            
            assert result is False

    def test_get_auth_headers_with_access_token(self, discord_adapter):
        """Test getting auth headers with access token."""
        headers = discord_adapter._get_auth_headers()
        
        assert "Authorization" in headers
        assert headers["Authorization"].startswith("Bearer ")
        assert headers["Authorization"] == "Bearer test_bot_token"

    def test_get_auth_headers_with_bot_token(self, discord_adapter_with_bot_token):
        """Test getting auth headers with bot token."""
        headers = discord_adapter_with_bot_token._get_auth_headers()
        
        assert "Authorization" in headers
        # Bot tokens should use "Bot " prefix
        assert headers["Authorization"] == "Bot fake-discord-bot-token"

    def test_get_auth_headers_no_credentials(self, discord_adapter_no_creds):
        """Test getting auth headers without credentials."""
        with pytest.raises(AuthenticationError):
            discord_adapter_no_creds._get_auth_headers()

    def test_get_api_base_url(self, discord_adapter):
        """Test getting API base URL."""
        url = discord_adapter._get_api_base_url()
        assert url == "https://discord.com/api/v10"

    def test_authentication_url_generation(self, discord_adapter):
        """Test OAuth2 authentication URL generation."""
        # Set up OAuth config
        discord_adapter.oauth_config.client_id = "test_client_id"
        discord_adapter.oauth_config.redirect_uri = "http://test.com/callback"
        discord_adapter.oauth_config.scope = ["identify", "guilds", "bot"]
        
        url = discord_adapter.get_authentication_url(state="test_state")
        
        assert "client_id=test_client_id" in url
        # redirect_uri is URL-encoded
        assert "redirect_uri=http%3A%2F%2Ftest.com%2Fcallback" in url or "redirect_uri=http://test.com/callback" in url
        assert "response_type=code" in url
        # scope uses spaces which get encoded as + or %20
        assert "scope=identify+guilds+bot" in url or "scope=identify%20guilds%20bot" in url or "scope=identify guilds bot" in url
        assert "state=test_state" in url
        assert "prompt=consent" in url
        assert "discord.com/api/oauth2/authorize" in url

    def test_execute_supported_action(self, discord_adapter):
        """Test executing a supported action."""
        with patch.object(discord_adapter, '_send_message') as mock_send:
            mock_send.return_value.success = True
            
            action = IntegrationAction(
                action_type="send_message",
                payload={"channel_id": "123456789", "content": "Hello"}
            )
            
            result = discord_adapter.execute(action)
            
            mock_send.assert_called_once_with({"channel_id": "123456789", "content": "Hello"})
            assert result.success is True

    def test_execute_unsupported_action(self, discord_adapter):
        """Test executing an unsupported action."""
        action = IntegrationAction(
            action_type="unsupported_action",
            payload={}
        )
        
        with pytest.raises(ActionNotSupportedError):
            discord_adapter.execute(action)

    def test_send_message(self, discord_adapter):
        """Test sending a message."""
        with patch.object(discord_adapter, '_make_request') as mock_request:
            mock_request.return_value = {
                "id": "123456789012345678",
                "channel_id": "123456789",
                "content": "Hello World",
                "timestamp": "2024-01-01T00:00:00.000Z",
            }
            
            payload = {
                "channel_id": "123456789",
                "content": "Hello World",
            }
            
            result = discord_adapter._send_message(payload)
            
            assert result.success is True
            mock_request.assert_called_once()
            call_args = mock_request.call_args
            assert call_args[0][0] == "POST"
            assert call_args[0][1] == "channels/123456789/messages"
            # channel_id is in the URL, not in the JSON body for Discord
            assert call_args[1]["json"]["content"] == "Hello World"

    def test_send_message_with_embeds(self, discord_adapter):
        """Test sending a message with embeds."""
        with patch.object(discord_adapter, '_make_request') as mock_request:
            mock_request.return_value = {"id": "123", "channel_id": "123456789"}
            
            payload = {
                "channel_id": "123456789",
                "content": "Hello",
                "embeds": [{"title": "Test", "description": "Test embed"}],
            }
            
            result = discord_adapter._send_message(payload)
            
            assert result.success is True
            call_args = mock_request.call_args
            assert "embeds" in call_args[1]["json"]

    def test_send_message_missing_required_fields(self, discord_adapter):
        """Test sending a message with missing required fields."""
        # Missing channel_id
        payload = {"content": "Hello"}
        result = discord_adapter._send_message(payload)
        assert result.success is False
        assert "channel_id" in result.error
        
        # Missing content
        payload = {"channel_id": "123456789"}
        result = discord_adapter._send_message(payload)
        assert result.success is False
        assert "content" in result.error

    def test_send_embed(self, discord_adapter):
        """Test sending a message with embed."""
        with patch.object(discord_adapter, '_make_request') as mock_request:
            mock_request.return_value = {"id": "123", "channel_id": "123456789"}
            
            payload = {
                "channel_id": "123456789",
                "embed": {
                    "title": "Test Embed",
                    "description": "This is a test",
                    "color": 0xFF0000,
                },
            }
            
            result = discord_adapter._send_embed(payload)
            
            assert result.success is True
            call_args = mock_request.call_args
            assert call_args[0][0] == "POST"
            assert call_args[0][1] == "channels/123456789/messages"
            assert "embeds" in call_args[1]["json"]

    def test_send_embed_missing_fields(self, discord_adapter):
        """Test sending an embed with missing fields."""
        # Missing channel_id
        payload = {"embed": {"title": "Test"}}
        result = discord_adapter._send_embed(payload)
        assert result.success is False
        
        # Missing embed
        payload = {"channel_id": "123456789"}
        result = discord_adapter._send_embed(payload)
        assert result.success is False

    def test_edit_message(self, discord_adapter):
        """Test editing a message."""
        with patch.object(discord_adapter, '_make_request') as mock_request:
            mock_request.return_value = {
                "id": "123",
                "channel_id": "123456789",
                "content": "Edited",
            }
            
            payload = {
                "channel_id": "123456789",
                "message_id": "123",
                "content": "Edited message",
            }
            
            result = discord_adapter._edit_message(payload)
            
            assert result.success is True
            call_args = mock_request.call_args
            assert call_args[0][0] == "PATCH"
            assert call_args[0][1] == "channels/123456789/messages/123"

    def test_delete_message(self, discord_adapter):
        """Test deleting a message."""
        with patch.object(discord_adapter, '_make_request') as mock_request:
            mock_request.return_value = {}  # DELETE returns empty body
            
            payload = {
                "channel_id": "123456789",
                "message_id": "123",
            }
            
            result = discord_adapter._delete_message(payload)
            
            assert result.success is True
            assert result.data["deleted"] is True
            call_args = mock_request.call_args
            assert call_args[0][0] == "DELETE"
            assert call_args[0][1] == "channels/123456789/messages/123"

    def test_list_channels(self, discord_adapter):
        """Test listing channels."""
        with patch.object(discord_adapter, '_make_request') as mock_request:
            mock_request.return_value = [
                {"id": "123456789", "name": "general", "type": 0},
                {"id": "987654321", "name": "random", "type": 0},
            ]
            
            payload = {"guild_id": "111222333"}
            
            result = discord_adapter._list_channels(payload)
            
            assert result.success is True
            assert len(result.data["channels"]) == 2
            assert result.data["count"] == 2
            call_args = mock_request.call_args
            assert call_args[0][0] == "GET"
            assert call_args[0][1] == "guilds/111222333/channels"

    def test_get_channel_info(self, discord_adapter):
        """Test getting channel info."""
        with patch.object(discord_adapter, '_make_request') as mock_request:
            mock_request.return_value = {
                "id": "123456789",
                "name": "general",
                "type": 0,
                "topic": "General chat",
            }
            
            payload = {"channel_id": "123456789"}
            
            result = discord_adapter._get_channel_info(payload)
            
            assert result.success is True
            assert result.data["channel"]["name"] == "general"

    def test_create_channel(self, discord_adapter):
        """Test creating a channel."""
        with patch.object(discord_adapter, '_make_request') as mock_request:
            mock_request.return_value = {
                "id": "123456789",
                "name": "new-channel",
                "type": 0,
            }
            
            payload = {
                "guild_id": "111222333",
                "name": "new-channel",
                "type": 0,
            }
            
            result = discord_adapter._create_channel(payload)
            
            assert result.success is True
            assert result.data["channel"]["name"] == "new-channel"

    def test_list_guilds(self, discord_adapter):
        """Test listing guilds."""
        with patch.object(discord_adapter, '_make_request') as mock_request:
            mock_request.return_value = [
                {"id": "111222333", "name": "Test Server 1", "icon": "..."},
                {"id": "444555666", "name": "Test Server 2", "icon": "..."},
            ]
            
            payload = {"limit": 100}
            
            result = discord_adapter._list_guilds(payload)
            
            assert result.success is True
            assert len(result.data["guilds"]) == 2
            assert result.data["count"] == 2

    def test_get_guild_info(self, discord_adapter):
        """Test getting guild info."""
        with patch.object(discord_adapter, '_make_request') as mock_request:
            mock_request.return_value = {
                "id": "111222333",
                "name": "Test Server",
                "owner_id": "123456789",
                "member_count": 100,
            }
            
            payload = {"guild_id": "111222333"}
            
            result = discord_adapter._get_guild_info(payload)
            
            assert result.success is True
            assert result.data["guild"]["name"] == "Test Server"

    def test_get_user_info(self, discord_adapter):
        """Test getting user info."""
        with patch.object(discord_adapter, '_make_request') as mock_request:
            mock_request.return_value = {
                "id": "123456789",
                "username": "testuser",
                "discriminator": "1234",
                "global_name": "Test User",
                "avatar": "...",
            }
            
            payload = {"user_id": "123456789"}
            
            result = discord_adapter._get_user_info(payload)
            
            assert result.success is True
            assert result.data["user"]["username"] == "testuser"
            assert result.data["user"]["global_name"] == "Test User"

    def test_list_guild_members(self, discord_adapter):
        """Test listing guild members."""
        with patch.object(discord_adapter, '_make_request') as mock_request:
            mock_request.return_value = [
                {"user": {"id": "123456789", "username": "user1"}, "roles": []},
                {"user": {"id": "987654321", "username": "user2"}, "roles": []},
            ]
            
            payload = {"guild_id": "111222333"}
            
            result = discord_adapter._list_guild_members(payload)
            
            assert result.success is True
            assert len(result.data["members"]) == 2

    def test_get_member_info(self, discord_adapter):
        """Test getting member info."""
        with patch.object(discord_adapter, '_make_request') as mock_request:
            mock_request.return_value = {
                "user": {"id": "123456789", "username": "testuser"},
                "nick": "TestNick",
                "roles": ["111222333"],
                "joined_at": "2024-01-01T00:00:00.000Z",
            }
            
            payload = {"guild_id": "111222333", "user_id": "123456789"}
            
            result = discord_adapter._get_member_info(payload)
            
            assert result.success is True
            assert result.data["member"]["nick"] == "TestNick"

    def test_list_roles(self, discord_adapter):
        """Test listing roles."""
        with patch.object(discord_adapter, '_make_request') as mock_request:
            mock_request.return_value = [
                {"id": "111222333", "name": "Admin", "color": 0xFF0000},
                {"id": "444555666", "name": "Member", "color": 0x00FF00},
            ]
            
            payload = {"guild_id": "111222333"}
            
            result = discord_adapter._list_roles(payload)
            
            assert result.success is True
            assert len(result.data["roles"]) == 2

    def test_create_role(self, discord_adapter):
        """Test creating a role."""
        with patch.object(discord_adapter, '_make_request') as mock_request:
            mock_request.return_value = {
                "id": "111222333",
                "name": "New Role",
                "color": 0x0000FF,
                "permissions": 0,
            }
            
            payload = {
                "guild_id": "111222333",
                "name": "New Role",
                "color": 0x0000FF,
            }
            
            result = discord_adapter._create_role(payload)
            
            assert result.success is True
            assert result.data["role"]["name"] == "New Role"

    def test_add_role_to_member(self, discord_adapter):
        """Test adding a role to a member."""
        with patch.object(discord_adapter, '_make_request') as mock_request:
            mock_request.return_value = {"id": "111222333", "name": "Admin"}
            
            payload = {
                "guild_id": "111222333",
                "user_id": "123456789",
                "role_id": "111222333",
            }
            
            result = discord_adapter._add_role_to_member(payload)
            
            assert result.success is True

    def test_remove_role_from_member(self, discord_adapter):
        """Test removing a role from a member."""
        with patch.object(discord_adapter, '_make_request') as mock_request:
            mock_request.return_value = {}  # DELETE returns empty
            
            payload = {
                "guild_id": "111222333",
                "user_id": "123456789",
                "role_id": "111222333",
            }
            
            result = discord_adapter._remove_role_from_member(payload)
            
            assert result.success is True

    def test_add_reaction(self, discord_adapter):
        """Test adding a reaction."""
        with patch.object(discord_adapter, '_make_request') as mock_request:
            mock_request.return_value = {}  # PUT returns empty
            
            payload = {
                "channel_id": "123456789",
                "message_id": "987654321",
                "emoji": ":smile:",
            }
            
            result = discord_adapter._add_reaction(payload)
            
            assert result.success is True
            call_args = mock_request.call_args
            assert call_args[0][0] == "PUT"
            assert ":smile:" in call_args[0][1]

    def test_add_reaction_with_custom_emoji(self, discord_adapter):
        """Test adding a custom emoji reaction."""
        with patch.object(discord_adapter, '_make_request') as mock_request:
            mock_request.return_value = {}
            
            payload = {
                "channel_id": "123456789",
                "message_id": "987654321",
                "emoji": "custom_emoji:123456789",
            }
            
            result = discord_adapter._add_reaction(payload)
            
            assert result.success is True

    def test_remove_reaction(self, discord_adapter):
        """Test removing a reaction."""
        with patch.object(discord_adapter, '_make_request') as mock_request:
            mock_request.return_value = {}
            
            payload = {
                "channel_id": "123456789",
                "message_id": "987654321",
                "emoji": ":smile:",
            }
            
            result = discord_adapter._remove_reaction(payload)
            
            assert result.success is True

    def test_create_slash_command(self, discord_adapter):
        """Test creating a slash command."""
        discord_adapter.oauth_config.client_id = "test_client"
        discord_adapter.oauth_config.client_secret = "test_secret"
        
        with patch('requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "id": "123456789012345678",
                "application_id": "111222333",
                "name": "test",
                "description": "Test command",
            }
            mock_post.return_value = mock_response
            
            payload = {
                "application_id": "111222333",
                "name": "test",
                "description": "Test command",
            }
            
            result = discord_adapter._create_slash_command(payload)
            
            assert result.success is True
            assert result.data["command"]["name"] == "test"

    def test_list_slash_commands(self, discord_adapter):
        """Test listing slash commands."""
        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = [
                {"id": "123", "name": "test1", "description": "Test 1"},
                {"id": "456", "name": "test2", "description": "Test 2"},
            ]
            mock_get.return_value = mock_response
            
            payload = {"application_id": "111222333"}
            
            result = discord_adapter._list_slash_commands(payload)
            
            assert result.success is True
            assert len(result.data["commands"]) == 2

    def test_delete_slash_command(self, discord_adapter):
        """Test deleting a slash command."""
        with patch('requests.delete') as mock_delete:
            mock_response = MagicMock()
            mock_response.status_code = 204
            mock_delete.return_value = mock_response
            
            payload = {
                "application_id": "111222333",
                "command_id": "123",
            }
            
            result = discord_adapter._delete_slash_command(payload)
            
            assert result.success is True
            assert result.data["deleted"] is True

    def test_create_webhook(self, discord_adapter):
        """Test creating a webhook."""
        with patch.object(discord_adapter, '_make_request') as mock_request:
            mock_request.return_value = {
                "id": "123456789",
                "name": "Test Webhook",
                "channel_id": "123456789",
                "token": "test-token",
                "url": "https://discord.com/api/webhooks/123456789/test-token",
            }
            
            payload = {
                "channel_id": "123456789",
                "name": "Test Webhook",
            }
            
            result = discord_adapter._create_webhook(payload)
            
            assert result.success is True
            assert result.data["webhook"]["name"] == "Test Webhook"

    def test_list_webhooks(self, discord_adapter):
        """Test listing webhooks."""
        with patch.object(discord_adapter, '_make_request') as mock_request:
            mock_request.return_value = [
                {"id": "123", "name": "Webhook 1", "channel_id": "123456789"},
                {"id": "456", "name": "Webhook 2", "channel_id": "987654321"},
            ]
            
            payload = {"guild_id": "111222333"}
            
            result = discord_adapter._list_webhooks(payload)
            
            assert result.success is True
            assert len(result.data["webhooks"]) == 2

    def test_execute_webhook(self, discord_adapter):
        """Test executing a webhook."""
        with patch('requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 204
            mock_post.return_value = mock_response
            
            payload = {
                "webhook_url": "https://discord.com/api/webhooks/123/test-token",
                "content": "Hello from webhook!",
            }
            
            result = discord_adapter._execute_webhook(payload)
            
            assert result.success is True
            assert result.data["webhook"] == "executed"

    def test_execute_webhook_with_embed(self, discord_adapter):
        """Test executing a webhook with embed."""
        with patch('requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 204
            mock_post.return_value = mock_response
            
            payload = {
                "webhook_url": "https://discord.com/api/webhooks/123/test-token",
                "content": "Hello",
                "embeds": [{"title": "Test", "description": "Test embed"}],
                "username": "AgentWorld",
                "avatar_url": "https://example.com/avatar.png",
            }
            
            result = discord_adapter._execute_webhook(payload)
            
            assert result.success is True

    def test_execute_webhook_missing_url(self, discord_adapter):
        """Test executing a webhook without URL."""
        payload = {"content": "Hello"}  # Missing webhook_url
        result = discord_adapter._execute_webhook(payload)
        assert result.success is False
        assert "webhook_url" in result.error

    def test_test_connection_success(self, discord_adapter):
        """Test successful connection test."""
        with patch.object(discord_adapter, '_make_request') as mock_request:
            mock_request.return_value = {
                "id": "123456789",
                "username": "testuser",
                "discriminator": "1234",
                "global_name": "Test User",
            }
            
            result = discord_adapter.test_connection()
            
            assert result.success is True
            assert result.data["user_id"] == "123456789"
            assert result.data["username"] == "testuser#1234"
            assert result.data["global_name"] == "Test User"

    def test_test_connection_failure(self, discord_adapter):
        """Test failed connection test."""
        with patch.object(discord_adapter, '_make_request') as mock_request:
            mock_request.side_effect = Exception("Connection failed")
            
            result = discord_adapter.test_connection()
            
            assert result.success is False

    def test_exchange_code_for_token_success(self, discord_adapter):
        """Test successful token exchange."""
        discord_adapter.oauth_config.client_id = "test_client"
        discord_adapter.oauth_config.client_secret = "test_secret"
        discord_adapter.oauth_config.redirect_uri = "http://test.com/callback"
        
        with patch('requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "access_token": "test_access_token",
                "token_type": "Bearer",
                "expires_in": 7200,
                "refresh_token": "test_refresh_token",
                "scope": "identify guilds",
            }
            mock_post.return_value = mock_response
            
            result = discord_adapter.exchange_code_for_token("test_code")
            
            assert result.access_token == "test_access_token"
            assert result.refresh_token == "test_refresh_token"
            assert result.token_expiry is not None

    def test_exchange_code_for_token_failure(self, discord_adapter):
        """Test failed token exchange."""
        discord_adapter.oauth_config.client_id = "test_client"
        discord_adapter.oauth_config.client_secret = "test_secret"
        discord_adapter.oauth_config.redirect_uri = "http://test.com/callback"
        
        with patch('requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 400
            mock_response.json.return_value = {
                "error": "invalid_grant",
                "error_description": "Invalid authorization code",
            }
            mock_post.return_value = mock_response
            
            with pytest.raises(ValueError):
                discord_adapter.exchange_code_for_token("invalid_code")

    def test_refresh_token_success(self, discord_adapter):
        """Test successful token refresh."""
        discord_adapter.oauth_config.client_id = "test_client"
        discord_adapter.oauth_config.client_secret = "test_secret"
        
        with patch('requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "access_token": "new_access_token",
                "token_type": "Bearer",
                "expires_in": 7200,
                "refresh_token": "new_refresh_token",
                "scope": "identify guilds",
            }
            mock_post.return_value = mock_response
            
            result = discord_adapter.refresh_token("old_refresh_token")
            
            assert result.access_token == "new_access_token"
            assert result.refresh_token == "new_refresh_token"


class TestDiscordIntegrationAdapterInitialization:
    """Test DiscordIntegrationAdapter initialization."""

    def test_init_with_config(self):
        """Test initialization with config."""
        config = IntegrationConfig(
            id=1,
            integration_type=IntegrationType.DISCORD,
            name="Test",
            credentials=IntegrationCredentials(access_token="test-token"),
        )
        
        adapter = DiscordIntegrationAdapter(config)
        
        assert adapter.config == config
        assert adapter.type == IntegrationType.DISCORD
        assert adapter.api_version == 10

    def test_init_without_config(self):
        """Test initialization without config."""
        adapter = DiscordIntegrationAdapter()
        
        assert adapter.config is None
        assert adapter.type == IntegrationType.DISCORD

    def test_init_with_oauth_config(self):
        """Test initialization with OAuth config."""
        from ..integration_types import OAuthConfig
        
        oauth_config = OAuthConfig(
            client_id="test_client",
            client_secret="test_secret",
            redirect_uri="http://test.com/callback",
            scope=["identify", "guilds"],
        )
        
        config = IntegrationConfig(
            id=1,
            integration_type=IntegrationType.DISCORD,
            oauth_config=oauth_config,
        )
        
        adapter = DiscordIntegrationAdapter(config)
        
        assert adapter.oauth_config == oauth_config
