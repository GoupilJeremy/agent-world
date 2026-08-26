"""GDPR / RGPD data export and erasure service."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict

from ..models.agent_history import AgentHistory
from ..models.audit_log import AuditLog
from ..models.base import db
from ..models.user import User


class GdprService:
    """Export and erase personal user data while preserving compliance records."""

    def export_data(self, user: User) -> Dict[str, Any]:
        return {
            "user": user.to_dict(),
            "agents": [agent.to_dict() for agent in getattr(user, "agents", [])],
            "projects": [
                project.to_dict() for project in getattr(user, "projects", [])
            ],
            "executions": [
                execution.to_dict() for execution in getattr(user, "executions", [])
            ],
            "agent_histories": [
                h.to_dict() for h in AgentHistory.get_by_author(user.id)
            ],
            "audit_logs": [log.to_dict() for log in AuditLog.get_by_actor(user.id)],
            "exported_at": datetime.utcnow().isoformat(),
        }

    def erase(self, user: User) -> None:
        user.email = f"deleted-{user.id}@deleted.local"
        user.username = f"deleted-{user.id}"
        user.first_name = None
        user.last_name = None
        user.password_hash = ""
        user.is_active = False
        user.totp_secret = None
        user.totp_enabled = False
        user.totp_verified_at = None
        user.backup_codes = None
        user.consent_given_at = None
        user.data_deleted_at = datetime.utcnow()
        db.session.add(user)
        db.session.commit()
