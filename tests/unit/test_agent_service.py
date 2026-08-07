# 🧪 Agent World - Agent Service Tests
# Version: 0.1.0 (MVP)
# Description: Tests unitaires pour le service AgentService

"""
Unit tests for the AgentService.

Ces tests vérifient le bon fonctionnement du service de gestion des agents.
"""

import pytest

from backend.app import create_app
from backend.config.settings import TestingConfig
from backend.models.agent import Agent
from backend.models.base import db
from backend.services.agent_service import AgentService


@pytest.fixture
def app():
    """Create and configure a new app instance for each test."""
    app = create_app(TestingConfig)

    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def agent_service(app):
    """Create an AgentService instance for testing."""
    return AgentService()


class TestAgentService:
    """Test cases for the AgentService."""

    def test_create_agent(self, app, agent_service):
        """Test creating an agent through the service."""
        with app.app_context():
            agent = agent_service.create_agent(
                name="Service Test Agent",
                model="mistral-small",
                description="Agent created via service",
            )

            assert agent is not None
            assert agent.name == "Service Test Agent"
            assert agent.model == "mistral-small"

    def test_create_agent_duplicate_name(self, app, agent_service):
        """Test that creating an agent with duplicate name raises error."""
        with app.app_context():
            agent_service.create_agent(name="Duplicate Agent")

            with pytest.raises(ValueError) as exc_info:
                agent_service.create_agent(name="Duplicate Agent")

            assert "already exists" in str(exc_info.value)

    def test_get_agent(self, app, agent_service):
        """Test getting an agent through the service."""
        with app.app_context():
            # Create an agent directly
            agent = Agent.create(name="Get Test Agent", model="gpt-4")

            # Get through service
            retrieved_agent = agent_service.get_agent(agent.id)

            assert retrieved_agent is not None
            assert retrieved_agent.id == agent.id

    def test_get_agent_not_found(self, app, agent_service):
        """Test getting a non-existent agent."""
        with app.app_context():
            agent = agent_service.get_agent(99999)
            assert agent is None

    def test_get_agent_by_name(self, app, agent_service):
        """Test getting an agent by name through the service."""
        with app.app_context():
            agent_service.create_agent(name="Name Test Agent")

            agent = agent_service.get_agent_by_name("Name Test Agent")

            assert agent is not None
            assert agent.name == "Name Test Agent"

    def test_get_all_agents(self, app, agent_service):
        """Test getting all agents through the service."""
        with app.app_context():
            # Create agents
            agent_service.create_agent(name="Agent 1")
            agent_service.create_agent(name="Agent 2")
            agent_service.create_agent(name="Agent 3", is_active=False)

            # Get all agents
            agents = agent_service.get_all_agents()
            assert len(agents) == 3

            # Get only active agents
            active_agents = agent_service.get_all_agents(only_active=True)
            assert len(active_agents) == 2

    def test_update_agent(self, app, agent_service):
        """Test updating an agent through the service."""
        with app.app_context():
            agent = agent_service.create_agent(name="Update Agent")

            updated_agent = agent_service.update_agent(
                agent.id, name="Updated Agent", description="Updated description"
            )

            assert updated_agent is not None
            assert updated_agent.name == "Updated Agent"
            assert updated_agent.description == "Updated description"

    def test_update_agent_not_found(self, app, agent_service):
        """Test updating a non-existent agent."""
        with app.app_context():
            agent = agent_service.update_agent(99999, name="Nonexistent")
            assert agent is None

    def test_delete_agent(self, app, agent_service):
        """Test deleting an agent through the service."""
        with app.app_context():
            agent = agent_service.create_agent(name="Delete Agent")
            agent_id = agent.id

            success = agent_service.delete_agent(agent_id)

            assert success is True

            # Verify deletion
            deleted_agent = agent_service.get_agent(agent_id)
            assert deleted_agent is None

    def test_delete_agent_not_found(self, app, agent_service):
        """Test deleting a non-existent agent."""
        with app.app_context():
            success = agent_service.delete_agent(99999)
            assert success is False

    def test_run_agent(self, app, agent_service):
        """Test running an agent through the service."""
        with app.app_context():
            agent = agent_service.create_agent(name="Run Agent")

            result = agent_service.run_agent(
                agent_id=agent.id, input_data={"text": "Hello, world!"}
            )

            assert result is not None
            assert "execution_id" in result
            assert "agent_id" in result
            assert "status" in result
            assert result["agent_id"] == agent.id

    def test_run_agent_not_found(self, app, agent_service):
        """Test running a non-existent agent."""
        with app.app_context():
            with pytest.raises(ValueError) as exc_info:
                agent_service.run_agent(agent_id=99999, input_data={"text": "Hello"})

            assert "not found" in str(exc_info.value)

    def test_run_inactive_agent(self, app, agent_service):
        """Test running an inactive agent."""
        with app.app_context():
            agent = agent_service.create_agent(name="Inactive Agent", is_active=False)

            with pytest.raises(ValueError) as exc_info:
                agent_service.run_agent(agent_id=agent.id, input_data={"text": "Hello"})

            assert "not active" in str(exc_info.value)

    def test_search_agents(self, app, agent_service):
        """Test searching agents."""
        with app.app_context():
            agent_service.create_agent(
                name="Search Test Agent", description="Test agent"
            )
            agent_service.create_agent(name="Another Agent", description="Different")
            agent_service.create_agent(name="Test Agent 2", description="Another test")

            results = agent_service.search_agents("test", limit=10)

            assert len(results) >= 2  # Should find at least 2 agents with 'test'

    def test_get_agent_statistics(self, app, agent_service):
        """Test getting agent statistics."""
        with app.app_context():
            agent = agent_service.create_agent(name="Stats Agent")

            # Run the agent a few times
            for i in range(3):
                agent_service.run_agent(
                    agent_id=agent.id, input_data={"text": f"Test run {i}"}
                )

            stats = agent_service.get_agent_statistics(agent.id)

            assert stats is not None
            assert stats["agent_id"] == agent.id
            assert stats["total_executions"] == 3
