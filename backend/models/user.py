# 👤 Agent World - User Model
# Version: 0.1.0 (MVP)
# Description: Modèle de données pour les utilisateurs

"""
User Model for Agent World.

Ce modèle représente un utilisateur de la plateforme Agent World.
Les utilisateurs peuvent créer, gérer et exécuter des agents IA.
"""

from datetime import datetime
from typing import List, Optional

from werkzeug.security import check_password_hash, generate_password_hash

from .base import BaseModel, db


class User(BaseModel):
    """
    User model representing a platform user.

    Attributes:
        id: Unique identifier for the user
        email: User's email address (unique)
        username: User's username (unique)
        password_hash: Hashed password
        first_name: User's first name
        last_name: User's last name
        is_active: Whether the user account is active
        is_admin: Whether the user has admin privileges
        created_at: Timestamp when the user was created
        updated_at: Timestamp when the user was last updated
    """

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email = db.Column(db.String(120), nullable=False, unique=True)
    username = db.Column(db.String(80), nullable=False, unique=True)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(50), nullable=True)
    last_name = db.Column(db.String(50), nullable=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    is_admin = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    projects = db.relationship(
        "Project",
        back_populates="creator",
        foreign_keys="Project.created_by",
    )
    agents = db.relationship(
        "Agent",
        back_populates="creator",
        foreign_keys="Agent.created_by",
    )
    workflows = db.relationship(
        "Workflow",
        back_populates="creator",
        foreign_keys="Workflow.created_by",
    )
    executions = db.relationship(
        "Execution",
        back_populates="executor",
        foreign_keys="Execution.executed_by",
    )

    def __init__(
        self,
        email: str,
        username: str,
        password: str,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        is_active: bool = True,
        is_admin: bool = False,
    ):
        """
        Initialize a new User instance.

        Args:
            email: User's email address
            username: User's username
            password: Plain text password (will be hashed)
            first_name: Optional first name
            last_name: Optional last name
            is_active: Whether the user is active (default: True)
            is_admin: Whether the user is admin (default: False)
        """
        self.email = email
        self.username = username
        self.password_hash = generate_password_hash(password)
        self.first_name = first_name
        self.last_name = last_name
        self.is_active = is_active
        self.is_admin = is_admin

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username={self.username}, email={self.email})>"

    @property
    def full_name(self) -> str:
        """Get user's full name."""
        return f"{self.first_name or ''} {self.last_name or ''}".strip()

    def set_password(self, password: str) -> None:
        """Set user password (hashes the password)."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """Check if the provided password matches the stored hash."""
        return check_password_hash(self.password_hash, password)

    def to_dict(self, include_password: bool = False) -> dict:
        """Convert user to dictionary for API responses."""
        user_dict = {
            "id": self.id,
            "email": self.email,
            "username": self.username,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "full_name": self.full_name,
            "is_active": self.is_active,
            "is_admin": self.is_admin,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

        if include_password:
            user_dict["password_hash"] = self.password_hash

        return user_dict

    def update(self, **kwargs) -> None:
        """Update user attributes."""
        if "password" in kwargs:
            self.set_password(kwargs.pop("password"))

        for key, value in kwargs.items():
            if hasattr(self, key) and key != "id":
                setattr(self, key, value)

        self.updated_at = datetime.utcnow()
        db.session.commit()

    @classmethod
    def create(cls, **kwargs) -> "User":
        """Create a new user and save to database."""
        user = cls(**kwargs)
        db.session.add(user)
        db.session.commit()
        return user

    @classmethod
    def get_by_id(cls, user_id: int) -> Optional["User"]:
        """Get user by ID."""
        return cls.query.get(user_id)

    @classmethod
    def get_by_email(cls, email: str) -> Optional["User"]:
        """Get user by email."""
        return cls.query.filter_by(email=email).first()

    @classmethod
    def get_by_username(cls, username: str) -> Optional["User"]:
        """Get user by username."""
        return cls.query.filter_by(username=username).first()

    @classmethod
    def get_all(cls) -> List["User"]:
        """Get all users."""
        return cls.query.all()

    @classmethod
    def get_active(cls) -> List["User"]:
        """Get all active users."""
        return cls.query.filter_by(is_active=True).all()

    def delete(self) -> None:
        """Delete the user from database."""
        db.session.delete(self)
        db.session.commit()
