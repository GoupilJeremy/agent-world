# 📩 Agent World - Invitation Model
# Version: 0.4.0 (Collaboration)
# Description: Modèle de données pour les invitations d'utilisateurs

"""
Invitation Model for Agent World.

Ce modèle représente une invitation envoyée à un utilisateur pour rejoindre un projet.
Les invitations sont valides pendant 7 jours par défaut.
"""

from datetime import datetime, timedelta
from enum import Enum
from typing import Optional

from .base import BaseModel, db


class InvitationStatus(str, Enum):
    """Status possible d'une invitation."""

    PENDING = "pending"
    ACCEPTED = "accepted"
    EXPIRED = "expired"
    REVOKED = "revoked"


class Invitation(BaseModel):
    """
    Invitation model representing a user invitation to a project.

    Attributes:
        id: Unique identifier for the invitation
        project_id: ID of the project being shared
        email: Email address of the invited user
        token: Unique token for accepting the invitation (JWT compatible)
        role: Role assigned to the user upon acceptance (member, admin, viewer)
        status: Current status of the invitation
        created_by: ID of the user who created the invitation
        created_at: Timestamp when the invitation was created
        expires_at: Timestamp when the invitation expires
        accepted_at: Timestamp when the invitation was accepted
    """

    __tablename__ = "invitations"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id"), nullable=False)
    email = db.Column(db.String(255), nullable=False)
    token = db.Column(db.String(255), nullable=False, unique=True)
    role = db.Column(db.String(50), nullable=False, default="member")
    status = db.Column(
        db.Enum(InvitationStatus), nullable=False, default=InvitationStatus.PENDING
    )
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    expires_at = db.Column(
        db.DateTime,
        nullable=False,
        default=lambda: datetime.utcnow() + timedelta(days=7),
    )
    accepted_at = db.Column(db.DateTime, nullable=True)

    # Relationships
    project = db.relationship("Project", backref=db.backref("invitations", lazy=True))
    creator = db.relationship(
        "User",
        foreign_keys=[created_by],
        backref=db.backref("created_invitations", lazy=True),
    )

    def __init__(
        self,
        project_id: int,
        email: str,
        token: str,
        role: str = "member",
        created_by: int = None,
        expires_at: Optional[datetime] = None,
        status: InvitationStatus = InvitationStatus.PENDING,
    ):
        """
        Initialize a new Invitation instance.

        Args:
            project_id: ID of the project to invite to
            email: Email address of the invited user
            token: Unique token for the invitation
            role: Role to assign (default: "member")
            created_by: ID of the user who created the invitation
            expires_at: Expiration timestamp (default: 7 days from now)
            status: Initial status (default: PENDING)
        """
        self.project_id = project_id
        self.email = email
        self.token = token
        self.role = role
        self.created_by = created_by
        self.status = status
        self.expires_at = expires_at or (datetime.utcnow() + timedelta(days=7))

    def __repr__(self) -> str:
        return f"<Invitation(id={self.id}, email={self.email}, project_id={self.project_id}, status={self.status})>"

    @property
    def is_expired(self) -> bool:
        """Check if the invitation has expired."""
        return datetime.utcnow() > self.expires_at

    @property
    def is_pending(self) -> bool:
        """Check if the invitation is still pending."""
        return self.status == InvitationStatus.PENDING and not self.is_expired

    @property
    def is_accepted(self) -> bool:
        """Check if the invitation has been accepted."""
        return self.status == InvitationStatus.ACCEPTED

    def accept(self) -> None:
        """Mark the invitation as accepted."""
        self.status = InvitationStatus.ACCEPTED
        self.accepted_at = datetime.utcnow()
        db.session.commit()

    def revoke(self) -> None:
        """Revoke the invitation."""
        self.status = InvitationStatus.REVOKED
        db.session.commit()

    def update_status(self, status: InvitationStatus) -> None:
        """Update the invitation status."""
        self.status = status
        db.session.commit()

    def to_dict(self) -> dict:
        """Convert invitation to dictionary for API responses."""
        return {
            "id": self.id,
            "project_id": self.project_id,
            "email": self.email,
            "role": self.role,
            "status": self.status.value,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "accepted_at": self.accepted_at.isoformat() if self.accepted_at else None,
        }

    @classmethod
    def create(
        cls,
        project_id: int,
        email: str,
        token: str,
        role: str = "member",
        created_by: int = None,
        expires_at: Optional[datetime] = None,
    ) -> "Invitation":
        """
        Create a new invitation and save to database.

        Args:
            project_id: ID of the project
            email: Email address of the invited user
            token: Unique token
            role: Role to assign
            created_by: ID of the creator
            expires_at: Expiration timestamp

        Returns:
            The created Invitation instance
        """
        invitation = cls(
            project_id=project_id,
            email=email,
            token=token,
            role=role,
            created_by=created_by,
            expires_at=expires_at,
        )
        db.session.add(invitation)
        db.session.commit()
        return invitation

    @classmethod
    def get_by_token(cls, token: str) -> Optional["Invitation"]:
        """Get an invitation by its token."""
        return cls.query.filter_by(token=token).first()

    @classmethod
    def get_by_project(cls, project_id: int) -> list["Invitation"]:
        """Get all invitations for a specific project."""
        return cls.query.filter_by(project_id=project_id).all()

    @classmethod
    def get_pending_by_email(cls, email: str) -> list["Invitation"]:
        """Get all pending invitations for an email address."""
        return (
            cls.query.filter_by(email=email, status=InvitationStatus.PENDING)
            .filter(datetime.utcnow() <= cls.expires_at)
            .all()
        )

    @classmethod
    def get_by_email_and_project(
        cls, email: str, project_id: int
    ) -> Optional["Invitation"]:
        """Get an invitation by email and project ID."""
        return cls.query.filter_by(email=email, project_id=project_id).first()
