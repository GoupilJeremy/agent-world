# 🧪 Agent World - Encryption Service Tests
# Version: 1.0.0 (EPIC 10 - US-067)
# Description: Tests unitaires pour le service EncryptionService

"""
Unit tests for EncryptionService.

Ces tests couvrent:
- Chiffrement et déchiffrement AES-256
- Gestion des clés de chiffrement
- Rotation des clés
- Chiffrement/déchiffrement de champs de modèles
- Masquage des données sensibles
"""

import unittest
from datetime import datetime, timedelta

from backend.app import create_app
from backend.models.base import db
from backend.models.encryption_key import EncryptionKey
from backend.services.encryption_service import (
    DecryptionError,
    EncryptionError,
    EncryptionService,
    KeyRotationError,
)


class TestEncryptionService(unittest.TestCase):
    """Test cases for EncryptionService."""

    def setUp(self):
        """Set up test fixtures."""
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
        self.app.config["AUTO_CREATE_DB"] = True
        self.app.config["ENCRYPTION_MASTER_KEY"] = "test-master-key-1234567890"
        self.app.config["ENCRYPTION_KEY_TTL_DAYS"] = 90
        
        self.client = self.app.test_client()
        
        with self.app.app_context():
            db.create_all()
            # Create encryption service with test master key
            self.encryption_service = EncryptionService(
                master_key="test-master-key-1234567890",
                key_ttl_days=90,
            )

    def tearDown(self):
        """Clean up test fixtures."""
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_encrypt_decrypt_string(self):
        """Test encrypting and decrypting a string."""
        with self.app.app_context():
            # Create and activate a key
            key = self.encryption_service.create_and_store_key()
            self.encryption_service.activate_key(key.key_id)
            
            plaintext = "Test sensitive data"
            encrypted = self.encryption_service.encrypt(plaintext)
            decrypted = self.encryption_service.decrypt(encrypted)
            
            self.assertNotEqual(encrypted, plaintext)
            self.assertEqual(decrypted, plaintext)

    def test_encrypt_decrypt_empty_string(self):
        """Test encrypting and decrypting an empty string."""
        with self.app.app_context():
            key = self.encryption_service.create_and_store_key()
            self.encryption_service.activate_key(key.key_id)
            
            plaintext = ""
            encrypted = self.encryption_service.encrypt(plaintext)
            decrypted = self.encryption_service.decrypt(encrypted)
            
            self.assertEqual(decrypted, plaintext)

    def test_encrypt_decrypt_special_characters(self):
        """Test encrypting and decrypting strings with special characters."""
        with self.app.app_context():
            key = self.encryption_service.create_and_store_key()
            self.encryption_service.activate_key(key.key_id)
            
            test_cases = [
                "Hello, World!",
                "Test with émojis 🎉",
                "Special chars: @#$%^&*()",
                "Line\nbreaks\tand\ttabs",
                "Unicode: 你好世界",
            ]
            
            for plaintext in test_cases:
                encrypted = self.encryption_service.encrypt(plaintext)
                decrypted = self.encryption_service.decrypt(encrypted)
                self.assertEqual(decrypted, plaintext)

    def test_multiple_keys_decryption(self):
        """Test that data encrypted with old keys can still be decrypted."""
        with self.app.app_context():
            # Create first key and encrypt some data
            key1 = self.encryption_service.create_and_store_key()
            self.encryption_service.activate_key(key1.key_id)
            
            data1 = "Data encrypted with key 1"
            encrypted1 = self.encryption_service.encrypt(data1)
            
            # Create second key and encrypt more data
            key2 = self.encryption_service.create_and_store_key()
            self.encryption_service.activate_key(key2.key_id)
            
            data2 = "Data encrypted with key 2"
            encrypted2 = self.encryption_service.encrypt(data2)
            
            # Deactivate key2 and reactivate key1
            EncryptionKey.deactivate_all()
            key1.is_active = True
            db.session.commit()
            self.encryption_service._fernet_cache.clear()
            
            # Both should still be decryptable
            self.assertEqual(self.encryption_service.decrypt(encrypted1), data1)
            self.assertEqual(self.encryption_service.decrypt(encrypted2), data2)

    def test_key_rotation(self):
        """Test rotating encryption keys."""
        with self.app.app_context():
            # Create initial key
            initial_key = self.encryption_service.get_active_key()
            initial_version = initial_key.version
            
            # Rotate key
            new_key = self.encryption_service.rotate_key(
                description="Test rotation"
            )
            
            # Check that new key is active
            self.assertTrue(new_key.is_active)
            self.assertEqual(new_key.version, initial_version + 1)
            
            # Check that old key is no longer active
            old_key = EncryptionKey.get_by_key_id(initial_key.key_id)
            self.assertFalse(old_key.is_active)

    def test_needs_rotation(self):
        """Test checking if key needs rotation."""
        with self.app.app_context():
            # Create a key that expires in 1 day
            key = self.encryption_service.create_and_store_key(
                description="Short-lived key",
                ttl_days=1,
            )
            self.encryption_service.activate_key(key.key_id)
            
            # Should not need rotation yet
            self.assertFalse(self.encryption_service.needs_rotation())
            
            # Expire the key (set expiration to past)
            key.expires_at = datetime.utcnow() - timedelta(days=1)
            db.session.commit()
            
            # Should need rotation now
            self.assertTrue(self.encryption_service.needs_rotation())

    def test_get_active_key_auto_create(self):
        """Test that get_active_key creates a default key if none exists."""
        with self.app.app_context():
            # Clear all keys
            EncryptionKey.query.delete()
            db.session.commit()
            
            # Clear cache
            self.encryption_service._fernet_cache.clear()
            
            # Get active key should create one
            key = self.encryption_service.get_active_key()
            
            self.assertIsNotNone(key)
            self.assertTrue(key.is_active)
            self.assertEqual(key.description, "Default auto-generated key")

    def test_activate_key(self):
        """Test activating a specific key."""
        with self.app.app_context():
            # Create two keys
            key1 = self.encryption_service.create_and_store_key()
            key2 = self.encryption_service.create_and_store_key()
            
            # Activate key2
            activated = self.encryption_service.activate_key(key2.key_id)
            
            self.assertEqual(activated.id, key2.id)
            self.assertTrue(key2.is_active)
            self.assertFalse(key1.is_active)

    def test_activate_nonexistent_key(self):
        """Test activating a non-existent key raises error."""
        with self.app.app_context():
            with self.assertRaises(EncryptionError):
                self.encryption_service.activate_key("nonexistent-key-id")

    def test_encrypt_field(self):
        """Test encrypting a model field."""
        with self.app.app_context():
            key = self.encryption_service.create_and_store_key()
            self.encryption_service.activate_key(key.key_id)
            
            # Create a simple object to test with
            class TestObject:
                def __init__(self):
                    self.sensitive_field = "secret value"
                    self.normal_field = "normal value"
            
            obj = TestObject()
            self.encryption_service.encrypt_field(obj, "sensitive_field")
            
            # The field should be encrypted
            self.assertNotEqual(obj.sensitive_field, "secret value")
            self.assertEqual(obj.normal_field, "normal value")
            
            # Decrypt it back
            self.encryption_service.decrypt_field(obj, "sensitive_field")
            self.assertEqual(obj.sensitive_field, "secret value")

    def test_mask_sensitive_data(self):
        """Test masking sensitive data."""
        masker = self.encryption_service
        
        # Test with default settings (show last 4 chars)
        self.assertEqual(masker.mask_sensitive_data("abc123xyz"), "*******xyz")
        self.assertEqual(masker.mask_sensitive_data("short"), "*****短")  # Shows all if <= 4
        self.assertEqual(masker.mask_sensitive_data(""), "")
        self.assertEqual(masker.mask_sensitive_data("abc"), "***")
        
        # Test with custom mask char
        self.assertEqual(masker.mask_sensitive_data("abc123xyz", "X"), "XXXXXXXxyz")
        
        # Test with custom show_last
        masker_custom = EncryptionService(master_key="test-key")
        # Can't easily change show_last after initialization, but we can test the method directly
        result = masker_custom._mask_string("abcdefgh")  # show_last=4 by default
        self.assertEqual(result, "****defgh")

    def test_mask_sensitive_data_custom(self):
        """Test masking with custom parameters."""
        # Test the method directly
        service = EncryptionService(master_key="test-key")
        
        # Test with different show_last values
        # We can't change show_last after init, but we can test the internal method
        # by creating a new service (though it's not ideal)
        result = service.mask_sensitive_data("abcdefghij", "X", 3)
        self.assertEqual(result, "XXXXXXXhij")

    def test_get_decrypted_model(self):
        """Test getting decrypted model data."""
        with self.app.app_context():
            key = self.encryption_service.create_and_store_key()
            self.encryption_service.activate_key(key.key_id)
            
            # Create a test object
            class TestModel:
                def __init__(self):
                    self.field1 = "value1"
                    self.field2 = "value2"
            
            obj = TestModel()
            
            # Encrypt fields
            encrypted1 = self.encryption_service.encrypt("value1")
            encrypted2 = self.encryption_service.encrypt("value2")
            obj.field1 = encrypted1
            obj.field2 = encrypted2
            
            # Get decrypted values
            decrypted = self.encryption_service.get_decrypted_model(
                obj, ["field1", "field2"]
            )
            
            self.assertEqual(decrypted["field1"], "value1")
            self.assertEqual(decrypted["field2"], "value2")

    def test_create_encrypted_model(self):
        """Test creating a model with encrypted fields."""
        with self.app.app_context():
            key = self.encryption_service.create_and_store_key()
            self.encryption_service.activate_key(key.key_id)
            
            # Create a simple model class
            class TestModel:
                def __init__(self, **kwargs):
                    for k, v in kwargs.items():
                        setattr(self, k, v)
            
            # Create with encrypted fields
            model = self.encryption_service.create_encrypted_model(
                TestModel,
                encrypted_fields=["secret"],
                name="test",
                secret="my-secret-value",
            )
            
            self.assertEqual(model.name, "test")
            self.assertNotEqual(model.secret, "my-secret-value")
            
            # Verify we can decrypt
            decrypted = self.encryption_service.decrypt(model.secret)
            self.assertEqual(decrypted, "my-secret-value")


class TestEncryptionKeyModel(unittest.TestCase):
    """Test cases for EncryptionKey model."""

    def setUp(self):
        """Set up test fixtures."""
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
        self.app.config["AUTO_CREATE_DB"] = True
        
        self.client = self.app.test_client()
        
        with self.app.app_context():
            db.create_all()

    def tearDown(self):
        """Clean up test fixtures."""
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_encryption_key_creation(self):
        """Test creating an encryption key."""
        with self.app.app_context():
            key = EncryptionKey(
                key_id="test-key-id",
                encrypted_key="test-encrypted-key",
                is_active=True,
                version=1,
                description="Test key",
            )
            db.session.add(key)
            db.session.commit()
            
            self.assertIsNotNone(key.id)
            self.assertEqual(key.key_id, "test-key-id")
            self.assertTrue(key.is_active)

    def test_get_active_key(self):
        """Test getting the active key."""
        with self.app.app_context():
            # Create an active key
            active_key = EncryptionKey(
                key_id="active-key",
                encrypted_key="encrypted",
                is_active=True,
                version=1,
            )
            db.session.add(active_key)
            
            # Create an inactive key
            inactive_key = EncryptionKey(
                key_id="inactive-key",
                encrypted_key="encrypted",
                is_active=False,
                version=2,
            )
            db.session.add(inactive_key)
            db.session.commit()
            
            # Should return the active key
            result = EncryptionKey.get_active_key()
            self.assertIsNotNone(result)
            self.assertEqual(result.key_id, "active-key")

    def test_get_by_key_id(self):
        """Test getting a key by its key_id."""
        with self.app.app_context():
            key = EncryptionKey(
                key_id="test-key-123",
                encrypted_key="encrypted",
                is_active=False,
                version=1,
            )
            db.session.add(key)
            db.session.commit()
            
            result = EncryptionKey.get_by_key_id("test-key-123")
            self.assertIsNotNone(result)
            self.assertEqual(result.key_id, "test-key-123")

    def test_get_all_versions(self):
        """Test getting all key versions."""
        with self.app.app_context():
            # Create keys with different versions
            for i in range(5):
                key = EncryptionKey(
                    key_id=f"key-{i}",
                    encrypted_key=f"encrypted-{i}",
                    is_active=(i == 3),  # Only one active
                    version=i + 1,
                )
                db.session.add(key)
            db.session.commit()
            
            keys = EncryptionKey.get_all_versions()
            self.assertEqual(len(keys), 5)
            # Should be ordered by version descending
            self.assertEqual(keys[0].version, 5)
            self.assertEqual(keys[4].version, 1)

    def test_deactivate_all(self):
        """Test deactivating all keys."""
        with self.app.app_context():
            # Create multiple active keys
            for i in range(3):
                key = EncryptionKey(
                    key_id=f"key-{i}",
                    encrypted_key=f"encrypted-{i}",
                    is_active=True,
                    version=i + 1,
                )
                db.session.add(key)
            db.session.commit()
            
            # Deactivate all
            EncryptionKey.deactivate_all()
            
            # Check that all are inactive
            keys = EncryptionKey.query.all()
            for key in keys:
                self.assertFalse(key.is_active)

    def test_to_dict(self):
        """Test converting key to dictionary."""
        with self.app.app_context():
            key = EncryptionKey(
                key_id="test-key",
                encrypted_key="encrypted",
                is_active=True,
                version=1,
                description="Test key",
            )
            db.session.add(key)
            db.session.commit()
            
            result = key.to_dict()
            
            self.assertIn("id", result)
            self.assertIn("key_id", result)
            self.assertEqual(result["key_id"], "test-key")
            self.assertIn("is_active", result)
            self.assertTrue(result["is_active"])
            self.assertIn("version", result)
            self.assertEqual(result["version"], 1)
            # Should not include encrypted_key
            self.assertNotIn("encrypted_key", result)


if __name__ == "__main__":
    unittest.main()
