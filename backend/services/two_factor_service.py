# 🔐 Agent World - Two-Factor Authentication Service
# Version: 1.0.0 (EPIC 10 - US-065)
# Description: Service pour gérer l'authentification à deux facteurs (2FA)

"""
Two-Factor Authentication Service for Agent World.

Ce service gère la génération, vérification et validation des codes TOTP
pour l'authentification à deux facteurs des utilisateurs.
"""

import base64
import json
import secrets
from typing import List, Optional, Tuple

import pyotp
from cryptography.fernet import Fernet

from ..models.base import db
from ..models.two_factor_auth import TwoFactorAuth
from ..models.user import User


class TwoFactorServiceError(Exception):
    """Base exception for TwoFactorService errors."""

    status_code = 400
    error_code = "two_factor_error"


class TwoFactorNotEnabledError(TwoFactorServiceError):
    """2FA is not enabled for this user."""

    status_code = 403
    error_code = "two_factor_not_enabled"


class InvalidTwoFactorCodeError(TwoFactorServiceError):
    """The provided 2FA code is invalid."""

    status_code = 401
    error_code = "invalid_two_factor_code"


class RecoveryCodeError(TwoFactorServiceError):
    """Recovery code related error."""

    status_code = 401
    error_code = "recovery_code_error"


class TwoFactorService:
    """
    Service for managing two-factor authentication (TOTP).

    This service handles:
    - Generation and verification of TOTP codes
    - Management of recovery codes
    - Encryption of sensitive data (secret keys, recovery codes)
    """

    # Number of recovery codes to generate
    RECOVERY_CODES_COUNT = 10
    # Length of each recovery code
    RECOVERY_CODE_LENGTH = 12

    def __init__(self, encryption_key: Optional[str] = None):
        """
        Initialize the TwoFactorService.

        Args:
            encryption_key: Optional encryption key for Fernet.
                           If None, a new key will be generated (for testing only).
        """
        if encryption_key:
            self._fernet = Fernet(encryption_key.encode())
        else:
            # Generate a new key for testing/development
            # In production, this should be provided via configuration
            self._fernet = Fernet(Fernet.generate_key())

    def _encrypt(self, data: str) -> str:
        """Encrypt a string using Fernet."""
        return self._fernet.encrypt(data.encode()).decode()

    def _decrypt(self, encrypted_data: str) -> str:
        """Decrypt a string using Fernet."""
        return self._fernet.decrypt(encrypted_data.encode()).decode()

    def generate_secret_key(self) -> str:
        """Generate a new TOTP secret key."""
        return pyotp.random_base32()

    def generate_recovery_codes(self) -> List[str]:
        """Generate a list of recovery codes."""
        return [
            self._generate_single_recovery_code()
            for _ in range(self.RECOVERY_CODES_COUNT)
        ]

    def _generate_single_recovery_code(self) -> str:
        """Generate a single recovery code."""
        # Use a readable format: XXXX-XXXX-XXXX
        parts = []
        for _ in range(3):
            part = secrets.token_urlsafe(self.RECOVERY_CODE_LENGTH // 3).replace("-", "")
            parts.append(part.upper()[:4])
        return "-".join(parts)

    def generate_totp_uri(self, secret_key: str, user_email: str, issuer: str = "Agent World") -> str:
        """
        Generate a TOTP URI for QR code generation.

        Args:
            secret_key: The TOTP secret key (base32 encoded)
            user_email: User's email (used as account name)
            issuer: The issuer name (default: "Agent World")

        Returns:
            A TOTP URI string (otpauth://totp/...)
        """
        return pyotp.totp.TOTP(secret_key).provisioning_uri(
            name=user_email,
            issuer_name=issuer,
        )

    def generate_qr_code_uri(
        self, secret_key: str, user_email: str, issuer: str = "Agent World"
    ) -> str:
        """
        Generate a QR code URI for easy scanning.

        Args:
            secret_key: The TOTP secret key (base32 encoded)
            user_email: User's email
            issuer: The issuer name

        Returns:
            A data URI for the QR code image (PNG)
        """
        import qrcode
        import io

        totp_uri = self.generate_totp_uri(secret_key, user_email, issuer)
        
        # Generate QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(totp_uri)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to PNG bytes
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)
        
        # Encode as base64 data URI
        img_base64 = base64.b64encode(buffer.getvalue()).decode()
        return f"data:image/png;base64,{img_base64}"

    def setup_two_factor(self, user: User) -> Tuple[str, str, List[str]]:
        """
        Set up two-factor authentication for a user.

        Args:
            user: The user to set up 2FA for

        Returns:
            Tuple of (secret_key, totp_uri, recovery_codes)
        """
        # Generate secret key
        secret_key = self.generate_secret_key()
        
        # Generate recovery codes
        recovery_codes = self.generate_recovery_codes()
        
        # Encrypt sensitive data
        encrypted_secret = self._encrypt(secret_key)
        encrypted_recovery_codes = [self._encrypt(code) for code in recovery_codes]
        
        # Create or update TwoFactorAuth record
        tfa = TwoFactorAuth.query.filter_by(user_id=user.id).first()
        if tfa:
            tfa.secret_key = encrypted_secret
            tfa.recovery_codes_list = encrypted_recovery_codes
            tfa.is_enabled = False  # Not enabled until verified
            tfa.updated_at = db.func.now()
        else:
            tfa = TwoFactorAuth(
                user_id=user.id,
                secret_key=encrypted_secret,
                is_enabled=False,
                recovery_codes=encrypted_recovery_codes,
            )
            db.session.add(tfa)
        db.session.commit()
        
        # Generate TOTP URI for QR code
        totp_uri = self.generate_totp_uri(secret_key, user.email)
        
        return secret_key, totp_uri, recovery_codes

    def verify_two_factor_code(self, user: User, code: str) -> bool:
        """
        Verify a TOTP code for a user.

        Args:
            user: The user to verify
            code: The TOTP code to verify

        Returns:
            True if the code is valid, False otherwise
        """
        tfa = TwoFactorAuth.query.filter_by(user_id=user.id).first()
        if not tfa or not tfa.is_enabled:
            raise TwoFactorNotEnabledError("2FA is not enabled for this user")
        
        # Decrypt the secret key
        secret_key = self._decrypt(tfa.secret_key)
        
        # Verify the code
        totp = pyotp.TOTP(secret_key)
        return totp.verify(code)

    def verify_and_enable_two_factor(self, user: User, code: str) -> bool:
        """
        Verify a TOTP code and enable 2FA if valid.

        Args:
            user: The user to verify
            code: The TOTP code to verify

        Returns:
            True if the code is valid and 2FA is now enabled
        """
        tfa = TwoFactorAuth.query.filter_by(user_id=user.id).first()
        if not tfa:
            raise TwoFactorServiceError("2FA not set up for this user")
        
        # Decrypt the secret key
        secret_key = self._decrypt(tfa.secret_key)
        
        # Verify the code
        totp = pyotp.TOTP(secret_key)
        if not totp.verify(code):
            raise InvalidTwoFactorCodeError("Invalid 2FA code")
        
        # Enable 2FA
        tfa.enable()
        return True

    def verify_recovery_code(self, user: User, code: str) -> bool:
        """
        Verify a recovery code for a user.

        Args:
            user: The user to verify
            code: The recovery code to verify

        Returns:
            True if the code is valid and has been used
        """
        tfa = TwoFactorAuth.query.filter_by(user_id=user.id).first()
        if not tfa:
            raise TwoFactorServiceError("2FA not set up for this user")
        
        # Decrypt all recovery codes
        decrypted_codes = [self._decrypt(c) for c in tfa.recovery_codes_list]
        
        if code not in decrypted_codes:
            raise RecoveryCodeError("Invalid recovery code")
        
        # Use the recovery code (removes it)
        encrypted_code_to_remove = tfa.recovery_codes_list[decrypted_codes.index(code)]
        tfa.recovery_codes_list.remove(encrypted_code_to_remove)
        db.session.commit()
        
        return True

    def disable_two_factor(self, user: User) -> bool:
        """
        Disable two-factor authentication for a user.

        Args:
            user: The user to disable 2FA for

        Returns:
            True if 2FA was disabled
        """
        tfa = TwoFactorAuth.query.filter_by(user_id=user.id).first()
        if not tfa:
            return False
        
        tfa.disable()
        return True

    def get_two_factor_status(self, user: User) -> dict:
        """
        Get the 2FA status for a user.

        Args:
            user: The user to check

        Returns:
            Dictionary with 2FA status information
        """
        tfa = TwoFactorAuth.query.filter_by(user_id=user.id).first()
        if not tfa:
            return {"enabled": False, "setup_required": True}
        
        return {
            "enabled": tfa.is_enabled,
            "setup_required": False,
            "recovery_codes_count": len(tfa.recovery_codes_list),
        }

    def regenerate_recovery_codes(self, user: User) -> List[str]:
        """
        Regenerate recovery codes for a user.

        Args:
            user: The user to regenerate codes for

        Returns:
            List of new recovery codes (plain text)
        """
        tfa = TwoFactorAuth.query.filter_by(user_id=user.id).first()
        if not tfa:
            raise TwoFactorServiceError("2FA not set up for this user")
        
        # Generate new recovery codes
        new_codes = self.generate_recovery_codes()
        encrypted_codes = [self._encrypt(code) for code in new_codes]
        
        # Update the recovery codes
        tfa.recovery_codes_list = encrypted_codes
        db.session.commit()
        
        return new_codes

    @staticmethod
    def is_two_factor_enabled(user: User) -> bool:
        """
        Check if 2FA is enabled for a user.

        Args:
            user: The user to check

        Returns:
            True if 2FA is enabled
        """
        return TwoFactorAuth.is_enabled_for_user(user.id)
