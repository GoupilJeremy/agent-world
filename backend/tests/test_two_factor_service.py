# 🧪 Agent World - Two-Factor Authentication Service Tests
# Version: 1.0.0 (EPIC 10 - US-065)
# Description: Tests unitaires pour le service TwoFactorService

"""
Unit tests for TwoFactorService.

Ces tests couvrent:
- Génération des clés secrètes TOTP
- Génération des codes de secours
- Chiffrement/déchiffrement des données
- Configuration de la 2FA
- Vérification des codes 2FA
- Vérification des codes de secours
- Gestion des codes de secours
"""

import json
import unittest
from unittest.mock import MagicMock, patch

from backend.app import create_app
from backend.models.base import db
from backend.models.user import User
from backend.services.two_factor_service import (
    InvalidTwoFactorCodeError,
    RecoveryCodeError,
    TwoFactorNotEnabledError,
    TwoFactorService,
    TwoFactorServiceError,
)


class TestTwoFactorService(unittest.TestCase):
    """Test cases for TwoFactorService."""

    def setUp(self):
        """Set up test fixtures."""
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
        self.app.config["AUTO_CREATE_DB"] = True
        
        self.client = self.app.test_client()
        
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
            
            # Create TwoFactorService with a test encryption key
            self.encryption_key = Fernet.generate_key().decode()
            self.two_factor_service = TwoFactorService(
                encryption_key=self.encryption_key
            )

    def tearDown(self):
        """Clean up test fixtures."""
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    @patch("backend.services.two_factor_service.pyotp")
    def test_generate_secret_key(self, mock_pyotp):
        """Test generating a TOTP secret key."""
        mock_pyotp.random_base32.return_value = "TESTSECRETKEY123"
        
        secret_key = self.two_factor_service.generate_secret_key()
        
        self.assertEqual(secret_key, "TESTSECRETKEY123")
        mock_pyotp.random_base32.assert_called_once()

    def test_generate_recovery_codes(self):
        """Test generating recovery codes."""
        codes = self.two_factor_service.generate_recovery_codes()
        
        self.assertEqual(len(codes), TwoFactorService.RECOVERY_CODES_COUNT)
        
        # Each code should be in the format XXXX-XXXX-XXXX
        for code in codes:
            parts = code.split("-")
            self.assertEqual(len(parts), 3)
            for part in parts:
                self.assertEqual(len(part), 4)
                self.assertTrue(part.isupper())

    def test_encrypt_decrypt(self):
        """Test encryption and decryption of data."""
        original_data = "Test secret data"
        
        encrypted = self.two_factor_service._encrypt(original_data)
        decrypted = self.two_factor_service._decrypt(encrypted)
        
        self.assertEqual(decrypted, original_data)

    def test_generate_totp_uri(self):
        """Test generating a TOTP URI."""
        secret_key = "TESTSECRETKEY123"
        user_email = "test@example.com"
        issuer = "Agent World"
        
        uri = self.two_factor_service.generate_totp_uri(
            secret_key, user_email, issuer
        )
        
        self.assertTrue(uri.startswith("otpauth://totp/"))
        self.assertIn(issuer, uri)
        self.assertIn(user_email, uri)

    @patch("backend.services.two_factor_service.qrcode")
    @patch("backend.services.two_factor_service.io")
    def test_generate_qr_code_uri(self, mock_io, mock_qrcode):
        """Test generating a QR code data URI."""
        # Mock QRCode
        mock_qr = MagicMock()
        mock_qrcode.QRCode.return_value = mock_qr
        
        # Mock the image
        mock_img = MagicMock()
        mock_qr.make_image.return_value = mock_img
        
        # Mock BytesIO
        mock_buffer = MagicMock()
        mock_io.BytesIO.return_value = mock_buffer
        mock_buffer.getvalue.return_value = b"test_png_data"
        
        secret_key = "TESTSECRETKEY123"
        user_email = "test@example.com"
        
        uri = self.two_factor_service.generate_qr_code_uri(secret_key, user_email)
        
        self.assertTrue(uri.startswith("data:image/png;base64,"))

    def test_setup_two_factor(self):
        """Test setting up 2FA for a user."""
        with self.app.app_context():
            secret_key, totp_uri, recovery_codes = (
                self.two_factor_service.setup_two_factor(self.user)
            )
            
            # Check that secret key is generated
            self.assertIsNotNone(secret_key)
            self.assertTrue(len(secret_key) > 0)
            
            # Check that TOTP URI is generated
            self.assertIsNotNone(totp_uri)
            self.assertTrue(totp_uri.startswith("otpauth://totp/"))
            
            # Check that recovery codes are generated
            self.assertEqual(len(recovery_codes), TwoFactorService.RECOVERY_CODES_COUNT)
            
            # Check that TwoFactorAuth record is created in database
            from backend.models.two_factor_auth import TwoFactorAuth
            tfa = TwoFactorAuth.query.filter_by(user_id=self.user.id).first()
            self.assertIsNotNone(tfa)
            self.assertFalse(tfa.is_enabled)

    @patch("backend.services.two_factor_service.pyotp")
    def test_verify_and_enable_two_factor(self, mock_pyotp):
        """Test verifying and enabling 2FA."""
        with self.app.app_context():
            # First, set up 2FA
            secret_key, _, _ = self.two_factor_service.setup_two_factor(self.user)
            
            # Mock TOTP verification to return True
            mock_totp = MagicMock()
            mock_totp.verify.return_value = True
            mock_pyotp.TOTP.return_value = mock_totp
            
            # Verify and enable
            result = self.two_factor_service.verify_and_enable_two_factor(
                self.user, "123456"
            )
            
            self.assertTrue(result)
            
            # Check that 2FA is now enabled
            from backend.models.two_factor_auth import TwoFactorAuth
            tfa = TwoFactorAuth.query.filter_by(user_id=self.user.id).first()
            self.assertTrue(tfa.is_enabled)

    @patch("backend.services.two_factor_service.pyotp")
    def test_verify_and_enable_two_factor_invalid_code(self, mock_pyotp):
        """Test verifying and enabling 2FA with invalid code."""
        with self.app.app_context():
            # First, set up 2FA
            self.two_factor_service.setup_two_factor(self.user)
            
            # Mock TOTP verification to return False
            mock_totp = MagicMock()
            mock_totp.verify.return_value = False
            mock_pyotp.TOTP.return_value = mock_totp
            
            # Verify and enable should raise exception
            with self.assertRaises(InvalidTwoFactorCodeError):
                self.two_factor_service.verify_and_enable_two_factor(
                    self.user, "invalid_code"
                )

    def test_verify_two_factor_code_not_enabled(self):
        """Test verifying 2FA code when 2FA is not enabled."""
        with self.app.app_context():
            # Set up 2FA but don't enable it
            self.two_factor_service.setup_two_factor(self.user)
            
            # Verify should raise exception
            with self.assertRaises(TwoFactorNotEnabledError):
                self.two_factor_service.verify_two_factor_code(self.user, "123456")

    def test_verify_recovery_code(self):
        """Test verifying a recovery code."""
        with self.app.app_context():
            # Set up 2FA
            _, _, recovery_codes = self.two_factor_service.setup_two_factor(self.user)
            
            # Enable 2FA first (for this test, we'll manually enable it)
            from backend.models.two_factor_auth import TwoFactorAuth
            tfa = TwoFactorAuth.query.filter_by(user_id=self.user.id).first()
            tfa.enable()
            
            # Use the first recovery code
            first_code = recovery_codes[0]
            result = self.two_factor_service.verify_recovery_code(
                self.user, first_code
            )
            
            self.assertTrue(result)
            
            # Check that the recovery code was removed
            tfa = TwoFactorAuth.query.filter_by(user_id=self.user.id).first()
            self.assertNotIn(first_code, tfa.recovery_codes_list)

    def test_disable_two_factor(self):
        """Test disabling 2FA."""
        with self.app.app_context():
            # Set up and enable 2FA
            self.two_factor_service.setup_two_factor(self.user)
            from backend.models.two_factor_auth import TwoFactorAuth
            tfa = TwoFactorAuth.query.filter_by(user_id=self.user.id).first()
            tfa.enable()
            
            # Disable 2FA
            result = self.two_factor_service.disable_two_factor(self.user)
            
            self.assertTrue(result)
            
            # Check that 2FA is now disabled
            tfa = TwoFactorAuth.query.filter_by(user_id=self.user.id).first()
            self.assertFalse(tfa.is_enabled)

    def test_get_two_factor_status_not_setup(self):
        """Test getting 2FA status when not set up."""
        with self.app.app_context():
            # User has no 2FA set up
            status = self.two_factor_service.get_two_factor_status(self.user)
            
            self.assertEqual(status["enabled"], False)
            self.assertEqual(status["setup_required"], True)

    def test_get_two_factor_status_enabled(self):
        """Test getting 2FA status when enabled."""
        with self.app.app_context():
            # Set up and enable 2FA
            self.two_factor_service.setup_two_factor(self.user)
            from backend.models.two_factor_auth import TwoFactorAuth
            tfa = TwoFactorAuth.query.filter_by(user_id=self.user.id).first()
            tfa.enable()
            
            status = self.two_factor_service.get_two_factor_status(self.user)
            
            self.assertEqual(status["enabled"], True)
            self.assertEqual(status["setup_required"], False)
            self.assertEqual(status["recovery_codes_count"], TwoFactorService.RECOVERY_CODES_COUNT)

    def test_regenerate_recovery_codes(self):
        """Test regenerating recovery codes."""
        with self.app.app_context():
            # Set up 2FA
            _, _, original_codes = self.two_factor_service.setup_two_factor(self.user)
            
            # Regenerate codes
            new_codes = self.two_factor_service.regenerate_recovery_codes(self.user)
            
            # Check that new codes are generated
            self.assertEqual(len(new_codes), TwoFactorService.RECOVERY_CODES_COUNT)
            
            # Check that new codes are different from original
            self.assertNotEqual(original_codes, new_codes)
            
            # Check that codes are updated in database
            from backend.models.two_factor_auth import TwoFactorAuth
            tfa = TwoFactorAuth.query.filter_by(user_id=self.user.id).first()
            self.assertEqual(tfa.recovery_codes_list, 
                           [self.two_factor_service._encrypt(code) for code in new_codes])

    @patch("backend.services.two_factor_service.TwoFactorAuth")
    def test_is_two_factor_enabled(self, mock_tfa):
        """Test checking if 2FA is enabled for a user."""
        # Mock the query to return a disabled 2FA record
        mock_result = MagicMock()
        mock_result.filter_by.return_value.first.return_value = MagicMock(
            is_enabled=False
        )
        mock_tfa.query = mock_result
        
        from backend.models.user import User
        mock_user = MagicMock(spec=User)
        mock_user.id = 1
        
        result = self.two_factor_service.is_two_factor_enabled(mock_user)
        self.assertFalse(result)


class TestTwoFactorAuthModel(unittest.TestCase):
    """Test cases for TwoFactorAuth model."""

    def setUp(self):
        """Set up test fixtures."""
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
        self.app.config["AUTO_CREATE_DB"] = True
        
        self.client = self.app.test_client()
        
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

    def test_two_factor_auth_creation(self):
        """Test creating a TwoFactorAuth record."""
        from backend.models.two_factor_auth import TwoFactorAuth
        
        with self.app.app_context():
            tfa = TwoFactorAuth(
                user_id=self.user.id,
                secret_key="encrypted_secret",
                is_enabled=False,
                recovery_codes=["code1", "code2", "code3"],
            )
            db.session.add(tfa)
            db.session.commit()
            
            # Check that record is created
            saved_tfa = TwoFactorAuth.query.filter_by(user_id=self.user.id).first()
            self.assertIsNotNone(saved_tfa)
            self.assertEqual(saved_tfa.secret_key, "encrypted_secret")
            self.assertFalse(saved_tfa.is_enabled)

    def test_two_factor_auth_recovery_codes_property(self):
        """Test recovery_codes_list property."""
        from backend.models.two_factor_auth import TwoFactorAuth
        
        with self.app.app_context():
            codes = ["code1", "code2", "code3"]
            tfa = TwoFactorAuth(
                user_id=self.user.id,
                secret_key="encrypted_secret",
                recovery_codes=codes,
            )
            db.session.add(tfa)
            db.session.commit()
            
            # Check that recovery_codes_list returns the list
            self.assertEqual(tfa.recovery_codes_list, codes)

    def test_two_factor_auth_enable_disable(self):
        """Test enable and disable methods."""
        from backend.models.two_factor_auth import TwoFactorAuth
        
        with self.app.app_context():
            tfa = TwoFactorAuth(
                user_id=self.user.id,
                secret_key="encrypted_secret",
                is_enabled=False,
            )
            db.session.add(tfa)
            db.session.commit()
            
            # Test enable
            tfa.enable()
            self.assertTrue(tfa.is_enabled)
            
            # Test disable
            tfa.disable()
            self.assertFalse(tfa.is_enabled)

    def test_two_factor_auth_use_recovery_code(self):
        """Test using a recovery code."""
        from backend.models.two_factor_auth import TwoFactorAuth
        
        with self.app.app_context():
            codes = ["code1", "code2", "code3"]
            tfa = TwoFactorAuth(
                user_id=self.user.id,
                secret_key="encrypted_secret",
                recovery_codes=codes,
            )
            db.session.add(tfa)
            db.session.commit()
            
            # Use a recovery code
            result = tfa.use_recovery_code("code2")
            self.assertTrue(result)
            
            # Check that code is removed
            self.assertNotIn("code2", tfa.recovery_codes_list)
            self.assertEqual(len(tfa.recovery_codes_list), 2)

    def test_two_factor_auth_use_invalid_recovery_code(self):
        """Test using an invalid recovery code."""
        from backend.models.two_factor_auth import TwoFactorAuth
        
        with self.app.app_context():
            codes = ["code1", "code2", "code3"]
            tfa = TwoFactorAuth(
                user_id=self.user.id,
                secret_key="encrypted_secret",
                recovery_codes=codes,
            )
            db.session.add(tfa)
            db.session.commit()
            
            # Try to use an invalid code
            result = tfa.use_recovery_code("invalid_code")
            self.assertFalse(result)


# Import Fernet for test setup
from cryptography.fernet import Fernet


if __name__ == "__main__":
    unittest.main()
