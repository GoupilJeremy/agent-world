# 🧪 Agent World - API Integration Tests
# Version: 0.1.0 (MVP)
# Description: Tests d'intégration pour l'API des agents

"""
Integration tests for the Agents API endpoints.

Ces tests vérifient le bon fonctionnement de l'API REST
pour la gestion des agents IA.
"""

import pytest
import json
from backend.app import create_app
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


class TestAgentsAPI:
    """Test cases for the Agents API endpoints."""

    def test_list_agents_empty(self, client):
        """Test listing agents when no agents exist."""
        response = client.get("/api/agents")

        assert response.status_code == 200
        assert response.get_json() == []

    def test_create_agent(self, client):
        """Test creating a new agent."""
        agent_data = {
            "name": "API Test Agent",
            "model": "mistral-small",
            "description": "Agent for API tests",
        }

        response = client.post(
            "/api/agents", data=json.dumps(agent_data), content_type="application/json"
        )

        assert response.status_code == 201

        data = response.get_json()
        assert data["name"] == "API Test Agent"
        assert data["model"] == "mistral-small"
        assert data["description"] == "Agent for API tests"
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data

    def test_create_agent_duplicate_name(self, client):
        """Test creating an agent with duplicate name."""
        # Create first agent
        agent_data = {"name": "Duplicate Agent", "model": "mistral-tiny"}
        client.post(
            "/api/agents", data=json.dumps(agent_data), content_type="application/json"
        )

        # Try to create duplicate
        response = client.post(
            "/api/agents", data=json.dumps(agent_data), content_type="application/json"
        )

        assert response.status_code == 409
        assert "already exists" in response.get_json()["error"]

    def test_list_agents(self, client):
        """Test listing all agents."""
        # Create multiple agents
        for i in range(3):
            agent_data = {"name": f"API Agent {i}", "model": "mistral-tiny"}
            client.post(
                "/api/agents",
                data=json.dumps(agent_data),
                content_type="application/json",
            )

        response = client.get("/api/agents")

        assert response.status_code == 200

        data = response.get_json()
        assert len(data) == 3

    def test_get_agent(self, client):
        """Test getting a specific agent."""
        # Create an agent
        create_response = client.post(
            "/api/agents",
            data=json.dumps({"name": "Get Agent", "model": "gpt-4"}),
            content_type="application/json",
        )
        agent_id = create_response.get_json()["id"]

        # Get the agent
        response = client.get(f"/api/agents/{agent_id}")

        assert response.status_code == 200

        data = response.get_json()
        assert data["id"] == agent_id
        assert data["name"] == "Get Agent"
        assert data["model"] == "gpt-4"

    def test_get_agent_not_found(self, client):
        """Test getting a non-existent agent."""
        response = client.get("/api/agents/99999")

        assert response.status_code == 404
        assert "not found" in response.get_json()["error"]

    def test_update_agent(self, client):
        """Test updating an agent."""
        # Create an agent
        create_response = client.post(
            "/api/agents",
            data=json.dumps({"name": "Update Agent", "model": "mistral-tiny"}),
            content_type="application/json",
        )
        agent_id = create_response.get_json()["id"]

        # Update the agent
        update_data = {
            "name": "Updated Agent",
            "description": "Updated description",
            "model": "gpt-4",
        }
        response = client.put(
            f"/api/agents/{agent_id}",
            data=json.dumps(update_data),
            content_type="application/json",
        )

        assert response.status_code == 200

        data = response.get_json()
        assert data["name"] == "Updated Agent"
        assert data["description"] == "Updated description"
        assert data["model"] == "gpt-4"

    def test_update_agent_not_found(self, client):
        """Test updating a non-existent agent."""
        update_data = {"name": "Nonexistent"}
        response = client.put(
            "/api/agents/99999",
            data=json.dumps(update_data),
            content_type="application/json",
        )

        assert response.status_code == 404
        assert "not found" in response.get_json()["error"]

    def test_delete_agent(self, client):
        """Test deleting an agent."""
        # Create an agent
        create_response = client.post(
            "/api/agents",
            data=json.dumps({"name": "Delete Agent", "model": "mistral-tiny"}),
            content_type="application/json",
        )
        agent_id = create_response.get_json()["id"]

        # Delete the agent
        response = client.delete(f"/api/agents/{agent_id}")

        assert response.status_code == 204

        # Verify deletion
        get_response = client.get(f"/api/agents/{agent_id}")
        assert get_response.status_code == 404

    def test_delete_agent_not_found(self, client):
        """Test deleting a non-existent agent."""
        response = client.delete("/api/agents/99999")

        assert response.status_code == 404
        assert "not found" in response.get_json()["error"]

    def test_run_agent(self, client):
        """Test running an agent."""
        # Create an agent
        create_response = client.post(
            "/api/agents",
            data=json.dumps({"name": "Run Agent", "model": "mistral-tiny"}),
            content_type="application/json",
        )
        agent_id = create_response.get_json()["id"]

        # Run the agent
        run_data = {"input": "Hello, world!"}
        response = client.post(
            f"/api/agents/{agent_id}/run",
            data=json.dumps(run_data),
            content_type="application/json",
        )

        assert response.status_code == 200

        data = response.get_json()
        assert "execution_id" in data
        assert data["agent_id"] == agent_id
        assert "status" in data

    def test_run_agent_not_found(self, client):
        """Test running a non-existent agent."""
        run_data = {"input": "Hello"}
        response = client.post(
            "/api/agents/99999/run",
            data=json.dumps(run_data),
            content_type="application/json",
        )

        assert response.status_code == 404
        assert "not found" in response.get_json()["error"]

    def test_run_agent_missing_input(self, client):
        """Test running an agent without input."""
        # Create an agent
        create_response = client.post(
            "/api/agents",
            data=json.dumps({"name": "Run Agent", "model": "mistral-tiny"}),
            content_type="application/json",
        )
        agent_id = create_response.get_json()["id"]

        # Run without input
        response = client.post(
            f"/api/agents/{agent_id}/run", content_type="application/json"
        )

        assert response.status_code == 400
        assert "Input is required" in response.get_json()["error"]

    def test_health_check(self, client):
        """Test the health check endpoint."""
        response = client.get("/health")

        assert response.status_code == 200

        data = response.get_json()
        assert data["status"] == "healthy"
        assert data["version"] == "0.1.0"
        assert data["service"] == "agent-world-backend"

    def test_root_endpoint(self, client):
        """Test the root endpoint."""
        response = client.get("/")

        assert response.status_code == 200

        data = response.get_json()
        assert data["name"] == "Agent World API"
        assert data["version"] == "0.1.0"
        assert "docs" in data
        assert "health" in data
