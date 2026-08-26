# Agent World - Notifications Routes
# Version: 0.3.1 (EPIC 4 - US-031)
# Description: Endpoints REST pour la gestion des notifications historiques

"""
Notifications Routes for Agent World API.

Ce module contient tous les endpoints REST pour la gestion des notifications.
"""

from flask import request
from flask_restful import Resource, reqparse

from ..models.base import db
from ..models.history_notification import (
    HistoryNotification,
    NotificationChannel,
    NotificationType,
)
from ..services.notification_service import (
    UserNotificationPreferences,
    notification_service,
)

# Initialize parser for request parsing
parser = reqparse.RequestParser()
parser.add_argument("user_id", type=int, required=True, help="User ID is required")
parser.add_argument(
    "notification_type", type=str, required=True, help="Notification type is required"
)
parser.add_argument(
    "channel",
    type=str,
    default="email",
    help="Notification channel (email, slack, discord)",
)
parser.add_argument(
    "title", type=str, required=True, help="Notification title is required"
)
parser.add_argument(
    "message", type=str, required=True, help="Notification message is required"
)
parser.add_argument(
    "send_immediately", type=bool, default=True, help="Send notification immediately"
)

# Parser for preferences
preferences_parser = reqparse.RequestParser()
preferences_parser.add_argument("email_notifications", type=bool, default=True)
preferences_parser.add_argument("slack_notifications", type=bool, default=False)
preferences_parser.add_argument("discord_notifications", type=bool, default=False)
preferences_parser.add_argument("important_events_only", type=bool, default=False)


class NotificationListResource(Resource):
    """Resource for listing notifications."""

    def get(self):
        """
        List all notifications for the current user.

        ---
        parameters:
          - in: query
            name: unread
            schema:
              type: boolean
            description: Filter by unread notifications only
          - in: query
            name: limit
            schema:
              type: integer
              default: 10
            description: Maximum number of results
        responses:
          200:
            description: A list of notifications
            content:
              application/json:
                schema:
                  type: array
                  items:
                    type: object
                    properties:
                      id:
                        type: integer
                      notification_type:
                        type: string
                      channel:
                        type: string
                      title:
                        type: string
                      is_read:
                        type: boolean
                      created_at:
                        type: string
        """
        # Parse query parameters
        args = request.args
        unread_only = args.get("unread", "false").lower() == "true"
        limit = int(args.get("limit", 10))

        # For now, we'll use user_id from header or default to 1
        # In production, this would come from authentication
        user_id = 1  # Default user for demo purposes

        if unread_only:
            notifications = HistoryNotification.get_unread_by_user(user_id)
        else:
            notifications = HistoryNotification.get_by_user(user_id)

        return [n.to_dict_minimal() for n in notifications[:limit]], 200


class NotificationResource(Resource):
    """Resource for individual notification operations."""

    def get(self, notification_id: int):
        """
        Get a specific notification by ID.

        ---
        parameters:
          - in: path
            name: notification_id
            schema:
              type: integer
            required: true
        responses:
          200:
            description: The requested notification
            content:
              application/json:
                schema:
                  type: object
          404:
            description: Notification not found
        """
        notification = HistoryNotification.get_by_id(notification_id)
        if not notification:
            return {"error": f"Notification with ID {notification_id} not found"}, 404

        return notification.to_dict(), 200

    def delete(self, notification_id: int):
        """
        Delete a notification.

        ---
        parameters:
          - in: path
            name: notification_id
            schema:
              type: integer
            required: true
        responses:
          204:
            description: Notification deleted successfully
          404:
            description: Notification not found
        """
        notification = HistoryNotification.get_by_id(notification_id)
        if not notification:
            return {"error": f"Notification with ID {notification_id} not found"}, 404

        notification.delete()
        return "", 204


class NotificationMarkReadResource(Resource):
    """Resource for marking notifications as read."""

    def post(self, notification_id: int):
        """
        Mark a notification as read.

        ---
        parameters:
          - in: path
            name: notification_id
            schema:
              type: integer
            required: true
        responses:
          200:
            description: Notification marked as read
          404:
            description: Notification not found
        """
        notification = HistoryNotification.get_by_id(notification_id)
        if not notification:
            return {"error": f"Notification with ID {notification_id} not found"}, 404

        notification.mark_as_read()
        return {"message": "Notification marked as read", "id": notification_id}, 200


class NotificationCreateResource(Resource):
    """Resource for creating notifications."""

    def post(self):
        """
        Create a new notification.

        ---
        requestBody:
          required: true
          content:
            application/json:
              schema:
                type: object
                required:
                  - user_id
                  - notification_type
                  - title
                  - message
                properties:
                  user_id:
                    type: integer
                  notification_type:
                    type: string
                    enum: [execution_failure, execution_success, agent_created,
                      agent_updated, agent_deleted, version_restored, template_created]
                  channel:
                    type: string
                    enum: [email, slack, discord]
                  title:
                    type: string
                  message:
                    type: string
                  extra_data:
                    type: object
                  send_immediately:
                    type: boolean
                    default: true
        responses:
          201:
            description: The created notification
            content:
              application/json:
                schema:
                  type: object
          400:
            description: Invalid input data
        """
        data = request.get_json(silent=True) or {}

        # Validate required fields
        required_fields = ["user_id", "notification_type", "title", "message"]
        for field in required_fields:
            if field not in data:
                return {"error": f"{field} is required"}, 400

        try:
            user_id = data["user_id"]
            notification_type = NotificationType(data["notification_type"])
            channel = NotificationChannel(data.get("channel", "email"))
            title = data["title"]
            message = data["message"]
            extra_data = data.get("extra_data", {})
            send_immediately = data.get("send_immediately", True)

            notification = notification_service.create_notification(
                user_id=user_id,
                notification_type=notification_type,
                channel=channel,
                title=title,
                message=message,
                extra_data=extra_data,
                send_immediately=send_immediately,
            )

            return notification.to_dict(), 201
        except ValueError as e:
            return {"error": f"Invalid value: {str(e)}"}, 400
        except Exception as e:
            db.session.rollback()
            return {"error": str(e)}, 500


class NotificationPreferencesResource(Resource):
    """Resource for managing user notification preferences."""

    def get(self, user_id: int):
        """
        Get notification preferences for a user.

        ---
        parameters:
          - in: path
            name: user_id
            schema:
              type: integer
            required: true
        responses:
          200:
            description: User notification preferences
            content:
              application/json:
                schema:
                  type: object
                  properties:
                    user_id:
                      type: integer
                    email_notifications:
                      type: boolean
                    slack_notifications:
                      type: boolean
                    discord_notifications:
                      type: boolean
          404:
            description: Preferences not found
        """
        preferences = notification_service.get_user_preferences(user_id)
        if not preferences:
            # Return default preferences
            return {
                "user_id": user_id,
                "email_notifications": True,
                "slack_notifications": False,
                "discord_notifications": False,
                "important_events_only": False,
            }, 200

        return {
            "user_id": preferences.user_id,
            "email_notifications": preferences.email_notifications,
            "slack_notifications": preferences.slack_notifications,
            "discord_notifications": preferences.discord_notifications,
            "important_events_only": preferences.important_events_only,
        }, 200

    def post(self, user_id: int):
        """
        Set notification preferences for a user.

        ---
        parameters:
          - in: path
            name: user_id
            schema:
              type: integer
            required: true
        requestBody:
          required: true
          content:
            application/json:
              schema:
                type: object
                properties:
                  email_notifications:
                    type: boolean
                  slack_notifications:
                    type: boolean
                  discord_notifications:
                    type: boolean
                  important_events_only:
                    type: boolean
        responses:
          200:
            description: Preferences updated successfully
        """
        data = request.get_json(silent=True) or {}

        preferences = UserNotificationPreferences(
            user_id=user_id,
            email_notifications=data.get("email_notifications", True),
            slack_notifications=data.get("slack_notifications", False),
            discord_notifications=data.get("discord_notifications", False),
            important_events_only=data.get("important_events_only", False),
        )

        notification_service.set_user_preferences(preferences)

        return {
            "message": "Preferences updated",
            "user_id": user_id,
        }, 200


class NotificationRetryResource(Resource):
    """Resource for retrying pending notifications."""

    def post(self):
        """
        Retry sending all pending notifications.

        ---
        responses:
          200:
            description: Retry result
            content:
              application/json:
                schema:
                  type: object
                  properties:
                    message:
                      type: string
                    retried:
                      type: integer
                    sent:
                      type: integer
        """
        try:
            pending_count = len(HistoryNotification.get_pending())
            sent_count = notification_service.retry_pending_notifications()

            return {
                "message": "Retry completed",
                "retried": pending_count,
                "sent": sent_count,
            }, 200
        except Exception as e:
            return {"error": str(e)}, 500


class NotificationTypesResource(Resource):
    """Resource for getting available notification types."""

    def get(self):
        """
        Get all available notification types.

        ---
        responses:
          200:
            description: List of notification types
            content:
              application/json:
                schema:
                  type: array
                  items:
                    type: string
        """
        return [t.value for t in NotificationType], 200


class NotificationChannelsResource(Resource):
    """Resource for getting available notification channels."""

    def get(self):
        """
        Get all available notification channels.

        ---
        responses:
          200:
            description: List of notification channels
            content:
              application/json:
                schema:
                  type: array
                  items:
                    type: string
        """
        return [c.value for c in NotificationChannel], 200


def register_resources(api):
    """Register notification resources with the Flask-RESTful API."""
    api.add_resource(NotificationListResource, "/notifications")
    api.add_resource(NotificationResource, "/notifications/<int:notification_id>")
    api.add_resource(
        NotificationMarkReadResource, "/notifications/<int:notification_id>/read"
    )
    api.add_resource(NotificationCreateResource, "/notifications/create")
    api.add_resource(
        NotificationPreferencesResource, "/notifications/preferences/<int:user_id>"
    )
    api.add_resource(NotificationRetryResource, "/notifications/retry")
    api.add_resource(NotificationTypesResource, "/notifications/types")
    api.add_resource(NotificationChannelsResource, "/notifications/channels")
