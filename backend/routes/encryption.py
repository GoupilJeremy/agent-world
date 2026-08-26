# 🔐 Agent World - Encryption Routes
# Version: 1.0.0 (EPIC 10 - US-067)
# Description: Endpoints API pour gérer le chiffrement

"""
Encryption Routes for Agent World.

Ces endpoints permettent aux administrateurs de :
- Gérer les clés de chiffrement
- Roter les clés de chiffrement
- Chiffrer/déchiffrer des données
"""

from __future__ import annotations

from functools import wraps
from typing import Any, Callable

from flask import current_app, request
from flask_restful import Resource

from ..models.base import db
from ..services.auth_service import AuthenticationError, AuthService
from ..services.encryption_service import (
    DecryptionError,
    EncryptionError,
    EncryptionService,
    KeyRotationError,
)
from ..services.permission_service import PermissionDeniedError, PermissionService

NO_STORE_HEADERS = {
    "Cache-Control": "no-store, max-age=0",
    "Pragma": "no-cache",
    "X-Content-Type-Options": "nosniff",
}


def _auth_service() -> AuthService:
    return current_app.extensions["auth_service"]


def _encryption_service() -> EncryptionService:
    return current_app.extensions["encryption_service"]


def _permission_service() -> PermissionService:
    return current_app.extensions["permission_service"]


def _response(
    data: Any,
    status: int = 200,
    headers: dict[str, str] | None = None,
) -> tuple[Any, int, dict[str, str]]:
    return data, status, headers or dict(NO_STORE_HEADERS)


def encryption_errors(function: Callable[..., Any]) -> Callable[..., Any]:
    """Handle encryption-related errors."""

    @wraps(function)
    def wrapped(*args: Any, **kwargs: Any) -> Any:
        try:
            return function(*args, **kwargs)
        except (EncryptionError, DecryptionError, KeyRotationError) as exc:
            db.session.rollback()
            return _response(
                {"error": exc.args[0] if exc.args else "Encryption error", "code": exc.error_code},
                exc.status_code,
            )
        except PermissionDeniedError as exc:
            db.session.rollback()
            return _response(
                {"error": exc.args[0] if exc.args else "Permission denied", "code": exc.error_code},
                exc.status_code,
            )
        except AuthenticationError as exc:
            db.session.rollback()
            headers = dict(NO_STORE_HEADERS)
            if exc.status_code == 401:
                headers["WWW-Authenticate"] = "Bearer"
            return _response(
                {"error": exc.message, "code": exc.error_code},
                exc.status_code,
                headers,
            )

    return wrapped


def get_current_user():
    """Get the current authenticated user."""
    auth_header = request.headers.get("Authorization")
    user = _auth_service().authenticate_authorization_header(auth_header)
    if user is None:
        raise AuthenticationError("A bearer access token is required")
    return user


def require_admin(f: Callable[..., Any]) -> Callable[..., Any]:
    """Require admin privileges."""

    @wraps(f)
    def wrapped(*args: Any, **kwargs: Any) -> Any:
        user = get_current_user()
        if not _permission_service().is_admin(user.id):
            raise PermissionDeniedError("Admin privileges required")
        return f(*args, **kwargs)

    return wrapped


class EncryptionKeyListResource(Resource):
    """List all encryption keys."""

    @encryption_errors
    @require_admin
    def get(self) -> tuple[Any, int, dict[str, str]]:
        """Get list of all encryption keys."""
        from ..models.encryption_key import EncryptionKey
        
        keys = EncryptionKey.get_all_versions()
        
        return _response({
            "keys": [k.to_dict() for k in keys],
            "count": len(keys),
            "active_key": _encryption_service().get_active_key().to_dict(),
        })


class EncryptionKeyResource(Resource):
    """Get information about the active encryption key."""

    @encryption_errors
    @require_admin
    def get(self) -> tuple[Any, int, dict[str, str]]:
        """Get information about the active encryption key."""
        key = _encryption_service().get_active_key()
        return _response(key.to_dict())


class RotateKeyResource(Resource):
    """Rotate the encryption key."""

    @encryption_errors
    @require_admin
    def post(self) -> tuple[Any, int, dict[str, str]]:
        """Create a new encryption key and make it active."""
        data = request.get_json(silent=True) or {}
        description = data.get("description", "Manual rotation")
        ttl_days = data.get("ttl_days")
        
        key = _encryption_service().rotate_key(
            description=description,
            ttl_days=ttl_days,
        )
        
        return _response({
            "message": "Encryption key rotated successfully",
            "key": key.to_dict(),
        })


class EncryptionStatusResource(Resource):
    """Check encryption service status."""

    @encryption_errors
    @require_admin
    def get(self) -> tuple[Any, int, dict[str, str]]:
        """Check if key rotation is needed."""
        needs_rotation = _encryption_service().needs_rotation()
        active_key = _encryption_service().get_active_key()
        
        return _response({
            "status": "healthy",
            "active_key_version": active_key.version,
            "active_key_expires_at": active_key.expires_at.isoformat() if active_key.expires_at else None,
            "needs_rotation": needs_rotation,
            "key_count": len(EncryptionKey.get_all_versions()),
        })


class EncryptResource(Resource):
    """Encrypt data (for testing and internal use)."""

    @encryption_errors
    @require_admin
    def post(self) -> tuple[Any, int, dict[str, str]]:
        """Encrypt a string."""
        data = request.get_json(silent=True)
        
        if not isinstance(data, dict):
            return _response(
                {"error": "A JSON object is required", "code": "invalid_request"},
                400,
            )
        
        plaintext = data.get("data")
        if not isinstance(plaintext, str) or not plaintext:
            return _response(
                {"error": "Data to encrypt is required", "code": "invalid_request"},
                400,
            )
        
        encrypted = _encryption_service().encrypt(plaintext)
        
        return _response({
            "plaintext": _encryption_service().mask_sensitive_data(plaintext),
            "encrypted": encrypted,
        })


class DecryptResource(Resource):
    """Decrypt data (for testing and internal use)."""

    @encryption_errors
    @require_admin
    def post(self) -> tuple[Any, int, dict[str, str]]:
        """Decrypt a string."""
        data = request.get_json(silent=True)
        
        if not isinstance(data, dict):
            return _response(
                {"error": "A JSON object is required", "code": "invalid_request"},
                400,
            )
        
        encrypted = data.get("encrypted_data")
        if not isinstance(encrypted, str) or not encrypted:
            return _response(
                {"error": "Encrypted data is required", "code": "invalid_request"},
                400,
            )
        
        try:
            decrypted = _encryption_service().decrypt(encrypted)
            return _response({
                "encrypted": _encryption_service().mask_sensitive_data(encrypted),
                "decrypted": decrypted,
            })
        except DecryptionError as e:
            return _response(
                {"error": str(e), "code": "decryption_failed"},
                400,
            )


class MaskDataResource(Resource):
    """Mask sensitive data for display."""

    @encryption_errors
    def post(self) -> tuple[Any, int, dict[str, str]]:
        """Mask sensitive data."""
        data = request.get_json(silent=True)
        
        if not isinstance(data, dict):
            return _response(
                {"error": "A JSON object is required", "code": "invalid_request"},
                400,
            )
        
        sensitive_data = data.get("data")
        mask_char = data.get("mask_char", "*")
        show_last = data.get("show_last", 4)
        
        if not isinstance(sensitive_data, str):
            return _response(
                {"error": "Data to mask must be a string", "code": "invalid_request"},
                400,
            )
        
        masked = _encryption_service().mask_sensitive_data(
            sensitive_data, mask_char, show_last
        )
        
        return _response({
            "original": _encryption_service().mask_sensitive_data(sensitive_data),
            "masked": masked,
        })


def register_encryption_resources(api: Any) -> None:
    """Register the encryption API resources."""
    api.add_resource(
        EncryptionKeyListResource,
        "/encryption/keys",
        endpoint="encryption_keys",
    )
    api.add_resource(
        EncryptionKeyResource,
        "/encryption/key",
        endpoint="encryption_key",
    )
    api.add_resource(
        RotateKeyResource,
        "/encryption/key/rotate",
        endpoint="rotate_key",
    )
    api.add_resource(
        EncryptionStatusResource,
        "/encryption/status",
        endpoint="encryption_status",
    )
    api.add_resource(
        EncryptResource,
        "/encryption/encrypt",
        endpoint="encrypt",
    )
    api.add_resource(
        DecryptResource,
        "/encryption/decrypt",
        endpoint="decrypt",
    )
    api.add_resource(
        MaskDataResource,
        "/encryption/mask",
        endpoint="mask_data",
    )
