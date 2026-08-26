# Agent World - Template Share Model
# Version: 0.3.1 (EPIC 5)
# Description: Modèle pour la gestion du partage des templates

"""
Template Share Model for Agent World.

Ce modèle gère le partage des templates avec des utilisateurs ou groupes spécifiques.
"""

from datetime import datetime
from typing import Optional

from .base import BaseModel, db


class SharePermission(BaseModel):
    """
    SharePermission model for managing template sharing permissions.

    Attributes:
        id: Unique identifier for the share permission
        template_id: ID of the template being shared
        shared_with_id: ID of the user the template is shared with
        permission_level: Level of permission (read, edit, admin)
        shared_by: ID of the user who shared the template
        created_at: Timestamp when the share was created
        expires_at: Optional expiration timestamp
        is_active: Whether the share is active
    """

    __tablename__ = "template_shares"

    # Permission levels
    READ = "read"
    EDIT = "edit"
    ADMIN = "admin"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    template_id = db.Column(db.Integer, db.ForeignKey("templates.id"), nullable=False)
    shared_with_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    permission_level = db.Column(db.String(20), nullable=False, default=READ)
    shared_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True)

    # Relationships
    template = db.relationship("Template", backref="shares")
    shared_with = db.relationship(
        "User", foreign_keys=[shared_with_id], backref="shared_templates"
    )
    sharer = db.relationship("User", foreign_keys=[shared_by], backref="shared_by_me")

    def __init__(
        self,
        template_id: int,
        shared_with_id: int,
        permission_level: str = READ,
        shared_by: Optional[int] = None,
        expires_at: Optional[datetime] = None,
        is_active: bool = True,
    ):
        """
        Initialize a new SharePermission instance.

        Args:
            template_id: ID of the template being shared
            shared_with_id: ID of the user the template is shared with
            permission_level: Level of permission (read, edit, admin)
            shared_by: ID of the user who shared the template
            expires_at: Optional expiration timestamp
            is_active: Whether the share is active
        """
        self.template_id = template_id
        self.shared_with_id = shared_with_id
        self.permission_level = permission_level
        self.shared_by = shared_by
        self.expires_at = expires_at
        self.is_active = is_active

    def __repr__(self) -> str:
        return (
            f"<SharePermission(id={self.id}, template_id={self.template_id}, "
            f"shared_with={self.shared_with_id}, permission={self.permission_level})>"
        )

    def to_dict(self) -> dict:
        """Convert share permission to dictionary."""
        return {
            "id": self.id,
            "template_id": self.template_id,
            "shared_with_id": self.shared_with_id,
            "permission_level": self.permission_level,
            "shared_by": self.shared_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "is_active": self.is_active,
        }

    @classmethod
    def create(cls, **kwargs) -> "SharePermission":
        """Create a new share permission and save to database."""
        share = cls(**kwargs)
        db.session.add(share)
        db.session.commit()
        return share

    @classmethod
    def get_by_id(cls, share_id: int) -> Optional["SharePermission"]:
        """Get share permission by ID."""
        return cls.query.get(share_id)

    @classmethod
    def get_by_template(cls, template_id: int) -> list:
        """Get all share permissions for a template."""
        return cls.query.filter_by(template_id=template_id).all()

    @classmethod
    def get_by_user(cls, user_id: int) -> list:
        """Get all templates shared with a user."""
        return cls.query.filter_by(shared_with_id=user_id).all()

    @classmethod
    def get_active_shares(cls, template_id: int) -> list:
        """Get all active share permissions for a template."""
        return cls.query.filter_by(template_id=template_id, is_active=True).all()

    @classmethod
    def get_share_with_user(
        cls, template_id: int, user_id: int
    ) -> Optional["SharePermission"]:
        """Get share permission for a specific template and user."""
        return cls.query.filter_by(
            template_id=template_id, shared_with_id=user_id
        ).first()

    def update_permission(self, new_level: str) -> None:
        """Update the permission level."""
        if new_level in [self.READ, self.EDIT, self.ADMIN]:
            self.permission_level = new_level
            db.session.commit()

    def deactivate(self) -> None:
        """Deactivate this share permission."""
        self.is_active = False
        db.session.commit()

    def activate(self) -> None:
        """Activate this share permission."""
        self.is_active = True
        db.session.commit()

    def delete(self) -> None:
        """Delete this share permission."""
        db.session.delete(self)
        db.session.commit()

    def has_permission(self, required_level: str) -> bool:
        """
        Check if this share has the required permission level.

        Args:
            required_level: Required permission level (read, edit, admin)

        Returns:
            True if the share has the required permission
        """
        levels = {self.READ: 0, self.EDIT: 1, self.ADMIN: 2}
        return levels.get(self.permission_level, 0) >= levels.get(required_level, 0)


class ShareToken(BaseModel):
    """
    ShareToken model for generating shareable links.

    Attributes:
        id: Unique identifier for the token
        template_id: ID of the template the token is for
        token: Unique token string
        permission_level: Permission level for this token
        created_by: ID of the user who created the token
        created_at: Timestamp when the token was created
        expires_at: Optional expiration timestamp
        is_active: Whether the token is active
    """

    __tablename__ = "share_tokens"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    template_id = db.Column(db.Integer, db.ForeignKey("templates.id"), nullable=False)
    token = db.Column(db.String(64), nullable=False, unique=True)
    permission_level = db.Column(
        db.String(20), nullable=False, default=SharePermission.READ
    )
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True)

    # Relationships
    template = db.relationship("Template")
    creator = db.relationship("User", foreign_keys=[created_by])

    def __init__(
        self,
        template_id: int,
        token: str,
        permission_level: str = SharePermission.READ,
        created_by: Optional[int] = None,
        expires_at: Optional[datetime] = None,
        is_active: bool = True,
    ):
        """
        Initialize a new ShareToken instance.

        Args:
            template_id: ID of the template
            token: Unique token string
            permission_level: Permission level for this token
            created_by: ID of the user who created the token
            expires_at: Optional expiration timestamp
            is_active: Whether the token is active
        """
        self.template_id = template_id
        self.token = token
        self.permission_level = permission_level
        self.created_by = created_by
        self.expires_at = expires_at
        self.is_active = is_active

    def __repr__(self) -> str:
        return (
            f"<ShareToken(id={self.id}, template_id={self.template_id}, "
            f"token={self.token[:8]}..., permission={self.permission_level})>"
        )

    def to_dict(self) -> dict:
        """Convert share token to dictionary (without the token for security)."""
        return {
            "id": self.id,
            "template_id": self.template_id,
            "permission_level": self.permission_level,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "is_active": self.is_active,
        }

    def to_dict_with_token(self) -> dict:
        """Convert share token to dictionary including the token."""
        data = self.to_dict()
        data["token"] = self.token
        return data

    @classmethod
    def generate_token(cls, length: int = 32) -> str:
        """Generate a random token string."""
        import secrets
        import string

        alphabet = string.ascii_letters + string.digits
        return "".join(secrets.choice(alphabet) for _ in range(length))

    @classmethod
    def create(cls, **kwargs) -> "ShareToken":
        """Create a new share token and save to database."""
        # Generate token if not provided
        if "token" not in kwargs:
            kwargs["token"] = cls.generate_token()

        token = cls(**kwargs)
        db.session.add(token)
        db.session.commit()
        return token

    @classmethod
    def get_by_token(cls, token_str: str) -> Optional["ShareToken"]:
        """Get share token by token string."""
        return cls.query.filter_by(token=token_str).first()

    @classmethod
    def get_by_template(cls, template_id: int) -> list:
        """Get all share tokens for a template."""
        return cls.query.filter_by(template_id=template_id).all()

    @classmethod
    def get_active_tokens(cls, template_id: int) -> list:
        """Get all active share tokens for a template."""
        return cls.query.filter_by(template_id=template_id, is_active=True).all()

    def is_valid(self) -> bool:
        """Check if the token is still valid."""
        if not self.is_active:
            return False
        if self.expires_at and self.expires_at < datetime.utcnow():
            return False
        return True

    def deactivate(self) -> None:
        """Deactivate this share token."""
        self.is_active = False
        db.session.commit()

    def delete(self) -> None:
        """Delete this share token."""
        db.session.delete(self)
        db.session.commit()
