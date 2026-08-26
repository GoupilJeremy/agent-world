# 🛡️ Agent World - GDPR Routes
# Version: 1.0.0 (EPIC 10 - US-069)
# Description: Endpoints API pour la conformité RGPD

"""
GDPR Routes for Agent World.

Ces endpoints permettent aux utilisateurs et administrateurs de:
- Gérer les consentements (opt-in/opt-out)
- Soumettre des demandes d'accès et de suppression
- Exporter leurs données personnelles
- Consulter la politique de confidentialité
"""

from __future__ import annotations

from functools import wraps
from typing import Any, Callable

from flask import current_app, request
from flask_restful import Resource

from ..models.base import db
from ..models.gdpr_compliance import (
    ConsentType,
    DataSubjectRequest,
    GDPRConsent,
    PrivacyPolicyVersion,
    RequestType,
)
from ..models.user import User
from ..services.audit_service import AuditAction, AuditResourceType
from ..services.auth_service import AuthenticationError, AuthService
from ..services.gdpr_service import (
    GDPRAccessDeniedError,
    GDPRConsentError,
    GDPRError,
    GDPRNotFoundError,
    GDPRRequestError,
    GDPRService,
)
from ..services.permission_service import (
    PermissionDeniedError,
    PermissionService,
)

NO_STORE_HEADERS = {
    "Cache-Control": "no-store, max-age=0",
    "Pragma": "no-cache",
    "X-Content-Type-Options": "nosniff",
}


def _auth_service() -> AuthService:
    return current_app.extensions["auth_service"]


def _gdpr_service() -> GDPRService:
    return current_app.extensions["gdpr_service"]


def _permission_service() -> PermissionService:
    return current_app.extensions["permission_service"]


def _audit_service() -> Any:
    return current_app.extensions.get("audit_service")


def _response(
    data: Any,
    status: int = 200,
    headers: dict[str, str] | None = None,
) -> tuple[Any, int, dict[str, str]]:
    return data, status, headers or dict(NO_STORE_HEADERS)


def gdpr_errors(function: Callable[..., Any]) -> Callable[..., Any]:
    """Handle GDPR-related errors and return appropriate responses."""

    @wraps(function)
    def wrapped(*args: Any, **kwargs: Any) -> Any:
        try:
            return function(*args, **kwargs)
        except (GDPRError, GDPRConsentError, GDPRRequestError, GDPRNotFoundError) as exc:
            db.session.rollback()
            headers = dict(NO_STORE_HEADERS)
            if exc.status_code == 401:
                headers["WWW-Authenticate"] = "Bearer"
            return _response(
                {"error": exc.args[0] if exc.args else "GDPR error", "code": exc.error_code},
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
        except PermissionDeniedError as exc:
            db.session.rollback()
            headers = dict(NO_STORE_HEADERS)
            if exc.status_code == 401:
                headers["WWW-Authenticate"] = "Bearer"
            return _response(
                {"error": exc.args[0] if exc.args else "Permission denied", "code": exc.error_code},
                exc.status_code,
                headers,
            )
        except Exception as exc:
            db.session.rollback()
            return _response(
                {"error": str(exc), "code": "internal_error"},
                500,
                dict(NO_STORE_HEADERS),
            )

    return wrapped


def get_current_user() -> User:
    """Get the current authenticated user from the request headers."""
    auth_header = request.headers.get("Authorization")
    user = _auth_service().authenticate_authorization_header(auth_header)
    if user is None:
        raise AuthenticationError("A bearer access token is required")
    return user


def require_gdpr_admin(f: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator to require GDPR admin privileges."""

    @wraps(f)
    def wrapped(*args: Any, **kwargs: Any) -> Any:
        user = get_current_user()
        if not _permission_service().has_permission(user.id, "gdpr:admin"):
            raise PermissionDeniedError("GDPR admin privileges required")
        return f(*args, **kwargs)

    return wrapped


# ==================== Consent Resources ====================

class ConsentListResource(Resource):
    """List and manage user consents."""

    @gdpr_errors
    def get(self) -> tuple[Any, int, dict[str, str]]:
        """Get all consents for the current user."""
        user = get_current_user()
        consents = _gdpr_service().get_all_consents(user.id)
        return _response({
            "consents": [c.to_dict() for c in consents],
            "count": len(consents),
        })

    @gdpr_errors
    def post(self) -> tuple[Any, int, dict[str, str]]:
        """Grant consent for a specific type."""
        user = get_current_user()
        data = request.get_json(silent=True)
        
        if not isinstance(data, dict):
            return _response(
                {"error": "A JSON object is required", "code": "invalid_request"},
                400,
            )
        
        consent_type = data.get("consent_type")
        version = data.get("version")
        consent_text = data.get("consent_text")
        
        if not consent_type:
            return _response(
                {"error": "consent_type is required", "code": "invalid_request"},
                400,
            )
        
        # Check if this is a valid consent type
        if consent_type not in [ct.value for ct in ConsentType]:
            return _response(
                {"error": f"Invalid consent type: {consent_type}", "code": "invalid_consent_type"},
                400,
            )
        
        consent = _gdpr_service().grant_consent(
            user_id=user.id,
            consent_type=consent_type,
            version=version,
            consent_text=consent_text,
        )
        
        # Audit log
        try:
            _audit_service().log_from_request(
                action=AuditAction.SETTING_UPDATED,
                user=user,
                resource_type=AuditResourceType.USER,
                resource_id=user.id,
                resource_name=f"Consent: {consent_type}",
                extra_data={"consent_type": consent_type, "status": "granted"},
            )
        except Exception:
            pass  # Don't fail if audit logging fails
        
        return _response({
            "message": "Consent granted successfully",
            "consent": consent.to_dict(),
        }, 201)


class ConsentResource(Resource):
    """Get or revoke a specific consent."""

    @gdpr_errors
    def get(self, consent_type: str) -> tuple[Any, int, dict[str, str]]:
        """Get consent for a specific type."""
        user = get_current_user()
        consent = _gdpr_service().get_consent(user.id, consent_type)
        
        if consent is None:
            return _response(
                {"error": "Consent not found", "code": "consent_not_found"},
                404,
            )
        
        return _response(consent.to_dict())

    @gdpr_errors
    def delete(self, consent_type: str) -> tuple[Any, int, dict[str, str]]:
        """Revoke consent for a specific type."""
        user = get_current_user()
        consent = _gdpr_service().revoke_consent(user.id, consent_type)
        
        # Audit log
        try:
            _audit_service().log_from_request(
                action=AuditAction.SETTING_UPDATED,
                user=user,
                resource_type=AuditResourceType.USER,
                resource_id=user.id,
                resource_name=f"Consent: {consent_type}",
                extra_data={"consent_type": consent_type, "status": "revoked"},
            )
        except Exception:
            pass
        
        return _response({
            "message": "Consent revoked successfully",
            "consent": consent.to_dict(),
        })


class ConsentCheckResource(Resource):
    """Check if user has a specific consent."""

    @gdpr_errors
    def get(self, consent_type: str) -> tuple[Any, int, dict[str, str]]:
        """Check if current user has consent for a type."""
        user = get_current_user()
        has_consent = _gdpr_service().has_consent(user.id, consent_type)
        return _response({
            "consent_type": consent_type,
            "has_consent": has_consent,
        })


class ConsentTypesResource(Resource):
    """Get all available consent types."""

    @gdpr_errors
    def get(self) -> tuple[Any, int, dict[str, str]]:
        """Get all available consent types."""
        consent_types = [ct.value for ct in ConsentType]
        return _response({
            "consent_types": consent_types,
            "count": len(consent_types),
        })


class RequiredConsentsResource(Resource):
    """Check all required consents for the current user."""

    @gdpr_errors
    def get(self) -> tuple[Any, int, dict[str, str]]:
        """Check all required consents."""
        user = get_current_user()
        consents = _gdpr_service().check_required_consents(user.id)
        return _response({
            "user_id": user.id,
            "consents": consents,
            "all_granted": all(c["has_consent"] for c in consents.values() if c["is_required"]),
        })


# ==================== Data Subject Request Resources ====================

class RequestListResource(Resource):
    """List data subject requests for the current user."""

    @gdpr_errors
    def get(self) -> tuple[Any, int, dict[str, str]]:
        """Get all requests for the current user."""
        user = get_current_user()
        requests = _gdpr_service().get_user_requests(user.id)
        return _response({
            "requests": [r.to_dict() for r in requests],
            "count": len(requests),
        })

    @gdpr_errors
    def post(self) -> tuple[Any, int, dict[str, str]]:
        """Create a new data subject request."""
        user = get_current_user()
        data = request.get_json(silent=True)
        
        if not isinstance(data, dict):
            return _response(
                {"error": "A JSON object is required", "code": "invalid_request"},
                400,
            )
        
        request_type = data.get("request_type")
        description = data.get("description")
        data_scope = data.get("data_scope")
        
        if not request_type:
            return _response(
                {"error": "request_type is required", "code": "invalid_request"},
                400,
            )
        
        if request_type not in [rt.value for rt in RequestType]:
            return _response(
                {"error": f"Invalid request type: {request_type}", "code": "invalid_request_type"},
                400,
            )
        
        dsr = _gdpr_service().create_request(
            user_id=user.id,
            request_type=request_type,
            description=description,
            data_scope=data_scope,
        )
        
        # Audit log
        try:
            _audit_service().log_from_request(
                action=AuditAction.SETTING_UPDATED,
                user=user,
                resource_type=AuditResourceType.USER,
                resource_id=user.id,
                resource_name=f"DSR: {request_type}",
                extra_data={"request_type": request_type, "request_id": dsr.request_id},
            )
        except Exception:
            pass
        
        return _response({
            "message": "Data subject request created successfully",
            "request": dsr.to_dict(),
        }, 201)


class RequestResource(Resource):
    """Get or update a specific data subject request."""

    @gdpr_errors
    def get(self, request_id: str) -> tuple[Any, int, dict[str, str]]:
        """Get a specific request by request_id."""
        user = get_current_user()
        dsr = _gdpr_service().get_request(request_id)
        
        # Check if user owns this request or is admin
        if dsr.user_id != user.id and not _permission_service().has_permission(user.id, "gdpr:admin"):
            raise GDPRAccessDeniedError("You can only access your own requests")
        
        return _response(dsr.to_dict())


class RequestExportResource(Resource):
    """Export user data (droit d'accès)."""

    @gdpr_errors
    def get(self) -> tuple[Any, int, dict[str, str]]:
        """Export all personal data for the current user."""
        user = get_current_user()
        
        # Check if user has any pending access requests
        pending_requests = _gdpr_service().get_user_requests(user.id)
        pending_access = [r for r in pending_requests if r.request_type == "access" and r.status == "pending"]
        
        if pending_access:
            return _response(
                {
                    "error": "You have a pending access request. Please wait for it to be processed.",
                    "code": "pending_request",
                    "pending_request_id": pending_access[0].request_id,
                },
                409,
            )
        
        # Collect user data
        try:
            data = _gdpr_service().collect_user_data(user.id)
        except GDPRNotFoundError:
            return _response(
                {"error": "User not found", "code": "user_not_found"},
                404,
            )
        
        # Audit log
        try:
            _audit_service().log_from_request(
                action=AuditAction.BACKUP_CREATED,
                user=user,
                resource_type=AuditResourceType.USER,
                resource_id=user.id,
                resource_name="Personal Data Export",
                extra_data={"data_types": list(data.get("data", {}).keys())},
            )
        except Exception:
            pass
        
        # Return as JSON
        headers = {
            **NO_STORE_HEADERS,
            "Content-Type": "application/json; charset=utf-8",
            "Content-Disposition": f"attachment; filename=user_{user.id}_data_export_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json",
        }
        
        import json
        return _response(
            json.dumps(data, indent=2, ensure_ascii=False, default=str),
            200,
            headers,
        )


class MyDataResource(Resource):
    """Get user's personal data in a structured format."""

    @gdpr_errors
    def get(self) -> tuple[Any, int, dict[str, str]]:
        """Get the current user's personal data."""
        user = get_current_user()
        
        # Build data response
        data = _gdpr_service().collect_user_data(user.id)
        
        return _response({
            "user_id": user.id,
            "export_date": data.get("export_date"),
            "data": data.get("data", {}),
        })


# ==================== Admin Resources ====================

class AdminRequestListResource(Resource):
    """Admin: List all data subject requests."""

    @gdpr_errors
    @require_gdpr_admin
    def get(self) -> tuple[Any, int, dict[str, str]]:
        """Get all requests (admin only)."""
        status = request.args.get("status")
        request_type = request.args.get("type")
        limit = request.args.get("limit", 100, type=int)
        
        query = DataSubjectRequest.query.order_by(DataSubjectRequest.created_at.desc())
        
        if status:
            query = query.filter_by(status=status)
        
        if request_type:
            query = query.filter_by(request_type=request_type)
        
        requests = query.limit(limit).all()
        
        return _response({
            "requests": [r.to_dict() for r in requests],
            "count": len(requests),
            "total": query.count(),
        })


class AdminRequestActionResource(Resource):
    """Admin: Process a data subject request."""

    @gdpr_errors
    @require_gdpr_admin
    def post(self, request_id: str, action: str) -> tuple[Any, int, dict[str, str]]:
        """Process a request (approve, reject, mark as processing)."""
        user = get_current_user()
        data = request.get_json(silent=True) or {}
        
        dsr = _gdpr_service().get_request(request_id)
        
        # Map action to status
        status_map = {
            "process": "processing",
            "approve": "completed",
            "complete": "completed",
            "reject": "rejected",
            "verify": "verified",
        }
        
        if action not in status_map:
            return _response(
                {"error": f"Invalid action: {action}", "code": "invalid_action"},
                400,
            )
        
        status = status_map[action]
        processing_notes = data.get("processing_notes")
        
        # For access and erasure requests, use specific methods
        if dsr.request_type == "access" and action in ["approve", "complete"]:
            dsr = _gdpr_service().process_access_request(
                request_id=request_id,
                processed_by=user.id,
            )
        elif dsr.request_type == "erasure" and action in ["approve", "complete"]:
            hard_delete = data.get("hard_delete", False)
            dsr = _gdpr_service().process_erasure_request(
                request_id=request_id,
                processed_by=user.id,
                hard_delete=hard_delete,
            )
        else:
            dsr = _gdpr_service().update_request_status(
                request_id=request_id,
                status=status,
                processed_by=user.id,
                processing_notes=processing_notes,
            )
        
        # Audit log
        try:
            _audit_service().log_from_request(
                action=AuditAction.SETTING_UPDATED,
                user=user,
                resource_type=AuditResourceType.USER,
                resource_id=dsr.user_id,
                resource_name=f"DSR: {dsr.request_type}",
                extra_data={"request_id": request_id, "action": action, "status": status},
            )
        except Exception:
            pass
        
        return _response({
            "message": f"Request {action}d successfully",
            "request": dsr.to_dict(),
        })


class AdminRequestStatsResource(Resource):
    """Admin: Get GDPR compliance statistics."""

    @gdpr_errors
    @require_gdpr_admin
    def get(self) -> tuple[Any, int, dict[str, str]]:
        """Get compliance statistics."""
        stats = _gdpr_service().get_compliance_stats()
        return _response(stats)


# ==================== Privacy Policy Resources ====================

class PrivacyPolicyResource(Resource):
    """Get the active privacy policy."""

    @gdpr_errors
    def get(self) -> tuple[Any, int, dict[str, str]]:
        """Get the currently active privacy policy."""
        policy = _gdpr_service().get_active_policy()
        
        if policy is None:
            return _response(
                {"error": "No active privacy policy found", "code": "no_active_policy"},
                404,
            )
        
        return _response(policy.to_dict())


class PrivacyPolicyVersionResource(Resource):
    """Get a specific privacy policy version."""

    @gdpr_errors
    def get(self, version: str) -> tuple[Any, int, dict[str, str]]:
        """Get a specific policy version."""
        policy = _gdpr_service().get_policy_version(version)
        return _response(policy.to_dict())


class PrivacyPolicyVersionsResource(Resource):
    """Get all privacy policy versions."""

    @gdpr_errors
    def get(self) -> tuple[Any, int, dict[str, str]]:
        """Get all policy versions."""
        policies = _gdpr_service().get_all_policies(limit=100)
        return _response({
            "policies": [p.to_dict() for p in policies],
            "count": len(policies),
        })


class PrivacyPolicyAcceptResource(Resource):
    """Accept the current privacy policy."""

    @gdpr_errors
    def post(self) -> tuple[Any, int, dict[str, str]]:
        """Accept the current privacy policy."""
        user = get_current_user()
        
        active_policy = _gdpr_service().get_active_policy()
        if not active_policy:
            return _response(
                {"error": "No active privacy policy to accept", "code": "no_active_policy"},
                400,
            )
        
        # Grant consent for privacy policy
        consent = _gdpr_service().grant_consent(
            user_id=user.id,
            consent_type="privacy_policy",
            version=active_policy.version,
        )
        
        # Audit log
        try:
            _audit_service().log_from_request(
                action=AuditAction.SETTING_UPDATED,
                user=user,
                resource_type=AuditResourceType.USER,
                resource_id=user.id,
                resource_name="Privacy Policy Acceptance",
                extra_data={"policy_version": active_policy.version},
            )
        except Exception:
            pass
        
        return _response({
            "message": "Privacy policy accepted successfully",
            "policy_version": active_policy.version,
            "consent": consent.to_dict(),
        }, 201)


class UserComplianceResource(Resource):
    """Get compliance status for the current user."""

    @gdpr_errors
    def get(self) -> tuple[Any, int, dict[str, str]]:
        """Get compliance status."""
        user = get_current_user()
        compliance = _gdpr_service().check_user_compliance(user.id)
        return _response(compliance)


# ==================== Register GDPR Resources ====================

def register_gdpr_resources(api: Any) -> None:
    """Register the GDPR API resources."""

    # Consent resources
    api.add_resource(
        ConsentListResource,
        "/gdpr/consents",
        endpoint="gdpr_consent_list",
    )
    api.add_resource(
        ConsentResource,
        "/gdpr/consents/<string:consent_type>",
        endpoint="gdpr_consent",
    )
    api.add_resource(
        ConsentCheckResource,
        "/gdpr/consents/<string:consent_type>/check",
        endpoint="gdpr_consent_check",
    )
    api.add_resource(
        ConsentTypesResource,
        "/gdpr/consent-types",
        endpoint="gdpr_consent_types",
    )
    api.add_resource(
        RequiredConsentsResource,
        "/gdpr/consents/required",
        endpoint="gdpr_required_consents",
    )

    # Data Subject Request resources
    api.add_resource(
        RequestListResource,
        "/gdpr/requests",
        endpoint="gdpr_request_list",
    )
    api.add_resource(
        RequestResource,
        "/gdpr/requests/<string:request_id>",
        endpoint="gdpr_request",
    )
    api.add_resource(
        RequestExportResource,
        "/gdpr/my-data/export",
        endpoint="gdpr_data_export",
    )
    api.add_resource(
        MyDataResource,
        "/gdpr/my-data",
        endpoint="gdpr_my_data",
    )

    # Admin resources
    api.add_resource(
        AdminRequestListResource,
        "/admin/gdpr/requests",
        endpoint="admin_gdpr_requests",
    )
    api.add_resource(
        AdminRequestActionResource,
        "/admin/gdpr/requests/<string:request_id>/<string:action>",
        endpoint="admin_gdpr_request_action",
    )
    api.add_resource(
        AdminRequestStatsResource,
        "/admin/gdpr/stats",
        endpoint="admin_gdpr_stats",
    )

    # Privacy policy resources
    api.add_resource(
        PrivacyPolicyResource,
        "/gdpr/privacy-policy",
        endpoint="gdpr_privacy_policy",
    )
    api.add_resource(
        PrivacyPolicyVersionResource,
        "/gdpr/privacy-policy/<string:version>",
        endpoint="gdpr_privacy_policy_version",
    )
    api.add_resource(
        PrivacyPolicyVersionsResource,
        "/gdpr/privacy-policy/versions",
        endpoint="gdpr_privacy_policy_versions",
    )
    api.add_resource(
        PrivacyPolicyAcceptResource,
        "/gdpr/privacy-policy/accept",
        endpoint="gdpr_privacy_policy_accept",
    )

    # Compliance resource
    api.add_resource(
        UserComplianceResource,
        "/gdpr/compliance",
        endpoint="gdpr_compliance",
    )


# Import datetime for use in routes
from datetime import datetime
