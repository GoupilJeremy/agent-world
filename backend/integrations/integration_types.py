# 📋 Agent World - Integration Types
# Version: 0.5.0 (Épic 7)
# Description: Types et interfaces pour les intégrations externes

"""
Integration Types for Agent World.

Ce module définit les types de données, énumérations et structures
utilisés par le système d'intégrations externes.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union


class IntegrationType(Enum):
    """Types d'intégrations supportées."""

    GITHUB = "github"
    SLACK = "slack"
    DISCORD = "discord"
    NOTION = "notion"
    GOOGLE_DRIVE = "google_drive"
    TRELLO = "trello"
    WEBHOOK = "webhook"


class AuthType(Enum):
    """Types d'authentification supportés."""

    OAUTH2 = "oauth2"
    API_KEY = "api_key"
    BEARER_TOKEN = "bearer_token"
    NONE = "none"


class IntegrationStatus(Enum):
    """Statut d'une intégration."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    PENDING_AUTH = "pending_auth"


@dataclass
class OAuthConfig:
    """Configuration pour l'authentification OAuth2."""

    client_id: str
    client_secret: str
    redirect_uri: str
    scope: List[str] = field(default_factory=list)
    authorization_url: str = ""
    token_url: str = ""
    userinfo_url: Optional[str] = None


@dataclass
class IntegrationCredentials:
    """Identifiants de connexion pour une intégration."""

    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    api_key: Optional[str] = None
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    webhook_url: Optional[str] = None
    webhook_secret: Optional[str] = None

    # Pour OAuth2
    token_expiry: Optional[datetime] = None

    def is_valid(self) -> bool:
        """Vérifie si les identifiants sont valides."""
        if self.access_token:
            if self.token_expiry and self.token_expiry < datetime.utcnow():
                return False
            return True
        if self.api_key:
            return True
        if self.webhook_url:
            return True
        return False

    def to_dict(self) -> Dict[str, Any]:
        """Convertit en dictionnaire (sans les tokens sensibles)."""
        return {
            "has_access_token": self.access_token is not None,
            "has_api_key": self.api_key is not None,
            "has_webhook": self.webhook_url is not None,
            "token_expiry": (
                self.token_expiry.isoformat() if self.token_expiry else None
            ),
        }


@dataclass
class IntegrationAction:
    """Action à exécuter via une intégration."""

    action_type: str  # Ex: "create_pr", "send_message", "create_card"
    payload: Dict[str, Any] = field(default_factory=dict)
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class IntegrationResult:
    """Résultat d'une action d'intégration."""

    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    error_code: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    duration_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convertit en dictionnaire."""
        return {
            "success": self.success,
            "data": self.data,
            "error": self.error,
            "error_code": self.error_code,
            "timestamp": self.timestamp.isoformat(),
            "duration_ms": self.duration_ms,
        }


@dataclass
class WebhookConfig:
    """Configuration pour un webhook."""

    url: str
    secret: Optional[str] = None
    events: List[str] = field(default_factory=list)
    active: bool = True
    rate_limit: Optional[int] = None  # Requêtes par minute

    def to_dict(self) -> Dict[str, Any]:
        """Convertit en dictionnaire."""
        return {
            "url": self.url,
            "events": self.events,
            "active": self.active,
            "rate_limit": self.rate_limit,
        }


@dataclass
class IntegrationConfig:
    """
    Configuration complète pour une intégration.

    Ce dataclass représente la configuration stockée en base de données
    pour une intégration utilisateur.
    """

    id: Optional[int] = None
    user_id: Optional[int] = None  # ID de l'utilisateur propriétaire
    integration_type: IntegrationType = IntegrationType.WEBHOOK
    name: str = ""
    description: str = ""
    credentials: IntegrationCredentials = field(default_factory=IntegrationCredentials)
    settings: Dict[str, Any] = field(default_factory=dict)
    status: IntegrationStatus = IntegrationStatus.INACTIVE
    oauth_config: Optional[OAuthConfig] = None
    webhook_config: Optional[WebhookConfig] = None

    # Métadonnées
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    last_used_at: Optional[datetime] = None
    usage_count: int = 0
    error_count: int = 0

    def __post_init__(self):
        """Initialisation post-création."""
        if isinstance(self.integration_type, str):
            self.integration_type = IntegrationType(self.integration_type)
        if isinstance(self.status, str):
            self.status = IntegrationStatus(self.status)
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()

    def to_dict(self, include_secrets: bool = False) -> Dict[str, Any]:
        """
        Convertit en dictionnaire.

        Args:
            include_secrets: Si True, inclut les informations sensibles
                            (NE PAS UTILISER en production!)
        """
        result = {
            "id": self.id,
            "user_id": self.user_id,
            "integration_type": self.integration_type.value,
            "name": self.name,
            "description": self.description,
            "status": self.status.value,
            "settings": self.settings,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_used_at": (
                self.last_used_at.isoformat() if self.last_used_at else None
            ),
            "usage_count": self.usage_count,
            "error_count": self.error_count,
        }

        if include_secrets:
            result["credentials"] = {
                "access_token": self.credentials.access_token,
                "refresh_token": self.credentials.refresh_token,
                "api_key": self.credentials.api_key,
                "webhook_url": self.credentials.webhook_url,
                "webhook_secret": self.credentials.webhook_secret,
            }
        else:
            result["credentials"] = self.credentials.to_dict()

        if self.oauth_config:
            result["oauth_config"] = {
                "client_id": self.oauth_config.client_id if include_secrets else "***",
                "redirect_uri": self.oauth_config.redirect_uri,
                "scope": self.oauth_config.scope,
            }

        if self.webhook_config:
            result["webhook_config"] = self.webhook_config.to_dict()

        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "IntegrationConfig":
        """Crée une IntegrationConfig à partir d'un dictionnaire."""
        return cls(
            id=data.get("id"),
            user_id=data.get("user_id"),
            integration_type=data.get("integration_type", "webhook"),
            name=data.get("name", ""),
            description=data.get("description", ""),
            credentials=IntegrationCredentials(
                access_token=data.get("credentials", {}).get("access_token"),
                refresh_token=data.get("credentials", {}).get("refresh_token"),
                api_key=data.get("credentials", {}).get("api_key"),
                webhook_url=data.get("credentials", {}).get("webhook_url"),
                webhook_secret=data.get("credentials", {}).get("webhook_secret"),
            ),
            settings=data.get("settings", {}),
            status=data.get("status", IntegrationStatus.INACTIVE.value),
            oauth_config=(
                OAuthConfig(**data.get("oauth_config", {}))
                if data.get("oauth_config")
                else None
            ),
            webhook_config=(
                WebhookConfig(**data.get("webhook_config", {}))
                if data.get("webhook_config")
                else None
            ),
            created_at=(
                datetime.fromisoformat(data.get("created_at"))
                if data.get("created_at")
                else None
            ),
            updated_at=(
                datetime.fromisoformat(data.get("updated_at"))
                if data.get("updated_at")
                else None
            ),
            last_used_at=(
                datetime.fromisoformat(data.get("last_used_at"))
                if data.get("last_used_at")
                else None
            ),
            usage_count=data.get("usage_count", 0),
            error_count=data.get("error_count", 0),
        )
