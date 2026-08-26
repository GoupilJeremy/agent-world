# 📋 Agent World - Audit Routes
# Version: 1.0.0 (EPIC 10 - US-068)
# Description: Endpoints API pour gérer l'audit des actions utilisateurs

"""
Audit Routes for Agent World.

Ces endpoints permettent aux administrateurs de:
- Lister et consulter les logs d'audit
- Exporter les logs au format JSON ou CSV
- Obtenir des statistiques sur les activités
- Rechercher dans les logs
- Nettoyer les anciens logs
"""

from __future__ import annotations

from functools import wraps
from typing import Any, Callable

from flask import current_app, request
from flask_restful import Resource

from ..models.base import db
from ..services.audit_service import (
    AuditError,
    AuditLogNotFoundError,
    AuditService,
)
from ..services.auth_service import AuthenticationError, AuthService
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


def _audit_service() -> AuditService:
    return current_app.extensions["audit_service"]


def _permission_service() -> PermissionService:
    return current_app.extensions["permission_service"]


def _response(
    data: Any,
    status: int = 200,
    headers: dict[str, str] | None = None,
) -> tuple[Any, int, dict[str, str]]:
    return data, status, headers or dict(NO_STORE_HEADERS)


def audit_errors(function: Callable[..., Any]) -> Callable[..., Any]:
    """Handle audit-related errors and return appropriate responses."""

    @wraps(function)
    def wrapped(*args: Any, **kwargs: Any) -> Any:
        try:
            return function(*args, **kwargs)
        except (AuditError, AuditLogNotFoundError) as exc:
            db.session.rollback()
            headers = dict(NO_STORE_HEADERS)
            if exc.status_code == 401:
                headers["WWW-Authenticate"] = "Bearer"
            return _response(
                {"error": exc.args[0] if exc.args else "Audit error", "code": exc.error_code},
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

    return wrapped


def get_current_user() -> Any:
    """Get the current authenticated user from the request headers."""
    auth_header = request.headers.get("Authorization")
    user = _auth_service().authenticate_authorization_header(auth_header)
    if user is None:
        raise AuthenticationError("A bearer access token is required")
    return user


def require_admin(f: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator to require admin privileges for audit operations."""

    @wraps(f)
    def wrapped(*args: Any, **kwargs: Any) -> Any:
        user = get_current_user()
        if not _permission_service().is_admin(user.id):
            raise PermissionDeniedError("Admin privileges required for audit operations")
        return f(*args, **kwargs)

    return wrapped


def require_audit_access(f: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator to require audit read access."""

    @wraps(f)
    def wrapped(*args: Any, **kwargs: Any) -> Any:
        user = get_current_user()
        # Check if user has audit read permission
        if not _permission_service().has_permission(user.id, "audit:read"):
            raise PermissionDeniedError("Audit read permission required")
        return f(*args, **kwargs)

    return wrapped


# ==================== Audit Log Resources ====================

class AuditLogListResource(Resource):
    """List and search audit logs."""

    @audit_errors
    @require_audit_access
    def get(self) -> tuple[Any, int, dict[str, str]]:
        """Get a list of audit logs with optional filters."""
        # Parse query parameters
        user_id = request.args.get("user_id", type=int)
        action = request.args.get("action")
        resource_type = request.args.get("resource_type")
        resource_id = request.args.get("resource_id", type=int)
        status = request.args.get("status")
        start_date = request.args.get("start_date")
        end_date = request.args.get("end_date")
        search = request.args.get("search")
        limit = request.args.get("limit", 100, type=int)
        offset = request.args.get("offset", 0, type=int)

        # Convert date strings to datetime objects
        from datetime import datetime
        start_date_dt = None
        end_date_dt = None

        if start_date:
            try:
                start_date_dt = datetime.fromisoformat(start_date)
            except ValueError:
                start_date_dt = datetime.strptime(start_date, "%Y-%m-%d")

        if end_date:
            try:
                end_date_dt = datetime.fromisoformat(end_date)
            except ValueError:
                end_date_dt = datetime.strptime(end_date, "%Y-%m-%d")

        if search:
            # Use search functionality
            logs = _audit_service().search_logs(search, limit=limit)
            total = len(logs)
        else:
            # Use filtered query
            logs = _audit_service().get_logs(
                user_id=user_id,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                start_date=start_date_dt,
                end_date=end_date_dt,
                status=status,
                limit=limit,
                offset=offset,
            )
            # Count total matching logs
            total = _audit_service().get_logs(
                user_id=user_id,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                start_date=start_date_dt,
                end_date=end_date_dt,
                status=status,
                limit=10000,  # Large limit to count
                offset=0,
            )
            total = len(total)

        return _response({
            "logs": [log.to_dict() for log in logs],
            "count": len(logs),
            "total": total,
            "limit": limit,
            "offset": offset,
        })


class AuditLogResource(Resource):
    """Get a specific audit log entry."""

    @audit_errors
    @require_audit_access
    def get(self, log_id: int) -> tuple[Any, int, dict[str, str]]:
        """Get a specific audit log entry by ID."""
        log = _audit_service().get_log(log_id)
        return _response(log.to_dict())


class AuditLogRecentResource(Resource):
    """Get recent audit logs."""

    @audit_errors
    @require_audit_access
    def get(self) -> tuple[Any, int, dict[str, str]]:
        """Get the most recent audit logs."""
        limit = request.args.get("limit", 100, type=int)
        logs = _audit_service().get_recent_logs(limit=limit)
        return _response({
            "logs": [log.to_dict() for log in logs],
            "count": len(logs),
        })


class AuditLogUserResource(Resource):
    """Get audit logs for a specific user."""

    @audit_errors
    @require_audit_access
    def get(self, user_id: int) -> tuple[Any, int, dict[str, str]]:
        """Get audit logs for a specific user."""
        limit = request.args.get("limit", 100, type=int)
        logs = _audit_service().get_logs_by_user(user_id, limit=limit)
        return _response({
            "user_id": user_id,
            "logs": [log.to_dict() for log in logs],
            "count": len(logs),
        })


class AuditLogActionResource(Resource):
    """Get audit logs for a specific action."""

    @audit_errors
    @require_audit_access
    def get(self, action: str) -> tuple[Any, int, dict[str, str]]:
        """Get audit logs for a specific action."""
        limit = request.args.get("limit", 100, type=int)
        logs = _audit_service().get_logs_by_action(action, limit=limit)
        return _response({
            "action": action,
            "logs": [log.to_dict() for log in logs],
            "count": len(logs),
        })


# ==================== Audit Statistics Resources ====================

class AuditStatisticsResource(Resource):
    """Get audit statistics."""

    @audit_errors
    @require_audit_access
    def get(self) -> tuple[Any, int, dict[str, str]]:
        """Get statistics about audit logs."""
        stats = _audit_service().get_statistics()
        return _response(stats)


# ==================== Audit Export Resources ====================

class AuditExportResource(Resource):
    """Export audit logs to JSON or CSV format."""

    @audit_errors
    @require_admin
    def get(self) -> tuple[Any, int, dict[str, str]]:
        """Export audit logs to the specified format."""
        format_type = request.args.get("format", "json")
        user_id = request.args.get("user_id", type=int)
        action = request.args.get("action")
        start_date = request.args.get("start_date")
        end_date = request.args.get("end_date")
        limit = request.args.get("limit", 10000, type=int)

        # Convert date strings to datetime objects
        from datetime import datetime
        start_date_dt = None
        end_date_dt = None

        if start_date:
            try:
                start_date_dt = datetime.fromisoformat(start_date)
            except ValueError:
                start_date_dt = datetime.strptime(start_date, "%Y-%m-%d")

        if end_date:
            try:
                end_date_dt = datetime.fromisoformat(end_date)
            except ValueError:
                end_date_dt = datetime.strptime(end_date, "%Y-%m-%d")

        if format_type == "csv":
            export_data = _audit_service().export_to_csv(
                user_id=user_id,
                action=action,
                start_date=start_date_dt,
                end_date=end_date_dt,
                limit=limit,
            )
            headers = {
                **NO_STORE_HEADERS,
                "Content-Type": "text/csv; charset=utf-8",
                "Content-Disposition": "attachment; filename=audit_logs.csv",
            }
            return _response(export_data, 200, headers)
        else:
            # Default to JSON
            export_data = _audit_service().export_to_json(
                user_id=user_id,
                action=action,
                start_date=start_date_dt,
                end_date=end_date_dt,
                limit=limit,
            )
            headers = {
                **NO_STORE_HEADERS,
                "Content-Type": "application/json; charset=utf-8",
                "Content-Disposition": "attachment; filename=audit_logs.json",
            }
            return _response(export_data, 200, headers)


# ==================== Audit Cleanup Resources ====================

class AuditCleanupResource(Resource):
    """Clean up old audit logs."""

    @audit_errors
    @require_admin
    def delete(self) -> tuple[Any, int, dict[str, str]]:
        """Clear old audit logs."""
        days = request.args.get("days", 90, type=int)
        deleted_count = _audit_service().clear_old_logs(days=days)
        return _response({
            "message": f"Cleared {deleted_count} old audit logs",
            "days": days,
            "deleted_count": deleted_count,
        })


class AuditClearAllResource(Resource):
    """Clear all audit logs (dangerous operation)."""

    @audit_errors
    @require_admin
    def delete(self) -> tuple[Any, int, dict[str, str]]:
        """Clear ALL audit logs. This is a dangerous operation."""
        deleted_count = _audit_service().clear_all_logs()
        return _response({
            "message": f"Cleared ALL {deleted_count} audit logs",
            "deleted_count": deleted_count,
            "warning": "All audit logs have been permanently deleted",
        })


# ==================== Audit Actions Resource ====================

class AuditActionsResource(Resource):
    """Get list of all available audit actions."""

    @audit_errors
    @require_audit_access
    def get(self) -> tuple[Any, int, dict[str, str]]:
        """Get all available audit actions from AuditAction enum."""
        from ..models.audit_log import AuditAction
        actions = AuditAction.get_all_values()
        return _response({
            "actions": sorted(actions),
            "count": len(actions),
        })


class AuditResourceTypesResource(Resource):
    """Get list of all available resource types."""

    @audit_errors
    @require_audit_access
    def get(self) -> tuple[Any, int, dict[str, str]]:
        """Get all available resource types from AuditResourceType enum."""
        from ..models.audit_log import AuditResourceType
        resource_types = AuditResourceType.__members__.keys()
        return _response({
            "resource_types": sorted(resource_types),
            "count": len(resource_types),
        })


# ==================== Register Audit Resources ====================

def register_audit_resources(api: Any) -> None:
    """Register the audit API resources."""

    # Audit log resources
    api.add_resource(
        AuditLogListResource,
        "/audit/logs",
        endpoint="audit_log_list",
    )
    api.add_resource(
        AuditLogResource,
        "/audit/logs/<int:log_id>",
        endpoint="audit_log",
    )
    api.add_resource(
        AuditLogRecentResource,
        "/audit/logs/recent",
        endpoint="audit_log_recent",
    )
    api.add_resource(
        AuditLogUserResource,
        "/audit/users/<int:user_id>/logs",
        endpoint="audit_log_user",
    )
    api.add_resource(
        AuditLogActionResource,
        "/audit/actions/<string:action>/logs",
        endpoint="audit_log_action",
    )

    # Statistics resource
    api.add_resource(
        AuditStatisticsResource,
        "/audit/statistics",
        endpoint="audit_statistics",
    )

    # Export resource
    api.add_resource(
        AuditExportResource,
        "/audit/logs/export",
        endpoint="audit_export",
    )

    # Cleanup resources
    api.add_resource(
        AuditCleanupResource,
        "/audit/logs/cleanup",
        endpoint="audit_cleanup",
    )
    api.add_resource(
        AuditClearAllResource,
        "/audit/logs/clear-all",
        endpoint="audit_clear_all",
    )

    # Reference data resources
    api.add_resource(
        AuditActionsResource,
        "/audit/actions",
        endpoint="audit_actions",
    )
    api.add_resource(
        AuditResourceTypesResource,
        "/audit/resource-types",
        endpoint="audit_resource_types",
    )
