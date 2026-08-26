"""Audit log model for security events."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from .base import BaseModel, db


class AuditLog(BaseModel):
    """Immutable record of a security-relevant action."""

    __tablename__ = "audit_logs"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    actor_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    action = db.Column(db.String(255), nullable=False)
    resource_type = db.Column(db.String(100), nullable=True)
    resource_id = db.Column(db.Integer, nullable=True)
    ip = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.String(255), nullable=True)
    meta = db.Column(db.JSON, nullable=True)
    created_at = db.Column(
        db.DateTime, nullable=False, default=datetime.utcnow, index=True
    )

    actor = db.relationship(
        "User", foreign_keys=[actor_id], backref=db.backref("audit_logs", lazy=True)
    )

    def __repr__(self) -> str:
        return (
            f"<AuditLog(id={self.id}, action={self.action}, "
            f"actor_id={self.actor_id}, created_at={self.created_at})>"
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "actor_id": self.actor_id,
            "action": self.action,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "ip": self.ip,
            "user_agent": self.user_agent,
            "meta": self.meta,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    @classmethod
    def create(
        cls,
        action: str,
        actor_id: Optional[int] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[int] = None,
        ip: Optional[str] = None,
        user_agent: Optional[str] = None,
        meta: Optional[dict] = None,
    ) -> "AuditLog":
        entry = cls(
            actor_id=actor_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            ip=ip,
            user_agent=user_agent,
            meta=meta,
        )
        db.session.add(entry)
        db.session.commit()
        return entry

    @classmethod
    def get_by_action(
        cls, action: str, limit: int = 100, offset: int = 0
    ) -> list["AuditLog"]:
        return (
            cls.query.filter_by(action=action)
            .order_by(cls.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

    @classmethod
    def get_by_actor(
        cls, actor_id: int, limit: int = 100, offset: int = 0
    ) -> list["AuditLog"]:
        return (
            cls.query.filter_by(actor_id=actor_id)
            .order_by(cls.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

    @classmethod
    def get_all(cls, limit: int = 100, offset: int = 0) -> list["AuditLog"]:
        return (
            cls.query.order_by(cls.created_at.desc()).offset(offset).limit(limit).all()
        )
