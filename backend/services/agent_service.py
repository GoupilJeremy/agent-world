# ⚙️ Agent World - Agent Service
# Version: 0.1.0 (MVP)
# Description: Service pour la gestion des agents

"""
Agent Service for Agent World.

Ce service contient la logique métier pour la gestion des agents IA.
Il fait le lien entre les modèles de données et les contrôleurs.
"""

from typing import Any, Dict, List, Optional

from ..models.agent import Agent
from ..models.execution import Execution, ExecutionStatus


class AgentService:
    """
    Service class for managing agents.

    This service provides business logic for agent operations including
    creation, retrieval, update, deletion, and execution.
    """

    def __init__(self):
        """Initialize the AgentService."""
        self.agent_model = Agent

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

        return self.agent_model.create(**agent_data)

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

    def update_agent(self, agent_id: int, **kwargs) -> Optional[Agent]:
        """
        Update an agent.

        Args:
            agent_id: ID of the agent to update
            **kwargs: Agent attributes to update

        Returns:
            Updated Agent instance or None if not found

        Raises:
            ValueError: If another agent with same name exists
        """
        agent = self.get_agent(agent_id)
        if not agent:
            return None

        if "name" in kwargs:
            existing_agent = self.get_agent_by_name(kwargs["name"])
            if existing_agent and existing_agent.id != agent_id:
                raise ValueError(f'Agent with name "{kwargs["name"]}" already exists')

        agent.update(**kwargs)
        return agent

    def delete_agent(self, agent_id: int) -> bool:
        """
        Delete an agent.

        Args:
            agent_id: ID of the agent to delete

        Returns:
            True if deleted successfully, False otherwise
        """
        agent = self.get_agent(agent_id)
        if not agent:
            return False

        agent.delete()
        return True

    def run_agent(
        self,
        agent_id: int,
        input_data: Dict[str, Any],
        model: Optional[str] = None,
        configuration: Optional[Dict[str, Any]] = None,
        executed_by: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Run an agent with the given input.

        Args:
            agent_id: ID of the agent to run
            input_data: Input data for the execution
            model: Optional model override
            configuration: Optional configuration override
            executed_by: Optional ID of the user who initiated the execution

        Returns:
            Dictionary containing execution information

        Raises:
            ValueError: If agent not found or not active
        """
        agent = self.get_agent(agent_id)
        if not agent:
            raise ValueError(f"Agent with ID {agent_id} not found")

        if not agent.is_active:
            raise ValueError(f"Agent with ID {agent_id} is not active")

        # Use provided model or agent's default
        model_used = model or agent.model
        config_used = configuration or agent.configuration

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

        # Mark as running
        execution.start()

        # TODO: Actual AI model execution will be implemented in US-006
        # For MVP, we just simulate a successful execution
        # This is a placeholder - real implementation will call AIService

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

        return {
            "execution_id": execution.id,
            "agent_id": agent_id,
            "status": execution.status.value,
            "output": output_data,
            "duration_ms": execution.duration_ms,
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
