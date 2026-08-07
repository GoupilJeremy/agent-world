# 🔄 Agent World - Workflow Model
# Version: 0.1.0 (MVP)
# Description: Modèle de données pour les workflows

"""
Workflow Model for Agent World.

Ce modèle représente un workflow qui peut être exécuté par un agent IA.
Un workflow est une séquence d'étapes que l'agent doit suivre.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from .base import BaseModel, db


class Workflow(BaseModel):
    """
    Workflow model representing a sequence of steps for an agent.

    Attributes:
        id: Unique identifier for the workflow
        name: Name of the workflow
        description: Description of what the workflow does
        agent_id: ID of the agent that owns this workflow
        steps: JSON array defining the workflow steps
        configuration: JSON configuration for the workflow
        is_active: Whether the workflow is active
        created_by: ID of the user who created the workflow
        created_at: Timestamp when the workflow was created
        updated_at: Timestamp when the workflow was last updated
    """

    __tablename__ = "workflows"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    agent_id = db.Column(db.Integer, db.ForeignKey("agents.id"), nullable=False)
    steps = db.Column(db.JSON, nullable=False, default=[])
    configuration = db.Column(db.JSON, nullable=False, default={})
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    agent = db.relationship("Agent", backref=db.backref("workflows", lazy=True))
    creator = db.relationship(
        "User",
        backref=db.backref("created_workflows", lazy=True),
        foreign_keys=[created_by],
    )
    executions = db.relationship(
        "Execution",
        backref=db.backref("workflow", lazy=True),
        cascade="all, delete-orphan",
    )

    def __init__(
        self,
        name: str,
        agent_id: int,
        steps: List[Dict[str, Any]],
        description: Optional[str] = None,
        configuration: Optional[dict] = None,
        is_active: bool = True,
        created_by: Optional[int] = None,
    ):
        """
        Initialize a new Workflow instance.

        Args:
            name: Name of the workflow
            agent_id: ID of the agent that owns this workflow
            steps: List of workflow steps
            description: Optional description
            configuration: Optional JSON configuration
            is_active: Whether the workflow is active (default: True)
            created_by: ID of the creating user
        """
        self.name = name
        self.agent_id = agent_id
        self.steps = steps
        self.description = description or f"Workflow for agent {agent_id}"
        self.configuration = configuration or {}
        self.is_active = is_active
        self.created_by = created_by

    def __repr__(self) -> str:
        return f"<Workflow(id={self.id}, name={self.name}, agent_id={self.agent_id})>"

    @property
    def step_count(self) -> int:
        """Get the number of steps in the workflow."""
        return len(self.steps) if self.steps else 0

    def add_step(self, step: Dict[str, Any]) -> None:
        """Add a step to the workflow."""
        if self.steps is None:
            self.steps = []
        self.steps.append(step)
        self.updated_at = datetime.utcnow()

    def remove_step(self, index: int) -> Optional[Dict[str, Any]]:
        """Remove a step from the workflow by index."""
        if self.steps and 0 <= index < len(self.steps):
            step = self.steps.pop(index)
            self.updated_at = datetime.utcnow()
            return step
        return None

    def to_dict(self) -> dict:
        """Convert workflow to dictionary for API responses."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "agent_id": self.agent_id,
            "steps": self.steps,
            "step_count": self.step_count,
            "configuration": self.configuration,
            "is_active": self.is_active,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def update(self, **kwargs) -> None:
        """Update workflow attributes."""
        for key, value in kwargs.items():
            if hasattr(self, key) and key != "id":
                setattr(self, key, value)
        self.updated_at = datetime.utcnow()
        db.session.commit()

    @classmethod
    def create(cls, **kwargs) -> "Workflow":
        """Create a new workflow and save to database."""
        workflow = cls(**kwargs)
        db.session.add(workflow)
        db.session.commit()
        return workflow

    @classmethod
    def get_by_id(cls, workflow_id: int) -> Optional["Workflow"]:
        """Get workflow by ID."""
        return cls.query.get(workflow_id)

    @classmethod
    def get_by_agent(cls, agent_id: int) -> List["Workflow"]:
        """Get all workflows for a specific agent."""
        return cls.query.filter_by(agent_id=agent_id).all()

    @classmethod
    def get_all(cls) -> List["Workflow"]:
        """Get all workflows."""
        return cls.query.all()

    @classmethod
    def get_active(cls) -> List["Workflow"]:
        """Get all active workflows."""
        return cls.query.filter_by(is_active=True).all()

    def delete(self) -> None:
        """Delete the workflow from database."""
        db.session.delete(self)
        db.session.commit()
