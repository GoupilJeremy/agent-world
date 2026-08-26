# 🧪 Agent World - Log Masking Service Tests
# Version: 1.0.0 (EPIC 10 - US-067)
# Description: Tests unitaires pour le service LogMaskingService

"""
Unit tests for LogMaskingService.

Ces tests couvrent:
- Masquage des champs sensibles dans les dictionnaires
- Masquage des motifs sensibles dans les chaînes
- Intégration avec le système de logging Python
- Configuration des champs et motifs sensibles
"""

import logging
import re
import unittest
from io import StringIO

from backend.services.log_masking_service import (
    DEFAULT_SENSITIVE_FIELDS,
    DEFAULT_SENSITIVE_PATTERNS,
    LogMaskingService,
    SensitiveDataFilter,
    create_sensitive_data_filter,
    setup_log_masking,
)


class TestSensitiveDataFilter(unittest.TestCase):
    """Test cases for SensitiveDataFilter."""

    def setUp(self):
        """Set up test fixtures."""
        self.filter = SensitiveDataFilter()

    def test_mask_string_default(self):
        """Test masking a string with default settings."""
        # String longer than 4 chars should show last 4
        self.assertEqual(self.filter._mask_string("abc123xyz"), "*******xyz")
        
        # String shorter than or equal to 4 chars should be fully masked
        self.assertEqual(self.filter._mask_string("abc"), "***")
        self.assertEqual(self.filter._mask_string("abcd"), "****")
        self.assertEqual(self.filter._mask_string(""), "")

    def test_mask_string_custom_mask_char(self):
        """Test masking with custom mask character."""
        filter_x = SensitiveDataFilter(mask_char="X")
        self.assertEqual(filter_x._mask_string("abc123xyz"), "XXXXXXXxyz")

    def test_mask_dict_with_sensitive_fields(self):
        """Test masking sensitive fields in a dictionary."""
        data = {
            "username": "john_doe",
            "password": "secret123",
            "email": "john@example.com",
            "api_key": "sk-abc123xyz",
            "name": "John Doe",
        }
        
        result = self.filter.mask_dict(data)
        
        # Sensitive fields should be masked
        self.assertEqual(result["password"], "*********23")
        self.assertEqual(result["email"], "***************com")
        self.assertEqual(result["api_key"], "***********xyz")
        
        # Non-sensitive fields should not be masked
        self.assertEqual(result["username"], "john_doe")
        self.assertEqual(result["name"], "John Doe")

    def test_mask_dict_nested(self):
        """Test masking nested dictionaries."""
        data = {
            "user": {
                "name": "John",
                "password": "secret123",
            },
            "config": {
                "api_key": "sk-abc123",
                "timeout": 30,
            },
        }
        
        result = self.filter.mask_value(data)
        
        # Check nested masking
        self.assertEqual(result["user"]["password"], "*********23")
        self.assertEqual(result["config"]["api_key"], "**********c")
        self.assertEqual(result["user"]["name"], "John")
        self.assertEqual(result["config"]["timeout"], 30)

    def test_mask_list(self):
        """Test masking lists and tuples."""
        data = [
            "normal_value",
            "password123",
            {"key": "api_key_value"},
        ]
        
        result = self.filter.mask_value(data)
        
        self.assertEqual(result[0], "normal_value")
        # password123 matches a sensitive pattern
        self.assertNotEqual(result[1], "password123")
        self.assertIn("*", result[1])
        self.assertIn("23", result[1])

    def test_mask_string_with_patterns(self):
        """Test masking strings that match sensitive patterns."""
        # Test with OpenAI API key pattern
        self.assertNotEqual(
            self.filter.mask_string_values("sk-abcdefghijklmnopqrstuvwxyz"),
            "sk-abcdefghijklmnopqrstuvwxyz"
        )
        
        # Test with bearer token pattern
        bearer_token = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozjgNryP4J3jVmNHl0w5N_XgL0n3I9PlFUP0THsR8U"
        masked = self.filter.mask_string_values(bearer_token)
        self.assertNotEqual(masked, bearer_token)
        self.assertIn("*", masked)

    def test_mask_preserves_structure(self):
        """Test that masking preserves data structure."""
        data = {
            "list": [1, 2, 3],
            "nested": {
                "inner": {
                    "password": "secret",
                }
            },
            "tuple": (1, 2, 3),
        }
        
        result = self.filter.mask_value(data)
        
        self.assertIsInstance(result["list"], list)
        self.assertIsInstance(result["nested"], dict)
        self.assertIsInstance(result["nested"]["inner"], dict)
        self.assertIsInstance(result["tuple"], tuple)

    def test_custom_sensitive_fields(self):
        """Test with custom sensitive fields."""
        custom_fields = {"custom_field", "another_field"}
        filter_custom = SensitiveDataFilter(sensitive_fields=custom_fields)
        
        data = {
            "custom_field": "sensitive_value",
            "another_field": "also_sensitive",
            "normal_field": "normal_value",
        }
        
        result = filter_custom.mask_dict(data)
        
        self.assertIn("*", result["custom_field"])
        self.assertIn("*", result["another_field"])
        self.assertEqual(result["normal_field"], "normal_value")

    def test_filter_modifies_log_record(self):
        """Test that the filter modifies log records correctly."""
        # Create a log record with sensitive data
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg={"password": "secret123", "username": "john"},
            args=(),
            exc_info=None,
        )
        
        # Apply filter
        self.filter.filter(record)
        
        # Check that sensitive data is masked
        self.assertIn("*", record.msg["password"])
        self.assertEqual(record.msg["username"], "john")

    def test_filter_with_string_message(self):
        """Test filter with string message containing sensitive data."""
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="User login with token: sk-abc123xyz",
            args=(),
            exc_info=None,
        )
        
        self.filter.filter(record)
        
        # The token should be masked
        self.assertIn("*", record.msg)
        self.assertNotIn("sk-abc123xyz", record.msg)

    def test_filter_with_args(self):
        """Test filter with log record arguments."""
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="User: %s, Password: %s",
            args=("john", "secret123"),
            exc_info=None,
        )
        
        self.filter.filter(record)
        
        # Check that password in args is masked
        self.assertIn("*", record.args[1])


class TestLogMaskingService(unittest.TestCase):
    """Test cases for LogMaskingService."""

    def setUp(self):
        """Set up test fixtures."""
        self.service = LogMaskingService()

    def test_create_filter(self):
        """Test creating a filter from the service."""
        filter_obj = self.service.create_filter()
        self.assertIsInstance(filter_obj, SensitiveDataFilter)

    def test_add_sensitive_field(self):
        """Test adding a sensitive field."""
        self.service.add_sensitive_field("custom_secret")
        
        filter_obj = self.service.create_filter()
        data = {"custom_secret": "value", "normal": "value"}
        result = filter_obj.mask_dict(data)
        
        self.assertIn("*", result["custom_secret"])
        self.assertEqual(result["normal"], "value")

    def test_add_sensitive_fields(self):
        """Test adding multiple sensitive fields."""
        self.service.add_sensitive_fields(["field1", "field2", "field3"])
        
        filter_obj = self.service.create_filter()
        data = {"field1": "v1", "field2": "v2", "field3": "v3", "field4": "v4"}
        result = filter_obj.mask_dict(data)
        
        self.assertIn("*", result["field1"])
        self.assertIn("*", result["field2"])
        self.assertIn("*", result["field3"])
        self.assertEqual(result["field4"], "v4")

    def test_add_sensitive_pattern(self):
        """Test adding a sensitive pattern."""
        # Add a pattern for custom IDs
        self.service.add_sensitive_pattern(r"CUSTOM-[A-Z0-9]{10}")
        
        filter_obj = self.service.create_filter()
        result = filter_obj.mask_string_values("My custom ID: CUSTOM-ABC1234567")
        
        self.assertNotIn("CUSTOM-ABC1234567", result)
        self.assertIn("*", result)

    def test_mask_data(self):
        """Test masking data with the service."""
        data = {
            "password": "secret123",
            "username": "john",
            "nested": {
                "api_key": "sk-abc123",
            },
        }
        
        result = self.service.mask_data(data)
        
        self.assertIn("*", result["password"])
        self.assertEqual(result["username"], "john")
        self.assertIn("*", result["nested"]["api_key"])

    def test_mask_string(self):
        """Test masking a string with the service."""
        result = self.service.mask_string("Email: john@example.com, Token: sk-abc123")
        
        self.assertNotIn("john@example.com", result)
        self.assertNotIn("sk-abc123", result)


class TestLoggingIntegration(unittest.TestCase):
    """Test cases for logging integration."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a logger for testing
        self.test_logger = logging.getLogger("test_log_masking")
        self.test_logger.setLevel(logging.INFO)
        
        # Remove any existing handlers
        for handler in self.test_logger.handlers[:]:
            self.test_logger.removeHandler(handler)
        
        # Add a string handler to capture output
        self.stream = StringIO()
        self.handler = logging.StreamHandler(self.stream)
        self.test_logger.addHandler(self.handler)

    def tearDown(self):
        """Clean up test fixtures."""
        # Remove the handler
        self.test_logger.removeHandler(self.handler)
        self.stream.close()

    def test_setup_log_masking(self):
        """Test setting up log masking for a logger."""
        # Set up masking
        setup_log_masking("test_log_masking")
        
        # Log sensitive data
        self.test_logger.info({"password": "secret123", "username": "john"})
        
        # Get the output
        output = self.stream.getvalue()
        
        # Password should be masked
        self.assertIn("*", output)
        # Username should not be masked
        self.assertIn("john", output)
        # Original password should not appear
        self.assertNotIn("secret123", output)

    def test_log_masking_with_string_message(self):
        """Test log masking with string message containing sensitive data."""
        setup_log_masking("test_log_masking")
        
        # Log a string with sensitive data
        self.test_logger.info("API key: sk-abc123xyz")
        
        output = self.stream.getvalue()
        
        # API key should be masked
        self.assertIn("*", output)
        self.assertNotIn("sk-abc123xyz", output)

    def test_log_masking_preserves_normal_logs(self):
        """Test that normal log messages are preserved."""
        setup_log_masking("test_log_masking")
        
        # Log normal data
        self.test_logger.info("Normal log message")
        
        output = self.stream.getvalue()
        
        self.assertIn("Normal log message", output)


class TestDefaultSensitiveFields(unittest.TestCase):
    """Test cases for default sensitive fields and patterns."""

    def test_default_sensitive_fields_exist(self):
        """Test that default sensitive fields are defined."""
        self.assertGreater(len(DEFAULT_SENSITIVE_FIELDS), 0)
        self.assertIn("password", DEFAULT_SENSITIVE_FIELDS)
        self.assertIn("api_key", DEFAULT_SENSITIVE_FIELDS)
        self.assertIn("token", DEFAULT_SENSITIVE_FIELDS)
        self.assertIn("secret", DEFAULT_SENSITIVE_FIELDS)

    def test_default_sensitive_patterns_exist(self):
        """Test that default sensitive patterns are defined."""
        self.assertGreater(len(DEFAULT_SENSITIVE_PATTERNS), 0)

    def test_pattern_matches_common_formats(self):
        """Test that patterns match common sensitive data formats."""
        patterns = DEFAULT_SENSITIVE_PATTERNS
        
        # Test with OpenAI API key format
        test_key = "sk-abcdefghijklmnopqrstuvwxyz"
        matched = any(pattern.search(test_key) for pattern in patterns)
        self.assertTrue(matched, f"No pattern matched: {test_key}")
        
        # Test with bearer token format
        test_token = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.test.test"
        matched = any(pattern.search(test_token) for pattern in patterns)
        self.assertTrue(matched, f"No pattern matched: {test_token}")
        
        # Test with email
        test_email = "test@example.com"
        matched = any(pattern.search(test_email) for pattern in patterns)
        self.assertTrue(matched, f"No pattern matched: {test_email}")


class TestConvenienceFunctions(unittest.TestCase):
    """Test cases for convenience functions."""

    def test_create_sensitive_data_filter(self):
        """Test creating a filter with convenience function."""
        filter_obj = create_sensitive_data_filter()
        self.assertIsInstance(filter_obj, SensitiveDataFilter)

    def test_create_sensitive_data_filter_with_custom_settings(self):
        """Test creating a filter with custom settings."""
        custom_fields = {"my_field"}
        filter_obj = create_sensitive_data_filter(
            sensitive_fields=custom_fields,
            mask_char="X",
            show_last=2,
        )
        
        self.assertIsInstance(filter_obj, SensitiveDataFilter)
        self.assertEqual(filter_obj.mask_char, "X")
        self.assertEqual(filter_obj.show_last, 2)
        
        # Test that it uses custom settings
        self.assertEqual(filter_obj._mask_string("test"), "XXst")


if __name__ == "__main__":
    unittest.main()
