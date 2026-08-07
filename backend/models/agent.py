# 🤖 Agent World - Agent Model
# Version: 0.1.0 (MVP)
# Description: Modèle de données pour les agents IA

"""
Agent Model for Agent World.

Ce modèle représente un agent IA dans la base de données.
Un agent peut être configuré avec différents paramètres, modèles IA,
et des workflows spécifiques.
"""

from datetime import datetime
from typing import List, Optional

from .base import BaseModel, db


class Agent(BaseModel):
    """
    Agent model representing an AI agent.

    Attributes:
        id: Unique identifier for the agent
        name: Name of the agent
        description: Description of what the agent does
        model: AI model used by the agent (e.g., 'mistral-tiny', 'gpt-3.5-turbo')
        configuration: JSON configuration for the agent
        is_active: Whether the agent is active and can be used
        created_by: ID of the user who created the agent
        created_at: Timestamp when the agent was created
        updated_at: Timestamp when the agent was last updated
    """

    __tablename__ = "agents"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=True)
    model = db.Column(db.String(50), nullable=False, default="mistral-tiny")
    configuration = db.Column(db.JSON, nullable=False, default={})
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    user = db.relationship("User", backref=db.backref("agents", lazy=True))
    workflows = db.relationship(
        "Workflow", backref=db.backref("agent", lazy=True), cascade="all, delete-orphan"
    )
    executions = db.relationship(
        "Execution",
        backref=db.backref("agent", lazy=True),
        cascade="all, delete-orphan",
    )

    def __init__(
        self,
        name: str,
        model: str = "mistral-tiny",
        description: Optional[str] = None,
        configuration: Optional[dict] = None,
        is_active: bool = True,
        created_by: Optional[int] = None,
    ):
        """
        Initialize a new Agent instance.

        Args:
            name: Name of the agent
            model: AI model to use (default: 'mistral-tiny')
            description: Optional description
            configuration: Optional JSON configuration
            is_active: Whether the agent is active (default: True)
            created_by: ID of the creating user
        """
        self.name = name
        self.model = model
        self.description = description or f"Agent using {model} model"
        self.configuration = configuration or {}
        self.is_active = is_active
        self.created_by = created_by

    def __repr__(self) -> str:
        return f"<Agent(id={self.id}, name={self.name}, model={self.model})>"

    def to_dict(self) -> dict:
        """Convert agent to dictionary for API responses."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "model": self.model,
            "configuration": self.configuration,
            "is_active": self.is_active,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def update(self, **kwargs) -> None:
        """Update agent attributes."""
        for key, value in kwargs.items():
            if hasattr(self, key) and key != "id":
                setattr(self, key, value)
        self.updated_at = datetime.utcnow()
        db.session.commit()

    @classmethod
    def create(cls, **kwargs) -> "Agent":
        """Create a new agent and save to database."""
        agent = cls(**kwargs)
        db.session.add(agent)
        db.session.commit()
        return agent

    @classmethod
    def get_by_id(cls, agent_id: int) -> Optional["Agent"]:
        """Get agent by ID."""
        return cls.query.get(agent_id)

    @classmethod
    def get_by_name(cls, name: str) -> Optional["Agent"]:
        """Get agent by name."""
        return cls.query.filter_by(name=name).first()

    @classmethod
    def get_all(cls) -> List["Agent"]:
        """Get all agents."""
        return cls.query.all()

    @classmethod
    def get_active(cls) -> List["Agent"]:
        """Get all active agents."""
        return cls.query.filter_by(is_active=True).all()

    def delete(self) -> None:
        """Delete the agent from database."""
        db.session.delete(self)
        db.session.commit()
