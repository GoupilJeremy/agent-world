"""Security routes: 2FA, permissions, audit, GDPR."""

from __future__ import annotations

import csv
import io
from datetime import datetime
from typing import Any

from flask import Blueprint, current_app, request
from flask_restful import Resource

from ..models.audit_log import AuditLog
from ..models.base import db
from ..models.role import Role
from ..models.user import User
from ..services.audit_service import audit_service
from ..services.auth_service import AuthenticationError, AuthService
from ..services.gdpr_service import GdprService
from ..services.permission_service import PermissionDeniedError
from ..services.two_factor_service import (
    BackupCodeUsedError,
    TwoFactorDisabledError,
    TwoFactorError,
    TwoFactorRequiredError,
    TwoFactorService,
)

security_bp = Blueprint("security", __name__, url_prefix="/api")

NO_STORE_HEADERS = {
    "Cache-Control": "no-store, max-age=0",
    "Pragma": "no-cache",
    "X-Content-Type-Options": "nosniff",
}


def _auth_service() -> AuthService:
    return current_app.extensions["auth_service"]


def _response(
    data: Any,
    status: int = 200,
    headers: dict[str, str] | None = None,
) -> tuple[Any, int, dict[str, str]]:
    return data, status, headers or dict(NO_STORE_HEADERS)


def _error_response(error: Any) -> tuple[Any, int, dict[str, str]]:
    headers = dict(NO_STORE_HEADERS)
    if getattr(error, "status_code", None) == 401:
        headers["WWW-Authenticate"] = "Bearer"
    return {"error": error.message, "code": error.error_code}, getattr(error, "status_code", 400), headers


class TwoFactorSetupResource(Resource):
    """Start 2FA enrollment by generating a secret and provisioning URI."""

    def post(self) -> tuple[Any, int, dict[str, str]]:
        user = _authenticate()
        service = _two_factor_service()
        secret, uri = service.enroll(user)
        return _response({
            "secret": secret,
            "provisioning_uri": uri,
        })


class TwoFactorEnableResource(Resource):
    """Verify a TOTP code to activate 2FA."""

    def post(self) -> tuple[Any, int, dict[str, str]]:
        user = _authenticate()
        data = request.get_json(silent=True) or {}
        code = data.get("code")
        if not isinstance(code, str):
            return _response({"error": "code is required", "code": "invalid_request"}, 400)
        service = _two_factor_service()
        service.enable(user, code)
        return _response({"totp_enabled": True})


class TwoFactorDisableResource(Resource):
    """Disable 2FA for the current user."""

    def post(self) -> tuple[Any, int, dict[str, str]]:
        user = _authenticate()
        data = request.get_json(silent=True) or {}
        code = data.get("code")
        service = _two_factor_service()
        service.disable(user, code)
        return _response({"totp_enabled": False})


class TwoFactorBackupCodesResource(Resource):
    """Generate new backup codes (replaces existing ones)."""

    def post(self) -> tuple[Any, int, dict[str, str]]:
        user = _authenticate()
        if not user.totp_enabled:
            return _response({"error": "2FA is not enabled", "code": "two_factor_disabled"}, 400)
        service = _two_factor_service()
        codes = service.generate_backup_codes(user)
        return _response({"backup_codes": codes})


class LoginTwoFactorResource(Resource):
    """Step-up login: verify TOTP or backup code after password."""

    def post(self) -> tuple[Any, int, dict[str, str]]:
        data = request.get_json(silent=True) or {}
        identifier = data.get("identifier")
        password = data.get("password")
        code = data.get("code")
        if (
            not isinstance(identifier, str)
            or not isinstance(password, str)
            or not isinstance(code, str)
        ):
            return _response(
                {"error": "identifier, password and code are required", "code": "invalid_request"},
                400,
            )
        auth_service = _auth_service()
        try:
            user = auth_service.authenticate_credentials(identifier, password)
        except AuthenticationError:
            return _response(
                {"error": "Invalid credentials", "code": "invalid_credentials"}, 401
            )
        if not user.totp_enabled:
            return _response(
                {"error": "Two-factor authentication is not enabled for this account", "code": "two_factor_not_enabled"},
                400,
            )
        service = _two_factor_service()
        if service.verify(user, code) or service.verify_backup_code(user, code):
            token = auth_service.issue_access_token(user)
            return _response({
                "access_token": token,
                "token_type": "Bearer",
                "expires_in": auth_service.access_token_ttl_seconds,
                "user": user.to_dict(),
            })
        return _response({"error": "Invalid two-factor code", "code": "invalid_2fa_code"}, 401)


class AccountExportResource(Resource):
    """Export current user's personal data (GDPR)."""

    def get(self) -> tuple[Any, int, dict[str, str]]:
        user = _authenticate()
        gdpr = GdprService()
        return _response(gdpr.export_data(user))


class AccountDeleteResource(Resource):
    """Right to erasure: anonymize current user data."""

    def delete(self) -> tuple[Any, int, dict[str, str]]:
        user = _authenticate()
        gdpr = GdprService()
        gdpr.erase(user)
        return _response({"status": "erased"})


class LegalPrivacyResource(Resource):
    """Return privacy policy text from config."""

    def get(self) -> tuple[Any, int, dict[str, str]]:
        policy = current_app.config.get("PRIVACY_POLICY_TEXT", "Privacy policy not configured.")
        return _response({"policy": policy})


class AdminRoleListResource(Resource):
    """List or create roles."""

    def get(self) -> tuple[Any, int, dict[str, str]]:
        _require_admin()
        return _response({"roles": [role.to_dict() for role in Role.get_all()]})

    def post(self) -> tuple[Any, int, dict[str, str]]:
        _require_admin()
        data = request.get_json(silent=True) or {}
        name = data.get("name")
        permissions = data.get("permissions", [])
        if not isinstance(name, str) or not name.strip():
            return _response({"error": "name is required", "code": "invalid_request"}, 400)
        if Role.get_by_name(name):
            return _response({"error": "Role already exists", "code": "conflict"}, 409)
        role = Role.create(name=name.strip(), permissions=permissions)
        return _response(role.to_dict(), 201)


class AdminUserRolesResource(Resource):
    """Assign or replace roles for a user."""

    def post(self, user_id: int) -> tuple[Any, int, dict[str, str]]:
        _require_admin()
        user = User.query.get(user_id)
        if user is None:
            return _response({"error": "User not found", "code": "not_found"}, 404)
        data = request.get_json(silent=True) or {}
        role_names = data.get("roles", [])
        if not isinstance(role_names, list):
            return _response({"error": "roles must be a list", "code": "invalid_request"}, 400)
        roles = []
        for name in role_names:
            role = Role.get_by_name(name)
            if role is None:
                return _response({"error": f"Role '{name}' not found", "code": "not_found"}, 404)
            roles.append(role)
        user.roles = roles
        db.session.add(user)
        db.session.commit()
        return _response({"user_id": user.id, "roles": [r.to_dict() for r in user.roles]})


class AdminAuditListResource(Resource):
    """List audit logs with optional filters."""

    def get(self) -> tuple[Any, int, dict[str, str]]:
        _require_admin()
        action = request.args.get("action")
        actor_id = request.args.get("actor_id")
        page = int(request.args.get("page", 1))
        per_page = min(int(request.args.get("per_page", 20)), 100)

        query = AuditLog.query.order_by(AuditLog.created_at.desc())
        if action:
            query = query.filter(AuditLog.action == action)
        if actor_id:
            query = query.filter(AuditLog.actor_id == int(actor_id))
        total = query.count()
        items = query.offset((page - 1) * per_page).limit(per_page).all()
        return _response({
            "items": [entry.to_dict() for entry in items],
            "total": total,
            "page": page,
            "per_page": per_page,
        })


class AdminAuditExportResource(Resource):
    """Export audit logs as CSV or JSON."""

    def get(self) -> tuple[Any, int, dict[str, str]]:
        _require_admin()
        fmt = request.args.get("format", "json").lower()
        entries = AuditLog.get_all(limit=1000)
        if fmt == "csv":
            output = io.StringIO()
            writer = csv.DictWriter(output, fieldnames=["id", "actor_id", "action", "resource_type", "resource_id", "ip", "created_at"])
            writer.writeheader()
            for entry in entries:
                writer.writerow({
                    "id": entry.id,
                    "actor_id": entry.actor_id,
                    "action": entry.action,
                    "resource_type": entry.resource_type,
                    "resource_id": entry.resource_id,
                    "ip": entry.ip,
                    "created_at": entry.created_at.isoformat() if entry.created_at else "",
                })
            return _response(output.getvalue(), 200, {"Content-Type": "text/csv"})
        return _response({"items": [entry.to_dict() for entry in entries]})


def _two_factor_service() -> TwoFactorService:
    if "two_factor_service" not in current_app.extensions:
        current_app.extensions["two_factor_service"] = TwoFactorService()
    return current_app.extensions["two_factor_service"]


def _authenticate() -> User:
    auth_service = _auth_service()
    user = auth_service.authenticate_authorization_header(
        request.headers.get("Authorization")
    )
    if user is None:
        raise AuthenticationError("A bearer access token is required")
    return user


def _require_admin() -> None:
    from ..services.permission_service import has_permission
    user = _authenticate()
    if not has_permission(user, "security:manage"):
        raise PermissionDeniedError("Permission denied")


def register_resources(api: Any) -> None:
    api.add_resource(TwoFactorSetupResource, "/auth/2fa/setup")
    api.add_resource(TwoFactorEnableResource, "/auth/2fa/enable")
    api.add_resource(TwoFactorDisableResource, "/auth/2fa/disable")
    api.add_resource(TwoFactorBackupCodesResource, "/auth/2fa/backup-codes")
    api.add_resource(LoginTwoFactorResource, "/auth/login/2fa")
    api.add_resource(AccountExportResource, "/account/export")
    api.add_resource(AccountDeleteResource, "/account")
    api.add_resource(LegalPrivacyResource, "/legal/privacy")
    api.add_resource(AdminRoleListResource, "/admin/roles")
    api.add_resource(AdminUserRolesResource, "/admin/users/<int:user_id>/roles")
    api.add_resource(AdminAuditListResource, "/admin/audit")
    api.add_resource(AdminAuditExportResource, "/admin/audit/export")

