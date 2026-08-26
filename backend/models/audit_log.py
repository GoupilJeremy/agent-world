# 📋 Agent World - Audit Log Model
# Version: 1.0.0 (EPIC 10 - US-068)
# Description: Modèle pour stocker l'historique des actions utilisateurs

"""
Audit Log Model for Agent World.

Ce modèle stocke toutes les actions importantes effectuées dans la plateforme
pour permettre l'audit et le suivi des activités.
"""

import json
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from .base import BaseModel, db


class AuditAction(str, Enum):
    """Enumeration of possible audit actions."""
    
    # Authentication actions
    LOGIN = "login"
    LOGOUT = "logout"
    LOGIN_FAILED = "login_failed"
    PASSWORD_CHANGED = "password_changed"
    PASSWORD_RESET = "password_reset"
    TWO_FACTOR_ENABLED = "two_factor_enabled"
    TWO_FACTOR_DISABLED = "two_factor_disabled"
    TWO_FACTOR_SETUP = "two_factor_setup"
    TWO_FACTOR_VERIFIED = "two_factor_verified"
    
    # User management
    USER_CREATED = "user_created"
    USER_UPDATED = "user_updated"
    USER_DELETED = "user_deleted"
    USER_ACTIVATED = "user_activated"
    USER_DEACTIVATED = "user_deactivated"
    ROLE_ASSIGNED = "role_assigned"
    ROLE_REMOVED = "role_removed"
    PERMISSION_GRANTED = "permission_granted"
    PERMISSION_REVOKED = "permission_revoked"
    
    # Agent management
    AGENT_CREATED = "agent_created"
    AGENT_UPDATED = "agent_updated"
    AGENT_DELETED = "agent_deleted"
    AGENT_EXECUTED = "agent_executed"
    AGENT_TESTED = "agent_tested"
    
    # Project management
    PROJECT_CREATED = "project_created"
    PROJECT_UPDATED = "project_updated"
    PROJECT_DELETED = "project_deleted"
    
    # Template management
    TEMPLATE_CREATED = "template_created"
    TEMPLATE_UPDATED = "template_updated"
    TEMPLATE_DELETED = "template_deleted"
    TEMPLATE_SHARED = "template_shared"
    TEMPLATE_IMPORTED = "template_imported"
    TEMPLATE_EXPORTED = "template_exported"
    
    # File management
    FILE_CREATED = "file_created"
    FILE_UPDATED = "file_updated"
    FILE_DELETED = "file_deleted"
    FILE_SHARED = "file_shared"
    FILE_DOWNLOADED = "file_downloaded"
    
    # Workflow management
    WORKFLOW_CREATED = "workflow_created"
    WORKFLOW_UPDATED = "workflow_updated"
    WORKFLOW_DELETED = "workflow_deleted"
    WORKFLOW_EXECUTED = "workflow_executed"
    
    # Integration management
    INTEGRATION_CREATED = "integration_created"
    INTEGRATION_UPDATED = "integration_updated"
    INTEGRATION_DELETED = "integration_deleted"
    INTEGRATION_TESTED = "integration_tested"
    
    # System actions
    SETTING_UPDATED = "setting_updated"
    BACKUP_CREATED = "backup_created"
    BACKUP_RESTORED = "backup_restored"
    ENCRYPTION_KEY_ROTATED = "encryption_key_rotated"
    AUDIT_LOG_CLEARED = "audit_log_cleared"
    
    # Security actions
    SECURITY_ALERT = "security_alert"
    PERMISSION_DENIED = "permission_denied"
    
    @classmethod
    def get_all_values(cls) -> List[str]:
        """Get all action values as a list."""
        return [action.value for action in cls]


class AuditResourceType(str, Enum):
    """Enumeration of resource types that can be audited."""
    
    USER = "user"
    AGENT = "agent"
    PROJECT = "project"
    TEMPLATE = "template"
    WORKFLOW = "workflow"
    FILE = "file"
    INTEGRATION = "integration"
    ROLE = "role"
    PERMISSION = "permission"
    SYSTEM = "system"
    SECURITY = "security"
    UNKNOWN = "unknown"


class AuditLog(BaseModel):
    """
    Model for storing audit log entries.
    
    Each log entry records:
    - Who performed the action (user_id)
    - What action was performed
    - What resource was affected
    - When the action occurred
    - Where the action came from (IP address, user agent)
    - Additional extra_data
    """
    
    __tablename__ = "audit_logs"
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    action = db.Column(db.String(50), nullable=False)
    resource_type = db.Column(db.String(50), nullable=True)
    resource_id = db.Column(db.Integer, nullable=True)
    resource_name = db.Column(db.String(255), nullable=True)
    extra_data = db.Column(db.Text, nullable=True)  # JSON string with additional data (renamed from metadata)
    ip_address = db.Column(db.String(45), nullable=True)  # IPv4 or IPv6
    user_agent = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), nullable=True, default="success")  # success, failure, warning
    error_message = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)
    
    # Relationship
    user = db.relationship("User", backref="audit_logs")
    
    def __init__(
        self,
        user_id: Optional[int] = None,
        action: str = "",
        resource_type: Optional[str] = None,
        resource_id: Optional[int] = None,
        resource_name: Optional[str] = None,
        extra_data: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        status: str = "success",
        error_message: Optional[str] = None,
    ):
        """
        Initialize a new AuditLog entry.
        
        Args:
            user_id: ID of the user who performed the action
            action: The action that was performed
            resource_type: Type of resource affected
            resource_id: ID of the resource affected
            resource_name: Name of the resource affected
            extra_data: Additional data as a dictionary (renamed from metadata)
            ip_address: IP address of the request
            user_agent: User agent of the request
            status: Status of the action (success, failure, warning)
            error_message: Error message if action failed
        """
        self.user_id = user_id
        self.action = action
        self.resource_type = resource_type
        self.resource_id = resource_id
        self.resource_name = resource_name
        self.extra_data = self._serialize_extra_data(extra_data) if extra_data else None
        self.ip_address = ip_address
        self.user_agent = user_agent
        self.status = status
        self.error_message = error_message
    
    @staticmethod
    def _serialize_extra_data(extra_data: Dict[str, Any]) -> str:
        """Serialize extra_data dictionary to JSON string."""
        return json.dumps(extra_data, default=str, ensure_ascii=False)
    
    @staticmethod
    def _deserialize_extra_data(extra_data: Optional[str]) -> Dict[str, Any]:
        """Deserialize extra_data JSON string to dictionary."""
        if extra_data is None:
            return {}
        try:
            return json.loads(extra_data)
        except (json.JSONDecodeError, TypeError):
            return {}
    
    @property
    def extra_data_dict(self) -> Dict[str, Any]:
        """Get extra_data as a dictionary."""
        return self._deserialize_extra_data(self.extra_data)
    
    @extra_data_dict.setter
    def extra_data_dict(self, value: Dict[str, Any]) -> None:
        """Set extra_data from a dictionary."""
        self.extra_data = self._serialize_extra_data(value)
    
    def __repr__(self) -> str:
        return (
            f"<AuditLog(id={self.id}, user_id={self.user_id}, "
            f"action={self.action}, resource={self.resource_type}, "
            f"status={self.status}, created_at={self.created_at})>"
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert audit log to dictionary for API responses."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "user": self.user.to_dict() if self.user else None,
            "action": self.action,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "resource_name": self.resource_name,
            "extra_data": self.extra_data_dict,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "status": self.status,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
    
    @classmethod
    def log(
        cls,
        user_id: Optional[int] = None,
        action: str = "",
        resource_type: Optional[str] = None,
        resource_id: Optional[int] = None,
        resource_name: Optional[str] = None,
        extra_data: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        status: str = "success",
        error_message: Optional[str] = None,
        commit: bool = True,
    ) -> "AuditLog":
        """
        Create and log an audit entry.
        
        Args:
            user_id: ID of the user
            action: The action performed
            resource_type: Type of resource
            resource_id: ID of the resource
            resource_name: Name of the resource
            extra_data: Additional data (renamed from metadata)
            ip_address: IP address
            user_agent: User agent
            status: Status of the action
            error_message: Error message if any
            commit: Whether to commit the changes
            
        Returns:
            The created AuditLog entry
        """
        log_entry = cls(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            resource_name=resource_name,
            extra_data=extra_data,
            ip_address=ip_address,
            user_agent=user_agent,
            status=status,
            error_message=error_message,
        )
        
        db.session.add(log_entry)
        if commit:
            db.session.commit()
        
        return log_entry
    
    @classmethod
    def get_by_id(cls, log_id: int) -> Optional["AuditLog"]:
        """Get an audit log entry by ID."""
        return cls.query.get(log_id)
    
    @classmethod
    def get_by_user(cls, user_id: int, limit: int = 100) -> List["AuditLog"]:
        """Get audit logs for a specific user."""
        return cls.query.filter_by(user_id=user_id).order_by(cls.created_at.desc()).limit(limit).all()
    
    @classmethod
    def get_by_action(cls, action: str, limit: int = 100) -> List["AuditLog"]:
        """Get audit logs for a specific action."""
        return cls.query.filter_by(action=action).order_by(cls.created_at.desc()).limit(limit).all()
    
    @classmethod
    def get_by_resource(cls, resource_type: str, resource_id: int) -> List["AuditLog"]:
        """Get audit logs for a specific resource."""
        return cls.query.filter_by(
            resource_type=resource_type,
            resource_id=resource_id,
        ).order_by(cls.created_at.desc()).all()
    
    @classmethod
    def get_recent(cls, limit: int = 100) -> List["AuditLog"]:
        """Get the most recent audit logs."""
        return cls.query.order_by(cls.created_at.desc()).limit(limit).all()
    
    @classmethod
    def get_by_date_range(
        cls,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 1000,
    ) -> List["AuditLog"]:
        """Get audit logs within a date range."""
        query = cls.query.order_by(cls.created_at.desc())
        
        if start_date:
            query = query.filter(cls.created_at >= start_date)
        if end_date:
            query = query.filter(cls.created_at <= end_date)
        
        return query.limit(limit).all()
    
    @classmethod
    def get_all_actions(cls) -> List[str]:
        """Get all unique actions from the audit logs."""
        return [row[0] for row in cls.query.with_entities(cls.action).distinct().all()]
    
    @classmethod
    def get_all_resource_types(cls) -> List[str]:
        """Get all unique resource types from the audit logs."""
        return [row[0] for row in cls.query.with_entities(cls.resource_type).distinct().all()]
    
    @classmethod
    def count_by_action(cls) -> Dict[str, int]:
        """Count logs by action."""
        from sqlalchemy import func
        results = db.session.query(cls.action, func.count(cls.id)).group_by(cls.action).all()
        return {action: count for action, count in results}
    
    @classmethod
    def count_by_user(cls) -> Dict[int, int]:
        """Count logs by user."""
        from sqlalchemy import func
        results = db.session.query(cls.user_id, func.count(cls.id)).group_by(cls.user_id).all()
        return {user_id: count for user_id, count in results if user_id is not None}
    
    @classmethod
    def clear_old_logs(cls, days: int = 90) -> int:
        """
        Clear audit logs older than a certain number of days.
        
        Args:
            days: Number of days to keep (default: 90)
            
        Returns:
            Number of logs deleted
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        count = cls.query.filter(cls.created_at < cutoff_date).delete()
        db.session.commit()
        return count
    
    @classmethod
    def clear_all(cls) -> int:
        """Clear all audit logs."""
        count = cls.query.delete()
        db.session.commit()
        return count