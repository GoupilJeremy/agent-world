# 📋 Agent World - OAuth Types
# Version: 0.5.0 (Épic 7)
# Description: Types et structures pour OAuth2

"""
OAuth Types for Agent World.

Ce module définit les types de données utilisés pour la gestion OAuth2.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional


class OAuthProvider(Enum):
    """Fournisseurs OAuth2 supportés."""

    GITHUB = "github"
    SLACK = "slack"
    DISCORD = "discord"
    NOTION = "notion"
    GOOGLE = "google"
    TRELLO = "trello"
    CUSTOM = "custom"


@dataclass
class OAuthTokenData:
    """Données d'un token OAuth2."""

    access_token: str
    token_type: str = "Bearer"
    expires_in: Optional[int] = None  # Secondes avant expiration
    refresh_token: Optional[str] = None
    scope: Optional[str] = None

    @property
    def expiry(self) -> Optional[datetime]:
        """Calcule la date d'expiration."""
        if self.expires_in:
            return datetime.utcnow() + timedelta(seconds=self.expires_in)
        return None

    def is_expired(self) -> bool:
        """Vérifie si le token est expiré."""
        if self.expiry:
            return datetime.utcnow() > self.expiry
        return False

    def to_dict(self) -> Dict[str, Any]:
        """Convertit en dictionnaire."""
        return {
            "access_token": self.access_token,
            "token_type": self.token_type,
            "expires_in": self.expires_in,
            "refresh_token": self.refresh_token,
            "scope": self.scope,
            "expiry": self.expiry.isoformat() if self.expiry else None,
            "is_expired": self.is_expired(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "OAuthTokenData":
        """Crée un OAuthTokenData à partir d'un dictionnaire."""
        return cls(
            access_token=data["access_token"],
            token_type=data.get("token_type", "Bearer"),
            expires_in=data.get("expires_in"),
            refresh_token=data.get("refresh_token"),
            scope=data.get("scope"),
        )


@dataclass
class OAuthState:
    """État OAuth2 pour la sécurité CSRF."""

    state: str
    provider: OAuthProvider
    redirect_path: str
    user_id: Optional[int] = None
    integration_id: Optional[int] = None
    created_at: datetime = field(default_factory=datetime.utcnow)

    def is_valid(self, ttl_seconds: int = 300) -> bool:
        """Vérifie si l'état est encore valide."""
        return (datetime.utcnow() - self.created_at).total_seconds() < ttl_seconds

    def to_dict(self) -> Dict[str, Any]:
        """Convertit en dictionnaire."""
        return {
            "state": self.state,
            "provider": self.provider.value,
            "redirect_path": self.redirect_path,
            "user_id": self.user_id,
            "integration_id": self.integration_id,
            "created_at": self.created_at.isoformat(),
            "is_valid": self.is_valid(),
        }


@dataclass
class OAuthProviderConfig:
    """Configuration pour un fournisseur OAuth2."""

    provider: OAuthProvider
    client_id: str
    client_secret: str
    redirect_uri: str
    authorization_url: str
    token_url: str
    userinfo_url: Optional[str] = None
    scope: List[str] = field(default_factory=list)

    # Configuration supplémentaire
    pkce_enabled: bool = True
    token_expiry_seconds: int = 3600
    refresh_token_enabled: bool = True

    def to_dict(self, include_secrets: bool = False) -> Dict[str, Any]:
        """Convertit en dictionnaire."""
        result = {
            "provider": self.provider.value,
            "redirect_uri": self.redirect_uri,
            "authorization_url": self.authorization_url,
            "token_url": self.token_url,
            "userinfo_url": self.userinfo_url,
            "scope": self.scope,
            "pkce_enabled": self.pkce_enabled,
            "token_expiry_seconds": self.token_expiry_seconds,
            "refresh_token_enabled": self.refresh_token_enabled,
        }

        if include_secrets:
            result["client_id"] = self.client_id
            result["client_secret"] = self.client_secret

        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "OAuthProviderConfig":
        """Crée une OAuthProviderConfig à partir d'un dictionnaire."""
        return cls(
            provider=OAuthProvider(data["provider"]),
            client_id=data["client_id"],
            client_secret=data["client_secret"],
            redirect_uri=data["redirect_uri"],
            authorization_url=data["authorization_url"],
            token_url=data["token_url"],
            userinfo_url=data.get("userinfo_url"),
            scope=data.get("scope", []),
            pkce_enabled=data.get("pkce_enabled", True),
            token_expiry_seconds=data.get("token_expiry_seconds", 3600),
            refresh_token_enabled=data.get("refresh_token_enabled", True),
        )


# Configuration par défaut pour les fournisseurs
DEFAULT_PROVIDER_CONFIGS = {
    OAuthProvider.GITHUB: OAuthProviderConfig(
        provider=OAuthProvider.GITHUB,
        client_id="",
        client_secret="",
        redirect_uri="http://localhost:5000/api/integrations/github/callback",
        authorization_url="https://github.com/login/oauth/authorize",
        token_url="https://github.com/login/oauth/access_token",
        userinfo_url="https://api.github.com/user",
        scope=["repo", "user"],
        pkce_enabled=False,  # GitHub ne supporte pas PKCE par défaut
        refresh_token_enabled=False,  # GitHub n'a pas de refresh token
    ),
    OAuthProvider.SLACK: OAuthProviderConfig(
        provider=OAuthProvider.SLACK,
        client_id="",
        client_secret="",
        redirect_uri="http://localhost:5000/api/integrations/slack/callback",
        authorization_url="https://slack.com/oauth/v2/authorize",
        token_url="https://slack.com/api/oauth.v2.access",
        userinfo_url="https://slack.com/api/users.identity",
        scope=["chat:write", "chat:write.public", "commands"],
        pkce_enabled=False,
        refresh_token_enabled=True,
    ),
    OAuthProvider.DISCORD: OAuthProviderConfig(
        provider=OAuthProvider.DISCORD,
        client_id="",
        client_secret="",
        redirect_uri="http://localhost:5000/api/integrations/discord/callback",
        authorization_url="https://discord.com/api/oauth2/authorize",
        token_url="https://discord.com/api/oauth2/token",
        userinfo_url="https://discord.com/api/users/@me",
        scope=["identify", "guilds", "messages"],
        pkce_enabled=False,
        refresh_token_enabled=True,
    ),
    OAuthProvider.NOTION: OAuthProviderConfig(
        provider=OAuthProvider.NOTION,
        client_id="",
        client_secret="",
        redirect_uri="http://localhost:5000/api/integrations/notion/callback",
        authorization_url="https://api.notion.com/v1/oauth/authorize",
        token_url="https://api.notion.com/v1/oauth/token",
        userinfo_url="https://api.notion.com/v1/users/me",
        scope=["read", "write"],
        pkce_enabled=False,
        refresh_token_enabled=True,
    ),
    OAuthProvider.GOOGLE: OAuthProviderConfig(
        provider=OAuthProvider.GOOGLE,
        client_id="",
        client_secret="",
        redirect_uri="http://localhost:5000/api/integrations/google/callback",
        authorization_url="https://accounts.google.com/o/oauth2/v2/auth",
        token_url="https://oauth2.googleapis.com/token",
        userinfo_url="https://www.googleapis.com/oauth2/v2/userinfo",
        scope=["https://www.googleapis.com/auth/drive"],
        pkce_enabled=False,
        refresh_token_enabled=True,
    ),
    OAuthProvider.TRELLO: OAuthProviderConfig(
        provider=OAuthProvider.TRELLO,
        client_id="",
        client_secret="",
        redirect_uri="http://localhost:5000/api/integrations/trello/callback",
        authorization_url="https://trello.com/1/OAuthAuthorizeToken",
        token_url="https://trello.com/1/OAuthGetAccessToken",
        userinfo_url=None,
        scope=["read", "write"],
        pkce_enabled=False,
        refresh_token_enabled=False,
    ),
}
