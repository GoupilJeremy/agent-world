"""Encryption service for sensitive data using Fernet (AES-256-CBC + HMAC-SHA256)."""

from __future__ import annotations

import base64
import os
from typing import Optional

from cryptography.fernet import Fernet, InvalidToken


class EncryptionError(RuntimeError):
    """Raised when encryption or decryption fails."""


class EncryptionService:
    """Fernet-based encryption service for sensitive data at rest."""

    def __init__(self, key: Optional[str] = None) -> None:
        if key is None:
            key = os.environ.get("ENCRYPTION_KEY")
        if not key:
            raise EncryptionError("ENCRYPTION_KEY is required")
        try:
            base64.urlsafe_b64decode(key.encode())
        except Exception as exc:
            raise EncryptionError(
                "ENCRYPTION_KEY must be a valid base64 url-safe 32-byte key"
            ) from exc
        self._fernet = Fernet(key.encode())

    def encrypt(self, plaintext: str) -> str:
        if not isinstance(plaintext, str):
            raise TypeError("plaintext must be a string")
        return self._fernet.encrypt(plaintext.encode()).decode()

    def decrypt(self, ciphertext: str) -> str:
        if not isinstance(ciphertext, str):
            raise TypeError("ciphertext must be a string")
        try:
            return self._fernet.decrypt(ciphertext.encode()).decode()
        except InvalidToken as exc:
            raise EncryptionError("Invalid ciphertext or wrong key") from exc

    @staticmethod
    def generate_key() -> str:
        return Fernet.generate_key().decode()


_encryption_service: Optional[EncryptionService] = None


def get_encryption_service() -> EncryptionService:
    global _encryption_service
    if _encryption_service is None:
        _encryption_service = EncryptionService()
    return _encryption_service
