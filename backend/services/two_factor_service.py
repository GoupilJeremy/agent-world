"""Two-factor authentication service using TOTP and backup codes."""

from __future__ import annotations

import hashlib
import hmac
import secrets
from datetime import datetime
from typing import Optional

import pyotp

from ..models.user import User
from ..services.encryption_service import get_encryption_service


class TwoFactorError(RuntimeError):
    status_code = 400
    error_code = "two_factor_error"


class TwoFactorDisabledError(TwoFactorError):
    error_code = "two_factor_disabled"


class TwoFactorRequiredError(TwoFactorError):
    status_code = 401
    error_code = "two_factor_required"


class BackupCodeUsedError(TwoFactorError):
    error_code = "backup_code_used"


def _constant_time_compare(a: str, b: str) -> bool:
    return hmac.compare_digest(a.encode(), b.encode())


class TwoFactorService:
    """Manage TOTP enrollment, verification, and backup codes."""

    def __init__(self) -> None:
        self._encryption = get_encryption_service()

    def enroll(self, user: User) -> tuple[str, str]:
        if user.totp_enabled:
            raise TwoFactorError("Two-factor authentication is already enabled")
        secret = pyotp.random_base32()
        provisioning_uri = pyotp.totp.TOTP(secret).provisioning_uri(
            name=user.email,
            issuer_name="Agent World",
        )
        user.totp_secret = self._encryption.encrypt(secret)
        db.session.add(user)
        db.session.commit()
        return secret, provisioning_uri

    def verify(self, user: User, code: str) -> bool:
        if not user.totp_secret:
            raise TwoFactorDisabledError("Two-factor authentication is not enrolled")
        secret = self._encryption.decrypt(user.totp_secret)
        totp = pyotp.TOTP(secret)
        return bool(totp.verify(code))

    def enable(self, user: User, code: str) -> None:
        if not self.verify(user, code):
            raise TwoFactorError("Invalid two-factor authentication code")
        user.totp_enabled = True
        user.totp_verified_at = datetime.utcnow()
        db.session.add(user)
        db.session.commit()

    def disable(self, user: User, code: Optional[str] = None) -> None:
        if code is not None and not self.verify(user, code):
            raise TwoFactorError("Invalid two-factor authentication code")
        user.totp_enabled = False
        user.totp_verified_at = None
        user.totp_secret = None
        user.backup_codes = None
        db.session.add(user)
        db.session.commit()

    def generate_backup_codes(self, user: User, count: int = 10) -> list[str]:
        if not user.totp_enabled:
            raise TwoFactorDisabledError("Two-factor authentication is not enabled")
        raw_codes = [secrets.token_hex(4) for _ in range(count)]
        hashed = [hashlib.sha256(code.encode()).hexdigest() for code in raw_codes]
        user.backup_codes = hashed
        db.session.add(user)
        db.session.commit()
        return raw_codes

    def verify_backup_code(self, user: User, code: str) -> bool:
        if not user.backup_codes:
            return False
        hashed = hashlib.sha256(code.encode()).hexdigest()
        codes = list(user.backup_codes)
        for index, stored in enumerate(codes):
            if _constant_time_compare(stored, hashed):
                user.backup_codes = codes[:index] + codes[index + 1 :]
                db.session.add(user)
                db.session.commit()
                return True
        return False


from ..models.base import db  # noqa: E402  # avoid circular import
