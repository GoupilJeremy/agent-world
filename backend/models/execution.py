# ▶️ Agent World - Execution Model
# Version: 0.1.0 (MVP)
# Description: Modèle de données pour les exécutions

"""
Execution Model for Agent World.

Ce modèle représente une exécution d'un agent ou d'un workflow.
Il stocke les informations sur l'exécution, y compris l'entrée, la sortie,
et le statut.
"""

from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum
from .base import BaseModel, db


class ExecutionStatus(str, Enum):
    """Status of an execution."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Execution(BaseModel):
    """
    Execution model representing a run of an agent or workflow.

    Attributes:
        id: Unique identifier for the execution
        agent_id: ID of the agent that was executed
        workflow_id: Optional ID of the workflow that was executed
        input_data: JSON input data for the execution
        output_data: JSON output data from the execution
        status: Current status of the execution
        error_message: Error message if the execution failed
        duration_ms: Duration of the execution in milliseconds
        started_at: Timestamp when the execution started
        completed_at: Timestamp when the execution completed
        executed_by: ID of the user who initiated the execution
        model_used: Model used for the execution
        created_at: Timestamp when the execution record was created
    """

    __tablename__ = "executions"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    agent_id = db.Column(db.Integer, db.ForeignKey("agents.id"), nullable=False)
    workflow_id = db.Column(db.Integer, db.ForeignKey("workflows.id"), nullable=True)
    input_data = db.Column(db.JSON, nullable=False, default={})
    output_data = db.Column(db.JSON, nullable=True)
    status = db.Column(
        db.Enum(ExecutionStatus), nullable=False, default=ExecutionStatus.PENDING
    )
    error_message = db.Column(db.Text, nullable=True)
    duration_ms = db.Column(db.Integer, nullable=True)
    started_at = db.Column(db.DateTime, nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)
    executed_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    model_used = db.Column(db.String(50), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    agent = db.relationship("Agent", backref=db.backref("executions", lazy=True))
    workflow = db.relationship("Workflow", backref=db.backref("executions", lazy=True))
    executor = db.relationship(
        "User",
        backref=db.backref("user_executions", lazy=True),
        foreign_keys=[executed_by],
    )

    def __init__(
        self,
        agent_id: int,
        input_data: Dict[str, Any],
        workflow_id: Optional[int] = None,
        executed_by: Optional[int] = None,
        model_used: Optional[str] = None,
    ):
        """
        Initialize a new Execution instance.

        Args:
            agent_id: ID of the agent being executed
            input_data: Input data for the execution
            workflow_id: Optional ID of the workflow being executed
            executed_by: Optional ID of the user who initiated the execution
            model_used: Optional model used for the execution
        """
        self.agent_id = agent_id
        self.workflow_id = workflow_id
        self.input_data = input_data
        self.executed_by = executed_by
        self.model_used = model_used or "mistral-tiny"
        self.status = ExecutionStatus.PENDING

    def __repr__(self) -> str:
        return (
            f"<Execution(id={self.id}, agent_id={self.agent_id}, "
            f"status={self.status.value})>"
        )

    @property
    def is_complete(self) -> bool:
        """Check if the execution is complete."""
        return self.status in [ExecutionStatus.COMPLETED, ExecutionStatus.FAILED]

    def start(self) -> None:
        """Mark the execution as started."""
        self.status = ExecutionStatus.RUNNING
        self.started_at = datetime.utcnow()
        db.session.commit()

    def complete(self, output_data: Dict[str, Any]) -> None:
        """Mark the execution as completed successfully."""
        self.status = ExecutionStatus.COMPLETED
        self.output_data = output_data
        self.completed_at = datetime.utcnow()
        self.duration_ms = self._calculate_duration()
        db.session.commit()

    def fail(self, error_message: str) -> None:
        """Mark the execution as failed."""
        self.status = ExecutionStatus.FAILED
        self.error_message = error_message
        self.completed_at = datetime.utcnow()
        self.duration_ms = self._calculate_duration()
        db.session.commit()

    def cancel(self) -> None:
        """Mark the execution as cancelled."""
        self.status = ExecutionStatus.CANCELLED
        self.completed_at = datetime.utcnow()
        self.duration_ms = self._calculate_duration()
        db.session.commit()

    def _calculate_duration(self) -> Optional[int]:
        """Calculate execution duration in milliseconds."""
        if self.started_at and self.completed_at:
            delta = self.completed_at - self.started_at
            return int(delta.total_seconds() * 1000)
        return None

    def to_dict(self) -> dict:
        """Convert execution to dictionary for API responses."""
        return {
            "id": self.id,
            "agent_id": self.agent_id,
            "workflow_id": self.workflow_id,
            "input_data": self.input_data,
            "output_data": self.output_data,
            "status": self.status.value,
            "error_message": self.error_message,
            "duration_ms": self.duration_ms,
            "model_used": self.model_used,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": (
                self.completed_at.isoformat() if self.completed_at else None
            ),
            "executed_by": self.executed_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    @classmethod
    def create(cls, **kwargs) -> "Execution":
        """Create a new execution and save to database."""
        execution = cls(**kwargs)
        db.session.add(execution)
        db.session.commit()
        return execution

    @classmethod
    def get_by_id(cls, execution_id: int) -> Optional["Execution"]:
        """Get execution by ID."""
        return cls.query.get(execution_id)

    @classmethod
    def get_by_agent(cls, agent_id: int) -> List["Execution"]:
        """Get all executions for a specific agent."""
        return cls.query.filter_by(agent_id=agent_id).all()

    @classmethod
    def get_by_workflow(cls, workflow_id: int) -> List["Execution"]:
        """Get all executions for a specific workflow."""
        return cls.query.filter_by(workflow_id=workflow_id).all()

    @classmethod
    def get_by_status(cls, status: ExecutionStatus) -> List["Execution"]:
        """Get all executions with a specific status."""
        return cls.query.filter_by(status=status).all()

    @classmethod
    def get_all(cls) -> List["Execution"]:
        """Get all executions."""
        return cls.query.all()

    def delete(self) -> None:
        """Delete the execution from database."""
        db.session.delete(self)
        db.session.commit()
