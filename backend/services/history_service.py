# 📜 Agent World - History Service
# Version: 0.3.0 (EPIC 4 - History)
# Description: Service pour la gestion de l'historique des agents et exécutions

"""
History Service for Agent World.

Ce service contient la logique métier pour la gestion de l'historique.
Il permet de :
- Logger les modifications des agents
- Logger les exécutions
- Gérer les versions et restaurations
- Comparer des versions
- Exporter l'historique
- Rechercher dans l'historique
"""

import logging
import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from ..models.agent import Agent
from ..models.agent_history import ActionType, AgentHistory
from ..models.base import db
from ..models.execution import Execution, ExecutionStatus
from ..models.user import User

logger = logging.getLogger(__name__)


class HistoryFilter(str, Enum):
    """Types de filtres pour l'historique."""

    DATE = "date"
    ACTION_TYPE = "action_type"
    AUTHOR = "author"
    AGENT = "agent"


class HistoryService:
    """
    Service class for managing agent and execution history.

    This service provides business logic for history operations including
    logging changes, retrieving history, version management, and more.
    """

    def __init__(self):
        """Initialize the HistoryService."""
        self.agent_history_model = AgentHistory

    # ========================================================================
    # Agent History Methods
    # ========================================================================

    def log_agent_change(
        self,
        agent_id: int,
        action_type: ActionType,
        author_id: Optional[int] = None,
        old_values: Optional[Dict[str, Any]] = None,
        new_values: Optional[Dict[str, Any]] = None,
        reason: Optional[str] = None,
        ip_address: Optional[str] = None,
        generate_version: bool = True,
    ) -> AgentHistory:
        """
        Log a change to an agent in the history.

        Args:
            agent_id: ID of the agent being modified
            action_type: Type of action performed
            author_id: Optional ID of the user who performed the action
            old_values: Optional dictionary of old values before the change
            new_values: Optional dictionary of new values after the change
            reason: Optional reason for the change
            ip_address: Optional IP address of the requester
            generate_version: Whether to generate a version ID (default: True)

        Returns:
            The created AgentHistory instance
        """
        change_data: Dict[str, Any] = {}

        if old_values:
            change_data["old_values"] = old_values
        if new_values:
            change_data["new_values"] = new_values
        if reason:
            change_data["reason"] = reason
        if ip_address:
            change_data["ip_address"] = ip_address

        version_id = str(uuid.uuid4()) if generate_version else None

        history_entry = self.agent_history_model.create(
            agent_id=agent_id,
            action_type=action_type,
            author_id=author_id,
            change_data=change_data,
            version_id=version_id,
        )

        return history_entry

    def get_agent_history(
        self,
        agent_id: int,
        action_type: Optional[ActionType] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        author_id: Optional[int] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        Get history for a specific agent with optional filters.

        Args:
            agent_id: ID of the agent
            action_type: Optional filter by action type
            start_date: Optional start date (inclusive)
            end_date: Optional end date (inclusive)
            author_id: Optional filter by author ID
            limit: Maximum number of entries to return (default: 100)
            offset: Number of entries to skip (default: 0)

        Returns:
            Tuple of (list of history entries as dicts, total count)
        """
        query = self.agent_history_model.query.filter_by(agent_id=agent_id)

        if action_type:
            query = query.filter_by(action_type=action_type)
        if author_id:
            query = query.filter_by(author_id=author_id)
        if start_date:
            query = query.filter(self.agent_history_model.timestamp >= start_date)
        if end_date:
            query = query.filter(self.agent_history_model.timestamp <= end_date)

        total = query.count()

        entries = (
            query.order_by(self.agent_history_model.timestamp.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

        return [entry.to_dict() for entry in entries], total

    def get_agent_history_by_version(self, version_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific history entry by its version ID.

        Args:
            version_id: UUID of the version

        Returns:
            History entry as dict or None if not found
        """
        entry = self.agent_history_model.get_by_version(version_id)
        if entry:
            return entry.to_dict()
        return None

    # ========================================================================
    # Execution History Methods
    # ========================================================================

    def log_execution(
        self,
        execution_id: int,
        agent_id: int,
        status: ExecutionStatus,
        duration_ms: Optional[int] = None,
        tokens_used: Optional[int] = None,
        cost: Optional[float] = None,
        error_message: Optional[str] = None,
        model_used: Optional[str] = None,
        change_data: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Log execution details to history.

        Note: This method updates the execution record directly since
        Execution already has all the necessary fields.

        Args:
            execution_id: ID of the execution
            agent_id: ID of the agent that was executed
            status: Final status of the execution
            duration_ms: Duration in milliseconds
            tokens_used: Number of tokens used
            cost: Cost of the execution
            error_message: Error message if execution failed
            model_used: Model used for execution
            change_data: Additional change_data
        """
        # For now, we just ensure the execution record is complete
        # The execution model already tracks all necessary data
        execution = Execution.get_by_id(execution_id)
        if execution:
            # Update execution with any missing data
            if duration_ms is not None:
                execution.duration_ms = duration_ms
            if tokens_used is not None:
                if not hasattr(execution, "tokens_used"):
                    # Add tokens_used field dynamically if it doesn't exist
                    # This will be added to the model in a migration
                    pass
            if cost is not None:
                if not hasattr(execution, "cost"):
                    # Add cost field dynamically if it doesn't exist
                    pass
            db.session.commit()

    def get_execution_history(
        self,
        agent_id: Optional[int] = None,
        status: Optional[ExecutionStatus] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        Get execution history with optional filters.

        Args:
            agent_id: Optional filter by agent ID
            status: Optional filter by execution status
            start_date: Optional start date (inclusive)
            end_date: Optional end date (inclusive)
            limit: Maximum number of entries to return (default: 100)
            offset: Number of entries to skip (default: 0)

        Returns:
            Tuple of (list of execution dicts, total count)
        """
        query = Execution.query

        if agent_id:
            query = query.filter_by(agent_id=agent_id)
        if status:
            query = query.filter_by(status=status)
        if start_date:
            query = query.filter(Execution.created_at >= start_date)
        if end_date:
            query = query.filter(Execution.created_at <= end_date)

        total = query.count()

        executions = (
            query.order_by(Execution.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

        return [exec.to_dict() for exec in executions], total

    # ========================================================================
    # Version Management Methods
    # ========================================================================

    def create_agent_snapshot(
        self,
        agent_id: int,
        author_id: Optional[int] = None,
        reason: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Create a snapshot of the current agent state as a version.

        Args:
            agent_id: ID of the agent to snapshot
            author_id: Optional ID of the user creating the snapshot
            reason: Optional reason for the snapshot

        Returns:
            Snapshot data as dict or None if agent not found
        """
        agent = Agent.get_by_id(agent_id)
        if not agent:
            return None

        # Create snapshot of current state
        snapshot_data = agent.to_dict()

        # Log this as a version in history
        history_entry = self.log_agent_change(
            agent_id=agent_id,
            action_type=ActionType.UPDATE,
            author_id=author_id,
            new_values=snapshot_data,
            reason=reason or "Manual snapshot",
            generate_version=True,
        )

        return {
            "version_id": history_entry.version_id,
            "agent_id": agent_id,
            "snapshot": snapshot_data,
            "created_at": history_entry.timestamp.isoformat(),
            "created_by": author_id,
        }

    def restore_agent_version(
        self,
        version_id: str,
        author_id: Optional[int] = None,
    ) -> Tuple[bool, Optional[str]]:
        """
        Restore an agent to a previous version.

        Args:
            version_id: UUID of the version to restore
            author_id: Optional ID of the user performing the restore

        Returns:
            Tuple of (success: bool, message: Optional[str])
        """
        history_entry = self.agent_history_model.get_by_version(version_id)
        if not history_entry:
            return False, f"Version {version_id} not found"

        agent = Agent.get_by_id(history_entry.agent_id)
        if not agent:
            return False, f"Agent {history_entry.agent_id} not found"

        # Get the snapshot from change_data
        old_values = history_entry.change_data.get("old_values", {})
        new_values = history_entry.change_data.get("new_values", {})

        # For restore, we use the new_values (the state after the change)
        # or old_values if this was a delete
        restore_data = new_values or old_values

        if not restore_data:
            return False, "No version data available for restore"

        try:
            # Restore agent data
            agent.name = restore_data.get("name", agent.name)
            agent.description = restore_data.get("description", agent.description)
            agent.model = restore_data.get("model", agent.model)
            agent.configuration = restore_data.get("configuration", agent.configuration)
            agent.is_active = restore_data.get("is_active", agent.is_active)
            agent.updated_at = datetime.utcnow()

            db.session.commit()

            # Log the restore action
            self.log_agent_change(
                agent_id=agent.id,
                action_type=ActionType.UPDATE,
                author_id=author_id,
                old_values=agent.to_dict(),
                new_values=restore_data,
                reason="Restored from version",
            )

            # Mark the restored version
            history_entry.is_restored = True
            db.session.commit()

            return True, f"Agent {agent.id} restored to version {version_id}"

        except Exception as e:
            db.session.rollback()
            return False, f"Failed to restore version: {str(e)}"

    def get_agent_versions(
        self,
        agent_id: int,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """
        Get all versions (snapshots) for a specific agent.

        Args:
            agent_id: ID of the agent
            limit: Maximum number of versions to return (default: 50)
            offset: Number of versions to skip (default: 0)

        Returns:
            List of version data as dicts
        """
        history_entries = (
            self.agent_history_model.query.filter(
                self.agent_history_model.agent_id == agent_id,
                self.agent_history_model.version_id.isnot(None),
            )
            .order_by(self.agent_history_model.timestamp.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

        versions = []
        for entry in history_entries:
            versions.append(
                {
                    "version_id": entry.version_id,
                    "agent_id": entry.agent_id,
                    "action_type": entry.action_type.value,
                    "timestamp": entry.timestamp.isoformat(),
                    "author_id": entry.author_id,
                    "change_data": entry.change_data,
                    "is_restored": entry.is_restored,
                }
            )

        return versions

    # ========================================================================
    # Comparison Methods
    # ========================================================================

    def compare_agent_versions(
        self,
        version_id_1: str,
        version_id_2: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Compare two versions of an agent.

        Args:
            version_id_1: First version UUID
            version_id_2: Second version UUID

        Returns:
            Comparison result as dict or None if versions not found
        """
        entry_1 = self.agent_history_model.get_by_version(version_id_1)
        entry_2 = self.agent_history_model.get_by_version(version_id_2)

        if not entry_1 or not entry_2:
            return None

        if entry_1.agent_id != entry_2.agent_id:
            return {
                "error": "Cannot compare versions from different agents",
                "version_1_agent": entry_1.agent_id,
                "version_2_agent": entry_2.agent_id,
            }

        # Get the data for each version
        data_1 = entry_1.change_data.get(
            "new_values", entry_1.change_data.get("old_values", {})
        )
        data_2 = entry_2.change_data.get(
            "new_values", entry_2.change_data.get("old_values", {})
        )

        # Find differences
        differences: Dict[str, Dict[str, Any]] = {}

        all_keys = set(data_1.keys()) | set(data_2.keys())

        for key in all_keys:
            val_1 = data_1.get(key)
            val_2 = data_2.get(key)

            if val_1 != val_2:
                differences[key] = {
                    "old": val_1,
                    "new": val_2,
                    "changed": True,
                }

        return {
            "version_1": version_id_1,
            "version_2": version_id_2,
            "agent_id": entry_1.agent_id,
            "timestamp_1": entry_1.timestamp.isoformat(),
            "timestamp_2": entry_2.timestamp.isoformat(),
            "differences": differences,
            "total_differences": len(differences),
        }

    def get_version_diff_text(
        self,
        version_id_1: str,
        version_id_2: str,
    ) -> Optional[str]:
        """
        Get a text-based diff between two versions.

        Args:
            version_id_1: First version UUID
            version_id_2: Second version UUID

        Returns:
            Text diff as string or None if versions not found
        """
        comparison = self.compare_agent_versions(version_id_1, version_id_2)
        if not comparison:
            return None

        if "error" in comparison:
            return comparison["error"]

        lines = []
        lines.append(f"Comparing versions: {version_id_1} vs {version_id_2}")
        lines.append(f"Agent ID: {comparison['agent_id']}")
        lines.append(f"Differences found: {comparison['total_differences']}")
        lines.append("")

        for field, diff in comparison["differences"].items():
            lines.append(f"Field: {field}")
            lines.append(f"  Old: {diff['old']}")
            lines.append(f"  New: {diff['new']}")
            lines.append("")

        return "\n".join(lines)

    # ========================================================================
    # Export Methods
    # ========================================================================

    def export_agent_history(
        self,
        agent_id: int,
        format_type: str = "json",
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Export agent history in the specified format.

        Args:
            agent_id: ID of the agent
            format_type: Export format ('json' or 'csv')
            start_date: Optional start date for filtering
            end_date: Optional end date for filtering

        Returns:
            Export data as dict with 'format', 'data', and 'filename' keys
        """
        entries, total = self.get_agent_history(
            agent_id=agent_id,
            start_date=start_date,
            end_date=end_date,
            limit=10000,  # Large limit for export
        )

        if format_type == "json":
            return {
                "format": "json",
                "data": entries,
                "filename": f"agent_{agent_id}_history_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json",
                "total_entries": total,
            }
        elif format_type == "csv":
            # Convert to CSV format (array of arrays)
            csv_data = [
                [
                    "id",
                    "agent_id",
                    "action_type",
                    "timestamp",
                    "author_id",
                    "change_data",
                ]
            ]
            for entry in entries:
                csv_data.append(
                    [
                        entry.get("id"),
                        entry.get("agent_id"),
                        entry.get("action_type"),
                        entry.get("timestamp"),
                        entry.get("author_id"),
                        str(entry.get("change_data")),
                    ]
                )

            return {
                "format": "csv",
                "data": csv_data,
                "filename": f"agent_{agent_id}_history_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv",
                "total_entries": total,
            }
        else:
            raise ValueError(f"Unsupported export format: {format_type}")

    # ========================================================================
    # Search Methods
    # ========================================================================

    def search_agent_history(
        self,
        query: str,
        agent_id: Optional[int] = None,
        action_type: Optional[ActionType] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        Search agent history entries.

        Args:
            query: Search query string
            agent_id: Optional filter by agent ID
            action_type: Optional filter by action type
            start_date: Optional start date
            end_date: Optional end date
            limit: Maximum number of results (default: 50)
            offset: Number of results to skip (default: 0)

        Returns:
            Tuple of (list of matching entries as dicts, total count)
        """
        from sqlalchemy import or_

        query_builder = self.agent_history_model.query

        if agent_id:
            query_builder = query_builder.filter_by(agent_id=agent_id)
        if action_type:
            query_builder = query_builder.filter_by(action_type=action_type)
        if start_date:
            query_builder = query_builder.filter(
                self.agent_history_model.timestamp >= start_date
            )
        if end_date:
            query_builder = query_builder.filter(
                self.agent_history_model.timestamp <= end_date
            )

        # Search in change_data JSON fields
        search_conditions = []

        # Try to parse query as integer for ID search
        try:
            query_int = int(query)
            search_conditions.append(
                or_(
                    self.agent_history_model.id == query_int,
                    self.agent_history_model.agent_id == query_int,
                    self.agent_history_model.author_id == query_int,
                )
            )
        except ValueError:
            pass

        # Search in change_data fields
        search_conditions.append(
            self.agent_history_model.change_data.contains({"reason": query})
        )
        search_conditions.append(
            self.agent_history_model.change_data.contains({"old_values": query})
        )
        search_conditions.append(
            self.agent_history_model.change_data.contains({"new_values": query})
        )

        if search_conditions:
            query_builder = query_builder.filter(or_(*search_conditions))

        total = query_builder.count()

        results = (
            query_builder.order_by(self.agent_history_model.timestamp.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

        return [result.to_dict() for result in results], total

    # ========================================================================
    # Statistics Methods
    # ========================================================================

    def get_agent_statistics(
        self,
        agent_id: int,
        period_days: int = 30,
    ) -> Dict[str, Any]:
        """
        Get statistics for a specific agent.

        Args:
            agent_id: ID of the agent
            period_days: Number of days to consider (default: 30)

        Returns:
            Statistics as dict
        """
        from datetime import timedelta

        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=period_days)

        # Get history for the period
        history_entries = self.agent_history_model.query.filter(
            self.agent_history_model.agent_id == agent_id,
            self.agent_history_model.timestamp >= start_date,
            self.agent_history_model.timestamp <= end_date,
        ).all()

        # Count by action type
        action_counts: Dict[str, int] = {}
        for action in ActionType:
            action_counts[action.value] = 0

        for entry in history_entries:
            action_counts[entry.action_type.value] += 1

        # Get executions for the period
        executions = Execution.query.filter(
            Execution.agent_id == agent_id,
            Execution.created_at >= start_date,
            Execution.created_at <= end_date,
        ).all()

        # Count by status
        status_counts: Dict[str, int] = {}
        for status in ExecutionStatus:
            status_counts[status.value] = 0

        for exec in executions:
            status_counts[exec.status.value] += 1

        # Calculate average duration
        durations = [e.duration_ms for e in executions if e.duration_ms]
        avg_duration = sum(durations) / len(durations) if durations else 0

        return {
            "agent_id": agent_id,
            "period_days": period_days,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "history_count": len(history_entries),
            "action_counts": action_counts,
            "execution_count": len(executions),
            "status_counts": status_counts,
            "average_duration_ms": avg_duration,
        }

    # ========================================================================
    # Notification Integration Methods (US-031)
    # ========================================================================

    def notify_execution_failure(
        self,
        user_id: int,
        agent_id: int,
        execution_id: int,
        error_message: str,
        send_immediately: bool = True,
    ) -> Optional[Any]:
        """
        Create a notification for an execution failure.

        This method integrates with the NotificationService to send
        notifications when executions fail.

        Args:
            user_id: ID of the user to notify
            agent_id: ID of the agent that failed
            execution_id: ID of the failed execution
            error_message: The error message
            send_immediately: Whether to send immediately

        Returns:
            The created notification, or None if failed
        """
        try:
            from .notification_service import notification_service

            return notification_service.create_execution_failure_notification(
                user_id=user_id,
                agent_id=agent_id,
                execution_id=execution_id,
                error_message=error_message,
            )
        except Exception as e:
            logger.error(f"Failed to create execution failure notification: {str(e)}")
            return None

    def notify_execution_success(
        self,
        user_id: int,
        agent_id: int,
        execution_id: int,
        duration: float,
        send_immediately: bool = True,
    ) -> Optional[Any]:
        """
        Create a notification for a successful execution.

        Args:
            user_id: ID of the user to notify
            agent_id: ID of the agent
            execution_id: ID of the execution
            duration: Execution duration in seconds
            send_immediately: Whether to send immediately

        Returns:
            The created notification, or None if failed
        """
        try:
            from .notification_service import notification_service

            return notification_service.create_execution_success_notification(
                user_id=user_id,
                agent_id=agent_id,
                execution_id=execution_id,
                duration=duration,
            )
        except Exception as e:
            logger.error(f"Failed to create execution success notification: {str(e)}")
            return None

    def notify_agent_modification(
        self,
        user_id: int,
        agent_id: int,
        action: str,
        send_immediately: bool = True,
    ) -> Optional[Any]:
        """
        Create a notification for an agent modification.

        Args:
            user_id: ID of the user to notify
            agent_id: ID of the agent
            action: The action performed (created, updated, deleted)
            send_immediately: Whether to send immediately

        Returns:
            The created notification, or None if failed
        """
        try:
            from .notification_service import notification_service

            return notification_service.create_agent_modification_notification(
                user_id=user_id,
                agent_id=agent_id,
                action=action,
            )
        except Exception as e:
            logger.error(f"Failed to create agent modification notification: {str(e)}")
            return None
