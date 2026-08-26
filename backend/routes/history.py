# 📜 Agent World - History Routes
# Version: 0.3.0 (EPIC 4 - History)
# Description: Endpoints REST pour la gestion de l'historique

"""
History Routes for Agent World API.

Ce module contient tous les endpoints REST pour :
- L'historique des agents (US-025)
- L'historique des exécutions (US-026)
- La restauration de versions (US-027)
- La comparaison de versions (US-028)
- L'export de l'historique (US-029)
- La recherche dans l'historique (US-030)
- Les statistiques d'utilisation (US-032)
"""

from datetime import datetime
from typing import Optional

from flask import current_app, request
from flask_restful import Resource, reqparse

from ..models.agent_history import ActionType
from ..models.execution import ExecutionStatus

# Initialize parsers for request parsing
history_parser = reqparse.RequestParser()
history_parser.add_argument(
    "action_type",
    type=str,
    required=False,
    help="Filter by action type (create, update, delete)",
)
history_parser.add_argument(
    "author_id", type=int, required=False, help="Filter by author ID"
)
history_parser.add_argument(
    "start_date", type=str, required=False, help="Start date (ISO format)"
)
history_parser.add_argument(
    "end_date", type=str, required=False, help="End date (ISO format)"
)
history_parser.add_argument(
    "limit", type=int, default=100, required=False, help="Limit results"
)
history_parser.add_argument(
    "offset", type=int, default=0, required=False, help="Offset for pagination"
)

execution_parser = reqparse.RequestParser()
execution_parser.add_argument(
    "status", type=str, required=False, help="Filter by execution status"
)
execution_parser.add_argument(
    "start_date", type=str, required=False, help="Start date (ISO format)"
)
execution_parser.add_argument(
    "end_date", type=str, required=False, help="End date (ISO format)"
)
execution_parser.add_argument(
    "limit", type=int, default=100, required=False, help="Limit results"
)
execution_parser.add_argument(
    "offset", type=int, default=0, required=False, help="Offset for pagination"
)

search_parser = reqparse.RequestParser()
search_parser.add_argument(
    "query", type=str, required=True, help="Search query is required"
)
search_parser.add_argument(
    "action_type", type=str, required=False, help="Filter by action type"
)
search_parser.add_argument(
    "start_date", type=str, required=False, help="Start date (ISO format)"
)
search_parser.add_argument(
    "end_date", type=str, required=False, help="End date (ISO format)"
)
search_parser.add_argument(
    "limit", type=int, default=50, required=False, help="Limit results"
)
search_parser.add_argument(
    "offset", type=int, default=0, required=False, help="Offset for pagination"
)

snapshot_parser = reqparse.RequestParser()
snapshot_parser.add_argument("reason", type=str, help="Reason for the snapshot")

restore_parser = reqparse.RequestParser()
restore_parser.add_argument(
    "version_id", type=str, required=True, help="Version ID to restore"
)

compare_parser = reqparse.RequestParser()
compare_parser.add_argument(
    "version_id_1", type=str, required=True, help="First version ID"
)
compare_parser.add_argument(
    "version_id_2", type=str, required=True, help="Second version ID"
)

export_parser = reqparse.RequestParser()
export_parser.add_argument(
    "format", type=str, default="json", help="Export format (json or csv)"
)
export_parser.add_argument("start_date", type=str, help="Start date (ISO format)")
export_parser.add_argument("end_date", type=str, help="End date (ISO format)")


def _parse_datetime(date_str: Optional[str]) -> Optional[datetime]:
    """Parse ISO format datetime string."""
    if not date_str:
        return None
    try:
        return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
    except ValueError:
        return None


def _parse_action_type(action_str: Optional[str]) -> Optional[ActionType]:
    """Parse action type string to enum."""
    if not action_str:
        return None
    try:
        return ActionType(action_str)
    except ValueError:
        return None


def _parse_execution_status(status_str: Optional[str]) -> Optional[ExecutionStatus]:
    """Parse execution status string to enum."""
    if not status_str:
        return None
    try:
        return ExecutionStatus(status_str)
    except ValueError:
        return None


# ============================================================================
# Agent History Routes (US-025)
# ============================================================================


class AgentHistoryListResource(Resource):
    """Resource for listing agent history entries."""

    def get(self, agent_id: int):
        """
        Get history for a specific agent.

        ---
        parameters:
          - in: path
            name: agent_id
            schema:
              type: integer
            required: true
          - in: query
            name: action_type
            schema:
              type: string
            description: Filter by action type
          - in: query
            name: author_id
            schema:
              type: integer
            description: Filter by author ID
          - in: query
            name: start_date
            schema:
              type: string
              format: date-time
            description: Filter by start date
          - in: query
            name: end_date
            schema:
              type: string
              format: date-time
            description: Filter by end date
          - in: query
            name: limit
            schema:
              type: integer
              default: 100
            description: Limit number of results
          - in: query
            name: offset
            schema:
              type: integer
              default: 0
            description: Offset for pagination
        responses:
          200:
            description: List of history entries for the agent
          404:
            description: Agent not found
        """
        agent = current_app.extensions["agent_service"].get_agent(agent_id)
        if not agent:
            return {"error": f"Agent with ID {agent_id} not found"}, 404

        # Parse query parameters from request.args
        action_type_str = request.args.get("action_type")
        action_type = _parse_action_type(action_type_str) if action_type_str else None
        author_id = request.args.get("author_id", type=int)
        start_date = _parse_datetime(request.args.get("start_date"))
        end_date = _parse_datetime(request.args.get("end_date"))
        limit = request.args.get("limit", default=100, type=int)
        offset = request.args.get("offset", default=0, type=int)

        history_service = current_app.extensions["history_service"]
        entries, total = history_service.get_agent_history(
            agent_id=agent_id,
            action_type=action_type,
            author_id=author_id,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
            offset=offset,
        )

        return {
            "entries": entries,
            "total": total,
            "limit": limit,
            "offset": offset,
            "agent_id": agent_id,
        }, 200


class AgentHistoryResource(Resource):
    """Resource for individual agent history entry."""

    def get(self, agent_id: int, history_id: int):
        """
        Get a specific history entry for an agent.

        ---
        parameters:
          - in: path
            name: agent_id
            schema:
              type: integer
            required: true
          - in: path
            name: history_id
            schema:
              type: integer
            required: true
        responses:
          200:
            description: The requested history entry
          404:
            description: History entry not found
        """
        agent = current_app.extensions["agent_service"].get_agent(agent_id)
        if not agent:
            return {"error": f"Agent with ID {agent_id} not found"}, 404

        history_service = current_app.extensions["history_service"]
        entries, _ = history_service.get_agent_history(
            agent_id=agent_id,
            limit=1,
            offset=0,
        )

        # Find the specific entry
        entry = next((e for e in entries if e.get("id") == history_id), None)
        if not entry:
            return {"error": f"History entry with ID {history_id} not found"}, 404

        return entry, 200


# ============================================================================
# Execution History Routes (US-026)
# ============================================================================


class ExecutionHistoryListResource(Resource):
    """Resource for listing execution history entries."""

    def get(self, agent_id: int):
        """
        Get execution history for a specific agent.

        ---
        parameters:
          - in: path
            name: agent_id
            schema:
              type: integer
            required: true
          - in: query
            name: status
            schema:
              type: string
            description: Filter by execution status
          - in: query
            name: start_date
            schema:
              type: string
              format: date-time
            description: Filter by start date
          - in: query
            name: end_date
            schema:
              type: string
              format: date-time
            description: Filter by end date
          - in: query
            name: limit
            schema:
              type: integer
              default: 100
            description: Limit number of results
          - in: query
            name: offset
            schema:
              type: integer
              default: 0
            description: Offset for pagination
        responses:
          200:
            description: List of execution history entries for the agent
            content:
              application/json:
                schema:
                  type: object
                  properties:
                    executions:
                      type: array
                      items:
                        type: object
                    total:
                      type: integer
                    limit:
                      type: integer
                    offset:
                      type: integer
          404:
            description: Agent not found
        """
        agent = current_app.extensions["agent_service"].get_agent(agent_id)
        if not agent:
            return {"error": f"Agent with ID {agent_id} not found"}, 404

        args = request.args

        status = _parse_execution_status(request.args.get("status"))
        start_date = _parse_datetime(request.args.get("start_date"))
        end_date = _parse_datetime(request.args.get("end_date"))
        limit = request.args.get("limit")
        offset = request.args.get("offset")

        history_service = current_app.extensions["history_service"]
        executions, total = history_service.get_execution_history(
            agent_id=agent_id,
            status=status,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
            offset=offset,
        )

        return {
            "executions": executions,
            "total": total,
            "limit": limit,
            "offset": offset,
            "agent_id": agent_id,
        }, 200


class ExecutionHistoryResource(Resource):
    """Resource for individual execution history entry."""

    def get(self, agent_id: int, execution_id: int):
        """
        Get a specific execution history entry.

        ---
        parameters:
          - in: path
            name: agent_id
            schema:
              type: integer
            required: true
          - in: path
            name: execution_id
            schema:
              type: integer
            required: true
        responses:
          200:
            description: The requested execution entry
          404:
            description: Execution entry not found
        """
        agent = current_app.extensions["agent_service"].get_agent(agent_id)
        if not agent:
            return {"error": f"Agent with ID {agent_id} not found"}, 404

        from ..models.execution import Execution

        execution = Execution.get_by_id(execution_id)
        if not execution or execution.agent_id != agent_id:
            return {
                "error": f"Execution with ID {execution_id} not found for agent {agent_id}"
            }, 404

        return execution.to_dict(), 200


# ============================================================================
# Version Management Routes (US-027, US-028)
# ============================================================================


class AgentVersionsListResource(Resource):
    """Resource for listing agent versions."""

    def get(self, agent_id: int):
        """
        Get all versions for a specific agent.

        ---
        parameters:
          - in: path
            name: agent_id
            schema:
              type: integer
            required: true
          - in: query
            name: limit
            schema:
              type: integer
              default: 50
            description: Limit number of results
          - in: query
            name: offset
            schema:
              type: integer
              default: 0
            description: Offset for pagination
        responses:
          200:
            description: List of versions for the agent
          404:
            description: Agent not found
        """
        agent = current_app.extensions["agent_service"].get_agent(agent_id)
        if not agent:
            return {"error": f"Agent with ID {agent_id} not found"}, 404

        # Parse query parameters from request.args
        limit = request.args.get("limit", default=50, type=int)
        offset = request.args.get("offset", default=0, type=int)

        history_service = current_app.extensions["history_service"]
        versions = history_service.get_agent_versions(
            agent_id=agent_id,
            limit=limit,
            offset=offset,
        )

        return {"versions": versions, "agent_id": agent_id}, 200

    def post(self, agent_id: int):
        """
        Create a snapshot of the current agent state.

        ---
        parameters:
          - in: path
            name: agent_id
            schema:
              type: integer
            required: true
        requestBody:
          required: false
          content:
            application/json:
              schema:
                type: object
                properties:
                  reason:
                    type: string
                    description: Reason for the snapshot
        responses:
          201:
            description: Snapshot created successfully
          404:
            description: Agent not found
        """
        agent = current_app.extensions["agent_service"].get_agent(agent_id)
        if not agent:
            return {"error": f"Agent with ID {agent_id} not found"}, 404

        data = request.get_json(silent=True) or {}
        reason = data.get("reason")

        # Get author_id from request context if available
        author_id = None
        if hasattr(request, "user") and request.user:
            author_id = request.user.id

        history_service = current_app.extensions["history_service"]
        snapshot = history_service.create_agent_snapshot(
            agent_id=agent_id,
            author_id=author_id,
            reason=reason,
        )

        if not snapshot:
            return {"error": "Failed to create snapshot"}, 500

        return snapshot, 201


class AgentVersionRestoreResource(Resource):
    """Resource for restoring an agent version."""

    def post(self, agent_id: int, version_id: str):
        """
        Restore an agent to a previous version (US-027).

        ---
        parameters:
          - in: path
            name: agent_id
            schema:
              type: integer
            required: true
          - in: path
            name: version_id
            schema:
              type: string
            required: true
            description: UUID of the version to restore
        responses:
          200:
            description: Agent restored successfully
          404:
            description: Agent or version not found
          400:
            description: Bad request
        """
        agent = current_app.extensions["agent_service"].get_agent(agent_id)
        if not agent:
            return {"error": f"Agent with ID {agent_id} not found"}, 404

        # Get author_id from request context if available
        author_id = None
        if hasattr(request, "user") and request.user:
            author_id = request.user.id

        history_service = current_app.extensions["history_service"]
        success, message = history_service.restore_agent_version(
            version_id=version_id,
            author_id=author_id,
        )

        if not success:
            return {"error": message}, 400

        return {"message": message, "agent_id": agent_id, "version_id": version_id}, 200


class AgentVersionsCompareResource(Resource):
    """Resource for comparing two agent versions."""

    def get(self, agent_id: int, version_id_1: str, version_id_2: str):
        """
        Compare two versions of an agent (US-028).

        ---
        parameters:
          - in: path
            name: agent_id
            schema:
              type: integer
            required: true
          - in: path
            name: version_id_1
            schema:
              type: string
            required: true
          - in: path
            name: version_id_2
            schema:
              type: string
            required: true
        responses:
          200:
            description: Comparison result
          404:
            description: Agent or versions not found
        """
        agent = current_app.extensions["agent_service"].get_agent(agent_id)
        if not agent:
            return {"error": f"Agent with ID {agent_id} not found"}, 404

        history_service = current_app.extensions["history_service"]
        comparison = history_service.compare_agent_versions(
            version_id_1=version_id_1,
            version_id_2=version_id_2,
        )

        if not comparison:
            return {"error": "One or both versions not found"}, 404

        if "error" in comparison:
            return {"error": comparison["error"]}, 400

        return comparison, 200

    def post(self, agent_id: int):
        """
        Compare two versions of an agent (alternative POST endpoint).

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
                  - version_id_1
                  - version_id_2
                properties:
                  version_id_1:
                    type: string
                  version_id_2:
                    type: string
        responses:
          200:
            description: Comparison result
          404:
            description: Agent or versions not found
        """
        agent = current_app.extensions["agent_service"].get_agent(agent_id)
        if not agent:
            return {"error": f"Agent with ID {agent_id} not found"}, 404

        data = request.get_json(silent=True)
        if not data:
            return {"error": "Request body is required"}, 400

        version_id_1 = data.get("version_id_1")
        version_id_2 = data.get("version_id_2")

        if not version_id_1 or not version_id_2:
            return {"error": "Both version_id_1 and version_id_2 are required"}, 400

        history_service = current_app.extensions["history_service"]
        comparison = history_service.compare_agent_versions(
            version_id_1=version_id_1,
            version_id_2=version_id_2,
        )

        if not comparison:
            return {"error": "One or both versions not found"}, 404

        if "error" in comparison:
            return {"error": comparison["error"]}, 400

        return comparison, 200


# ============================================================================
# Export Routes (US-029)
# ============================================================================


class AgentHistoryExportResource(Resource):
    """Resource for exporting agent history."""

    def get(self, agent_id: int):
        """
        Export agent history (US-029).

        ---
        parameters:
          - in: path
            name: agent_id
            schema:
              type: integer
            required: true
          - in: query
            name: format
            schema:
              type: string
              default: json
            description: Export format (json or csv)
          - in: query
            name: start_date
            schema:
              type: string
              format: date-time
            description: Filter by start date
          - in: query
            name: end_date
            schema:
              type: string
              format: date-time
            description: Filter by end date
        responses:
          200:
            description: Export data
          404:
            description: Agent not found
        """
        agent = current_app.extensions["agent_service"].get_agent(agent_id)
        if not agent:
            return {"error": f"Agent with ID {agent_id} not found"}, 404

        format_type = request.args.get("format", "json")
        start_date = _parse_datetime(request.args.get("start_date"))
        end_date = _parse_datetime(request.args.get("end_date"))

        history_service = current_app.extensions["history_service"]

        try:
            export_data = history_service.export_agent_history(
                agent_id=agent_id,
                format_type=format_type,
                start_date=start_date,
                end_date=end_date,
            )
            return export_data, 200
        except ValueError as e:
            return {"error": str(e)}, 400


# ============================================================================
# Search Routes (US-030)
# ============================================================================


class AgentHistorySearchResource(Resource):
    """Resource for searching agent history."""

    def get(self, agent_id: int):
        """
        Search agent history (US-030).

        ---
        parameters:
          - in: path
            name: agent_id
            schema:
              type: integer
            required: true
          - in: query
            name: query
            schema:
              type: string
            required: true
            description: Search query string
          - in: query
            name: action_type
            schema:
              type: string
            description: Filter by action type
          - in: query
            name: start_date
            schema:
              type: string
              format: date-time
            description: Filter by start date
          - in: query
            name: end_date
            schema:
              type: string
              format: date-time
            description: Filter by end date
          - in: query
            name: limit
            schema:
              type: integer
              default: 50
            description: Limit number of results
          - in: query
            name: offset
            schema:
              type: integer
              default: 0
            description: Offset for pagination
        responses:
          200:
            description: Search results
          404:
            description: Agent not found
        """
        agent = current_app.extensions["agent_service"].get_agent(agent_id)
        if not agent:
            return {"error": f"Agent with ID {agent_id} not found"}, 404

        query = request.args.get("query")
        action_type = _parse_action_type(request.args.get("action_type"))
        start_date = _parse_datetime(request.args.get("start_date"))
        end_date = _parse_datetime(request.args.get("end_date"))
        limit = request.args.get("limit")
        offset = request.args.get("offset")

        history_service = current_app.extensions["history_service"]
        results, total = history_service.search_agent_history(
            query=query,
            agent_id=agent_id,
            action_type=action_type,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
            offset=offset,
        )

        return {
            "results": results,
            "total": total,
            "query": query,
            "limit": limit,
            "offset": offset,
        }, 200


# ============================================================================
# Statistics Routes (US-032)
# ============================================================================


class AgentStatisticsResource(Resource):
    """Resource for agent statistics."""

    def get(self, agent_id: int):
        """
        Get statistics for a specific agent (US-032).

        ---
        parameters:
          - in: path
            name: agent_id
            schema:
              type: integer
            required: true
          - in: query
            name: period_days
            schema:
              type: integer
              default: 30
            description: Number of days to consider
        responses:
          200:
            description: Agent statistics
          404:
            description: Agent not found
        """
        agent = current_app.extensions["agent_service"].get_agent(agent_id)
        if not agent:
            return {"error": f"Agent with ID {agent_id} not found"}, 404

        # Parse query parameters from request.args
        period_days = request.args.get("period_days", default=30, type=int)

        history_service = current_app.extensions["history_service"]
        statistics = history_service.get_agent_statistics(
            agent_id=agent_id,
            period_days=period_days,
        )

        return statistics, 200


# Register resources with the blueprint
def register_history_resources(api):
    """Register history resources with the Flask-RESTful API."""
    # Agent History (US-025)
    api.add_resource(AgentHistoryListResource, "/agents/<int:agent_id>/history")
    api.add_resource(
        AgentHistoryResource, "/agents/<int:agent_id>/history/<int:history_id>"
    )

    # Execution History (US-026)
    api.add_resource(ExecutionHistoryListResource, "/agents/<int:agent_id>/executions")
    api.add_resource(
        ExecutionHistoryResource, "/agents/<int:agent_id>/executions/<int:execution_id>"
    )

    # Version Management (US-027, US-028)
    api.add_resource(AgentVersionsListResource, "/agents/<int:agent_id>/versions")
    api.add_resource(
        AgentVersionRestoreResource,
        "/agents/<int:agent_id>/versions/<string:version_id>/restore",
    )
    api.add_resource(
        AgentVersionsCompareResource,
        "/agents/<int:agent_id>/versions/<string:version_id_1>/compare/<string:version_id_2>",
    )

    # Export (US-029)
    api.add_resource(
        AgentHistoryExportResource, "/agents/<int:agent_id>/history/export"
    )

    # Search (US-030)
    api.add_resource(
        AgentHistorySearchResource, "/agents/<int:agent_id>/history/search"
    )

    # Statistics (US-032)
    api.add_resource(AgentStatisticsResource, "/agents/<int:agent_id>/statistics")
