"""Role-based access control models for Agent World."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from .base import BaseModel, db


class Role(BaseModel):
    """Application role with an optional permissions JSON payload."""

    __tablename__ = "roles"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(80), nullable=False, unique=True)
    permissions = db.Column(db.JSON, nullable=False, default=list)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    users = db.relationship(
        "User",
        secondary="user_roles",
        back_populates="roles",
    )

    def __repr__(self) -> str:
        return f"<Role(id={self.id}, name={self.name})>"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "permissions": self.permissions,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def create(cls, name: str, permissions: Optional[List[str]] = None, **kwargs) -> "Role":
        role = cls(name=name, permissions=permissions or [], **kwargs)
        db.session.add(role)
        db.session.commit()
        return role

    @classmethod
    def get_by_name(cls, name: str) -> Optional["Role"]:
        return cls.query.filter_by(name=name).first()

    @classmethod
    def get_all(cls) -> List["Role"]:
        return cls.query.all()


user_roles = db.Table(
    "user_roles",
    db.Column("user_id", db.Integer, db.ForeignKey("users.id"), primary_key=True),
    db.Column("role_id", db.Integer, db.ForeignKey("roles.id"), primary_key=True),
    db.Column("created_at", db.DateTime, nullable=False, default=datetime.utcnow),
)
