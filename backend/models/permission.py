# 🔐 Agent World - Permission Model
# Version: 1.0.0 (EPIC 10 - US-066)
# Description: Modèle pour gérer les permissions de la plateforme

"""
Permission Model for Agent World.

Ce modèle définit les permissions de base disponibles dans la plateforme.
"""

from datetime import datetime

from .base import BaseModel, db


class Permission(BaseModel):
    """
    Model for storing system permissions.

    Attributes:
        id: Unique identifier
        name: Unique name of the permission (e.g., 'read_agent', 'create_agent')
        description: Description of what the permission allows
        category: Category of the permission (e.g., 'agent', 'user', 'project')
        created_at: Timestamp when the permission was created
        updated_at: Timestamp when the permission was last updated
    """

    __tablename__ = "permissions"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(80), nullable=False, unique=True)
    description = db.Column(db.String(255), nullable=True)
    category = db.Column(db.String(50), nullable=False, default="general")
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
    roles = db.relationship(
        "Role",
        secondary="role_permissions",
        back_populates="permissions",
    )

    def __init__(
        self,
        name: str,
        description: str = "",
        category: str = "general",
    ):
        """
        Initialize a new Permission instance.

        Args:
            name: Unique name of the permission
            description: Description of the permission
            category: Category of the permission
        """
        self.name = name
        self.description = description
        self.category = category

    def __repr__(self) -> str:
        return f"<Permission(id={self.id}, name={self.name}, category={self.category})>"

    def to_dict(self) -> dict:
        """Convert permission to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def get_by_name(cls, name: str) -> "Permission | None":
        """Get permission by name."""
        return cls.query.filter_by(name=name).first()

    @classmethod
    def get_all_by_category(cls, category: str) -> list["Permission"]:
        """Get all permissions by category."""
        return cls.query.filter_by(category=category).all()


# Association table for many-to-many relationship between Role and Permission
role_permissions = db.Table(
    "role_permissions",
    db.Column(
        "role_id",
        db.Integer,
        db.ForeignKey("roles.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    db.Column(
        "permission_id",
        db.Integer,
        db.ForeignKey("permissions.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    db.Column(
        "created_at",
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
    ),
)
