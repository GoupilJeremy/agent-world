# 📋 Agent World - Webhook Types
# Version: 0.5.0 (Épic 7 - US-053)
# Description: Types pour les webhooks

"""
Webhook Types for Agent World.

Ce module définit les types de données utilisés pour la gestion des webhooks.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class WebhookEventType(Enum):
    """Types d'événements webhook."""
    
    # Événements système
    SYSTEM_STARTUP = "system.startup"
    SYSTEM_SHUTDOWN = "system.shutdown"
    
    # Événements agents
    AGENT_CREATED = "agent.created"
    AGENT_UPDATED = "agent.updated"
    AGENT_DELETED = "agent.deleted"
    AGENT_EXECUTED = "agent.executed"
    
    # Événements workflows
    WORKFLOW_STARTED = "workflow.started"
    WORKFLOW_COMPLETED = "workflow.completed"
    WORKFLOW_FAILED = "workflow.failed"
    
    # Événements fichiers
    FILE_CREATED = "file.created"
    FILE_UPDATED = "file.updated"
    FILE_DELETED = "file.deleted"
    
    # Événements personnalisés
    CUSTOM = "custom"


class WebhookStatus(Enum):
    """Statut d'un webhook."""
    
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    PENDING = "pending"


@dataclass
class WebhookEvent:
    """Événement webhook."""
    
    event_type: str
    source: str  # Ex: "agent", "workflow", "file"
    source_id: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    # Données de l'événement
    data: Dict[str, Any] = field(default_factory=dict)
    
    # Métadonnées
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit en dictionnaire."""
        return {
            "event_type": self.event_type,
            "source": self.source,
            "source_id": self.source_id,
            "timestamp": self.timestamp.isoformat(),
            "data": self.data,
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WebhookEvent":
        """Crée un WebhookEvent à partir d'un dictionnaire."""
        return cls(
            event_type=data["event_type"],
            source=data["source"],
            source_id=data.get("source_id"),
            timestamp=datetime.fromisoformat(data["timestamp"]) if data.get("timestamp") else datetime.utcnow(),
            data=data.get("data", {}),
            metadata=data.get("metadata", {}),
        )


@dataclass
class WebhookPayload:
    """Payload d'un webhook entrant."""
    
    # En-têtes HTTP
    headers: Dict[str, str] = field(default_factory=dict)
    
    # Données du corps
    body: Dict[str, Any] = field(default_factory=dict)
    
    # Query parameters
    query_params: Dict[str, str] = field(default_factory=dict)
    
    # Identification du webhook
    webhook_id: Optional[str] = None
    webhook_secret: Optional[str] = None
    
    # Horodatage
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def verify_signature(
        self, 
        expected_signature: str,
        secret: str
    ) -> bool:
        """
        Vérifie la signature du webhook.
        
        Args:
            expected_signature: Signature attendue
            secret: Secret partagé
            
        Returns:
            True si la signature est valide
        """
        import hmac
        import hashlib
        
        # Pour GitHub, la signature est "sha256=<hash>"
        if expected_signature.startswith("sha256="):
            expected_hash = expected_signature[7:]
            
            # Calculer le hash
            payload_bytes = self.body if isinstance(self.body, bytes) else str(self.body).encode()
            computed_hash = hmac.new(
                secret.encode(),
                payload_bytes,
                hashlib.sha256
            ).hexdigest()
            
            # Comparaison sécurisée
            import hmac as hmac_compare
            return hmac_compare.compare_digest(computed_hash, expected_hash)
        
        return False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit en dictionnaire."""
        return {
            "headers": self.headers,
            "body": self.body,
            "query_params": self.query_params,
            "webhook_id": self.webhook_id,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class WebhookResponse:
    """Réponse d'un webhook."""
    
    status_code: int = 200
    success: bool = True
    message: str = "OK"
    data: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit en dictionnaire."""
        result = {
            "success": self.success,
            "message": self.message,
            "data": self.data,
        }
        
        if self.error:
            result["error"] = self.error
        
        return result
    
    def to_flask_response(self) -> Any:
        """
        Convertit en réponse Flask.
        
        Returns:
            Réponse Flask
        """
        from flask import jsonify, make_response
        
        response = make_response(
            jsonify(self.to_dict()),
            self.status_code,
        )
        
        return response


@dataclass
class WebhookSubscription:
    """Abonnement à un webhook."""
    
    id: Optional[int] = None
    name: str = ""
    url: str = ""
    events: List[str] = field(default_factory=list)
    secret: Optional[str] = None
    active: bool = True
    status: WebhookStatus = WebhookStatus.PENDING
    
    # Statistiques
    calls_count: int = 0
    success_count: int = 0
    error_count: int = 0
    
    # Métadonnées
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    last_called_at: Optional[datetime] = None
    last_error_at: Optional[datetime] = None
    last_error: Optional[str] = None
    
    def to_dict(self, include_secret: bool = False) -> Dict[str, Any]:
        """Convertit en dictionnaire."""
        result = {
            "id": self.id,
            "name": self.name,
            "url": self.url,
            "events": self.events,
            "active": self.active,
            "status": self.status.value,
            "calls_count": self.calls_count,
            "success_count": self.success_count,
            "error_count": self.error_count,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "last_called_at": self.last_called_at.isoformat() if self.last_called_at else None,
            "last_error_at": self.last_error_at.isoformat() if self.last_error_at else None,
            "last_error": self.last_error,
        }
        
        if include_secret and self.secret:
            result["secret"] = self.secret
        
        return result
