# Agent World - Notification Tests
# Version: 0.3.1 (EPIC 4 - US-031)
# Description: Tests pour les notifications historiques

"""
Tests for historical notifications functionality.
"""

import unittest
from datetime import datetime

from backend.app import create_app
from backend.models.base import db
from backend.models.history_notification import (
    HistoryNotification,
    NotificationChannel,
    NotificationType,
)
from backend.models.user import User
from backend.services.notification_service import (
    NotificationConfig,
    NotificationService,
    UserNotificationPreferences,
    notification_service,
)


class TestNotificationModel(unittest.TestCase):
    """Test cases for HistoryNotification model."""

    def setUp(self):
        """Set up test fixtures."""
        self.app = create_app(
            {"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:"}
        )
        self.app_context = self.app.app_context()
        self.app_context.push()

        db.create_all()

        # Create test user
        self.user = User.create(
            username="testuser",
            email="test@agentworld.ai",
            password_hash="hashed_password",
        )

    def tearDown(self):
        """Tear down test fixtures."""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_create_notification(self):
        """Test creating a notification."""
        notification = HistoryNotification.create(
            user_id=self.user.id,
            notification_type=NotificationType.EXECUTION_FAILURE,
            channel=NotificationChannel.EMAIL,
            title="Test Execution Failure",
            message="Test execution failed",
            extra_data={"agent_id": 1, "execution_id": 100},
        )

        self.assertIsNotNone(notification.id)
        self.assertEqual(notification.user_id, self.user.id)
        self.assertEqual(
            notification.notification_type, NotificationType.EXECUTION_FAILURE
        )
        self.assertEqual(notification.channel, NotificationChannel.EMAIL)
        self.assertEqual(notification.title, "Test Execution Failure")
        self.assertEqual(notification.message, "Test execution failed")
        self.assertEqual(notification.extra_data, {"agent_id": 1, "execution_id": 100})
        self.assertFalse(notification.is_sent)
        self.assertEqual(notification.send_attempts, 0)
        self.assertIsNotNone(notification.created_at)
        self.assertIsNone(notification.sent_at)
        self.assertIsNone(notification.read_at)
        self.assertTrue(notification.is_active)

    def test_get_by_id(self):
        """Test getting notification by ID."""
        notification = HistoryNotification.create(
            user_id=self.user.id,
            notification_type=NotificationType.EXECUTION_SUCCESS,
            channel=NotificationChannel.SLACK,
            title="Test Success",
            message="Test execution succeeded",
        )

        retrieved = HistoryNotification.get_by_id(notification.id)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.id, notification.id)

    def test_get_by_user(self):
        """Test getting notifications by user."""
        # Create multiple notifications for different users
        notification1 = HistoryNotification.create(
            user_id=self.user.id,
            notification_type=NotificationType.AGENT_CREATED,
            channel=NotificationChannel.EMAIL,
            title="Test 1",
            message="Message 1",
        )

        user2 = User.create(
            username="testuser2",
            email="test2@agentworld.ai",
            password_hash="hashed_password",
        )
        notification2 = HistoryNotification.create(
            user_id=user2.id,
            notification_type=NotificationType.AGENT_UPDATED,
            channel=NotificationChannel.SLACK,
            title="Test 2",
            message="Message 2",
        )

        user_notifications = HistoryNotification.get_by_user(self.user.id)
        self.assertEqual(len(user_notifications), 1)
        self.assertEqual(user_notifications[0].id, notification1.id)

    def test_get_unread_by_user(self):
        """Test getting unread notifications by user."""
        # Create read and unread notifications
        notification1 = HistoryNotification.create(
            user_id=self.user.id,
            notification_type=NotificationType.AGENT_DELETED,
            channel=NotificationChannel.DISCORD,
            title="Unread",
            message="Unread message",
        )

        notification2 = HistoryNotification.create(
            user_id=self.user.id,
            notification_type=NotificationType.AGENT_CREATED,
            channel=NotificationChannel.EMAIL,
            title="Read",
            message="Read message",
        )
        notification2.mark_as_read()

        unread = HistoryNotification.get_unread_by_user(self.user.id)
        self.assertEqual(len(unread), 1)
        self.assertEqual(unread[0].id, notification1.id)

    def test_get_pending(self):
        """Test getting pending notifications."""
        notification1 = HistoryNotification.create(
            user_id=self.user.id,
            notification_type=NotificationType.EXECUTION_FAILURE,
            channel=NotificationChannel.EMAIL,
            title="Pending",
            message="Pending message",
        )

        notification2 = HistoryNotification.create(
            user_id=self.user.id,
            notification_type=NotificationType.EXECUTION_SUCCESS,
            channel=NotificationChannel.SLACK,
            title="Sent",
            message="Sent message",
        )
        notification2.mark_as_sent()

        pending = HistoryNotification.get_pending()
        self.assertEqual(len(pending), 1)
        self.assertEqual(pending[0].id, notification1.id)

    def test_mark_as_sent(self):
        """Test marking notification as sent."""
        notification = HistoryNotification.create(
            user_id=self.user.id,
            notification_type=NotificationType.EXECUTION_FAILURE,
            channel=NotificationChannel.EMAIL,
            title="Test",
            message="Test message",
        )

        self.assertFalse(notification.is_sent)
        self.assertIsNone(notification.sent_at)

        notification.mark_as_sent()

        # Refresh from database
        db.session.refresh(notification)
        self.assertTrue(notification.is_sent)
        self.assertIsNotNone(notification.sent_at)

    def test_mark_as_read(self):
        """Test marking notification as read."""
        notification = HistoryNotification.create(
            user_id=self.user.id,
            notification_type=NotificationType.EXECUTION_FAILURE,
            channel=NotificationChannel.EMAIL,
            title="Test",
            message="Test message",
        )

        self.assertIsNone(notification.read_at)

        notification.mark_as_read()

        # Refresh from database
        db.session.refresh(notification)
        self.assertIsNotNone(notification.read_at)

    def test_increment_attempts(self):
        """Test incrementing send attempts."""
        notification = HistoryNotification.create(
            user_id=self.user.id,
            notification_type=NotificationType.EXECUTION_FAILURE,
            channel=NotificationChannel.EMAIL,
            title="Test",
            message="Test message",
        )

        self.assertEqual(notification.send_attempts, 0)

        notification.increment_attempts()
        notification.increment_attempts()

        # Refresh from database
        db.session.refresh(notification)
        self.assertEqual(notification.send_attempts, 2)

    def test_deactivate(self):
        """Test deactivating notification."""
        notification = HistoryNotification.create(
            user_id=self.user.id,
            notification_type=NotificationType.EXECUTION_FAILURE,
            channel=NotificationChannel.EMAIL,
            title="Test",
            message="Test message",
        )

        self.assertTrue(notification.is_active)

        notification.deactivate()

        # Refresh from database
        db.session.refresh(notification)
        self.assertFalse(notification.is_active)

    def test_to_dict(self):
        """Test converting notification to dictionary."""
        notification = HistoryNotification.create(
            user_id=self.user.id,
            notification_type=NotificationType.EXECUTION_FAILURE,
            channel=NotificationChannel.EMAIL,
            title="Test",
            message="Test message",
            extra_data={"agent_id": 1},
        )

        result = notification.to_dict()

        self.assertIn("id", result)
        self.assertIn("user_id", result)
        self.assertIn("notification_type", result)
        self.assertIn("channel", result)
        self.assertIn("title", result)
        self.assertIn("message", result)
        self.assertIn("extra_data", result)
        self.assertIn("is_sent", result)
        self.assertIn("send_attempts", result)
        self.assertIn("created_at", result)

    def test_to_dict_minimal(self):
        """Test converting notification to minimal dictionary."""
        notification = HistoryNotification.create(
            user_id=self.user.id,
            notification_type=NotificationType.EXECUTION_FAILURE,
            channel=NotificationChannel.EMAIL,
            title="Test",
            message="Test message",
        )

        result = notification.to_dict_minimal()

        self.assertIn("id", result)
        self.assertIn("notification_type", result)
        self.assertIn("channel", result)
        self.assertIn("title", result)
        self.assertIn("is_read", result)
        self.assertIn("created_at", result)


class TestNotificationService(unittest.TestCase):
    """Test cases for NotificationService."""

    def setUp(self):
        """Set up test fixtures."""
        self.app = create_app(
            {"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:"}
        )
        self.app_context = self.app.app_context()
        self.app_context.push()

        db.create_all()

        # Create test user
        self.user = User.create(
            username="testuser",
            email="test@agentworld.ai",
            password_hash="hashed_password",
        )

    def tearDown(self):
        """Tear down test fixtures."""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_create_notification_via_service(self):
        """Test creating notification via service."""
        notification = notification_service.create_notification(
            user_id=self.user.id,
            notification_type=NotificationType.EXECUTION_FAILURE,
            title="Service Test Failure",
            message="Execution failed via service",
            extra_data={"agent_id": 1, "execution_id": 100},
            send_immediately=False,  # Don't actually send
        )

        self.assertIsNotNone(notification.id)
        self.assertEqual(notification.user_id, self.user.id)
        self.assertEqual(
            notification.notification_type, NotificationType.EXECUTION_FAILURE
        )

    def test_create_execution_failure_notification(self):
        """Test creating execution failure notification."""
        notification = notification_service.create_execution_failure_notification(
            user_id=self.user.id,
            agent_id=1,
            execution_id=100,
            error_message="Test error",
        )

        self.assertIsNotNone(notification)
        self.assertEqual(
            notification.notification_type, NotificationType.EXECUTION_FAILURE
        )
        self.assertIn("agent_id", notification.extra_data)
        self.assertIn("execution_id", notification.extra_data)
        self.assertIn("error", notification.extra_data)

    def test_create_execution_success_notification(self):
        """Test creating execution success notification."""
        notification = notification_service.create_execution_success_notification(
            user_id=self.user.id,
            agent_id=1,
            execution_id=100,
            duration=15.5,
        )

        self.assertIsNotNone(notification)
        self.assertEqual(
            notification.notification_type, NotificationType.EXECUTION_SUCCESS
        )
        self.assertIn("agent_id", notification.extra_data)
        self.assertIn("execution_id", notification.extra_data)
        self.assertIn("duration", notification.extra_data)

    def test_create_agent_modification_notification(self):
        """Test creating agent modification notification."""
        for action in ["created", "updated", "deleted"]:
            notification = notification_service.create_agent_modification_notification(
                user_id=self.user.id,
                agent_id=1,
                action=action,
            )

            self.assertIsNotNone(notification)
            if action == "created":
                self.assertEqual(
                    notification.notification_type, NotificationType.AGENT_CREATED
                )
            elif action == "updated":
                self.assertEqual(
                    notification.notification_type, NotificationType.AGENT_UPDATED
                )
            elif action == "deleted":
                self.assertEqual(
                    notification.notification_type, NotificationType.AGENT_DELETED
                )

    def test_set_user_preferences(self):
        """Test setting user preferences."""
        preferences = UserNotificationPreferences(
            user_id=self.user.id,
            email_notifications=True,
            slack_notifications=True,
            discord_notifications=False,
            important_events_only=True,
        )

        notification_service.set_user_preferences(preferences)

        retrieved = notification_service.get_user_preferences(self.user.id)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.user_id, self.user.id)
        self.assertTrue(retrieved.email_notifications)
        self.assertTrue(retrieved.slack_notifications)
        self.assertFalse(retrieved.discord_notifications)
        self.assertTrue(retrieved.important_events_only)

    def test_get_user_preferences_default(self):
        """Test getting default user preferences."""
        preferences = notification_service.get_user_preferences(
            999
        )  # Non-existent user
        self.assertIsNone(preferences)


class TestNotificationTypesAndChannels(unittest.TestCase):
    """Test cases for notification types and channels."""

    def test_notification_types(self):
        """Test notification type enum."""
        types = list(NotificationType)
        self.assertGreater(len(types), 0)
        self.assertIn(NotificationType.EXECUTION_FAILURE, types)
        self.assertIn(NotificationType.EXECUTION_SUCCESS, types)
        self.assertIn(NotificationType.AGENT_CREATED, types)
        self.assertIn(NotificationType.AGENT_UPDATED, types)
        self.assertIn(NotificationType.AGENT_DELETED, types)
        self.assertIn(NotificationType.VERSION_RESTORED, types)
        self.assertIn(NotificationType.TEMPLATE_CREATED, types)

    def test_notification_channels(self):
        """Test notification channel enum."""
        channels = list(NotificationChannel)
        self.assertGreater(len(channels), 0)
        self.assertIn(NotificationChannel.EMAIL, channels)
        self.assertIn(NotificationChannel.SLACK, channels)
        self.assertIn(NotificationChannel.DISCORD, channels)


if __name__ == "__main__":
    unittest.main()
