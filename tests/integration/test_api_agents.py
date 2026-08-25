# 🧪 Agent World - API Integration Tests
# Version: 0.1.0 (MVP)
# Description: Tests d'intégration pour l'API des agents

"""
Integration tests for the Agents API endpoints.

Ces tests vérifient le bon fonctionnement de l'API REST
pour la gestion des agents IA.
"""

import json

import pytest

from backend.app import create_app
from backend.config.settings import TestingConfig
from backend.models.base import db
from backend.models.execution import Execution, ExecutionStatus
from backend.models.generated_file import GeneratedFile


@pytest.fixture
def app():
    """Create and configure a new app instance for each test."""
    app = create_app(TestingConfig)

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
        assert data["status"] == ExecutionStatus.COMPLETED.value
        assert data["message"] == "Agent Run Agent execution completed"
        assert data["output"]["input"] == {"text": "Hello, world!"}

        execution = db.session.get(Execution, data["execution_id"])
        assert execution is not None
        assert execution.status == ExecutionStatus.COMPLETED
        assert execution.completed_at is not None
        assert execution.output_data == data["output"]

    def test_run_agent_can_catalog_a_smart_named_previewable_output(
        self, app, client, tmp_path
    ):
        """A saved execution is immediately available through the file catalogue."""

        app.extensions["file_service"].output_dir = tmp_path
        create_response = client.post(
            "/api/agents",
            data=json.dumps({"name": "File Agent", "model": "mistral-tiny"}),
            content_type="application/json",
        )
        agent_id = create_response.get_json()["id"]

        response = client.post(
            f"/api/agents/{agent_id}/run",
            data=json.dumps(
                {
                    "input": "Analyse the report",
                    "save": {"format": "md", "prefix": "Client"},
                }
            ),
            content_type="application/json",
        )

        assert response.status_code == 200
        payload = response.get_json()
        file_data = payload["file"]
        assert file_data["name"].startswith("client_mock_response_from_")
        assert file_data["name"].endswith(".md")
        assert file_data["execution_id"] == payload["execution_id"]
        assert file_data["management_token"]

        catalogued = db.session.get(GeneratedFile, file_data["id"])
        assert catalogued is not None
        assert catalogued.agent_id == agent_id
        preview = client.get(
            file_data["preview_url"],
            headers={"X-Management-Token": file_data["management_token"]},
        )
        assert preview.status_code == 200
        assert "Mock response" in preview.get_json()["html"]

    def test_run_agent_rejects_invalid_save_options_before_execution(
        self, app, client
    ):
        """Invalid file options never trigger the expensive execution."""

        create_response = client.post(
            "/api/agents",
            data=json.dumps({"name": "Invalid Save Agent"}),
            content_type="application/json",
        )
        agent_id = create_response.get_json()["id"]
        calls = []

        class StubAgentService:
            def run_agent(self, **kwargs):
                calls.append(kwargs)
                raise AssertionError("execution must not start")

        app.extensions["agent_service"] = StubAgentService()
        response = client.post(
            f"/api/agents/{agent_id}/run",
            data=json.dumps(
                {
                    "input": "Do not run",
                    "save": {"format": "json", "name": "report.md"},
                }
            ),
            content_type="application/json",
        )

        assert response.status_code == 400
        assert response.get_json()["code"] == "invalid_file"
        assert calls == []

    def test_run_agent_delegates_to_registered_service(self, app, client):
        """Test that the API uses the application AgentService instance."""
        create_response = client.post(
            "/api/agents",
            data=json.dumps({"name": "Delegated Agent", "model": "mistral-tiny"}),
            content_type="application/json",
        )
        agent_id = create_response.get_json()["id"]
        captured = {}

        class StubAgentService:
            def run_agent(self, **kwargs):
                captured.update(kwargs)
                return {
                    "execution_id": 42,
                    "agent_id": kwargs["agent_id"],
                    "status": ExecutionStatus.COMPLETED.value,
                    "output": {"result": "done"},
                    "duration_ms": 1,
                }

        app.extensions["agent_service"] = StubAgentService()

        response = client.post(
            f"/api/agents/{agent_id}/run",
            data=json.dumps(
                {
                    "input": "Delegate this",
                    "model": "gpt-4",
                    "configuration": {"temperature": 0.2},
                }
            ),
            content_type="application/json",
        )

        assert response.status_code == 200
        assert response.get_json()["status"] == ExecutionStatus.COMPLETED.value
        assert captured == {
            "agent_id": agent_id,
            "input_data": {"text": "Delegate this"},
            "model": "gpt-4",
            "configuration": {"temperature": 0.2},
        }

    def test_run_agent_preserves_an_explicit_empty_configuration(self, client):
        """Test that the API treats an empty configuration as an override."""
        create_response = client.post(
            "/api/agents",
            data=json.dumps(
                {
                    "name": "API Configuration Agent",
                    "configuration": {"temperature": 0.7},
                }
            ),
            content_type="application/json",
        )
        agent_id = create_response.get_json()["id"]

        response = client.post(
            f"/api/agents/{agent_id}/run",
            data=json.dumps({"input": "Override configuration", "configuration": {}}),
            content_type="application/json",
        )

        assert response.status_code == 200
        execution = db.session.get(Execution, response.get_json()["execution_id"])
        assert execution is not None
        assert execution.input_data["config"] == {}

    def test_run_agent_failure_is_persisted_as_failed(self, client, monkeypatch):
        """Test that a service failure cannot leave a running execution."""
        create_response = client.post(
            "/api/agents",
            data=json.dumps({"name": "API Failing Agent"}),
            content_type="application/json",
        )
        agent_id = create_response.get_json()["id"]

        def fail_completion(self, output_data):
            raise RuntimeError("provider failed")

        monkeypatch.setattr(Execution, "complete", fail_completion)

        response = client.post(
            f"/api/agents/{agent_id}/run",
            data=json.dumps({"input": "Trigger failure"}),
            content_type="application/json",
        )

        assert response.status_code == 500
        assert response.get_json()["error"] == "provider failed"
        [execution] = Execution.get_by_agent(agent_id)
        assert execution.status == ExecutionStatus.FAILED
        assert execution.error_message == "provider failed"
        assert execution.completed_at is not None

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

    def test_run_agent_rejects_oversized_request(self, app, client):
        """Test that Flask enforces the server-side request size limit."""
        create_response = client.post(
            "/api/agents",
            data=json.dumps({"name": "Oversized Request Agent"}),
            content_type="application/json",
        )
        agent_id = create_response.get_json()["id"]
        request_body = json.dumps({"input": "x" * app.config["MAX_CONTENT_LENGTH"]})

        assert len(request_body.encode("utf-8")) > app.config["MAX_CONTENT_LENGTH"]

        response = client.post(
            f"/api/agents/{agent_id}/run",
            data=request_body,
            content_type="application/json",
        )

        assert response.status_code == 413
        assert Execution.get_all() == []

    @pytest.mark.parametrize(
        ("payload", "expected_error"),
        [
            ({"input": "   "}, "Input must be a non-empty string"),
            ({"input": 42}, "Input must be a non-empty string"),
            ({"input": "ok", "model": ""}, "Model must be a non-empty string"),
            (
                {"input": "ok", "configuration": []},
                "Configuration must be an object",
            ),
        ],
    )
    def test_run_agent_rejects_invalid_payloads(self, client, payload, expected_error):
        """Test that execution payloads are validated before persistence."""
        create_response = client.post(
            "/api/agents",
            data=json.dumps({"name": f"Invalid {expected_error}"}),
            content_type="application/json",
        )
        agent_id = create_response.get_json()["id"]

        response = client.post(
            f"/api/agents/{agent_id}/run",
            data=json.dumps(payload),
            content_type="application/json",
        )

        assert response.status_code == 400
        assert response.get_json()["error"] == expected_error
        assert Execution.get_all() == []

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
