# Tests for Integration Manager
# Version: 0.5.0 (Épic 7 - US-047)

"""
Unit tests for the IntegrationManager class.
"""

import pytest
from datetime import datetime

from ..integration_types import (
    IntegrationConfig,
    IntegrationCredentials,
    IntegrationStatus,
    IntegrationType,
)
from ..integration_manager import IntegrationManager
from ..oauth.oauth_service import OAuthService
from ..webhooks.webhook_service import WebhookService


@pytest.fixture
def integration_manager():
    """Create a test IntegrationManager instance."""
    oauth_service = OAuthService()
    webhook_service = WebhookService()
    return IntegrationManager(
        oauth_service=oauth_service,
        webhook_service=webhook_service,
    )


class TestIntegrationManager:
    """Tests for IntegrationManager."""

    def test_create_integration(self, integration_manager):
        """Test creating a new integration."""
        config = integration_manager.create_integration(
            integration_type=IntegrationType.GITHUB,
            name="Test GitHub Integration",
            description="Test description",
        )
        
        assert config is not None
        assert config.id is not None
        assert config.integration_type == IntegrationType.GITHUB
        assert config.name == "Test GitHub Integration"
        assert config.description == "Test description"
        assert config.status == IntegrationStatus.INACTIVE

    def test_get_integration(self, integration_manager):
        """Test getting an integration by ID."""
        # Create an integration first
        created_config = integration_manager.create_integration(
            integration_type=IntegrationType.GITHUB,
            name="Test GitHub Integration",
        )
        
        # Get it back
        retrieved_config = integration_manager.get_integration(created_config.id)
        
        assert retrieved_config is not None
        assert retrieved_config.id == created_config.id
        assert retrieved_config.name == created_config.name

    def test_list_integrations(self, integration_manager):
        """Test listing integrations."""
        # Create a few integrations
        integration_manager.create_integration(
            integration_type=IntegrationType.GITHUB,
            name="GitHub 1",
        )
        integration_manager.create_integration(
            integration_type=IntegrationType.SLACK,
            name="Slack 1",
        )
        
        # List all
        integrations = integration_manager.list_integrations()
        
        assert len(integrations) >= 2

    def test_update_integration(self, integration_manager):
        """Test updating an integration."""
        # Create an integration
        config = integration_manager.create_integration(
            integration_type=IntegrationType.GITHUB,
            name="Original Name",
        )
        
        # Update it
        updated_config = integration_manager.update_integration(
            config.id,
            name="Updated Name",
            description="New description",
        )
        
        assert updated_config is not None
        assert updated_config.name == "Updated Name"
        assert updated_config.description == "New description"

    def test_delete_integration(self, integration_manager):
        """Test deleting an integration."""
        # Create an integration
        config = integration_manager.create_integration(
            integration_type=IntegrationType.GITHUB,
            name="To Delete",
        )
        
        # Delete it
        result = integration_manager.delete_integration(config.id)
        
        assert result is True
        
        # Verify it's gone
        assert integration_manager.get_integration(config.id) is None

    def test_get_supported_integrations(self, integration_manager):
        """Test getting supported integrations."""
        supported = integration_manager.get_supported_integrations()
        
        assert len(supported) > 0
        
        # Check that GitHub is supported
        github_supported = any(
            integration["type"] == "github" 
            for integration in supported
        )
        assert github_supported

    def test_get_integration_metadata(self, integration_manager):
        """Test getting integration metadata."""
        metadata = integration_manager.get_integration_metadata(
            IntegrationType.GITHUB
        )
        
        assert metadata is not None
        assert "type" in metadata
        assert metadata["type"] == "github"
        assert "name" in metadata
        assert "supported_actions" in metadata

    def test_get_statistics(self, integration_manager):
        """Test getting statistics."""
        # Create some integrations
        integration_manager.create_integration(
            integration_type=IntegrationType.GITHUB,
            name="GitHub",
        )
        integration_manager.create_integration(
            integration_type=IntegrationType.SLACK,
            name="Slack",
        )
        
        stats = integration_manager.get_statistics()
        
        assert "total_integrations" in stats
        assert stats["total_integrations"] >= 2
        assert "active_integrations" in stats
        assert "webhook_stats" in stats


class TestIntegrationWithCredentials:
    """Tests for integrations with credentials."""

    def test_create_with_credentials(self, integration_manager):
        """Test creating an integration with credentials."""
        credentials = IntegrationCredentials(
            access_token="test_token_123",
            api_key="test_api_key",
        )
        
        config = integration_manager.create_integration(
            integration_type=IntegrationType.GITHUB,
            name="GitHub with Credentials",
            credentials=credentials,
        )
        
        assert config is not None
        assert config.credentials.access_token == "test_token_123"
        assert config.credentials.api_key == "test_api_key"

    def test_credentials_validation(self, integration_manager):
        """Test that credentials are validated."""
        credentials = IntegrationCredentials(
            access_token="valid_token",
        )
        
        assert credentials.is_valid() is True
        
        expired_credentials = IntegrationCredentials(
            access_token="token",
            token_expiry=datetime(2020, 1, 1),  # Long expired
        )
        
        assert expired_credentials.is_valid() is False


class TestIntegrationConfig:
    """Tests for IntegrationConfig."""

    def test_to_dict(self):
        """Test converting IntegrationConfig to dict."""
        config = IntegrationConfig(
            id=1,
            user_id=123,
            integration_type=IntegrationType.GITHUB,
            name="Test Integration",
            credentials=IntegrationCredentials(access_token="token123"),
        )
        
        data = config.to_dict(include_secrets=False)
        
        assert data["id"] == 1
        assert data["user_id"] == 123
        assert data["integration_type"] == "github"
        assert data["name"] == "Test Integration"
        # Secrets should not be included
        assert "access_token" not in data["credentials"]

    def test_to_dict_with_secrets(self):
        """Test converting IntegrationConfig to dict with secrets."""
        config = IntegrationConfig(
            id=1,
            integration_type=IntegrationType.GITHUB,
            name="Test Integration",
            credentials=IntegrationCredentials(access_token="token123"),
        )
        
        data = config.to_dict(include_secrets=True)
        
        assert data["credentials"]["access_token"] == "token123"

    def test_from_dict(self):
        """Test creating IntegrationConfig from dict."""
        data = {
            "id": 1,
            "user_id": 123,
            "integration_type": "github",
            "name": "Test Integration",
            "credentials": {
                "access_token": "token123",
            },
        }
        
        config = IntegrationConfig.from_dict(data)
        
        assert config.id == 1
        assert config.user_id == 123
        assert config.integration_type == IntegrationType.GITHUB
        assert config.name == "Test Integration"
        assert config.credentials.access_token == "token123"
