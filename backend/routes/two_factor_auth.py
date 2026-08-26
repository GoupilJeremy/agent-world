# 🔐 Agent World - Two-Factor Authentication Routes
# Version: 1.0.0 (EPIC 10 - US-065)
# Description: Endpoints API pour la gestion de l'authentification à deux facteurs

"""
Two-Factor Authentication Routes for Agent World.

Ces endpoints permettent aux utilisateurs de :
- Configurer la 2FA (génération de clé secrète et codes de secours)
- Vérifier un code 2FA
- Activer/Désactiver la 2FA
- Utiliser un code de secours
- Obtenir le statut de la 2FA
"""

from __future__ import annotations

from functools import wraps
from typing import Any, Callable

from flask import current_app, request
from flask_restful import Resource

from ..models.base import db
from ..models.user import User
from ..services.auth_service import AuthenticationError, AuthService
from ..services.two_factor_service import (
    InvalidTwoFactorCodeError,
    RecoveryCodeError,
    TwoFactorNotEnabledError,
    TwoFactorService,
    TwoFactorServiceError,
)

NO_STORE_HEADERS = {
    "Cache-Control": "no-store, max-age=0",
    "Pragma": "no-cache",
    "X-Content-Type-Options": "nosniff",
}


def _auth_service() -> AuthService:
    return current_app.extensions["auth_service"]


def _two_factor_service() -> TwoFactorService:
    return current_app.extensions["two_factor_service"]


def _response(
    data: Any,
    status: int = 200,
    headers: dict[str, str] | None = None,
) -> tuple[Any, int, dict[str, str]]:
    return data, status, headers or dict(NO_STORE_HEADERS)


def two_factor_errors(function: Callable[..., Any]) -> Callable[..., Any]:
    """Handle 2FA-specific errors and return appropriate responses."""

    @wraps(function)
    def wrapped(*args: Any, **kwargs: Any) -> Any:
        try:
            return function(*args, **kwargs)
        except TwoFactorServiceError as exc:
            db.session.rollback()
            headers = dict(NO_STORE_HEADERS)
            if exc.status_code == 401:
                headers["WWW-Authenticate"] = "Bearer"
            return _response(
                {"error": exc.args[0] if exc.args else "Two-factor authentication error", "code": exc.error_code},
                exc.status_code,
                headers,
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


def get_current_user() -> User:
    """Get the current authenticated user from the request headers."""
    auth_header = request.headers.get("Authorization")
    user = _auth_service().authenticate_authorization_header(auth_header)
    if user is None:
        raise AuthenticationError("A bearer access token is required")
    return user


class TwoFactorSetupResource(Resource):
    """Generate a new 2FA secret and recovery codes for the user."""

    @two_factor_errors
    def post(self) -> tuple[Any, int, dict[str, str]]:
        """
        Set up two-factor authentication for the current user.
        Generates a secret key and recovery codes.
        
        Returns:
            - secret_key: The TOTP secret key (base32 encoded)
            - qr_code_uri: Data URI for the QR code image
            - recovery_codes: List of recovery codes
        """
        user = get_current_user()
        
        secret_key, totp_uri, recovery_codes = _two_factor_service().setup_two_factor(user)
        qr_code_uri = _two_factor_service().generate_qr_code_uri(
            secret_key, user.email
        )
        
        return _response({
            "message": "2FA setup generated. Scan the QR code with your authenticator app.",
            "secret_key": secret_key,
            "qr_code_uri": qr_code_uri,
            "recovery_codes": recovery_codes,
            "recovery_codes_count": len(recovery_codes),
        })


class TwoFactorVerifyResource(Resource):
    """Verify a 2FA code and enable 2FA for the user."""

    @two_factor_errors
    def post(self) -> tuple[Any, int, dict[str, str]]:
        """
        Verify a TOTP code and enable 2FA for the current user.
        
        Request body:
            - code: The TOTP code from the authenticator app
        """
        user = get_current_user()
        data = request.get_json(silent=True)
        
        if not isinstance(data, dict):
            return _response(
                {"error": "A JSON object is required", "code": "invalid_request"},
                400,
            )
        
        code = data.get("code")
        if not isinstance(code, str) or not code.strip():
            return _response(
                {"error": "A valid 2FA code is required", "code": "invalid_request"},
                400,
            )
        
        _two_factor_service().verify_and_enable_two_factor(user, code.strip())
        
        return _response({
            "message": "2FA enabled successfully",
            "enabled": True,
        })


class TwoFactorVerifyCodeResource(Resource):
    """Verify a 2FA code without enabling (for login flow)."""

    @two_factor_errors
    def post(self) -> tuple[Any, int, dict[str, str]]:
        """
        Verify a TOTP code for the current user (for login flow).
        
        Request body:
            - code: The TOTP code from the authenticator app
        """
        user = get_current_user()
        data = request.get_json(silent=True)
        
        if not isinstance(data, dict):
            return _response(
                {"error": "A JSON object is required", "code": "invalid_request"},
                400,
            )
        
        code = data.get("code")
        if not isinstance(code, str) or not code.strip():
            return _response(
                {"error": "A valid 2FA code is required", "code": "invalid_request"},
                400,
            )
        
        is_valid = _two_factor_service().verify_two_factor_code(user, code.strip())
        
        return _response({
            "valid": is_valid,
        })


class TwoFactorRecoveryCodeResource(Resource):
    """Verify and use a recovery code."""

    @two_factor_errors
    def post(self) -> tuple[Any, int, dict[str, str]]:
        """
        Verify and use a recovery code for the current user.
        
        Request body:
            - recovery_code: The recovery code to use
        """
        user = get_current_user()
        data = request.get_json(silent=True)
        
        if not isinstance(data, dict):
            return _response(
                {"error": "A JSON object is required", "code": "invalid_request"},
                400,
            )
        
        recovery_code = data.get("recovery_code")
        if not isinstance(recovery_code, str) or not recovery_code.strip():
            return _response(
                {"error": "A valid recovery code is required", "code": "invalid_request"},
                400,
            )
        
        _two_factor_service().verify_recovery_code(user, recovery_code.strip())
        
        return _response({
            "message": "Recovery code used successfully",
            "valid": True,
        })


class TwoFactorDisableResource(Resource):
    """Disable two-factor authentication for the user."""

    @two_factor_errors
    def post(self) -> tuple[Any, int, dict[str, str]]:
        """
        Disable 2FA for the current user.
        
        Request body:
            - password: User's password (for confirmation)
        """
        user = get_current_user()
        data = request.get_json(silent=True)
        
        if not isinstance(data, dict):
            return _response(
                {"error": "A JSON object is required", "code": "invalid_request"},
                400,
            )
        
        password = data.get("password")
        if not isinstance(password, str) or not password.strip():
            return _response(
                {"error": "Password is required to disable 2FA", "code": "invalid_request"},
                400,
            )
        
        # Verify password before disabling 2FA
        if not user.check_password(password):
            return _response(
                {"error": "Invalid password", "code": "invalid_password"},
                401,
            )
        
        _two_factor_service().disable_two_factor(user)
        
        return _response({
            "message": "2FA disabled successfully",
            "enabled": False,
        })


class TwoFactorStatusResource(Resource):
    """Get the 2FA status for the current user."""

    @two_factor_errors
    def get(self) -> tuple[Any, int, dict[str, str]]:
        """Get the 2FA status for the current user."""
        user = get_current_user()
        status = _two_factor_service().get_two_factor_status(user)
        
        return _response(status)


class TwoFactorRecoveryCodesRegenerateResource(Resource):
    """Regenerate recovery codes for the user."""

    @two_factor_errors
    def post(self) -> tuple[Any, int, dict[str, str]]:
        """
        Regenerate recovery codes for the current user.
        
        Request body:
            - password: User's password (for confirmation)
        """
        user = get_current_user()
        data = request.get_json(silent=True)
        
        if not isinstance(data, dict):
            return _response(
                {"error": "A JSON object is required", "code": "invalid_request"},
                400,
            )
        
        password = data.get("password")
        if not isinstance(password, str) or not password.strip():
            return _response(
                {"error": "Password is required to regenerate recovery codes", "code": "invalid_request"},
                400,
            )
        
        # Verify password before regenerating codes
        if not user.check_password(password):
            return _response(
                {"error": "Invalid password", "code": "invalid_password"},
                401,
            )
        
        new_codes = _two_factor_service().regenerate_recovery_codes(user)
        
        return _response({
            "message": "Recovery codes regenerated successfully",
            "recovery_codes": new_codes,
            "recovery_codes_count": len(new_codes),
        })


def register_two_factor_resources(api: Any) -> None:
    """Register the 2FA API resources."""
    api.add_resource(
        TwoFactorSetupResource,
        "/auth/2fa/setup",
        endpoint="two_factor_setup",
    )
    api.add_resource(
        TwoFactorVerifyResource,
        "/auth/2fa/verify",
        endpoint="two_factor_verify",
    )
    api.add_resource(
        TwoFactorVerifyCodeResource,
        "/auth/2fa/verify-code",
        endpoint="two_factor_verify_code",
    )
    api.add_resource(
        TwoFactorRecoveryCodeResource,
        "/auth/2fa/recovery",
        endpoint="two_factor_recovery",
    )
    api.add_resource(
        TwoFactorDisableResource,
        "/auth/2fa/disable",
        endpoint="two_factor_disable",
    )
    api.add_resource(
        TwoFactorStatusResource,
        "/auth/2fa/status",
        endpoint="two_factor_status",
    )
    api.add_resource(
        TwoFactorRecoveryCodesRegenerateResource,
        "/auth/2fa/recovery-codes/regenerate",
        endpoint="two_factor_recovery_codes_regenerate",
    )
