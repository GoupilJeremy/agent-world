# 🧪 Agent World - Audit Service Tests
# Version: 1.0.0 (EPIC 10 - US-068)
# Description: Tests unitaires pour le service AuditService

"""
Unit tests for AuditService.

Ces tests couvrent:
- Enregistrement des actions utilisateurs
- Consultation des logs d'audit
- Export des logs au format JSON et CSV
- Statistiques d'audit
- Recherche dans les logs
- Nettoyage des anciens logs
"""

import csv
import io
import json
from datetime import datetime, timedelta

import unittest
from unittest.mock import MagicMock, patch

from backend.app import create_app
from backend.models.audit_log import AuditAction, AuditLog, AuditResourceType
from backend.models.base import db
from backend.models.user import User
from backend.services.audit_service import (
    AuditError,
    AuditLogNotFoundError,
    AuditService,
)


class TestAuditService(unittest.TestCase):
    """Test cases for AuditService."""

    def setUp(self):
        """Set up test fixtures."""
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
        self.app.config["AUTO_CREATE_DB"] = True

        self.client = self.app.test_client()

        with self.app.app_context():
            db.create_all()
            self.audit_service = AuditService(retention_days=30)

            # Create a test user
            self.user = User(
                email="test@example.com",
                username="testuser",
                password="testpassword123",
            )
            db.session.add(self.user)
            db.session.commit()

    def tearDown(self):
        """Clean up test fixtures."""
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    # ==================== Test Log Action ====================

    def test_log_action_basic(self):
        """Test basic action logging."""
        with self.app.app_context():
            log = self.audit_service.log_action(
                action=AuditAction.AGENT_CREATED,
                user_id=self.user.id,
                resource_type=AuditResourceType.AGENT,
                resource_id=1,
                resource_name="Test Agent",
                status="success",
            )

            self.assertIsNotNone(log)
            self.assertEqual(log.action, "agent_created")
            self.assertEqual(log.user_id, self.user.id)
            self.assertEqual(log.resource_type, "agent")
            self.assertEqual(log.resource_id, 1)
            self.assertEqual(log.resource_name, "Test Agent")
            self.assertEqual(log.status, "success")
            self.assertIsNotNone(log.created_at)

    def test_log_action_with_metadata(self):
        """Test action logging with metadata."""
        with self.app.app_context():
            metadata = {"key1": "value1", "key2": 123, "nested": {"a": "b"}}
            log = self.audit_service.log_action(
                action=AuditAction.USER_CREATED,
                user_id=self.user.id,
                metadata=metadata,
            )

            self.assertIsNotNone(log)
            self.assertEqual(log.metadata_dict["key1"], "value1")
            self.assertEqual(log.metadata_dict["key2"], 123)
            self.assertEqual(log.metadata_dict["nested"]["a"], "b")

    def test_log_action_with_string_action(self):
        """Test action logging with string action instead of enum."""
        with self.app.app_context():
            log = self.audit_service.log_action(
                action="custom_action",
                user_id=self.user.id,
            )

            self.assertIsNotNone(log)
            self.assertEqual(log.action, "custom_action")

    def test_log_action_with_error(self):
        """Test action logging with error status."""
        with self.app.app_context():
            log = self.audit_service.log_action(
                action=AuditAction.LOGIN_FAILED,
                user_id=self.user.id,
                status="failure",
                error_message="Invalid password",
            )

            self.assertIsNotNone(log)
            self.assertEqual(log.status, "failure")
            self.assertEqual(log.error_message, "Invalid password")

    def test_log_action_with_request_info(self):
        """Test action logging with IP and user agent."""
        with self.app.app_context():
            log = self.audit_service.log_action(
                action=AuditAction.LOGIN,
                user_id=self.user.id,
                ip_address="192.168.1.1",
                user_agent="Mozilla/5.0",
            )

            self.assertIsNotNone(log)
            self.assertEqual(log.ip_address, "192.168.1.1")
            self.assertEqual(log.user_agent, "Mozilla/5.0")

    def test_log_action_no_commit(self):
        """Test action logging without commit."""
        with self.app.app_context():
            log = self.audit_service.log_action(
                action=AuditAction.AGENT_CREATED,
                user_id=self.user.id,
                commit=False,
            )

            self.assertIsNotNone(log)
            # Rollback to clean up
            db.session.rollback()

    # ==================== Test Get Log ====================

    def test_get_log_success(self):
        """Test getting a specific log by ID."""
        with self.app.app_context():
            # Create a log
            log = self.audit_service.log_action(
                action=AuditAction.AGENT_CREATED,
                user_id=self.user.id,
            )
            log_id = log.id

            # Get the log
            fetched_log = self.audit_service.get_log(log_id)

            self.assertEqual(fetched_log.id, log_id)
            self.assertEqual(fetched_log.action, "agent_created")

    def test_get_log_not_found(self):
        """Test getting a non-existent log raises error."""
        with self.app.app_context():
            with self.assertRaises(AuditLogNotFoundError):
                self.audit_service.get_log(99999)

    # ==================== Test Get Logs ====================

    def test_get_logs_no_filters(self):
        """Test getting all logs without filters."""
        with self.app.app_context():
            # Create multiple logs
            for i in range(5):
                self.audit_service.log_action(
                    action=AuditAction.AGENT_CREATED,
                    user_id=self.user.id,
                    resource_id=i,
                )

            logs = self.audit_service.get_logs()

            self.assertEqual(len(logs), 5)

    def test_get_logs_with_user_filter(self):
        """Test getting logs filtered by user ID."""
        with self.app.app_context():
            # Create logs for different users
            for i in range(3):
                self.audit_service.log_action(
                    action=AuditAction.AGENT_CREATED,
                    user_id=self.user.id if i % 2 == 0 else None,
                )

            logs = self.audit_service.get_logs(user_id=self.user.id)

            self.assertEqual(len(logs), 2)
            for log in logs:
                self.assertEqual(log.user_id, self.user.id)

    def test_get_logs_with_action_filter(self):
        """Test getting logs filtered by action."""
        with self.app.app_context():
            # Create logs with different actions
            self.audit_service.log_action(
                action=AuditAction.AGENT_CREATED,
                user_id=self.user.id,
            )
            self.audit_service.log_action(
                action=AuditAction.AGENT_DELETED,
                user_id=self.user.id,
            )
            self.audit_service.log_action(
                action=AuditAction.AGENT_CREATED,
                user_id=self.user.id,
            )

            logs = self.audit_service.get_logs(action="agent_created")

            self.assertEqual(len(logs), 2)
            for log in logs:
                self.assertEqual(log.action, "agent_created")

    def test_get_logs_with_resource_type_filter(self):
        """Test getting logs filtered by resource type."""
        with self.app.app_context():
            self.audit_service.log_action(
                action=AuditAction.AGENT_CREATED,
                user_id=self.user.id,
                resource_type=AuditResourceType.AGENT,
            )
            self.audit_service.log_action(
                action=AuditAction.USER_CREATED,
                user_id=self.user.id,
                resource_type=AuditResourceType.USER,
            )

            logs = self.audit_service.get_logs(resource_type="agent")

            self.assertEqual(len(logs), 1)
            self.assertEqual(logs[0].resource_type, "agent")

    def test_get_logs_with_date_range(self):
        """Test getting logs within a date range."""
        with self.app.app_context():
            now = datetime.utcnow()

            # Create logs with different timestamps
            self.audit_service.log_action(
                action=AuditAction.AGENT_CREATED,
                user_id=self.user.id,
            )

            # Modify the created_at for testing
            log1 = self.audit_service.log_action(
                action=AuditAction.AGENT_CREATED,
                user_id=self.user.id,
                commit=False,
            )
            log1.created_at = now - timedelta(days=5)
            db.session.add(log1)

            log2 = self.audit_service.log_action(
                action=AuditAction.AGENT_CREATED,
                user_id=self.user.id,
                commit=False,
            )
            log2.created_at = now - timedelta(days=1)
            db.session.add(log2)

            db.session.commit()

            # Get logs from the last 2 days
            logs = self.audit_service.get_logs(
                start_date=now - timedelta(days=2),
                end_date=now,
            )

            # Should get log2 and the first log (created now)
            self.assertEqual(len(logs), 2)

    def test_get_logs_with_status_filter(self):
        """Test getting logs filtered by status."""
        with self.app.app_context():
            self.audit_service.log_action(
                action=AuditAction.LOGIN,
                user_id=self.user.id,
                status="success",
            )
            self.audit_service.log_action(
                action=AuditAction.LOGIN_FAILED,
                user_id=self.user.id,
                status="failure",
            )

            logs = self.audit_service.get_logs(status="failure")

            self.assertEqual(len(logs), 1)
            self.assertEqual(logs[0].status, "failure")

    def test_get_logs_with_pagination(self):
        """Test getting logs with pagination."""
        with self.app.app_context():
            # Create 10 logs
            for i in range(10):
                self.audit_service.log_action(
                    action=AuditAction.AGENT_CREATED,
                    user_id=self.user.id,
                    resource_id=i,
                )

            # Get first 5
            logs = self.audit_service.get_logs(limit=5, offset=0)
            self.assertEqual(len(logs), 5)

            # Get next 3
            logs = self.audit_service.get_logs(limit=3, offset=5)
            self.assertEqual(len(logs), 3)

    # ==================== Test Get Recent Logs ====================

    def test_get_recent_logs(self):
        """Test getting recent logs."""
        with self.app.app_context():
            # Create multiple logs
            for i in range(10):
                self.audit_service.log_action(
                    action=AuditAction.AGENT_CREATED,
                    user_id=self.user.id,
                )

            recent = self.audit_service.get_recent_logs(limit=5)

            self.assertEqual(len(recent), 5)
            # Should be in descending order by created_at
            for i in range(len(recent) - 1):
                self.assertGreaterEqual(
                    recent[i].created_at, recent[i + 1].created_at
                )

    # ==================== Test Get Logs By User ====================

    def test_get_logs_by_user(self):
        """Test getting logs for a specific user."""
        with self.app.app_context():
            # Create logs for the test user
            for i in range(5):
                self.audit_service.log_action(
                    action=AuditAction.AGENT_CREATED,
                    user_id=self.user.id,
                )

            # Create logs for another user
            other_user = User(
                email="other@example.com",
                username="otheruser",
                password="otherpassword123",
            )
            db.session.add(other_user)
            db.session.commit()

            for i in range(3):
                self.audit_service.log_action(
                    action=AuditAction.AGENT_CREATED,
                    user_id=other_user.id,
                )

            logs = self.audit_service.get_logs_by_user(self.user.id, limit=10)

            self.assertEqual(len(logs), 5)
            for log in logs:
                self.assertEqual(log.user_id, self.user.id)

    # ==================== Test Get Logs By Action ====================

    def test_get_logs_by_action(self):
        """Test getting logs for a specific action."""
        with self.app.app_context():
            # Create logs with different actions
            self.audit_service.log_action(
                action=AuditAction.AGENT_CREATED,
                user_id=self.user.id,
            )
            self.audit_service.log_action(
                action=AuditAction.AGENT_DELETED,
                user_id=self.user.id,
            )
            self.audit_service.log_action(
                action=AuditAction.AGENT_CREATED,
                user_id=self.user.id,
            )

            logs = self.audit_service.get_logs_by_action("agent_created", limit=10)

            self.assertEqual(len(logs), 2)
            for log in logs:
                self.assertEqual(log.action, "agent_created")

    # ==================== Test Search Logs ====================

    def test_search_logs_by_action(self):
        """Test searching logs by action."""
        with self.app.app_context():
            self.audit_service.log_action(
                action=AuditAction.AGENT_CREATED,
                user_id=self.user.id,
                resource_name="Test Agent",
            )
            self.audit_service.log_action(
                action=AuditAction.AGENT_DELETED,
                user_id=self.user.id,
                resource_name="Another Agent",
            )

            logs = self.audit_service.search_logs("created")

            self.assertEqual(len(logs), 1)
            self.assertEqual(logs[0].action, "agent_created")

    def test_search_logs_by_resource_name(self):
        """Test searching logs by resource name."""
        with self.app.app_context():
            self.audit_service.log_action(
                action=AuditAction.AGENT_CREATED,
                user_id=self.user.id,
                resource_name="Test Agent",
            )
            self.audit_service.log_action(
                action=AuditAction.AGENT_CREATED,
                user_id=self.user.id,
                resource_name="Production Agent",
            )

            logs = self.audit_service.search_logs("Test")

            self.assertEqual(len(logs), 1)
            self.assertEqual(logs[0].resource_name, "Test Agent")

    # ==================== Test Statistics ====================

    def test_get_statistics(self):
        """Test getting audit statistics."""
        with self.app.app_context():
            # Create various logs
            self.audit_service.log_action(
                action=AuditAction.AGENT_CREATED,
                user_id=self.user.id,
                resource_type=AuditResourceType.AGENT,
            )
            self.audit_service.log_action(
                action=AuditAction.AGENT_CREATED,
                user_id=self.user.id,
                resource_type=AuditResourceType.AGENT,
            )
            self.audit_service.log_action(
                action=AuditAction.USER_CREATED,
                user_id=self.user.id,
                resource_type=AuditResourceType.USER,
            )

            stats = self.audit_service.get_statistics()

            self.assertIn("total_logs", stats)
            self.assertEqual(stats["total_logs"], 3)
            self.assertIn("action_counts", stats)
            self.assertEqual(stats["action_counts"]["agent_created"], 2)
            self.assertEqual(stats["action_counts"]["user_created"], 1)
            self.assertIn("user_counts", stats)
            self.assertEqual(stats["user_counts"][self.user.id], 3)
            self.assertIn("recent_logs", stats)
            self.assertEqual(len(stats["recent_logs"]), 10)  # Default limit

    # ==================== Test Export ====================

    def test_export_to_json(self):
        """Test exporting logs to JSON format."""
        with self.app.app_context():
            # Create some logs
            self.audit_service.log_action(
                action=AuditAction.AGENT_CREATED,
                user_id=self.user.id,
                resource_name="Test Agent",
            )
            self.audit_service.log_action(
                action=AuditAction.AGENT_DELETED,
                user_id=self.user.id,
                resource_name="Another Agent",
            )

            json_str = self.audit_service.export_to_json(
                user_id=self.user.id, limit=10
            )

            # Parse the JSON to verify
            logs = json.loads(json_str)
            self.assertEqual(len(logs), 2)
            self.assertEqual(logs[0]["action"], "agent_deleted")
            self.assertEqual(logs[1]["action"], "agent_created")

    def test_export_to_csv(self):
        """Test exporting logs to CSV format."""
        with self.app.app_context():
            # Create some logs
            self.audit_service.log_action(
                action=AuditAction.AGENT_CREATED,
                user_id=self.user.id,
                resource_name="Test Agent",
                ip_address="192.168.1.1",
                user_agent="Mozilla/5.0",
            )

            csv_str = self.audit_service.export_to_csv(user_id=self.user.id, limit=10)

            # Parse CSV to verify
            reader = csv.DictReader(io.StringIO(csv_str))
            rows = list(reader)

            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["action"], "agent_created")
            self.assertEqual(rows[0]["user_id"], str(self.user.id))
            self.assertEqual(rows[0]["resource_name"], "Test Agent")

    # ==================== Test Clear Old Logs ====================

    def test_clear_old_logs(self):
        """Test clearing old audit logs."""
        with self.app.app_context():
            now = datetime.utcnow()

            # Create a recent log
            self.audit_service.log_action(
                action=AuditAction.AGENT_CREATED,
                user_id=self.user.id,
            )

            # Create an old log (manually set the date)
            old_log = AuditLog(
                action="old_action",
                user_id=self.user.id,
                created_at=now - timedelta(days=100),
            )
            db.session.add(old_log)
            db.session.commit()

            # Clear logs older than 90 days
            deleted_count = self.audit_service.clear_old_logs(days=90)

            self.assertEqual(deleted_count, 1)

            # Verify the old log is deleted
            logs = self.audit_service.get_logs()
            self.assertEqual(len(logs), 1)  # Only the recent log remains

    def test_clear_all_logs(self):
        """Test clearing all audit logs."""
        with self.app.app_context():
            # Create multiple logs
            for i in range(5):
                self.audit_service.log_action(
                    action=AuditAction.AGENT_CREATED,
                    user_id=self.user.id,
                )

            # Clear all logs
            deleted_count = self.audit_service.clear_all_logs()

            self.assertEqual(deleted_count, 5)

            # Verify all logs are deleted
            logs = self.audit_service.get_logs()
            self.assertEqual(len(logs), 0)

    # ==================== Test Request Info ====================

    def test_get_request_info(self):
        """Test getting request info (IP and user agent)."""
        with self.app.app_context():
            with self.app.test_request_context(
                "/test",
                headers={
                    "User-Agent": "Test-Agent",
                    "X-Forwarded-For": "10.0.0.1, 192.168.1.1",
                },
            ):
                info = self.audit_service.get_request_info()
                self.assertEqual(info["ip_address"], "10.0.0.1")
                self.assertEqual(info["user_agent"], "Test-Agent")

    # ==================== Test Log From Request ====================

    def test_log_from_request(self):
        """Test logging from request context."""
        with self.app.app_context():
            with self.app.test_request_context(
                "/test",
                headers={
                    "User-Agent": "Test-Agent",
                    "X-Forwarded-For": "10.0.0.1",
                },
            ):
                log = self.audit_service.log_from_request(
                    action=AuditAction.AGENT_CREATED,
                    user=self.user,
                    resource_type=AuditResourceType.AGENT,
                    resource_id=1,
                    resource_name="Test Agent",
                )

                self.assertIsNotNone(log)
                self.assertEqual(log.action, "agent_created")
                self.assertEqual(log.user_id, self.user.id)
                self.assertEqual(log.ip_address, "10.0.0.1")
                self.assertEqual(log.user_agent, "Test-Agent")

    # ==================== Test Audit Decorator ====================

    def test_audit_decorator(self):
        """Test the audit decorator for automatic logging."""
        with self.app.app_context():
            # Create a simple function to decorate
            @self.audit_service.create_audit_decorator(
                action=AuditAction.AGENT_CREATED,
                resource_type=AuditResourceType.AGENT,
                get_resource_id="agent_id",
                get_resource_name="agent_name",
            )
            def create_agent(agent_id: int, agent_name: str, current_user: User = None):
                return {"id": agent_id, "name": agent_name}

            # Call the decorated function
            with self.app.test_request_context(
                "/test",
                headers={
                    "User-Agent": "Test-Agent",
                    "X-Forwarded-For": "10.0.0.1",
                },
            ):
                result = create_agent(
                    agent_id=1,
                    agent_name="Test Agent",
                    current_user=self.user,
                )

                # Verify the action was logged
                logs = self.audit_service.get_logs(
                    action="agent_created",
                    user_id=self.user.id,
                )

                self.assertEqual(len(logs), 1)
                self.assertEqual(logs[0].resource_id, 1)
                self.assertEqual(logs[0].resource_name, "Test Agent")


class TestAuditLogModel(unittest.TestCase):
    """Test cases for AuditLog model."""

    def setUp(self):
        """Set up test fixtures."""
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
        self.app.config["AUTO_CREATE_DB"] = True

        with self.app.app_context():
            db.create_all()

            # Create a test user
            self.user = User(
                email="test@example.com",
                username="testuser",
                password="testpassword123",
            )
            db.session.add(self.user)
            db.session.commit()

    def tearDown(self):
        """Clean up test fixtures."""
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_audit_log_creation(self):
        """Test creating an AuditLog directly."""
        with self.app.app_context():
            log = AuditLog(
                action="test_action",
                user_id=self.user.id,
                resource_type="test_resource",
                resource_id=1,
                resource_name="Test Resource",
                status="success",
            )
            db.session.add(log)
            db.session.commit()

            self.assertIsNotNone(log.id)
            self.assertEqual(log.action, "test_action")

    def test_audit_log_static_log_method(self):
        """Test the static log method."""
        with self.app.app_context():
            log = AuditLog.log(
                action="test_action",
                user_id=self.user.id,
                resource_type="test_resource",
                resource_id=1,
            )

            self.assertIsNotNone(log.id)
            self.assertEqual(log.action, "test_action")

    def test_audit_log_to_dict(self):
        """Test converting audit log to dictionary."""
        with self.app.app_context():
            log = AuditLog.log(
                action="test_action",
                user_id=self.user.id,
                resource_name="Test Resource",
            )

            log_dict = log.to_dict()

            self.assertIn("id", log_dict)
            self.assertEqual(log_dict["action"], "test_action")
            self.assertEqual(log_dict["user_id"], self.user.id)
            self.assertIn("created_at", log_dict)

    def test_audit_action_enum(self):
        """Test AuditAction enum values."""
        self.assertEqual(AuditAction.AGENT_CREATED.value, "agent_created")
        self.assertEqual(AuditAction.USER_DELETED.value, "user_deleted")
        self.assertIn("LOGIN", [a.value for a in AuditAction])

    def test_audit_resource_type_enum(self):
        """Test AuditResourceType enum values."""
        self.assertEqual(AuditResourceType.AGENT.value, "agent")
        self.assertEqual(AuditResourceType.USER.value, "user")
        self.assertIn("SYSTEM", [r.value for r in AuditResourceType])

    def test_get_all_actions(self):
        """Test getting all action values."""
        actions = AuditAction.get_all_values()
        self.assertIn("agent_created", actions)
        self.assertIn("user_created", actions)
        self.assertIn("login", actions)


class TestAuditErrorHandling(unittest.TestCase):
    """Test cases for audit error handling."""

    def test_audit_error_base(self):
        """Test AuditError base exception."""
        error = AuditError("Test error")
        self.assertEqual(error.status_code, 400)
        self.assertEqual(error.error_code, "audit_error")

    def test_audit_log_not_found_error(self):
        """Test AuditLogNotFoundError exception."""
        error = AuditLogNotFoundError("Log not found")
        self.assertEqual(error.status_code, 404)
        self.assertEqual(error.error_code, "audit_log_not_found")


if __name__ == "__main__":
    unittest.main()
