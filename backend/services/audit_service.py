"""Audit logging service for security-relevant actions."""

from __future__ import annotations

from typing import Any, Optional

from ..models.audit_log import AuditLog
from ..models.user import User


class AuditService:
    """Record security and compliance audit events."""

    def record(
        self,
        action: str,
        actor: Optional[User],
        request: Any,
        resource_type: Optional[str] = None,
        resource_id: Optional[int] = None,
        meta: Optional[dict] = None,
    ) -> AuditLog:
        user_agent = None
        if getattr(request, "user_agent", None) is not None:
            user_agent = (
                request.user_agent.string
                if hasattr(request.user_agent, "string")
                else str(request.user_agent)
            )
        return AuditLog.create(
            actor_id=actor.id if actor else None,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            ip=getattr(request, "remote_addr", None),
            user_agent=user_agent,
            meta=meta,
        )


audit_service = AuditService()


def audit(action: str, resource_type: Optional[str] = None):
    def decorator(function):
        def wrapper(*args, **kwargs):
            from flask import request

            result = function(*args, **kwargs)
            user = kwargs.get("user")
            audit_service.record(
                action=action,
                actor=user,
                request=request,
                resource_type=resource_type,
                meta={"route": request.path},
            )
            return result

        return wrapper

    return decorator
