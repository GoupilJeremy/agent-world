# 📡 Agent World - Agents Routes
# Version: 0.1.0 (MVP)
# Description: Endpoints REST pour la gestion des agents

"""
Agents Routes for Agent World API.

Ce module contient tous les endpoints REST pour la gestion des agents IA.
Il implémente les opérations CRUD de base.
"""

import json

from flask import current_app, request
from flask_restful import Resource, reqparse

from ..models.agent import Agent
from ..models.base import db
from ..services.cache_service import cache_response, invalidate_cache
from ..services.file_naming import generate_filename, normalize_extension
from ..services.file_service import FileServiceError, FileValidationError
from ..services.pagination_service import PaginationService

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


def _parse_save_request(data):
    """Validate the optional generated-file request before executing an agent."""

    value = data.get("save", False)
    if value is False or value is None:
        return None
    if value is True:
        options = {}
    elif isinstance(value, dict):
        options = dict(value)
    else:
        raise FileValidationError("save must be a boolean or an object")

    allowed = {"format", "name", "prefix", "suffix", "is_temporary"}
    unknown = set(options) - allowed
    if unknown:
        raise FileValidationError(f"Unknown save option: {sorted(unknown)[0]}")

    try:
        file_format = normalize_extension(options.get("format", "json"))
    except (TypeError, ValueError) as exc:
        raise FileValidationError(str(exc)) from exc

    name = options.get("name")
    if name is not None:
        if not isinstance(name, str) or not name.strip():
            raise FileValidationError("save.name must be a non-empty string")
        if options.get("prefix") is not None or options.get("suffix") is not None:
            raise FileValidationError(
                "save.prefix and save.suffix cannot be combined with save.name"
            )
        extension = name.rsplit(".", 1)[-1] if "." in name else None
        if extension is not None:
            try:
                inferred = normalize_extension(extension)
            except (TypeError, ValueError) as exc:
                raise FileValidationError(str(exc)) from exc
            if inferred != file_format:
                raise FileValidationError("save.name extension must match save.format")

    for key in ("prefix", "suffix"):
        if (
            key in options
            and options[key] is not None
            and not isinstance(options[key], str)
        ):
            raise FileValidationError(f"save.{key} must be a string")
    is_temporary = options.get("is_temporary", False)
    if not isinstance(is_temporary, bool):
        raise FileValidationError("save.is_temporary must be a boolean")

    return {
        "format": file_format,
        "name": name.strip() if isinstance(name, str) else None,
        "prefix": options.get("prefix"),
        "suffix": options.get("suffix"),
        "is_temporary": is_temporary,
    }


def _generated_content(result):
    """Return the semantic generated content used for names and text exports."""

    output = result.get("output", result)
    if isinstance(output, str):
        return output
    if isinstance(output, dict):
        for key in ("title", "summary", "result", "answer"):
            candidate = output.get(key)
            if isinstance(candidate, str) and candidate.strip():
                return candidate
    return json.dumps(output, ensure_ascii=False, sort_keys=True)


class AgentListResource(Resource):
    """Resource for listing and creating agents."""

    @cache_response(timeout=300, key_prefix="agents:list")
    def get(self):
        """
        List all agents with pagination support.

        ---
        parameters:
          - in: query
            name: page
            schema:
              type: integer
              default: 1
            description: Page number (1-based)
          - in: query
            name: per_page
            schema:
              type: integer
              default: 20
              maximum: 100
            description: Number of items per page
        responses:
          200:
            description: Paginated list of agents
            content:
              application/json:
                schema:
                  type: object
                  properties:
                    items:
                      type: array
                      items:
                        $ref: '#/components/schemas/Agent'
                    pagination:
                      type: object
                      properties:
                        total:
                          type: integer
                        page:
                          type: integer
                        per_page:
                          type: integer
                        total_pages:
                          type: integer
                        has_next:
                          type: boolean
                        has_prev:
                          type: boolean
        """
        # Get pagination parameters
        page, per_page = PaginationService.get_pagination_params()

        # Get all agents and paginate
        agents = Agent.get_all()
        paginated = PaginationService.paginate_list(
            [agent.to_dict() for agent in agents], page=page, per_page=per_page
        )

        return paginated.to_dict(), 200

    @invalidate_cache(key_prefix="agents:list")
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

    @invalidate_cache(key_prefix="agents:list")
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

    @invalidate_cache(key_prefix="agents:list")
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
                required:
                  - input
                properties:
                  input:
                    type: string
                    minLength: 1
                    description: The input text for the agent
                  model:
                    type: string
                    minLength: 1
                    description: Override the default model
                  configuration:
                    type: object
                    description: Override the agent configuration
        responses:
          200:
            description: Execution completed successfully
            content:
              application/json:
                schema:
                  type: object
                  properties:
                    execution_id:
                      type: integer
                    agent_id:
                      type: integer
                    message:
                      type: string
                    status:
                      type: string
                    output:
                      type: object
                    duration_ms:
                      type: integer
          404:
            description: Agent not found
          400:
            description: Invalid input
          413:
            description: Request body exceeds the configured size limit
          500:
            description: Agent execution failed
        """
        agent = Agent.get_by_id(agent_id)
        if not agent:
            return {"error": f"Agent with ID {agent_id} not found"}, 404

        if not agent.is_active:
            return {"error": f"Agent with ID {agent_id} is not active"}, 400

        data = request.get_json(silent=True)
        if not isinstance(data, dict) or "input" not in data:
            return {"error": "Input is required"}, 400

        input_data = data.get("input")
        if not isinstance(input_data, str) or not input_data.strip():
            return {"error": "Input must be a non-empty string"}, 400

        model = data.get("model", agent.model)
        if not isinstance(model, str) or not model.strip():
            return {"error": "Model must be a non-empty string"}, 400

        config = data.get("configuration", agent.configuration)
        if not isinstance(config, dict):
            return {"error": "Configuration must be an object"}, 400

        try:
            save_request = _parse_save_request(data)
        except FileServiceError as error:
            return {"error": error.message, "code": error.error_code}, error.status_code

        try:
            agent_service = current_app.extensions["agent_service"]
            result = agent_service.run_agent(
                agent_id=agent_id,
                input_data={"text": input_data},
                model=model,
                configuration=config,
            )
            if save_request is not None:
                file_format = save_request["format"]
                logical_name = save_request["name"]
                if logical_name is None:
                    requested_suffix = save_request["suffix"]
                    run_suffix = f"run-{result['execution_id']}"
                    suffix = (
                        f"{requested_suffix}-{run_suffix}"
                        if requested_suffix
                        else run_suffix
                    )
                    logical_name = generate_filename(
                        _generated_content(result),
                        extension=file_format,
                        prefix=save_request["prefix"],
                        suffix=suffix,
                    )
                content = (
                    result if file_format == "json" else _generated_content(result)
                )
                file_service = current_app.extensions["file_service"]
                generated_file, management_token = file_service.create_file(
                    agent_id=agent_id,
                    logical_name=logical_name,
                    file_format=file_format,
                    content=content,
                    execution_id=result["execution_id"],
                    is_temporary=save_request["is_temporary"],
                )
                file_data = generated_file.to_dict()
                file_data.update(
                    {
                        "management_token": management_token,
                        "versions_url": f"/api/files/{generated_file.id}/versions",
                        "preview_url": f"/api/files/{generated_file.id}/preview",
                        "preview_page_url": (
                            f"/api/files/{generated_file.id}/preview?view=html"
                        ),
                        "download_url": f"/api/files/{generated_file.id}/download",
                    }
                )
                result["file"] = file_data
            result["message"] = f"Agent {agent.name} execution completed"
            return result, 200
        except FileServiceError as error:
            db.session.rollback()
            return {"error": error.message, "code": error.error_code}, error.status_code
        except Exception as e:
            db.session.rollback()
            return {"error": str(e)}, 500


# Register resources with the blueprint
def register_resources(api):
    """Register agent resources with the Flask-RESTful API."""
    api.add_resource(AgentListResource, "/agents")
    api.add_resource(AgentResource, "/agents/<int:agent_id>")
    api.add_resource(AgentRunResource, "/agents/<int:agent_id>/run")
