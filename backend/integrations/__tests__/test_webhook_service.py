# Tests for Webhook Service
# Version: 0.5.0 (Épic 7 - US-053)

"""
Unit tests for the WebhookService class.
"""

import pytest
from datetime import datetime
from unittest.mock import MagicMock, patch

from ..integration_types import (
    IntegrationConfig,
    IntegrationCredentials,
    IntegrationType,
)
from ..webhooks.webhook_service import WebhookService
from ..webhooks.webhook_types import (
    WebhookEvent,
    WebhookEventType,
    WebhookPayload,
    WebhookResponse,
    WebhookStatus,
    WebhookSubscription,
)


@pytest.fixture
def webhook_service():
    """Create a test WebhookService instance."""
    return WebhookService()


@pytest.fixture
def sample_webhook_event():
    """Create a sample webhook event."""
    return WebhookEvent(
        event_type=WebhookEventType.AGENT_CREATED.value,
        source="agent",
        source_id="123",
        data={"agent_id": "123", "name": "Test Agent"},
        metadata={"version": "1.0"},
    )


@pytest.fixture
def sample_webhook_payload():
    """Create a sample webhook payload."""
    return WebhookPayload(
        headers={"Content-Type": "application/json"},
        body={"event_type": "agent.created", "data": {"test": "value"}},
        query_params={},
        webhook_id="test-webhook-id",
        webhook_secret="test-secret",
    )


class TestWebhookServiceSubscriptionManagement:
    """Tests for webhook subscription management."""

    def test_create_subscription(self, webhook_service):
        """Test creating a webhook subscription."""
        subscription = webhook_service.create_subscription(
            name="Test Webhook",
            url="https://example.com/webhook",
            events=["agent.created", "agent.updated"],
            secret="test-secret",
        )
        
        assert subscription.name == "Test Webhook"
        assert subscription.url == "https://example.com/webhook"
        assert subscription.events == ["agent.created", "agent.updated"]
        assert subscription.secret == "test-secret"
        assert subscription.active is True
        assert subscription.status == WebhookStatus.ACTIVE

    def test_create_subscription_without_secret(self, webhook_service):
        """Test creating a subscription without a secret (auto-generated)."""
        subscription = webhook_service.create_subscription(
            name="Test Webhook",
            url="https://example.com/webhook",
            events=["agent.created"],
        )
        
        assert subscription.secret is not None
        assert len(subscription.secret) > 0

    def test_get_subscription(self, webhook_service):
        """Test getting a subscription by ID."""
        # Create a subscription first
        subscription = webhook_service.create_subscription(
            name="Test Webhook",
            url="https://example.com/webhook",
            events=["agent.created"],
        )
        
        # Get the subscription by ID
        retrieved = webhook_service.get_subscription(subscription.id)
        
        assert retrieved is not None
        assert retrieved.name == "Test Webhook"

    def test_get_nonexistent_subscription(self, webhook_service):
        """Test getting a non-existent subscription."""
        subscription = webhook_service.get_subscription("nonexistent-id")
        assert subscription is None

    def test_list_subscriptions(self, webhook_service):
        """Test listing all subscriptions."""
        # Create some subscriptions
        webhook_service.create_subscription(
            name="Webhook 1",
            url="https://example1.com/webhook",
            events=["agent.created"],
        )
        webhook_service.create_subscription(
            name="Webhook 2",
            url="https://example2.com/webhook",
            events=["agent.updated"],
        )
        
        subscriptions = webhook_service.list_subscriptions()
        
        assert len(subscriptions) == 2
        names = [s.name for s in subscriptions]
        assert "Webhook 1" in names
        assert "Webhook 2" in names

    def test_update_subscription(self, webhook_service):
        """Test updating a subscription."""
        subscription = webhook_service.create_subscription(
            name="Test Webhook",
            url="https://example.com/webhook",
            events=["agent.created"],
        )
        
        # Update the subscription
        updated = webhook_service.update_subscription(
            subscription.id,
            name="Updated Webhook",
            url="https://updated.com/webhook",
        )
        
        assert updated is not None
        assert updated.name == "Updated Webhook"
        assert updated.url == "https://updated.com/webhook"

    def test_delete_subscription(self, webhook_service):
        """Test deleting a subscription."""
        subscription = webhook_service.create_subscription(
            name="Test Webhook",
            url="https://example.com/webhook",
            events=["agent.created"],
        )
        
        # Delete the subscription
        result = webhook_service.delete_subscription(subscription.id)
        
        assert result is True
        
        # Verify it's deleted
        assert webhook_service.get_subscription(subscription.id) is None

    def test_activate_subscription(self, webhook_service):
        """Test activating a subscription."""
        subscription = webhook_service.create_subscription(
            name="Test Webhook",
            url="https://example.com/webhook",
            events=["agent.created"],
        )
        
        # Deactivate first
        webhook_service.deactivate_subscription(subscription.id)
        
        # Activate the subscription
        result = webhook_service.activate_subscription(subscription.id)
        
        assert result is True
        
        # Verify it's activated
        updated = webhook_service.get_subscription(subscription.id)
        assert updated.active is True
        assert updated.status == WebhookStatus.ACTIVE

    def test_deactivate_subscription(self, webhook_service):
        """Test deactivating a subscription."""
        subscription = webhook_service.create_subscription(
            name="Test Webhook",
            url="https://example.com/webhook",
            events=["agent.created"],
        )
        
        # Deactivate the subscription
        result = webhook_service.deactivate_subscription(subscription.id)
        
        assert result is True
        
        # Verify it's deactivated
        updated = webhook_service.get_subscription(subscription.id)
        assert updated.active is False
        assert updated.status == WebhookStatus.INACTIVE


class TestWebhookServiceHandlerManagement:
    """Tests for webhook handler management."""

    def test_register_incoming_handler(self, webhook_service):
        """Test registering an incoming webhook handler."""
        def test_handler(payload, config):
            return WebhookResponse(success=True, message="Test handler called")
        
        webhook_service.register_incoming_handler("test.event", test_handler)
        
        # Check that the handler is registered
        assert "test.event" in webhook_service._incoming_handlers
        assert test_handler in webhook_service._incoming_handlers["test.event"]

    def test_register_multiple_handlers(self, webhook_service):
        """Test registering multiple handlers for the same event."""
        def handler1(payload, config):
            return WebhookResponse(success=True, message="Handler 1")
        
        def handler2(payload, config):
            return WebhookResponse(success=True, message="Handler 2")
        
        webhook_service.register_incoming_handler("test.event", handler1)
        webhook_service.register_incoming_handler("test.event", handler2)
        
        assert len(webhook_service._incoming_handlers["test.event"]) == 2

    def test_unregister_handler(self, webhook_service):
        """Test unregistering a webhook handler."""
        def test_handler(payload, config):
            return WebhookResponse(success=True)
        
        webhook_service.register_incoming_handler("test.event", test_handler)
        
        # Unregister the handler
        result = webhook_service.unregister_handler("test.event", test_handler)
        
        assert result is True
        assert len(webhook_service._incoming_handlers.get("test.event", [])) == 0

    def test_register_outgoing_handler(self, webhook_service):
        """Test registering an outgoing webhook handler."""
        def test_handler(payload, config):
            return WebhookResponse(success=True)
        
        webhook_service.register_outgoing_handler("slack", test_handler)
        
        assert "slack" in webhook_service._outgoing_handlers
        assert webhook_service._outgoing_handlers["slack"] == test_handler


class TestWebhookServiceEmitEvents:
    """Tests for emitting webhook events."""

    def test_emit_event_to_matching_subscriptions(self, webhook_service):
        """Test emitting an event to matching subscriptions."""
        # Create subscriptions for different events
        sub1 = webhook_service.create_subscription(
            name="Agent Events",
            url="https://example.com/agent-events",
            events=["agent.created", "agent.updated"],
        )
        
        sub2 = webhook_service.create_subscription(
            name="Workflow Events",
            url="https://example.com/workflow-events",
            events=["workflow.started"],
        )
        
        # Emit an agent.created event
        event = WebhookEvent(
            event_type="agent.created",
            source="agent",
            source_id="123",
        )
        
        # Mock requests.post to avoid actual HTTP calls
        with patch('requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_post.return_value = mock_response
            
            responses = webhook_service.emit_event(event)
            
            # Should only emit to the first subscription
            assert len(responses) == 1
            
            # Check that the correct URL was called
            call_args = mock_post.call_args
            assert sub1.url in call_args[0][0]

    def test_emit_event_to_all_subscriptions_with_wildcard(self, webhook_service):
        """Test emitting an event to all subscriptions with wildcard."""
        # Create a subscription with wildcard
        sub = webhook_service.create_subscription(
            name="All Events",
            url="https://example.com/all-events",
            events=["*"],  # Wildcard for all events
        )
        
        # Emit any event
        event = WebhookEvent(
            event_type="custom.event",
            source="custom",
            source_id="123",
        )
        
        with patch('requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_post.return_value = mock_response
            
            responses = webhook_service.emit_event(event)
            
            assert len(responses) == 1

    def test_emit_event_no_matching_subscriptions(self, webhook_service):
        """Test emitting an event with no matching subscriptions."""
        # Create a subscription for a different event
        webhook_service.create_subscription(
            name="Agent Events",
            url="https://example.com/agent-events",
            events=["agent.created"],
        )
        
        # Emit a different event
        event = WebhookEvent(
            event_type="workflow.started",
            source="workflow",
            source_id="123",
        )
        
        with patch('requests.post') as mock_post:
            responses = webhook_service.emit_event(event)
            
            assert len(responses) == 0
            mock_post.assert_not_called()

    def test_emit_to_integration(self, webhook_service):
        """Test emitting an event to a specific integration."""
        # Create an integration config
        config = IntegrationConfig(
            id=1,
            integration_type=IntegrationType.SLACK,
            name="Test Slack",
            credentials=IntegrationCredentials(
                access_token="test-token",
                webhook_url="https://hooks.slack.com/services/test",
                webhook_secret="test-secret",
            ),
        )
        
        # Register an outgoing handler for Slack
        def slack_handler(payload, integration_config):
            return WebhookResponse(
                success=True,
                message="Event sent to Slack",
            )
        
        webhook_service.register_outgoing_handler("slack", slack_handler)
        
        # Create an event
        event = WebhookEvent(
            event_type="agent.created",
            source="agent",
            source_id="123",
        )
        
        # Emit to the specific integration
        response = webhook_service.emit_to_integration(event, config)
        
        assert response.success is True
        assert response.message == "Event sent to Slack"

    def test_handle_incoming_webhook(self, webhook_service):
        """Test handling an incoming webhook."""
        # Register a handler
        def test_handler(payload, config):
            return WebhookResponse(
                success=True,
                message="Incoming webhook handled",
                data={"received": True},
            )
        
        webhook_service.register_incoming_handler("test.event", test_handler)
        
        # Create a payload
        payload = WebhookPayload(
            body={"event_type": "test.event", "data": {"test": "value"}},
        )
        
        # Handle the incoming webhook
        response = webhook_service.handle_incoming_webhook(payload)
        
        assert response.success is True
        assert response.message == "Incoming webhook handled"

    def test_handle_incoming_webhook_no_handler(self, webhook_service):
        """Test handling an incoming webhook with no handler."""
        payload = WebhookPayload(
            body={"event_type": "unknown.event", "data": {}},
        )
        
        response = webhook_service.handle_incoming_webhook(payload)
        
        assert response.success is False
        assert "No handler" in response.error

    def test_handle_incoming_webhook_with_wildcard_handler(self, webhook_service):
        """Test handling an incoming webhook with wildcard handler."""
        # Register a wildcard handler
        def wildcard_handler(payload, config):
            return WebhookResponse(
                success=True,
                message="Wildcard handler called",
            )
        
        webhook_service.register_incoming_handler("*", wildcard_handler)
        
        # Handle any event
        payload = WebhookPayload(
            body={"event_type": "any.event", "data": {}},
        )
        
        response = webhook_service.handle_incoming_webhook(payload)
        
        assert response.success is True
        assert response.message == "Wildcard handler called"


class TestWebhookServiceSignatureVerification:
    """Tests for webhook signature verification."""

    def test_verify_webhook_signature(self, webhook_service):
        """Test verifying a webhook signature."""
        secret = "test-secret"
        test_body = {"test": "data"}
        
        # Generate the correct signature for the test body
        import hmac
        import hashlib
        payload_bytes = str(test_body).encode()
        computed_hash = hmac.new(
            secret.encode(),
            payload_bytes,
            hashlib.sha256
        ).hexdigest()
        expected_signature = f"sha256={computed_hash}"
        
        payload = WebhookPayload(
            body=test_body,
            headers={"X-Hub-Signature-256": expected_signature},
        )
        
        result = webhook_service.verify_webhook_signature(
            payload,
            secret,
            expected_signature
        )
        
        assert result is True

    def test_verify_webhook_signature_with_header(self, webhook_service):
        """Test verifying signature with header from payload."""
        secret = "test-secret"
        test_body = {"test": "data"}
        
        # Generate the correct signature for the test body
        import hmac
        import hashlib
        payload_bytes = str(test_body).encode()
        computed_hash = hmac.new(
            secret.encode(),
            payload_bytes,
            hashlib.sha256
        ).hexdigest()
        expected_signature = f"sha256={computed_hash}"
        
        payload = WebhookPayload(
            body=test_body,
            headers={"X-Hub-Signature-256": expected_signature},
        )
        
        result = webhook_service.verify_webhook_signature(payload, secret)
        
        assert result is True

    def test_verify_webhook_signature_failure(self, webhook_service):
        """Test signature verification with wrong secret."""
        payload = WebhookPayload(
            body={"test": "data"},
            headers={"X-Hub-Signature-256": "sha256=5257c8e2e079762f73326a3593042c4250a00152af637066313450161c8f657c"},
        )
        
        # Use wrong secret
        result = webhook_service.verify_webhook_signature(payload, "wrong-secret")
        
        assert result is False

    def test_generate_signature(self, webhook_service):
        """Test generating a signature."""
        data = '{"test": "data"}'
        secret = "test-secret"
        
        signature = webhook_service.generate_signature(data, secret)
        
        assert signature.startswith("sha256=")
        assert len(signature) == 7 + 64  # "sha256=" + 64 hex chars


class TestWebhookServiceStatistics:
    """Tests for webhook service statistics."""

    def test_get_statistics_empty(self, webhook_service):
        """Test getting statistics with no subscriptions."""
        stats = webhook_service.get_statistics()
        
        assert stats["total_subscriptions"] == 0
        assert stats["active_subscriptions"] == 0
        assert stats["total_calls"] == 0

    def test_get_statistics_with_subscriptions(self, webhook_service):
        """Test getting statistics with subscriptions."""
        # Create some subscriptions
        sub1 = webhook_service.create_subscription(
            name="Active Webhook",
            url="https://example.com/webhook",
            events=["agent.created"],
        )
        
        sub2 = webhook_service.create_subscription(
            name="Inactive Webhook",
            url="https://example.com/webhook2",
            events=["workflow.started"],
        )
        
        # Deactivate sub2
        webhook_service.deactivate_subscription(sub2.id)
        
        # Update subscription stats for sub1
        sub1.calls_count = 10
        sub1.success_count = 8
        sub1.error_count = 2
        
        stats = webhook_service.get_statistics()
        
        assert stats["total_subscriptions"] == 2
        assert stats["active_subscriptions"] == 1
        assert stats["total_calls"] == 10
        assert stats["total_success"] == 8
        assert stats["total_errors"] == 2
        assert stats["success_rate"] == 0.8


class TestWebhookServiceCleanup:
    """Tests for webhook service cleanup."""

    def test_cleanup(self, webhook_service):
        """Test cleanup of webhook service."""
        # Create some subscriptions
        webhook_service.create_subscription(
            name="Test Webhook",
            url="https://example.com/webhook",
            events=["agent.created"],
        )
        
        # Register a handler
        def test_handler(payload, config):
            return WebhookResponse(success=True)
        
        webhook_service.register_incoming_handler("test.event", test_handler)
        
        # Cleanup
        webhook_service.cleanup()
        
        # Verify cleanup
        assert len(webhook_service._subscriptions) == 0
        assert len(webhook_service._incoming_handlers) == 0
        assert len(webhook_service._outgoing_handlers) == 0
        assert len(webhook_service._webhook_secrets) == 0


class TestWebhookTypes:
    """Tests for webhook types."""

    def test_webhook_event_to_dict(self, sample_webhook_event):
        """Test converting webhook event to dict."""
        result = sample_webhook_event.to_dict()
        
        assert result["event_type"] == "agent.created"
        assert result["source"] == "agent"
        assert result["source_id"] == "123"
        assert "timestamp" in result
        assert result["data"] == {"agent_id": "123", "name": "Test Agent"}
        assert result["metadata"] == {"version": "1.0"}

    def test_webhook_event_from_dict(self, sample_webhook_event):
        """Test creating webhook event from dict."""
        event_dict = sample_webhook_event.to_dict()
        
        event = WebhookEvent.from_dict(event_dict)
        
        assert event.event_type == sample_webhook_event.event_type
        assert event.source == sample_webhook_event.source
        assert event.source_id == sample_webhook_event.source_id

    def test_webhook_payload_to_dict(self, sample_webhook_payload):
        """Test converting webhook payload to dict."""
        result = sample_webhook_payload.to_dict()
        
        assert "headers" in result
        assert "body" in result
        assert "query_params" in result
        assert "webhook_id" in result
        assert "timestamp" in result

    def test_webhook_response_to_dict(self):
        """Test converting webhook response to dict."""
        response = WebhookResponse(
            status_code=200,
            success=True,
            message="OK",
            data={"test": "value"},
        )
        
        result = response.to_dict()
        
        assert result["success"] is True
        assert result["message"] == "OK"
        assert result["data"] == {"test": "value"}
        assert "error" not in result

    def test_webhook_response_with_error(self):
        """Test webhook response with error."""
        response = WebhookResponse(
            status_code=400,
            success=False,
            message="Error",
            error="Something went wrong",
        )
        
        result = response.to_dict()
        
        assert result["success"] is False
        assert result["error"] == "Something went wrong"

    def test_webhook_subscription_to_dict(self):
        """Test converting webhook subscription to dict."""
        subscription = WebhookSubscription(
            id=1,
            name="Test Webhook",
            url="https://example.com/webhook",
            events=["agent.created"],
            secret="test-secret",
            active=True,
        )
        
        result = subscription.to_dict()
        
        assert result["id"] == 1
        assert result["name"] == "Test Webhook"
        assert result["url"] == "https://example.com/webhook"
        assert result["events"] == ["agent.created"]
        assert result["active"] is True

    def test_webhook_subscription_to_dict_with_secret(self):
        """Test converting webhook subscription to dict with secret."""
        subscription = WebhookSubscription(
            id=1,
            name="Test Webhook",
            url="https://example.com/webhook",
            secret="test-secret",
        )
        
        result = subscription.to_dict(include_secret=True)
        
        assert result["secret"] == "test-secret"

    def test_webhook_subscription_to_dict_without_secret(self):
        """Test converting webhook subscription to dict without secret."""
        subscription = WebhookSubscription(
            id=1,
            name="Test Webhook",
            url="https://example.com/webhook",
            secret="test-secret",
        )
        
        result = subscription.to_dict(include_secret=False)
        
        assert "secret" not in result
