# 🧪 Agent World - Agent Model Tests
# Version: 0.1.0 (MVP)
# Description: Tests unitaires pour le modèle Agent

"""
Unit tests for the Agent model.

Ces tests vérifient le bon fonctionnement du modèle Agent
et de ses méthodes.
"""

from datetime import datetime

import pytest

from backend.app import create_app
from backend.models.agent import Agent
from backend.models.base import db


@pytest.fixture
def app():
    """Create and configure a new app instance for each test."""
    app = create_app()
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def client(app):
    """Create a test client for the app."""
    return app.test_client()


@pytest.fixture
def sample_agent():
    """Create a sample agent for testing."""
    return {
        "name": "Test Agent",
        "model": "mistral-tiny",
        "description": "A test agent for unit tests",
        "configuration": {"test": True},
        "is_active": True,
    }


class TestAgentModel:
    """Test cases for the Agent model."""

    def test_create_agent(self, app):
        """Test creating a new agent."""
        with app.app_context():
            agent_data = {
                "name": "Unit Test Agent",
                "model": "mistral-small",
                "description": "Agent for unit tests",
            }

            agent = Agent.create(**agent_data)

            assert agent.id is not None
            assert agent.name == "Unit Test Agent"
            assert agent.model == "mistral-small"
            assert agent.description == "Agent for unit tests"
            assert agent.is_active is True
            assert agent.created_at is not None
            assert agent.updated_at is not None

    def test_get_agent_by_id(self, app):
        """Test getting an agent by ID."""
        with app.app_context():
            # Create an agent
            agent_data = {"name": "Get By ID Agent", "model": "gpt-3.5-turbo"}
            created_agent = Agent.create(**agent_data)

            # Retrieve by ID
            retrieved_agent = Agent.get_by_id(created_agent.id)

            assert retrieved_agent is not None
            assert retrieved_agent.id == created_agent.id
            assert retrieved_agent.name == "Get By ID Agent"

    def test_get_agent_by_name(self, app):
        """Test getting an agent by name."""
        with app.app_context():
            # Create an agent
            agent_data = {"name": "Unique Name Agent", "model": "mistral-medium"}
            Agent.create(**agent_data)

            # Retrieve by name
            retrieved_agent = Agent.get_by_name("Unique Name Agent")

            assert retrieved_agent is not None
            assert retrieved_agent.name == "Unique Name Agent"

    def test_get_all_agents(self, app):
        """Test getting all agents."""
        with app.app_context():
            # Create multiple agents
            for i in range(3):
                Agent.create(name=f"Agent {i}", model="mistral-tiny")

            # Get all agents
            agents = Agent.get_all()

            assert len(agents) == 3

    def test_get_active_agents(self, app):
        """Test getting only active agents."""
        with app.app_context():
            # Create active and inactive agents
            Agent.create(name="Active Agent 1", model="mistral-tiny", is_active=True)
            Agent.create(name="Inactive Agent", model="mistral-tiny", is_active=False)
            Agent.create(name="Active Agent 2", model="mistral-tiny", is_active=True)

            # Get only active agents
            active_agents = Agent.get_active()

            assert len(active_agents) == 2
            for agent in active_agents:
                assert agent.is_active is True

    def test_update_agent(self, app):
        """Test updating an agent."""
        with app.app_context():
            # Create an agent
            agent = Agent.create(name="Update Test Agent", model="mistral-tiny")

            # Update the agent
            agent.update(name="Updated Agent", description="Updated description")

            # Refresh from database
            updated_agent = Agent.get_by_id(agent.id)

            assert updated_agent.name == "Updated Agent"
            assert updated_agent.description == "Updated description"

    def test_delete_agent(self, app):
        """Test deleting an agent."""
        with app.app_context():
            # Create an agent
            agent = Agent.create(name="Delete Test Agent", model="mistral-tiny")
            agent_id = agent.id

            # Delete the agent
            agent.delete()

            # Verify deletion
            deleted_agent = Agent.get_by_id(agent_id)
            assert deleted_agent is None

    def test_agent_to_dict(self, app):
        """Test converting agent to dictionary."""
        with app.app_context():
            agent_data = {
                "name": "Dict Test Agent",
                "model": "mistral-large",
                "description": "Agent for dict test",
            }
            agent = Agent.create(**agent_data)

            agent_dict = agent.to_dict()

            assert agent_dict["id"] == agent.id
            assert agent_dict["name"] == "Dict Test Agent"
            assert agent_dict["model"] == "mistral-large"
            assert agent_dict["description"] == "Agent for dict test"
            assert "created_at" in agent_dict
            assert "updated_at" in agent_dict

    def test_agent_repr(self, app):
        """Test agent string representation."""
        with app.app_context():
            agent = Agent.create(name="Repr Test Agent", model="gpt-4")

            repr_str = repr(agent)

            assert "Agent" in repr_str
            assert str(agent.id) in repr_str
            assert "Repr Test Agent" in repr_str
            assert "gpt-4" in repr_str

    def test_duplicate_agent_name(self, app):
        """Test that duplicate agent names are not allowed."""
        with app.app_context():
            # Create first agent
            Agent.create(name="Duplicate Name", model="mistral-tiny")

            # Try to create second agent with same name
            from sqlalchemy.exc import IntegrityError

            with pytest.raises(IntegrityError):
                Agent.create(name="Duplicate Name", model="gpt-3.5-turbo")
                db.session.commit()

    def test_agent_default_values(self, app):
        """Test agent default values."""
        with app.app_context():
            # Create agent with minimal data
            agent = Agent.create(name="Minimal Agent")

            assert agent.model == "mistral-tiny"
            assert agent.is_active is True
            assert agent.configuration == {}
            assert agent.description == "Agent using mistral-tiny model"
