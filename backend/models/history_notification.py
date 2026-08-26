# Agent World - History Notification Model
# Version: 0.3.1 (EPIC 4 - US-031)
# Description: Modèle pour les notifications historiques

"""
History Notification Model for Agent World.

Ce modèle gère les notifications envoyées pour les événements historiques importants.
"""

from datetime import datetime
from enum import Enum
from typing import Optional

from .base import BaseModel, db


class NotificationType(str, Enum):
    """Types de notifications historiques."""

    EXECUTION_FAILURE = "execution_failure"
    EXECUTION_SUCCESS = "execution_success"
    AGENT_CREATED = "agent_created"
    AGENT_UPDATED = "agent_updated"
    AGENT_DELETED = "agent_deleted"
    VERSION_RESTORED = "version_restored"
    TEMPLATE_CREATED = "template_created"


class NotificationChannel(str, Enum):
    """Canaux de notification."""

    EMAIL = "email"
    SLACK = "slack"
    DISCORD = "discord"


class HistoryNotification(BaseModel):
    """
    HistoryNotification model for tracking sent notifications.

    Attributes:
        id: Unique identifier
        user_id: ID of the user who should receive the notification
        notification_type: Type of the notification (from NotificationType enum)
        channel: Channel used for notification (from NotificationChannel enum)
        title: Notification title
        message: Notification message content
        metadata: Additional data in JSON format
        is_sent: Whether the notification was successfully sent
        send_attempts: Number of send attempts
        sent_at: Timestamp when notification was sent
        created_at: Timestamp when notification was created
        read_at: Timestamp when notification was read by user
        is_active: Whether the notification is still active
    """

    __tablename__ = "history_notifications"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    notification_type = db.Column(
        db.Enum(NotificationType),
        nullable=False,
        default=NotificationType.EXECUTION_FAILURE,
    )
    channel = db.Column(
        db.Enum(NotificationChannel), nullable=False, default=NotificationChannel.EMAIL
    )
    title = db.Column(db.String(255), nullable=False)
    message = db.Column(db.Text, nullable=False)
    extra_data = db.Column(db.JSON, nullable=True)
    is_sent = db.Column(db.Boolean, nullable=False, default=False)
    send_attempts = db.Column(db.Integer, nullable=False, default=0)
    sent_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    read_at = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True)

    # Relationships
    user = db.relationship("User", backref="history_notifications")

    def __init__(
        self,
        user_id: int,
        notification_type: NotificationType,
        channel: NotificationChannel,
        title: str,
        message: str,
        extra_data: Optional[dict] = None,
        is_sent: bool = False,
        send_attempts: int = 0,
        sent_at: Optional[datetime] = None,
        read_at: Optional[datetime] = None,
        is_active: bool = True,
    ):
        """
        Initialize a new HistoryNotification instance.

        Args:
            user_id: ID of the user to notify
            notification_type: Type of notification
            channel: Notification channel
            title: Notification title
            message: Notification message
            extra_data: Additional data
            is_sent: Whether notification was sent
            send_attempts: Number of send attempts
            sent_at: When notification was sent
            read_at: When notification was read
            is_active: Whether notification is active
        """
        self.user_id = user_id
        self.notification_type = notification_type
        self.channel = channel
        self.title = title
        self.message = message
        self.extra_data = extra_data or {}
        self.is_sent = is_sent
        self.send_attempts = send_attempts
        self.sent_at = sent_at
        self.read_at = read_at
        self.is_active = is_active

    def __repr__(self) -> str:
        return (
            f"<HistoryNotification(id={self.id}, user_id={self.user_id}, "
            f"type={self.notification_type}, channel={self.channel})>"
        )

    def to_dict(self) -> dict:
        """Convert notification to dictionary."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "notification_type": self.notification_type.value,
            "channel": self.channel.value,
            "title": self.title,
            "message": self.message,
            "extra_data": self.extra_data,
            "is_sent": self.is_sent,
            "send_attempts": self.send_attempts,
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
            "created_at": self.created_at.isoformat(),
            "read_at": self.read_at.isoformat() if self.read_at else None,
            "is_active": self.is_active,
        }

    def to_dict_minimal(self) -> dict:
        """Convert notification to minimal dictionary."""
        return {
            "id": self.id,
            "notification_type": self.notification_type.value,
            "channel": self.channel.value,
            "title": self.title,
            "is_read": self.read_at is not None,
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def create(cls, **kwargs) -> "HistoryNotification":
        """Create a new notification and save to database."""
        notification = cls(**kwargs)
        db.session.add(notification)
        db.session.commit()
        return notification

    @classmethod
    def get_by_id(cls, notification_id: int) -> Optional["HistoryNotification"]:
        """Get notification by ID."""
        return cls.query.get(notification_id)

    @classmethod
    def get_by_user(cls, user_id: int) -> list:
        """Get all notifications for a user."""
        return (
            cls.query.filter_by(user_id=user_id).order_by(cls.created_at.desc()).all()
        )

    @classmethod
    def get_unread_by_user(cls, user_id: int) -> list:
        """Get all unread notifications for a user."""
        return (
            cls.query.filter_by(user_id=user_id, read_at=None, is_active=True)
            .order_by(cls.created_at.desc())
            .all()
        )

    @classmethod
    def get_by_type(cls, notification_type: NotificationType) -> list:
        """Get all notifications of a specific type."""
        return cls.query.filter_by(notification_type=notification_type).all()

    @classmethod
    def get_pending(cls) -> list:
        """Get all pending notifications (not sent yet)."""
        return cls.query.filter_by(is_sent=False, is_active=True).all()

    def mark_as_sent(self) -> None:
        """Mark notification as sent."""
        self.is_sent = True
        self.sent_at = datetime.utcnow()
        db.session.commit()

    def mark_as_read(self) -> None:
        """Mark notification as read."""
        self.read_at = datetime.utcnow()
        db.session.commit()

    def increment_attempts(self) -> None:
        """Increment send attempts counter."""
        self.send_attempts += 1
        db.session.commit()

    def deactivate(self) -> None:
        """Deactivate this notification."""
        self.is_active = False
        db.session.commit()

    def delete(self) -> None:
        """Delete this notification."""
        db.session.delete(self)
        db.session.commit()
