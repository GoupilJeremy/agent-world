# 📁 Agent World - Project Model
# Version: 0.4.0 (Collaboration)
# Description: Modèle de données pour les projets

"""
Project Model for Agent World.

Ce modèle représente un projet dans la plateforme Agent World.
Un projet est un espace de travail qui peut contenir plusieurs agents,
workflows et fichiers. Les projets permettent aux utilisateurs de collaborer
sur des ensembles d'agents liés.
"""

from datetime import datetime
from typing import List, Optional

from .base import BaseModel, db


class Project(BaseModel):
    """
    Project model representing a workspace for agents.

    Attributes:
        id: Unique identifier for the project
        name: Name of the project
        description: Description of the project
        created_by: ID of the user who created the project
        is_public: Whether the project is publicly visible
        is_shared: Whether the project is shared with other users
        created_at: Timestamp when the project was created
        updated_at: Timestamp when the project was last updated
    """

    __tablename__ = "projects"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    is_public = db.Column(db.Boolean, nullable=False, default=False)
    is_shared = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    creator = db.relationship(
        "User", back_populates="projects", foreign_keys=[created_by]
    )
    agents = db.relationship(
        "Agent", back_populates="project", cascade="all, delete-orphan"
    )

    def __init__(
        self,
        name: str,
        created_by: int,
        description: Optional[str] = None,
        is_public: bool = False,
        is_shared: bool = False,
    ):
        """
        Initialize a new Project instance.

        Args:
            name: Name of the project
            created_by: ID of the user who created the project
            description: Optional description
            is_public: Whether the project is public (default: False)
            is_shared: Whether the project is shared (default: False)
        """
        self.name = name
        self.description = description
        self.created_by = created_by
        self.is_public = is_public
        self.is_shared = is_shared

    def __repr__(self) -> str:
        return f"<Project(id={self.id}, name={self.name}, created_by={self.created_by})>"

    def to_dict(self) -> dict:
        """Convert project to dictionary for API responses."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "created_by": self.created_by,
            "is_public": self.is_public,
            "is_shared": self.is_shared,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def update(self, **kwargs) -> None:
        """Update project attributes."""
        for key, value in kwargs.items():
            if hasattr(self, key) and key != "id":
                setattr(self, key, value)
        self.updated_at = datetime.utcnow()
        db.session.commit()

    @classmethod
    def create(cls, **kwargs) -> "Project":
        """Create a new project and save to database."""
        project = cls(**kwargs)
        db.session.add(project)
        db.session.commit()
        return project

    @classmethod
    def get_by_id(cls, project_id: int) -> Optional["Project"]:
        """Get project by ID."""
        return cls.query.get(project_id)

    @classmethod
    def get_by_name(cls, name: str) -> Optional["Project"]:
        """Get project by name."""
        return cls.query.filter_by(name=name).first()

    @classmethod
    def get_all(cls) -> List["Project"]:
        """Get all projects."""
        return cls.query.all()

    @classmethod
    def get_by_user(cls, user_id: int) -> List["Project"]:
        """Get all projects created by a user."""
        return cls.query.filter_by(created_by=user_id).all()

    def delete(self) -> None:
        """Delete the project from database."""
        db.session.delete(self)
        db.session.commit()
