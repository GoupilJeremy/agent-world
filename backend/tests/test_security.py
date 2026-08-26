"""Security tests for Epic 10."""

from __future__ import annotations

import os
import unittest
from datetime import datetime

from cryptography.fernet import Fernet

from ..app import create_app
from ..config.settings import TestingConfig
from ..models.base import db
from ..models.user import User
from ..services.encryption_service import EncryptionService, get_encryption_service
from ..services.permission_service import has_permission, role_permissions
from ..services.two_factor_service import TwoFactorService

os.environ.setdefault("ENCRYPTION_KEY", Fernet.generate_key().decode())


class EncryptionServiceTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(config_class=TestingConfig)
        with self.app.app_context():
            db.create_all()
            self.encryption = EncryptionService()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_encrypt_decrypt_roundtrip(self):
        plaintext = "sensitive-data-123"
        ciphertext = self.encryption.encrypt(plaintext)
        self.assertNotEqual(plaintext, ciphertext)
        self.assertEqual(plaintext, self.encryption.decrypt(ciphertext))

    def test_decrypt_invalid_raises(self):
        with self.assertRaises(Exception):
            self.encryption.decrypt("invalid-ciphertext")


class TwoFactorServiceTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(config_class=TestingConfig)
        with self.app.app_context():
            db.create_all()
            self.user = User.create(
                username="2fa-user",
                email="2fa@example.com",
                password="password123",
            )
            self.user_id = self.user.id

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def _get_user(self):
        with self.app.app_context():
            return db.session.get(User, self.user_id)

    def test_enroll_generates_secret(self):
        with self.app.app_context():
            user = self._get_user()
            service = TwoFactorService()
            secret, uri = service.enroll(user)
            self.assertIsNotNone(secret)
            self.assertIn("Agent%20World", uri)
            self.assertIn("2fa%40example.com", uri)

    def test_enable_and_verify(self):
        with self.app.app_context():
            user = self._get_user()
            service = TwoFactorService()
            secret, _ = service.enroll(user)
            totp = __import__("pyotp").totp.TOTP(secret)
            code = totp.now()
            service.enable(user, code)
            self.assertTrue(user.totp_enabled)
            self.assertTrue(service.verify(user, code))

    def test_disable(self):
        with self.app.app_context():
            user = self._get_user()
            service = TwoFactorService()
            secret, _ = service.enroll(user)
            totp = __import__("pyotp").totp.TOTP(secret)
            code = totp.now()
            service.enable(user, code)
            service.disable(user, code)
            self.assertFalse(user.totp_enabled)
            self.assertIsNone(user.totp_secret)

    def test_backup_codes(self):
        with self.app.app_context():
            user = self._get_user()
            service = TwoFactorService()
            secret, _ = service.enroll(user)
            totp = __import__("pyotp").totp.TOTP(secret)
            service.enable(user, totp.now())
            codes = service.generate_backup_codes(user)
            self.assertEqual(len(codes), 10)
            self.assertTrue(service.verify_backup_code(user, codes[0]))
            self.assertFalse(service.verify_backup_code(user, "wrong-code"))


class PermissionServiceTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(config_class=TestingConfig)
        with self.app.app_context():
            db.create_all()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_admin_has_all_permissions(self):
        with self.app.app_context():
            user = User(
                email="admin@example.com",
                username="admin",
                password="pass",
                is_admin=True,
            )
            self.assertTrue(has_permission(user, "user:delete"))
            self.assertTrue(has_permission(user, "audit:read"))

    def test_member_has_write_permissions(self):
        with self.app.app_context():
            user = User(
                email="member@example.com",
                username="member",
                password="pass",
            )
            from ..models.role import Role, user_roles

            role = Role.create(name="member")
            user.roles = [role]
            self.assertTrue(has_permission(user, "agent:write"))
            self.assertFalse(has_permission(user, "audit:read"))


class SecurityHeadersTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(config_class=TestingConfig)

    def test_security_headers_present(self):
        with self.app.test_client() as client:
            resp = client.get("/health")
            self.assertEqual(resp.headers.get("X-Content-Type-Options"), "nosniff")
            self.assertEqual(resp.headers.get("X-Frame-Options"), "DENY")
            self.assertIn("Content-Security-Policy", resp.headers)


class CORSConfigurationTestCase(unittest.TestCase):
    def test_default_cors_is_not_wildcard(self):
        from ..config.settings import Config

        self.assertNotEqual(Config.CORS_ORIGINS, ["*"])


class SQLInjectionTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(config_class=TestingConfig)
        with self.app.app_context():
            db.create_all()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_table_name_validation(self):
        from ..services.db_optimization_service import DBOptimizationService

        with self.app.app_context():
            service = DBOptimizationService()
            with self.assertRaises(ValueError):
                service._validate_table_name("evil_table; DROP TABLE users; --")


if __name__ == "__main__":
    unittest.main()
