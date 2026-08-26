# 📜 Agent World - Agent History Model
# Version: 0.3.0 (EPIC 4 - History)
# Description: Modèle de données pour l'historique des modifications des agents

"""
Agent History Model for Agent World.

Ce modèle représente l'historique des modifications apportées aux agents IA.
Il permet de tracer toutes les actions (création, mise à jour, suppression) 
sur un agent, avec les valeurs avant/après et les métadonnées associées.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from .base import BaseModel, db


class ActionType(str, Enum):
    """Type d'action effectuée sur un agent."""

    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    RENAME = "rename"
    TOGGLE_ACTIVE = "toggle_active"


class AgentHistory(BaseModel):
    """
    Agent History model representing a change to an agent.

    Attributes:
        id: Unique identifier for the history entry
        agent_id: ID of the agent that was modified
        version_id: UUID for version tracking (optional)
        action_type: Type of action performed (CREATE, UPDATE, DELETE, etc.)
        timestamp: When the action was performed
        author_id: ID of the user who performed the action
        metadata: JSON containing old/new values, reason, IP address, etc.
        is_restored: Whether this version was restored from history
    """

    __tablename__ = "agent_histories"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    agent_id = db.Column(
        db.Integer, db.ForeignKey("agents.id", ondelete="SET NULL"), nullable=True
    )
    version_id = db.Column(db.String(36), nullable=True, unique=True)
    action_type = db.Column(
        db.Enum(ActionType), nullable=False, default=ActionType.CREATE
    )
    timestamp = db.Column(
        db.DateTime, nullable=False, default=datetime.utcnow, index=True
    )
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    change_data = db.Column(db.JSON, nullable=False, default={})
    is_restored = db.Column(db.Boolean, nullable=False, default=False)

    # Relationships
    agent = db.relationship("Agent", backref=db.backref("histories", lazy=True))
    author = db.relationship(
        "User", backref=db.backref("agent_histories", lazy=True)
    )

    def __init__(
        self,
        agent_id: int,
        action_type: ActionType,
        author_id: Optional[int] = None,
        change_data: Optional[Dict[str, Any]] = None,
        version_id: Optional[str] = None,
    ):
        """
        Initialize a new AgentHistory instance.

        Args:
            agent_id: ID of the agent being modified
            action_type: Type of action performed
            author_id: Optional ID of the user who performed the action
            change_data: Optional JSON data (old_values, new_values, reason, etc.)
            version_id: Optional UUID for version tracking
        """
        self.agent_id = agent_id
        self.action_type = action_type
        self.author_id = author_id
        self.change_data = change_data or {}
        self.version_id = version_id

    def __repr__(self) -> str:
        return (
            f"<AgentHistory(id={self.id}, agent_id={self.agent_id}, "
            f"action={self.action_type.value}, timestamp={self.timestamp})>"
        )

    def to_dict(self) -> dict:
        """Convert agent history entry to dictionary for API responses."""
        return {
            "id": self.id,
            "agent_id": self.agent_id,
            "version_id": self.version_id,
            "action_type": self.action_type.value,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "author_id": self.author_id,
            "change_data": self.change_data,
            "is_restored": self.is_restored,
        }

    @classmethod
    def create(
        cls,
        agent_id: int,
        action_type: ActionType,
        author_id: Optional[int] = None,
        change_data: Optional[Dict[str, Any]] = None,
        version_id: Optional[str] = None,
    ) -> "AgentHistory":
        """
        Create a new agent history entry and save to database.

        Args:
            agent_id: ID of the agent being modified
            action_type: Type of action performed
            author_id: Optional ID of the user who performed the action
            change_data: Optional JSON data
            version_id: Optional UUID for version tracking

        Returns:
            The created AgentHistory instance
        """
        history = cls(
            agent_id=agent_id,
            action_type=action_type,
            author_id=author_id,
            change_data=change_data,
            version_id=version_id,
        )
        db.session.add(history)
        db.session.commit()
        return history

    @classmethod
    def get_by_agent(cls, agent_id: int) -> List["AgentHistory"]:
        """
        Get all history entries for a specific agent.

        Args:
            agent_id: ID of the agent

        Returns:
            List of AgentHistory instances
        """
        return cls.query.filter_by(agent_id=agent_id).order_by(
            cls.timestamp.desc()
        ).all()

    @classmethod
    def get_by_action_type(
        cls, agent_id: int, action_type: ActionType
    ) -> List["AgentHistory"]:
        """
        Get history entries for a specific agent and action type.

        Args:
            agent_id: ID of the agent
            action_type: Type of action to filter by

        Returns:
            List of AgentHistory instances
        """
        return (
            cls.query.filter_by(agent_id=agent_id, action_type=action_type)
            .order_by(cls.timestamp.desc())
            .all()
        )

    @classmethod
    def get_by_date_range(
        cls,
        agent_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List["AgentHistory"]:
        """
        Get history entries for a specific agent within a date range.

        Args:
            agent_id: ID of the agent
            start_date: Optional start date (inclusive)
            end_date: Optional end date (inclusive)

        Returns:
            List of AgentHistory instances
        """
        query = cls.query.filter_by(agent_id=agent_id).order_by(cls.timestamp.desc())

        if start_date:
            query = query.filter(cls.timestamp >= start_date)
        if end_date:
            query = query.filter(cls.timestamp <= end_date)

        return query.all()

    @classmethod
    def get_by_version(cls, version_id: str) -> Optional["AgentHistory"]:
        """
        Get a specific history entry by its version ID.

        Args:
            version_id: UUID of the version

        Returns:
            AgentHistory instance or None if not found
        """
        return cls.query.filter_by(version_id=version_id).first()

    @classmethod
    def get_all(cls, limit: int = 100, offset: int = 0) -> List["AgentHistory"]:
        """
        Get all history entries with pagination.

        Args:
            limit: Maximum number of entries to return (default: 100)
            offset: Number of entries to skip (default: 0)

        Returns:
            List of AgentHistory instances
        """
        return cls.query.order_by(cls.timestamp.desc()).offset(offset).limit(limit).all()

    @classmethod
    def get_by_author(cls, author_id: int, limit: int = 100, offset: int = 0) -> List["AgentHistory"]:
        """
        Get history entries by author ID.

        Args:
            author_id: ID of the author
            limit: Maximum number of entries to return (default: 100)
            offset: Number of entries to skip (default: 0)

        Returns:
            List of AgentHistory instances
        """
        return (
            cls.query.filter_by(author_id=author_id)
            .order_by(cls.timestamp.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

    @classmethod
    def delete_by_agent(cls, agent_id: int) -> int:
        """
        Delete all history entries for a specific agent.

        Args:
            agent_id: ID of the agent

        Returns:
            Number of entries deleted
        """
        result = cls.query.filter_by(agent_id=agent_id).delete()
        db.session.commit()
        return result

    def delete(self) -> None:
        """Delete this history entry from database."""
        db.session.delete(self)
        db.session.commit()
