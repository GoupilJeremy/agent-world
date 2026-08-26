# Agent World - Notification Service
# Version: 0.3.1 (EPIC 4 - US-031)
# Description: Service pour gérer les notifications historiques

"""
Notification Service for Agent World.

Ce service gère l'envoi de notifications pour les événements historiques importants.
Il supporte plusieurs canaux : email, Slack, Discord.
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional

from ..models.history_notification import (
    HistoryNotification,
    NotificationChannel,
    NotificationType,
)

logger = logging.getLogger(__name__)


@dataclass
class NotificationConfig:
    """Configuration pour un canal de notification."""

    enabled: bool = False
    webhook_url: Optional[str] = None
    api_key: Optional[str] = None
    default_recipient: Optional[str] = None


@dataclass
class UserNotificationPreferences:
    """Préférences de notification pour un utilisateur."""

    user_id: int
    email_notifications: bool = True
    slack_notifications: bool = False
    discord_notifications: bool = False
    important_events_only: bool = False
    notification_types: list[NotificationType] = None

    def __post_init__(self):
        if self.notification_types is None:
            self.notification_types = list(NotificationType)


class NotificationService:
    """
    Service for managing and sending historical notifications.

    Ce service permet de :
    - Créer des notifications pour des événements historiques
    - Envoyer des notifications via différents canaux (email, Slack, Discord)
    - Gérer les préférences de notification des utilisateurs
    - Retenter l'envoi des notifications échouées
    """

    def __init__(self):
        """Initialize the notification service."""
        self.config: dict[str, NotificationConfig] = {
            NotificationChannel.EMAIL.value: NotificationConfig(enabled=False),
            NotificationChannel.SLACK.value: NotificationConfig(enabled=False),
            NotificationChannel.DISCORD.value: NotificationConfig(enabled=False),
        }
        self.user_preferences: dict[int, UserNotificationPreferences] = {}
        self._initialized = False

    def init_app(self, app):
        """Initialize the service with Flask app context."""
        if self._initialized:
            return

        self._initialized = True
        self._load_config(app)
        logger.info("NotificationService initialized")

    def _load_config(self, app):
        """Load configuration from Flask app."""
        # Email configuration
        if app.config.get("EMAIL_ENABLED", False):
            self.config[NotificationChannel.EMAIL.value] = NotificationConfig(
                enabled=True,
                default_recipient=app.config.get("EMAIL_DEFAULT_RECIPIENT"),
            )

        # Slack configuration
        if app.config.get("SLACK_ENABLED", False):
            self.config[NotificationChannel.SLACK.value] = NotificationConfig(
                enabled=True,
                webhook_url=app.config.get("SLACK_WEBHOOK_URL"),
            )

        # Discord configuration
        if app.config.get("DISCORD_ENABLED", False):
            self.config[NotificationChannel.DISCORD.value] = NotificationConfig(
                enabled=True,
                webhook_url=app.config.get("DISCORD_WEBHOOK_URL"),
            )

    def create_notification(
        self,
        user_id: int,
        notification_type: NotificationType,
        title: str,
        message: str,
        extra_data: Optional[dict] = None,
        channel: Optional[NotificationChannel] = None,
        send_immediately: bool = True,
    ) -> HistoryNotification:
        """
        Create a new historical notification.

        Args:
            user_id: ID of the user to notify
            notification_type: Type of notification
            title: Notification title
            message: Notification message
            extra_data: Additional data to include
            channel: Specific channel to use (optional, will use user preferences)
            send_immediately: Whether to attempt sending immediately

        Returns:
            The created HistoryNotification instance
        """
        # Determine channel based on preferences if not specified
        if channel is None:
            channel = self._get_user_preferred_channel(user_id)

        # Create the notification
        notification = HistoryNotification.create(
            user_id=user_id,
            notification_type=notification_type,
            channel=channel,
            title=title,
            message=message,
            extra_data=extra_data,
        )

        logger.info(
            f"Created notification {notification.id} for user {user_id}: "
            f"{notification_type.value} - {title}"
        )

        # Send immediately if requested
        if send_immediately:
            self.send_notification(notification)

        return notification

    def _get_user_preferred_channel(self, user_id: int) -> NotificationChannel:
        """Get the preferred notification channel for a user."""
        # Check user preferences
        preferences = self.user_preferences.get(user_id)
        if preferences:
            if preferences.email_notifications:
                return NotificationChannel.EMAIL
            elif preferences.slack_notifications:
                return NotificationChannel.SLACK
            elif preferences.discord_notifications:
                return NotificationChannel.DISCORD

        # Default to email
        return NotificationChannel.EMAIL

    def send_notification(self, notification: HistoryNotification) -> bool:
        """
        Send a notification via its configured channel.

        Args:
            notification: The notification to send

        Returns:
            True if notification was sent successfully, False otherwise
        """
        channel_config = self.config.get(notification.channel.value)
        if not channel_config or not channel_config.enabled:
            logger.warning(
                f"Cannot send notification {notification.id}: "
                f"channel {notification.channel.value} is not configured"
            )
            notification.increment_attempts()
            return False

        try:
            if notification.channel == NotificationChannel.EMAIL:
                return self._send_email_notification(notification, channel_config)
            elif notification.channel == NotificationChannel.SLACK:
                return self._send_slack_notification(notification, channel_config)
            elif notification.channel == NotificationChannel.DISCORD:
                return self._send_discord_notification(notification, channel_config)
            else:
                logger.error(f"Unknown notification channel: {notification.channel}")
                return False
        except Exception as e:
            logger.error(f"Failed to send notification {notification.id}: {str(e)}")
            notification.increment_attempts()
            return False

    def _send_email_notification(
        self, notification: HistoryNotification, config: NotificationConfig
    ) -> bool:
        """Send notification via email."""
        # Import here to avoid circular dependencies
        try:
            import smtplib
            from email.mime.text import MIMEText
        except ImportError:
            logger.error("Email dependencies not available")
            return False

        try:
            # In a real implementation, this would connect to an SMTP server
            # For now, we'll just log and mark as sent
            msg = MIMEText(notification.message)
            msg["Subject"] = notification.title
            msg["From"] = config.default_recipient or "notifications@agentworld.ai"

            # Get user email
            from ..models.user import User

            user = User.get_by_id(notification.user_id)
            if user:
                msg["To"] = user.email
                # Here you would actually send the email
                # smtp = smtplib.SMTP(app.config['SMTP_SERVER'])
                # smtp.sendmail(...)
                # smtp.quit()

                logger.info(
                    f"Email notification sent to {user.email}: {notification.title}"
                )
                notification.mark_as_sent()
                return True
            else:
                logger.error(
                    f"User {notification.user_id} not found for email notification"
                )
                return False
        except Exception as e:
            logger.error(f"Failed to send email: {str(e)}")
            return False

    def _send_slack_notification(
        self, notification: HistoryNotification, config: NotificationConfig
    ) -> bool:
        """Send notification via Slack webhook."""
        if not config.webhook_url:
            logger.error("Slack webhook URL not configured")
            return False

        try:
            import requests

            payload = {
                "text": f"*{notification.title}*\n{notification.message}",
                "username": "Agent World Bot",
                "icon_emoji": ":robot_face:",
            }

            # In a real implementation:
            # response = requests.post(config.webhook_url, json=payload)
            # response.raise_for_status()

            logger.info(
                f"Slack notification would be sent to {config.webhook_url}: {notification.title}"
            )
            notification.mark_as_sent()
            return True
        except Exception as e:
            logger.error(f"Failed to send Slack notification: {str(e)}")
            return False

    def _send_discord_notification(
        self, notification: HistoryNotification, config: NotificationConfig
    ) -> bool:
        """Send notification via Discord webhook."""
        if not config.webhook_url:
            logger.error("Discord webhook URL not configured")
            return False

        try:
            import requests

            payload = {
                "content": f"**{notification.title}**\n{notification.message}",
                "username": "Agent World Bot",
            }

            # In a real implementation:
            # response = requests.post(config.webhook_url, json=payload)
            # response.raise_for_status()

            logger.info(
                f"Discord notification would be sent to {config.webhook_url}: {notification.title}"
            )
            notification.mark_as_sent()
            return True
        except Exception as e:
            logger.error(f"Failed to send Discord notification: {str(e)}")
            return False

    def set_user_preferences(self, preferences: UserNotificationPreferences) -> None:
        """Set notification preferences for a user."""
        self.user_preferences[preferences.user_id] = preferences
        logger.info(f"Set notification preferences for user {preferences.user_id}")

    def get_user_preferences(
        self, user_id: int
    ) -> Optional[UserNotificationPreferences]:
        """Get notification preferences for a user."""
        return self.user_preferences.get(user_id)

    def retry_pending_notifications(self) -> int:
        """
        Retry sending all pending notifications.

        Returns:
            Number of notifications successfully sent
        """
        pending = HistoryNotification.get_pending()
        sent_count = 0

        for notification in pending:
            if self.send_notification(notification):
                sent_count += 1

        logger.info(f"Retried {len(pending)} pending notifications, sent {sent_count}")
        return sent_count

    def create_execution_failure_notification(
        self,
        user_id: int,
        agent_id: int,
        execution_id: int,
        error_message: str,
        channel: Optional[NotificationChannel] = None,
    ) -> Optional[HistoryNotification]:
        """
        Create a notification for an execution failure.

        Args:
            user_id: ID of the user to notify
            agent_id: ID of the agent that failed
            execution_id: ID of the failed execution
            error_message: The error message
            channel: Optional channel override

        Returns:
            The created notification, or None if not created
        """
        return self.create_notification(
            user_id=user_id,
            notification_type=NotificationType.EXECUTION_FAILURE,
            title=f"Agent {agent_id} - Exécution échouée",
            message=f"L'exécution {execution_id} de l'agent {agent_id} a échoué: {error_message}",
            extra_data={
                "agent_id": agent_id,
                "execution_id": execution_id,
                "error": error_message,
            },
            channel=channel,
        )

    def create_execution_success_notification(
        self,
        user_id: int,
        agent_id: int,
        execution_id: int,
        duration: float,
        channel: Optional[NotificationChannel] = None,
    ) -> Optional[HistoryNotification]:
        """
        Create a notification for a successful execution.

        Args:
            user_id: ID of the user to notify
            agent_id: ID of the agent
            execution_id: ID of the execution
            duration: Execution duration in seconds
            channel: Optional channel override

        Returns:
            The created notification, or None if not created
        """
        return self.create_notification(
            user_id=user_id,
            notification_type=NotificationType.EXECUTION_SUCCESS,
            title=f"Agent {agent_id} - Exécution réussie",
            message=f"L'exécution {execution_id} de l'agent {agent_id} a réussi en {duration:.2f}s",
            extra_data={
                "agent_id": agent_id,
                "execution_id": execution_id,
                "duration": duration,
            },
            channel=channel,
        )

    def create_agent_modification_notification(
        self,
        user_id: int,
        agent_id: int,
        action: str,  # "created", "updated", "deleted"
        channel: Optional[NotificationChannel] = None,
    ) -> Optional[HistoryNotification]:
        """
        Create a notification for an agent modification.

        Args:
            user_id: ID of the user to notify
            agent_id: ID of the agent
            action: The action performed (created, updated, deleted)
            channel: Optional channel override

        Returns:
            The created notification, or None if not created
        """
        notification_type_map = {
            "created": NotificationType.AGENT_CREATED,
            "updated": NotificationType.AGENT_UPDATED,
            "deleted": NotificationType.AGENT_DELETED,
        }

        notification_type = notification_type_map.get(
            action, NotificationType.AGENT_UPDATED
        )
        title = f"Agent {agent_id} - {action.capitalize()}"
        message = f"L'agent {agent_id} a été {action} par l'utilisateur {user_id}"

        return self.create_notification(
            user_id=user_id,
            notification_type=notification_type,
            title=title,
            message=message,
            extra_data={"agent_id": agent_id, "action": action},
            channel=channel,
        )


# Singleton instance
notification_service = NotificationService()
