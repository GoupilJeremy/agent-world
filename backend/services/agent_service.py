# ⚙️ Agent World - Agent Service
# Version: 0.1.0 (MVP)
# Description: Service pour la gestion des agents

"""
Agent Service for Agent World.

Ce service contient la logique métier pour la gestion des agents IA.
Il fait le lien entre les modèles de données et les contrôleurs.
"""

import logging
from typing import Any, Dict, List, Optional

from ..models.agent import Agent
from ..models.agent_history import ActionType
from ..models.base import db
from ..models.execution import Execution, ExecutionStatus
from .agent_cache_service import get_agent_cache_service


class AgentService:
    """
    Service class for managing agents.

    This service provides business logic for agent operations including
    creation, retrieval, update, deletion, and execution.
    """

    def __init__(self, history_service=None):
        """Initialize the AgentService."""
        self.agent_model = Agent
        self.history_service = history_service

    def create_agent(
        self,
        name: str,
        model: str = "mistral-tiny",
        description: Optional[str] = None,
        configuration: Optional[Dict[str, Any]] = None,
        is_active: bool = True,
        created_by: Optional[int] = None,
    ) -> Agent:
        """
        Create a new agent.

        Args:
            name: Name of the agent
            model: AI model to use (default: 'mistral-tiny')
            description: Optional description
            configuration: Optional JSON configuration
            is_active: Whether the agent is active (default: True)
            created_by: ID of the creating user

        Returns:
            The created Agent instance

        Raises:
            ValueError: If agent with same name already exists
        """
        existing_agent = self.agent_model.get_by_name(name)
        if existing_agent:
            raise ValueError(f'Agent with name "{name}" already exists')

        agent_data = {
            "name": name,
            "model": model,
            "description": description or f"Agent using {model} model",
            "configuration": configuration or {},
            "is_active": is_active,
            "created_by": created_by,
        }

        agent = self.agent_model.create(**agent_data)

        # Log the creation in history
        if self.history_service:
            self.history_service.log_agent_change(
                agent_id=agent.id,
                action_type=ActionType.CREATE,
                author_id=created_by,
                new_values=agent.to_dict(),
                reason="Agent created",
            )

        return agent

    def get_agent(self, agent_id: int) -> Optional[Agent]:
        """
        Get an agent by ID.

        Args:
            agent_id: ID of the agent to retrieve

        Returns:
            Agent instance or None if not found
        """
        return self.agent_model.get_by_id(agent_id)

    def get_agent_by_name(self, name: str) -> Optional[Agent]:
        """
        Get an agent by name.

        Args:
            name: Name of the agent to retrieve

        Returns:
            Agent instance or None if not found
        """
        return self.agent_model.get_by_name(name)

    def get_all_agents(self, only_active: bool = False) -> List[Agent]:
        """
        Get all agents.

        Args:
            only_active: If True, only return active agents (default: False)

        Returns:
            List of Agent instances
        """
        if only_active:
            return self.agent_model.get_active()
        return self.agent_model.get_all()

    def update_agent(
        self, agent_id: int, author_id: Optional[int] = None, **kwargs
    ) -> Optional[Agent]:
        """
        Update an agent.

        Args:
            agent_id: ID of the agent to update
            author_id: Optional ID of the user performing the update
            **kwargs: Agent attributes to update

        Returns:
            Updated Agent instance or None if not found

        Raises:
            ValueError: If another agent with same name exists
        """
        agent = self.get_agent(agent_id)
        if not agent:
            return None

        # Store old values for history
        old_values = agent.to_dict()

        if "name" in kwargs:
            existing_agent = self.get_agent_by_name(kwargs["name"])
            if existing_agent and existing_agent.id != agent_id:
                raise ValueError(f'Agent with name "{kwargs["name"]}" already exists')

        agent.update(**kwargs)

        # Log the update in history
        if self.history_service:
            self.history_service.log_agent_change(
                agent_id=agent.id,
                action_type=ActionType.UPDATE,
                author_id=author_id,
                old_values=old_values,
                new_values=agent.to_dict(),
                reason="Agent updated",
            )

        return agent

    def delete_agent(self, agent_id: int, author_id: Optional[int] = None) -> bool:
        """
        Delete an agent.

        Args:
            agent_id: ID of the agent to delete
            author_id: Optional ID of the user performing the deletion

        Returns:
            True if deleted successfully, False otherwise
        """
        agent = self.get_agent(agent_id)
        if not agent:
            return False

        # Store agent data for history before deletion
        old_values = agent.to_dict()

        # Log the deletion in history
        if self.history_service:
            self.history_service.log_agent_change(
                agent_id=agent.id,
                action_type=ActionType.DELETE,
                author_id=author_id,
                old_values=old_values,
                reason="Agent deleted",
            )

        agent.delete()
        return True

    def run_agent(
        self,
        agent_id: int,
        input_data: Dict[str, Any],
        model: Optional[str] = None,
        configuration: Optional[Dict[str, Any]] = None,
        executed_by: Optional[int] = None,
        use_cache: bool = True,
    ) -> Dict[str, Any]:
        """
        Run an agent with the given input.

        Args:
            agent_id: ID of the agent to run
            input_data: Input data for the execution
            model: Optional model override
            configuration: Optional configuration override
            executed_by: Optional ID of the user who initiated the execution
            use_cache: Whether to use cached results if available (default: True)

        Returns:
            Dictionary containing execution information

        Raises:
            ValueError: If agent not found or not active
        """
        logger = logging.getLogger(__name__)
        agent = self.get_agent(agent_id)
        if not agent:
            raise ValueError(f"Agent with ID {agent_id} not found")

        if not agent.is_active:
            raise ValueError(f"Agent with ID {agent_id} is not active")

        # Use provided model or agent's default
        model_used = model or agent.model
        config_used = agent.configuration if configuration is None else configuration

        # Vérifier le cache si activé
        if use_cache:
            agent_cache = get_agent_cache_service()
            cached_result = agent_cache.get_execution_result(
                agent_id=agent_id,
                input_data=input_data,
                model=model_used,
                configuration=config_used,
            )

            if cached_result is not None:
                logger.info(f"✅ Cache hit for agent {agent_id} execution")
                # Retourner le résultat en cache avec un flag
                return {
                    **cached_result,
                    "from_cache": True,
                    "cache_hit": True,
                }

        # Create execution record
        execution = Execution.create(
            agent_id=agent_id,
            input_data={
                "text": input_data.get("text", ""),
                "model": model_used,
                "config": config_used,
            },
            model_used=model_used,
            executed_by=executed_by,
        )

        # TODO: Actual AI model execution will be implemented in US-006
        # For MVP, we just simulate a successful execution
        # This is a placeholder - real implementation will call AIService

        try:
            # Mark as running only once failure handling is in place. The
            # execution record was already committed by ``Execution.create``.
            execution.start()

            # Simulate execution (remove this in production)
            import time

            time.sleep(0.1)  # Simulate processing time

            # Mock output
            output_data = {
                "result": f"Mock response from {model_used} for agent {agent.name}",
                "input": input_data,
                "model": model_used,
                "timestamp": execution.created_at.isoformat(),
            }

            execution.complete(output_data)

            # Mettre en cache le résultat
            if use_cache:
                agent_cache = get_agent_cache_service()
                agent_cache.cache_execution_result(
                    agent_id=agent_id,
                    input_data=input_data,
                    result={
                        "execution_id": execution.id,
                        "agent_id": agent_id,
                        "status": execution.status.value,
                        "output": output_data,
                        "duration_ms": execution.duration_ms,
                    },
                    model=model_used,
                    configuration=config_used,
                )
                logger.info(f"📦 Cached agent {agent_id} execution result")

        except Exception as error:
            # ``start`` and ``complete`` commit independently. Roll back first
            # so a failed flush/commit cannot prevent the terminal FAILED state
            # from being persisted in a fresh transaction.
            db.session.rollback()
            try:
                execution.fail(str(error))
            except Exception:
                db.session.rollback()
            raise

        return {
            "execution_id": execution.id,
            "agent_id": agent_id,
            "status": execution.status.value,
            "output": output_data,
            "duration_ms": execution.duration_ms,
            "from_cache": False,
            "cache_hit": False,
        }

    def get_agent_executions(
        self, agent_id: int, limit: int = 10, offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get executions for a specific agent.

        Args:
            agent_id: ID of the agent
            limit: Maximum number of executions to return (default: 10)
            offset: Number of executions to skip (default: 0)

        Returns:
            List of execution dictionaries
        """
        executions = Execution.get_by_agent(agent_id)
        return [e.to_dict() for e in executions[offset : offset + limit]]

    def search_agents(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search agents by name or description.

        Args:
            query: Search query string
            limit: Maximum number of results to return (default: 10)

        Returns:
            List of matching agent dictionaries
        """
        agents = (
            self.agent_model.query.filter(
                (Agent.name.ilike(f"%{query}%"))
                | (Agent.description.ilike(f"%{query}%"))
            )
            .limit(limit)
            .all()
        )

        return [agent.to_dict() for agent in agents]

    def get_agent_statistics(self, agent_id: int) -> Dict[str, Any]:
        """
        Get statistics for a specific agent.

        Args:
            agent_id: ID of the agent

        Returns:
            Dictionary containing agent statistics
        """
        agent = self.get_agent(agent_id)
        if not agent:
            return {}

        executions = Execution.get_by_agent(agent_id)

        # Count executions by status
        status_counts = {}
        for status in ExecutionStatus:
            count = len([e for e in executions if e.status == status])
            status_counts[status.value] = count

        # Calculate average duration
        durations = [e.duration_ms for e in executions if e.duration_ms]
        avg_duration = sum(durations) / len(durations) if durations else 0

        return {
            "agent_id": agent_id,
            "total_executions": len(executions),
            "status_counts": status_counts,
            "average_duration_ms": avg_duration,
            "models_used": list(set(e.model_used for e in executions)),
        }
