# 👥 Agent World - Role Model
# Version: 1.0.0 (EPIC 10 - US-066)
# Description: Modèle pour gérer les rôles de la plateforme

"""
Role Model for Agent World.

Ce modèle définit les rôles disponibles dans la plateforme avec leurs permissions.
"""

from datetime import datetime
from typing import List, Optional

from .base import BaseModel, db
from .permission import role_permissions


class Role(BaseModel):
    """
    Model for storing user roles.

    Attributes:
        id: Unique identifier
        name: Unique name of the role (e.g., 'admin', 'member', 'guest')
        description: Description of the role
        is_default: Whether this is the default role for new users
        is_system: Whether this is a system role (cannot be deleted)
        created_at: Timestamp when the role was created
        updated_at: Timestamp when the role was last updated
    """

    __tablename__ = "roles"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    description = db.Column(db.String(255), nullable=True)
    is_default = db.Column(db.Boolean, nullable=False, default=False)
    is_system = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(
        db.DateTime, nullable=False, default=datetime.utcnow
    )
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    # Relationships
    permissions = db.relationship(
        "Permission",
        secondary="role_permissions",
        back_populates="roles",
    )
    users = db.relationship(
        "User",
        secondary="user_roles",
        back_populates="roles",
    )

    def __init__(
        self,
        name: str,
        description: str = "",
        is_default: bool = False,
        is_system: bool = False,
    ):
        """
        Initialize a new Role instance.

        Args:
            name: Unique name of the role
            description: Description of the role
            is_default: Whether this is the default role
            is_system: Whether this is a system role
        """
        self.name = name
        self.description = description
        self.is_default = is_default
        self.is_system = is_system

    def __repr__(self) -> str:
        return f"<Role(id={self.id}, name={self.name}, is_system={self.is_system})>"

    def to_dict(self) -> dict:
        """Convert role to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "is_default": self.is_default,
            "is_system": self.is_system,
            "permission_count": len(self.permissions),
            "user_count": len(self.users),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def has_permission(self, permission_name: str) -> bool:
        """Check if this role has a specific permission."""
        for permission in self.permissions:
            if permission.name == permission_name:
                return True
        return False

    def get_permission_names(self) -> List[str]:
        """Get list of permission names for this role."""
        return [p.name for p in self.permissions]

    @classmethod
    def get_by_name(cls, name: str) -> Optional["Role"]:
        """Get role by name."""
        return cls.query.filter_by(name=name).first()

    @classmethod
    def get_default(cls) -> Optional["Role"]:
        """Get the default role."""
        return cls.query.filter_by(is_default=True).first()

    @classmethod
    def get_all_system_roles(cls) -> List["Role"]:
        """Get all system roles."""
        return cls.query.filter_by(is_system=True).all()


# Association table for many-to-many relationship between User and Role
user_roles = db.Table(
    "user_roles",
    db.Column(
        "user_id",
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    db.Column(
        "role_id",
        db.Integer,
        db.ForeignKey("roles.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    db.Column(
        "created_at",
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
    ),
)
