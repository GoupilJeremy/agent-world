# 📋 Agent World - Audit Service
# Version: 1.0.0 (EPIC 10 - US-068)
# Description: Service pour gérer l'audit des actions utilisateurs

"""
Audit Service for Agent World.

Ce service gère:
- L'enregistrement des actions utilisateurs
- La consultation des logs d'audit
- L'export des logs
- Le nettoyage des anciens logs
- Les statistiques d'utilisation
"""

import csv
import json
from datetime import datetime, timedelta
from io import StringIO
from typing import Any, Dict, List, Optional, Union

from flask import request

from ..models.audit_log import AuditAction, AuditLog, AuditResourceType
from ..models.base import db
from ..models.user import User


class AuditError(Exception):
    """Base exception for audit-related errors."""

    status_code = 400
    error_code = "audit_error"


class AuditLogNotFoundError(AuditError):
    """Audit log not found."""

    status_code = 404
    error_code = "audit_log_not_found"


class AuditService:
    """
    Service for managing audit logs.

    This service provides functionality for:
    - Logging user actions
    - Retrieving audit logs with various filters
    - Exporting audit logs to JSON or CSV
    - Getting statistics from audit logs
    - Managing audit log retention
    """

    # Default retention period in days
    DEFAULT_RETENTION_DAYS = 90

    def __init__(self, retention_days: int = DEFAULT_RETENTION_DAYS):
        """
        Initialize the AuditService.

        Args:
            retention_days: Number of days to keep audit logs (default: 90)
        """
        self.retention_days = retention_days

    def log_action(
        self,
        action: Union[str, AuditAction],
        user_id: Optional[int] = None,
        resource_type: Optional[Union[str, AuditResourceType]] = None,
        resource_id: Optional[int] = None,
        resource_name: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        status: str = "success",
        error_message: Optional[str] = None,
        commit: bool = True,
    ) -> AuditLog:
        """
        Log an action to the audit trail.

        Args:
            action: The action that was performed
            user_id: ID of the user who performed the action
            resource_type: Type of resource affected
            resource_id: ID of the resource affected
            resource_name: Name of the resource affected
            metadata: Additional metadata
            ip_address: IP address of the request
            user_agent: User agent of the request
            status: Status of the action (success, failure, warning)
            error_message: Error message if action failed
            commit: Whether to commit the changes immediately

        Returns:
            The created AuditLog entry
        """
        return AuditLog.log(
            user_id=user_id,
            action=action.value if isinstance(action, AuditAction) else action,
            resource_type=resource_type.value if isinstance(resource_type, AuditResourceType) else resource_type,
            resource_id=resource_id,
            resource_name=resource_name,
            metadata=metadata,
            ip_address=ip_address,
            user_agent=user_agent,
            status=status,
            error_message=error_message,
            commit=commit,
        )

    def get_log(self, log_id: int) -> AuditLog:
        """
        Get a specific audit log entry by ID.

        Args:
            log_id: The ID of the audit log

        Returns:
            The AuditLog entry

        Raises:
            AuditLogNotFoundError: If the log entry doesn't exist
        """
        log = AuditLog.get_by_id(log_id)
        if not log:
            raise AuditLogNotFoundError(f"Audit log with ID {log_id} not found")
        return log

    def get_logs(
        self,
        user_id: Optional[int] = None,
        action: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[AuditLog]:
        """
        Get audit logs with optional filters.

        Args:
            user_id: Filter by user ID
            action: Filter by action type
            resource_type: Filter by resource type
            resource_id: Filter by resource ID
            start_date: Filter by start date
            end_date: Filter by end date
            status: Filter by status
            limit: Maximum number of results to return
            offset: Number of results to skip

        Returns:
            List of matching AuditLog entries
        """
        from sqlalchemy import and_, or_
        
        query = AuditLog.query.order_by(AuditLog.created_at.desc())
        
        # Apply filters
        filters = []
        
        if user_id is not None:
            filters.append(AuditLog.user_id == user_id)
        
        if action is not None:
            filters.append(AuditLog.action == action)
        
        if resource_type is not None:
            filters.append(AuditLog.resource_type == resource_type)
        
        if resource_id is not None:
            filters.append(AuditLog.resource_id == resource_id)
        
        if start_date is not None:
            filters.append(AuditLog.created_at >= start_date)
        
        if end_date is not None:
            filters.append(AuditLog.created_at <= end_date)
        
        if status is not None:
            filters.append(AuditLog.status == status)
        
        if filters:
            query = query.filter(and_(*filters))
        
        return query.offset(offset).limit(limit).all()

    def get_recent_logs(self, limit: int = 100) -> List[AuditLog]:
        """
        Get the most recent audit logs.

        Args:
            limit: Maximum number of results to return

        Returns:
            List of recent AuditLog entries
        """
        return AuditLog.get_recent(limit)

    def get_logs_by_user(self, user_id: int, limit: int = 100) -> List[AuditLog]:
        """
        Get audit logs for a specific user.

        Args:
            user_id: The user ID to filter by
            limit: Maximum number of results to return

        Returns:
            List of AuditLog entries for the user
        """
        return AuditLog.get_by_user(user_id, limit)

    def get_logs_by_action(self, action: str, limit: int = 100) -> List[AuditLog]:
        """
        Get audit logs for a specific action.

        Args:
            action: The action to filter by
            limit: Maximum number of results to return

        Returns:
            List of AuditLog entries for the action
        """
        return AuditLog.get_by_action(action, limit)

    def search_logs(
        self,
        query: str,
        limit: int = 100,
    ) -> List[AuditLog]:
        """
        Search audit logs by action, resource type, or resource name.

        Args:
            query: Search term
            limit: Maximum number of results to return

        Returns:
            List of matching AuditLog entries
        """
        from sqlalchemy import or_
        
        search_filters = [
            AuditLog.action.ilike(f"%{query}%"),
            AuditLog.resource_type.ilike(f"%{query}%"),
            AuditLog.resource_name.ilike(f"%{query}%"),
        ]
        
        return AuditLog.query.filter(or_(*search_filters)) \
            .order_by(AuditLog.created_at.desc()) \
            .limit(limit) \
            .all()

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about audit logs.

        Returns:
            Dictionary with audit statistics
        """
        total_logs = AuditLog.query.count()
        
        # Get count by action
        action_counts = AuditLog.count_by_action()
        
        # Get count by user
        user_counts = AuditLog.count_by_user()
        
        # Get recent activity
        recent_logs = self.get_recent_logs(10)
        
        # Get all actions and resource types
        all_actions = AuditLog.get_all_actions()
        all_resource_types = AuditLog.get_all_resource_types()
        
        # Get logs by date (last 7 days)
        from sqlalchemy import func
        from datetime import date
        
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        recent_date_counts = (
            db.session.query(
                func.date(AuditLog.created_at),
                func.count(AuditLog.id)
            )
            .filter(AuditLog.created_at >= seven_days_ago)
            .group_by(func.date(AuditLog.created_at))
            .all()
        )
        
        return {
            "total_logs": total_logs,
            "action_counts": action_counts,
            "user_counts": user_counts,
            "recent_logs": [log.to_dict() for log in recent_logs],
            "all_actions": all_actions,
            "all_resource_types": all_resource_types,
            "recent_date_counts": {
                str(date): count for date, count in recent_date_counts
            },
        }

    def export_to_json(
        self,
        user_id: Optional[int] = None,
        action: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 10000,
    ) -> str:
        """
        Export audit logs to JSON format.

        Args:
            user_id: Filter by user ID
            action: Filter by action
            start_date: Filter by start date
            end_date: Filter by end date
            limit: Maximum number of logs to export

        Returns:
            JSON string with audit logs
        """
        logs = self.get_logs(
            user_id=user_id,
            action=action,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
        )
        
        return json.dumps(
            [log.to_dict() for log in logs],
            indent=2,
            ensure_ascii=False,
            default=str,
        )

    def export_to_csv(
        self,
        user_id: Optional[int] = None,
        action: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 10000,
    ) -> str:
        """
        Export audit logs to CSV format.

        Args:
            user_id: Filter by user ID
            action: Filter by action
            start_date: Filter by start date
            end_date: Filter by end date
            limit: Maximum number of logs to export

        Returns:
            CSV string with audit logs
        """
        logs = self.get_logs(
            user_id=user_id,
            action=action,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
        )
        
        output = StringIO()
        writer = csv.DictWriter(
            output,
            fieldnames=[
                "id",
                "user_id",
                "user_email",
                "action",
                "resource_type",
                "resource_id",
                "resource_name",
                "status",
                "error_message",
                "ip_address",
                "user_agent",
                "created_at",
            ],
        )
        
        writer.writeheader()
        
        for log in logs:
            row = {
                "id": log.id,
                "user_id": log.user_id,
                "user_email": log.user.email if log.user else "",
                "action": log.action,
                "resource_type": log.resource_type or "",
                "resource_id": log.resource_id,
                "resource_name": log.resource_name or "",
                "status": log.status or "",
                "error_message": log.error_message or "",
                "ip_address": log.ip_address or "",
                "user_agent": log.user_agent or "",
                "created_at": log.created_at.isoformat() if log.created_at else "",
            }
            writer.writerow(row)
        
        return output.getvalue()

    def clear_old_logs(self, days: int = 90) -> int:
        """
        Clear audit logs older than a certain number of days.

        Args:
            days: Number of days to keep (default: 90)

        Returns:
            Number of logs deleted
        """
        return AuditLog.clear_old_logs(days)

    def clear_all_logs(self) -> int:
        """
        Clear all audit logs.

        Returns:
            Number of logs deleted
        """
        return AuditLog.clear_all()

    def get_request_info(self) -> Dict[str, Optional[str]]:
        """
        Get IP address and user agent from the current request.

        Returns:
            Dictionary with ip_address and user_agent
        """
        from flask import request
        
        ip_address = None
        user_agent = None
        
        if request:
            # Get IP address (handle proxy headers)
            ip_address = request.remote_addr
            if request.headers.get("X-Forwarded-For"):
                ip_address = request.headers.get("X-Forwarded-For").split(",")[0].strip()
            elif request.headers.get("X-Real-IP"):
                ip_address = request.headers.get("X-Real-IP")
            
            # Get user agent
            user_agent = request.headers.get("User-Agent")
        
        return {
            "ip_address": ip_address,
            "user_agent": user_agent,
        }

    def log_from_request(
        self,
        action: Union[str, AuditAction],
        user: Optional[User] = None,
        resource_type: Optional[Union[str, AuditResourceType]] = None,
        resource_id: Optional[int] = None,
        resource_name: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        status: str = "success",
        error_message: Optional[str] = None,
        commit: bool = True,
    ) -> AuditLog:
        """
        Log an action using information from the current request.

        Args:
            action: The action that was performed
            user: The user who performed the action (User object)
            resource_type: Type of resource affected
            resource_id: ID of the resource affected
            resource_name: Name of the resource affected
            metadata: Additional metadata
            status: Status of the action
            error_message: Error message if action failed
            commit: Whether to commit immediately

        Returns:
            The created AuditLog entry
        """
        request_info = self.get_request_info()
        
        return self.log_action(
            action=action,
            user_id=user.id if user else None,
            resource_type=resource_type,
            resource_id=resource_id,
            resource_name=resource_name,
            metadata=metadata,
            ip_address=request_info.get("ip_address"),
            user_agent=request_info.get("user_agent"),
            status=status,
            error_message=error_message,
            commit=commit,
        )

    def create_audit_decorator(
        self,
        action: Union[str, AuditAction],
        resource_type: Optional[Union[str, AuditResourceType]] = None,
        get_resource_id: Optional[str] = None,
        get_resource_name: Optional[str] = None,
    ):
        """
        Create a decorator for automatically logging function calls.

        Args:
            action: The action to log
            resource_type: The resource type
            get_resource_id: Name of the function argument that contains the resource ID
            get_resource_name: Name of the function argument that contains the resource name

        Returns:
            A decorator function
        """
        from functools import wraps
        from typing import Callable
        
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs):
                # Get user from current context
                user = None
                if hasattr(kwargs, "get") and "current_user" in kwargs:
                    user = kwargs["current_user"]
                elif len(args) > 0 and hasattr(args[0], "id"):
                    # First argument might be user
                    user = args[0]
                
                # Get resource ID and name
                resource_id = None
                resource_name = None
                
                if get_resource_id and get_resource_id in kwargs:
                    resource_id = kwargs[get_resource_id]
                elif get_resource_id and len(args) > 0:
                    # Try to get from args
                    arg_names = func.__code__.co_varnames[:func.__code__.co_argcount]
                    if get_resource_id in arg_names:
                        index = arg_names.index(get_resource_id)
                        if index < len(args):
                            resource_id = args[index]
                
                if get_resource_name and get_resource_name in kwargs:
                    resource_name = kwargs[get_resource_name]
                elif get_resource_name and len(args) > 0:
                    arg_names = func.__code__.co_varnames[:func.__code__.co_argcount]
                    if get_resource_name in arg_names:
                        index = arg_names.index(get_resource_name)
                        if index < len(args):
                            resource_name = args[index]
                
                # Call the original function
                result = func(*args, **kwargs)
                
                # Log the action
                self.log_from_request(
                    action=action,
                    user=user,
                    resource_type=resource_type,
                    resource_id=resource_id,
                    resource_name=resource_name,
                    status="success",
                )
                
                return result
            
            return wrapper
        
        return decorator
