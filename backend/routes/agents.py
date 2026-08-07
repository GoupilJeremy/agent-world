# 📡 Agent World - Agents Routes
# Version: 0.1.0 (MVP)
# Description: Endpoints REST pour la gestion des agents

"""
Agents Routes for Agent World API.

Ce module contient tous les endpoints REST pour la gestion des agents IA.
Il implémente les opérations CRUD de base.
"""

from flask import request, jsonify
from flask_restful import Resource, reqparse
from ..models.agent import Agent
from ..models.base import db
from ..services.agent_service import AgentService

# Initialize parser for request parsing
parser = reqparse.RequestParser()
parser.add_argument("name", type=str, required=True, help="Agent name is required")
parser.add_argument("description", type=str, help="Agent description")
parser.add_argument(
    "model",
    type=str,
    default="mistral-tiny",
    help="AI model to use (default: mistral-tiny)",
)
parser.add_argument(
    "configuration", type=dict, default={}, help="Agent configuration as JSON"
)
parser.add_argument(
    "is_active",
    type=bool,
    default=True,
    help="Whether the agent is active (default: True)",
)


class AgentListResource(Resource):
    """Resource for listing and creating agents."""

    def get(self):
        """
        List all agents.

        ---
        responses:
          200:
            description: A list of all agents
            content:
              application/json:
                schema:
                  type: array
                  items:
                    $ref: '#/components/schemas/Agent'
        """
        agents = Agent.get_all()
        return [agent.to_dict() for agent in agents], 200

    def post(self):
        """
        Create a new agent.

        ---
        requestBody:
          required: true
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/AgentInput'
        responses:
          201:
            description: The created agent
            content:
              application/json:
                schema:
                  $ref: '#/components/schemas/Agent'
          400:
            description: Invalid input data
        """
        args = parser.parse_args()

        # Check if agent with same name already exists
        existing_agent = Agent.get_by_name(args.name)
        if existing_agent:
            return {"error": f'Agent with name "{args.name}" already exists'}, 409

        # Create new agent
        agent_data = {
            "name": args.name,
            "description": args.description,
            "model": args.model,
            "configuration": args.configuration,
            "is_active": args.is_active,
        }

        try:
            agent = Agent.create(**agent_data)
            return agent.to_dict(), 201
        except Exception as e:
            db.session.rollback()
            return {"error": str(e)}, 500


class AgentResource(Resource):
    """Resource for individual agent operations."""

    def get(self, agent_id):
        """
        Get a specific agent by ID.

        ---
        parameters:
          - in: path
            name: agent_id
            schema:
              type: integer
            required: true
        responses:
          200:
            description: The requested agent
            content:
              application/json:
                schema:
                  $ref: '#/components/schemas/Agent'
          404:
            description: Agent not found
        """
        agent = Agent.get_by_id(agent_id)
        if not agent:
            return {"error": f"Agent with ID {agent_id} not found"}, 404

        return agent.to_dict(), 200

    def put(self, agent_id):
        """
        Update an existing agent.

        ---
        parameters:
          - in: path
            name: agent_id
            schema:
              type: integer
            required: true
        requestBody:
          required: true
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/AgentInput'
        responses:
          200:
            description: The updated agent
            content:
              application/json:
                schema:
                  $ref: '#/components/schemas/Agent'
          404:
            description: Agent not found
        """
        agent = Agent.get_by_id(agent_id)
        if not agent:
            return {"error": f"Agent with ID {agent_id} not found"}, 404

        args = parser.parse_args()

        # Check if another agent with same name exists
        existing_agent = Agent.get_by_name(args.name)
        if existing_agent and existing_agent.id != agent_id:
            return {"error": f'Agent with name "{args.name}" already exists'}, 409

        update_data = {}
        if args.name:
            update_data["name"] = args.name
        if args.description:
            update_data["description"] = args.description
        if args.model:
            update_data["model"] = args.model
        if args.configuration:
            update_data["configuration"] = args.configuration
        if args.is_active is not None:
            update_data["is_active"] = args.is_active

        try:
            agent.update(**update_data)
            return agent.to_dict(), 200
        except Exception as e:
            db.session.rollback()
            return {"error": str(e)}, 500

    def delete(self, agent_id):
        """
        Delete an agent.

        ---
        parameters:
          - in: path
            name: agent_id
            schema:
              type: integer
            required: true
        responses:
          204:
            description: Agent deleted successfully
          404:
            description: Agent not found
        """
        agent = Agent.get_by_id(agent_id)
        if not agent:
            return {"error": f"Agent with ID {agent_id} not found"}, 404

        try:
            agent.delete()
            return "", 204
        except Exception as e:
            db.session.rollback()
            return {"error": str(e)}, 500


class AgentRunResource(Resource):
    """Resource for running an agent."""

    def post(self, agent_id):
        """
        Run an agent with the given input.

        ---
        parameters:
          - in: path
            name: agent_id
            schema:
              type: integer
            required: true
        requestBody:
          required: true
          content:
            application/json:
              schema:
                type: object
                properties:
                  input:
                    type: string
                    description: The input text for the agent
                  model:
                    type: string
                    description: Override the default model
                  configuration:
                    type: object
                    description: Override the agent configuration
        responses:
          200:
            description: Execution started successfully
            content:
              application/json:
                schema:
                  type: object
                  properties:
                    execution_id:
                      type: integer
                    message:
                      type: string
          404:
            description: Agent not found
          400:
            description: Invalid input
        """
        from ..models.execution import Execution, ExecutionStatus

        agent = Agent.get_by_id(agent_id)
        if not agent:
            return {"error": f"Agent with ID {agent_id} not found"}, 404

        if not agent.is_active:
            return {"error": f"Agent with ID {agent_id} is not active"}, 400

        data = request.get_json()
        if not data or "input" not in data:
            return {"error": "Input is required"}, 400

        input_data = data.get("input", "")
        model = data.get("model", agent.model)
        config = data.get("configuration", agent.configuration)

        try:
            # Create execution record
            execution = Execution.create(
                agent_id=agent_id,
                input_data={"text": input_data, "model": model, "config": config},
                model_used=model,
            )

            # Mark as running
            execution.start()

            # TODO: Here we would actually run the agent
            # For MVP, we just return the execution ID
            # US-006 will implement the actual AI model integration

            return {
                "execution_id": execution.id,
                "message": f"Agent {agent.name} execution started",
                "status": execution.status.value,
            }, 200
        except Exception as e:
            db.session.rollback()
            return {"error": str(e)}, 500


# Register resources with the blueprint
def register_resources(api):
    """Register agent resources with the Flask-RESTful API."""
    api.add_resource(AgentListResource, "/agents")
    api.add_resource(AgentResource, "/agents/<int:agent_id>")
    api.add_resource(AgentRunResource, "/agents/<int:agent_id>/run")
