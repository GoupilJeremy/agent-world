# 🎮 Agent World - Discord Integration Adapter
# Version: 0.5.0 (Épic 7 - US-049)
# Description: Adapter pour l'intégration avec Discord

"""
Discord Integration Adapter for Agent World.

Ce module implémente l'adapter pour l'intégration avec Discord.
Il permet aux agents d'envoyer des messages, de gérer des serveurs,
de créer des salons et d'interagir avec les utilisateurs Discord.

Requirements:
    - requests: Pour les requêtes HTTP
    - requests-oauthlib: Pour OAuth2 (optionnel)
"""

import logging
import secrets
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from urllib.parse import urlencode

import requests

from ..base_adapter import (
    ActionNotSupportedError,
    AuthenticationError,
    BaseIntegrationAdapter,
    ConnectionError,
)
from ..integration_types import (
    AuthType,
    IntegrationAction,
    IntegrationConfig,
    IntegrationCredentials,
    IntegrationResult,
    IntegrationType,
    OAuthConfig,
)

logger = logging.getLogger(__name__)

# Importer le décorateur depuis le module parent
from . import register_adapter  # noqa: E402


@register_adapter
class DiscordIntegrationAdapter(BaseIntegrationAdapter):
    """
    Adapter pour l'intégration avec Discord.

    Cet adapter permet aux agents d'effectuer les actions suivantes :
    - Envoyer un message à un salon
    - Créer un salon (canal)
    - Lister les salons
    - Obtenir des informations sur un utilisateur
    - Gérer les rôles
    - Réagir à un message
    - Créer des commandements personnalisées
    - Envoyer des embeds riches

    Authentication:
        - OAuth2 (recommandé)
        - Bot Token
        - Webhook URL (pour les incoming webhooks)

    Note: Discord utilise une API REST avec des tokens Bearer.
    L'API Discord a des rate limits stricts (50 requêtes par seconde globalement).
    """

    # Configuration de l'adapter
    type = IntegrationType.DISCORD
    name = "Discord"
    description = (
        "Intégration avec Discord pour envoyer des messages, "
        "notifications et interagir avec les serveurs"
    )
    auth_type = AuthType.OAUTH2
    icon = "discord"
    color = "#5865F2"

    # Actions supportées
    supported_actions = [
        # Messages
        "send_message",
        "send_embed",
        "edit_message",
        "delete_message",
        "pin_message",
        "unpin_message",
        # Salons (Channels)
        "list_channels",
        "get_channel_info",
        "create_channel",
        "edit_channel",
        "delete_channel",
        # Serveurs (Guilds)
        "list_guilds",
        "get_guild_info",
        "create_guild",
        # Utilisateurs
        "get_user_info",
        "list_guild_members",
        "get_member_info",
        "kick_member",
        "ban_member",
        # Rôles
        "list_roles",
        "create_role",
        "edit_role",
        "delete_role",
        "add_role_to_member",
        "remove_role_from_member",
        # Réactions
        "add_reaction",
        "remove_reaction",
        # Commandes personnalisées
        "create_slash_command",
        "list_slash_commands",
        "delete_slash_command",
        # Webhooks
        "create_webhook",
        "list_webhooks",
        "delete_webhook",
        "execute_webhook",
    ]

    # Configuration OAuth2 par défaut pour Discord
    # Note: Discord utilise un flux OAuth2 spécial avec un "Bot Token" pour les bots
    OAUTH_CONFIG = OAuthConfig(
        client_id="",  # À configurer (Client ID de l'application Discord)
        client_secret="",  # À configurer (Client Secret)
        redirect_uri="http://localhost:5000/api/integrations/discord/callback",
        authorization_url="https://discord.com/api/oauth2/authorize",
        token_url="https://discord.com/api/oauth2/token",
        userinfo_url="https://discord.com/api/users/@me",
        scope=[
            "identify",
            "email",
            "connections",
            "guilds",
            "guilds.join",
            "messages.read",
            "applications.commands",
            "bot",
        ],
    )

    def __init__(self, config: Optional[IntegrationConfig] = None):
        """Initialise l'adapter Discord."""
        # Si une config OAuth globale est fournie, l'utiliser
        if config and config.oauth_config:
            self.oauth_config = config.oauth_config
        else:
            self.oauth_config = self.OAUTH_CONFIG

        super().__init__(config)
        self.session = requests.Session()

        # Ajouter les headers par défaut
        self.session.headers.update(
            {
                "Content-Type": "application/json",
                "User-Agent": "AgentWorld/0.5.0 (Discord Bot)",
            }
        )

        # Stocker la version de l'API Discord
        self.api_version = 10  # Version actuelle de l'API Discord

    def _get_auth_headers(self) -> Dict[str, str]:
        """
        Obtient les headers d'authentification.

        Returns:
            Dictionnaire des headers
        """
        if not self.config or not self.config.credentials:
            raise AuthenticationError("No credentials configured", self.type)

        credentials = self.config.credentials

        # Discord utilise un Bearer token
        # Peut être un Bot Token (commence par OD...) ou un User Token
        if credentials.access_token:
            return {"Authorization": f"Bearer {credentials.access_token}"}
        elif credentials.api_key:
            # Pour les Bot Tokens
            if credentials.api_key.startswith("OD") or credentials.api_key.startswith(
                "M"
            ):
                return {"Authorization": f"Bot {credentials.api_key}"}
            # Pour les User Tokens
            return {"Authorization": f"Bearer {credentials.api_key}"}

        raise AuthenticationError("No valid Discord token found", self.type)

    def _get_api_base_url(self) -> str:
        """Retourne l'URL de base de l'API Discord."""
        return f"https://discord.com/api/v{self.api_version}"

    def _make_request(self, method: str, endpoint: str, **kwargs) -> Any:
        """
        Effectue une requête à l'API Discord avec gestion des erreurs.

        Args:
            method: Méthode HTTP (GET, POST, etc.)
            endpoint: Endpoint de l'API Discord (sans l'URL de base)
            **kwargs: Arguments supplémentaires pour requests

        Returns:
            Réponse JSON ou None

        Raises:
            ConnectionError: En cas d'erreur de connexion
        """
        url = f"{self._get_api_base_url()}/{endpoint}"
        headers = self._get_auth_headers()
        headers.update(kwargs.pop("headers", {}))

        try:
            response = self.session.request(
                method, url, headers=headers, timeout=30, **kwargs
            )

            # Gérer les erreurs HTTP
            if response.status_code >= 400:
                error_data = {"status_code": response.status_code}
                try:
                    response_json = response.json()
                    error_data["response"] = response_json
                    # Discord retourne un champ 'message' et 'code'
                    error_data["discord_error"] = response_json.get(
                        "message", "Unknown error"
                    )
                    error_data["error_code"] = response_json.get("code")
                except Exception:
                    error_data["response"] = response.text

                logger.error(f"Discord API error: {error_data}")

                if response.status_code == 401:
                    raise AuthenticationError(
                        "Invalid or expired Discord token", self.type
                    )
                elif response.status_code == 429:
                    # Discord rate limit - attendre et réessayer
                    retry_after = response.json().get("retry_after", 5)
                    raise ConnectionError(
                        f"Discord API rate limit exceeded. Retry after {retry_after}s",
                        self.type,
                    )
                else:
                    error_msg = error_data.get("discord_error", response.text)
                    raise ConnectionError(f"Discord API error: {error_msg}", self.type)

            # Retourner la réponse JSON
            try:
                return response.json()
            except ValueError:
                return response.text

        except requests.exceptions.RequestException as e:
            logger.error(f"Discord request failed: {e}")
            raise ConnectionError(str(e), self.type)

    def authenticate(self, credentials: IntegrationCredentials) -> bool:
        """
        Authentifie l'intégration avec Discord.

        Args:
            credentials: Identifiants à utiliser

        Returns:
            True si l'authentification réussit
        """
        try:
            # Temporairement utiliser ces credentials pour tester
            old_credentials = self.config.credentials if self.config else None

            # Créer une config temporaire
            temp_config = IntegrationConfig(
                integration_type=self.type,
                credentials=credentials,
            )
            self.config = temp_config

            # Tester la connexion
            result = self.test_connection()

            # Restaurer les credentials d'origine
            if old_credentials:
                self.config.credentials = old_credentials

            return result.success

        except Exception as e:
            logger.error(f"Discord authentication failed: {e}")
            return False

    def get_authentication_url(self, state: Optional[str] = None) -> str:
        """
        Génère l'URL d'authentification OAuth2 pour Discord.

        Args:
            state: Valeur state pour la sécurité CSRF (générée si non fournie)

        Returns:
            URL d'authentification OAuth2
        """
        if not state:
            state = secrets.token_urlsafe(16)

        params = {
            "client_id": self.oauth_config.client_id,
            "redirect_uri": self.oauth_config.redirect_uri,
            "response_type": "code",
            "scope": " ".join(self.oauth_config.scope),
            "state": state,
            "prompt": "consent",  # Demander explicitement les permissions
        }

        return f"{self.oauth_config.authorization_url}?{urlencode(params)}"

    def exchange_code_for_token(self, code: str) -> IntegrationCredentials:
        """
        Échange un code d'autorisation OAuth2 contre un token Discord.

        Args:
            code: Code d'autorisation reçu de Discord

        Returns:
            IntegrationCredentials avec le token d'accès

        Raises:
            ValueError: Si l'échange échoue
        """
        try:
            data = {
                "client_id": self.oauth_config.client_id,
                "client_secret": self.oauth_config.client_secret,
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": self.oauth_config.redirect_uri,
            }

            headers = {
                "Content-Type": "application/x-www-form-urlencoded",
            }

            response = requests.post(
                self.oauth_config.token_url,
                data=data,
                headers=headers,
                timeout=30,
            )

            if response.status_code != 200:
                error_msg = f"Failed to exchange code: {response.status_code}"
                try:
                    error_data = response.json()
                    error_msg += f" - {error_data.get('message', 'Unknown error')}"
                except Exception:
                    error_msg += f" - {response.text}"
                raise ValueError(error_msg)

            token_data = response.json()
            access_token = token_data.get("access_token")
            refresh_token = token_data.get("refresh_token")
            expires_in = token_data.get("expires_in", 3600)

            if not access_token:
                raise ValueError("No access token received from Discord")

            # Calculer l'expiration
            token_expiry = datetime.utcnow() + timedelta(seconds=expires_in)

            return IntegrationCredentials(
                access_token=access_token,
                refresh_token=refresh_token,
                token_expiry=token_expiry,
            )

        except requests.exceptions.RequestException as e:
            logger.error(f"Discord token exchange failed: {e}")
            raise ValueError(f"Discord token exchange failed: {e}")

    def refresh_token(self, refresh_token: str) -> IntegrationCredentials:
        """
        Rafraîchit le token d'accès avec un refresh token.

        Args:
            refresh_token: Refresh token à utiliser

        Returns:
            IntegrationCredentials avec les nouveaux tokens

        Raises:
            ValueError: Si le rafraîchissement échoue
        """
        try:
            data = {
                "client_id": self.oauth_config.client_id,
                "client_secret": self.oauth_config.client_secret,
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
            }

            headers = {
                "Content-Type": "application/x-www-form-urlencoded",
            }

            response = requests.post(
                self.oauth_config.token_url,
                data=data,
                headers=headers,
                timeout=30,
            )

            if response.status_code != 200:
                error_msg = f"Failed to refresh token: {response.status_code}"
                try:
                    error_data = response.json()
                    error_msg += f" - {error_data.get('message', 'Unknown error')}"
                except Exception:
                    error_msg += f" - {response.text}"
                raise ValueError(error_msg)

            token_data = response.json()
            access_token = token_data.get("access_token")
            new_refresh_token = token_data.get("refresh_token", refresh_token)
            expires_in = token_data.get("expires_in", 3600)

            if not access_token:
                raise ValueError("No new access token received from Discord")

            # Calculer l'expiration
            token_expiry = datetime.utcnow() + timedelta(seconds=expires_in)

            return IntegrationCredentials(
                access_token=access_token,
                refresh_token=new_refresh_token,
                token_expiry=token_expiry,
            )

        except requests.exceptions.RequestException as e:
            logger.error(f"Discord token refresh failed: {e}")
            raise ValueError(f"Discord token refresh failed: {e}")

    def test_connection(self) -> IntegrationResult:
        """
        Teste la connexion à Discord.

        Returns:
            IntegrationResult avec le résultat du test
        """
        try:
            # Appeler l'API users/@me pour vérifier l'authentification
            result = self._make_request("GET", "users/@me")

            if result and isinstance(result, dict):
                username = result.get("username")
                discriminator = result.get("discriminator")
                user_id = result.get("id")
                global_name = result.get("global_name")

                return IntegrationResult(
                    success=True,
                    data={
                        "user_id": user_id,
                        "username": (
                            f"{username}#{discriminator}"
                            if username and discriminator
                            else username
                        ),
                        "global_name": global_name,
                        "message": "Successfully connected to Discord",
                    },
                )
            else:
                return IntegrationResult(
                    success=False,
                    error="Invalid response from Discord",
                )
        except Exception as e:
            logger.error(f"Discord connection test failed: {e}")
            return IntegrationResult(
                success=False,
                error=str(e),
            )

    def execute(self, action: IntegrationAction) -> IntegrationResult:
        """
        Exécute une action Discord.

        Args:
            action: Action à exécuter

        Returns:
            IntegrationResult avec le résultat de l'action

        Raises:
            ActionNotSupportedError: Si l'action n'est pas supportée
        """
        if not self.is_action_supported(action.action_type):
            raise ActionNotSupportedError(action.action_type, self.type)

        # Router vers la méthode appropriée
        handler_method = getattr(self, f"_{action.action_type}", None)

        if handler_method:
            return handler_method(action.payload)
        else:
            raise ActionNotSupportedError(action.action_type, self.type)

    # ==================== Action Handlers ====================

    def _send_message(self, payload: Dict[str, Any]) -> IntegrationResult:
        """Envoye un message à un salon."""
        try:
            channel_id = payload.get("channel_id")
            content = payload.get("content")
            embeds = payload.get("embeds")
            components = payload.get("components")
            tts = payload.get("tts", False)

            if not channel_id or not content:
                return IntegrationResult(
                    success=False,
                    error="channel_id and content are required",
                )

            message_data = {
                "content": content,
            }

            if embeds:
                message_data["embeds"] = embeds
            if components:
                message_data["components"] = components
            if tts:
                message_data["tts"] = tts

            result = self._make_request(
                "POST", f"channels/{channel_id}/messages", json=message_data
            )

            return IntegrationResult(
                success=True,
                data={
                    "message": result,
                    "channel_id": channel_id,
                    "message_id": result.get("id") if result else None,
                },
            )

        except Exception as e:
            logger.error(f"Failed to send Discord message: {e}")
            return IntegrationResult(
                success=False,
                error=str(e),
            )

    def _send_embed(self, payload: Dict[str, Any]) -> IntegrationResult:
        """Envoye un message avec un embed riche."""
        try:
            channel_id = payload.get("channel_id")
            embed = payload.get("embed")
            content = payload.get("content", "")

            if not channel_id or not embed:
                return IntegrationResult(
                    success=False,
                    error="channel_id and embed are required",
                )

            # Construire l'embed avec les champs standards
            embed_data = {
                "title": embed.get("title", ""),
                "description": embed.get("description", ""),
                "url": embed.get("url", ""),
                "color": embed.get("color", 0x00FF00),
            }

            # Ajouter les champs optionnels
            if "fields" in embed:
                embed_data["fields"] = embed["fields"]
            if "author" in embed:
                embed_data["author"] = embed["author"]
            if "footer" in embed:
                embed_data["footer"] = embed["footer"]
            if "image" in embed:
                embed_data["image"] = embed["image"]
            if "thumbnail" in embed:
                embed_data["thumbnail"] = embed["thumbnail"]
            if "timestamp" in embed:
                embed_data["timestamp"] = embed["timestamp"]

            message_data = {
                "content": content,
                "embeds": [embed_data],
            }

            result = self._make_request(
                "POST", f"channels/{channel_id}/messages", json=message_data
            )

            return IntegrationResult(
                success=True,
                data={
                    "message": result,
                    "channel_id": channel_id,
                    "message_id": result.get("id") if result else None,
                },
            )

        except Exception as e:
            logger.error(f"Failed to send Discord embed: {e}")
            return IntegrationResult(
                success=False,
                error=str(e),
            )

    def _edit_message(self, payload: Dict[str, Any]) -> IntegrationResult:
        """Modifie un message existant."""
        try:
            channel_id = payload.get("channel_id")
            message_id = payload.get("message_id")
            content = payload.get("content")
            embeds = payload.get("embeds")

            if not channel_id or not message_id:
                return IntegrationResult(
                    success=False,
                    error="channel_id and message_id are required",
                )

            message_data = {}
            if content:
                message_data["content"] = content
            if embeds:
                message_data["embeds"] = embeds

            if not message_data:
                return IntegrationResult(
                    success=False,
                    error="At least one of content or embeds is required",
                )

            result = self._make_request(
                "PATCH",
                f"channels/{channel_id}/messages/{message_id}",
                json=message_data,
            )

            return IntegrationResult(
                success=True,
                data={"message": result},
            )

        except Exception as e:
            logger.error(f"Failed to edit Discord message: {e}")
            return IntegrationResult(
                success=False,
                error=str(e),
            )

    def _delete_message(self, payload: Dict[str, Any]) -> IntegrationResult:
        """Supprime un message."""
        try:
            channel_id = payload.get("channel_id")
            message_id = payload.get("message_id")

            if not channel_id or not message_id:
                return IntegrationResult(
                    success=False,
                    error="channel_id and message_id are required",
                )

            # L'API Discord pour supprimer un message utilise DELETE
            # Mais elle ne retourne pas de corps, juste un 204
            self._make_request(
                "DELETE",
                f"channels/{channel_id}/messages/{message_id}",
            )

            return IntegrationResult(
                success=True,
                data={
                    "deleted": True,
                    "channel_id": channel_id,
                    "message_id": message_id,
                },
            )

        except Exception as e:
            logger.error(f"Failed to delete Discord message: {e}")
            return IntegrationResult(
                success=False,
                error=str(e),
            )

    def _list_channels(self, payload: Dict[str, Any]) -> IntegrationResult:
        """Liste les salons (canaux) disponibles."""
        try:
            guild_id = payload.get("guild_id")
            limit = payload.get("limit", 100)

            if not guild_id:
                return IntegrationResult(
                    success=False,
                    error="guild_id is required",
                )

            params = {"limit": limit}

            result = self._make_request(
                "GET", f"guilds/{guild_id}/channels", params=params
            )

            channels = result if isinstance(result, list) else []

            return IntegrationResult(
                success=True,
                data={
                    "channels": channels,
                    "count": len(channels),
                },
            )

        except Exception as e:
            logger.error(f"Failed to list Discord channels: {e}")
            return IntegrationResult(
                success=False,
                error=str(e),
            )

    def _get_channel_info(self, payload: Dict[str, Any]) -> IntegrationResult:
        """Obtient les informations d'un salon."""
        try:
            channel_id = payload.get("channel_id")

            if not channel_id:
                return IntegrationResult(
                    success=False,
                    error="channel_id is required",
                )

            result = self._make_request(
                "GET",
                f"channels/{channel_id}",
            )

            return IntegrationResult(
                success=True,
                data={"channel": result},
            )

        except Exception as e:
            logger.error(f"Failed to get channel info: {e}")
            return IntegrationResult(
                success=False,
                error=str(e),
            )

    def _create_channel(self, payload: Dict[str, Any]) -> IntegrationResult:
        """Crée un nouveau salon (canal textuel)."""
        try:
            guild_id = payload.get("guild_id")
            name = payload.get("name")
            channel_type = payload.get("type", 0)  # 0 = text, 2 = voice, 4 = category
            topic = payload.get("topic", "")
            nsfw = payload.get("nsfw", False)
            parent_id = payload.get("parent_id")  # Pour les salons dans une catégorie

            if not guild_id or not name:
                return IntegrationResult(
                    success=False,
                    error="guild_id and name are required",
                )

            channel_data = {
                "name": name,
                "type": channel_type,
            }

            if topic:
                channel_data["topic"] = topic
            if nsfw:
                channel_data["nsfw"] = nsfw
            if parent_id:
                channel_data["parent_id"] = parent_id

            result = self._make_request(
                "POST", f"guilds/{guild_id}/channels", json=channel_data
            )

            return IntegrationResult(
                success=True,
                data={"channel": result},
            )

        except Exception as e:
            logger.error(f"Failed to create Discord channel: {e}")
            return IntegrationResult(
                success=False,
                error=str(e),
            )

    def _list_guilds(self, payload: Dict[str, Any]) -> IntegrationResult:
        """Liste les serveurs (guilds) accessibles."""
        try:
            limit = payload.get("limit", 100)
            before = payload.get("before")  # ID de la guilde avant laquelle commencer
            after = payload.get("after")  # ID de la guilde après laquelle commencer

            params = {"limit": limit}
            if before:
                params["before"] = before
            if after:
                params["after"] = after

            result = self._make_request("GET", "users/@me/guilds", params=params)

            guilds = result if isinstance(result, list) else []

            return IntegrationResult(
                success=True,
                data={
                    "guilds": guilds,
                    "count": len(guilds),
                },
            )

        except Exception as e:
            logger.error(f"Failed to list Discord guilds: {e}")
            return IntegrationResult(
                success=False,
                error=str(e),
            )

    def _get_guild_info(self, payload: Dict[str, Any]) -> IntegrationResult:
        """Obtient les informations d'un serveur (guilde)."""
        try:
            guild_id = payload.get("guild_id")
            with_counts = payload.get(
                "with_counts", True
            )  # Inclure les comptes de membres

            if not guild_id:
                return IntegrationResult(
                    success=False,
                    error="guild_id is required",
                )

            params = {"with_counts": str(with_counts).lower()}

            result = self._make_request("GET", f"guilds/{guild_id}", params=params)

            return IntegrationResult(
                success=True,
                data={"guild": result},
            )

        except Exception as e:
            logger.error(f"Failed to get guild info: {e}")
            return IntegrationResult(
                success=False,
                error=str(e),
            )

    def _get_user_info(self, payload: Dict[str, Any]) -> IntegrationResult:
        """Obtient les informations d'un utilisateur."""
        try:
            user_id = payload.get("user_id")

            if not user_id:
                return IntegrationResult(
                    success=False,
                    error="user_id is required",
                )

            result = self._make_request(
                "GET",
                f"users/{user_id}",
            )

            return IntegrationResult(
                success=True,
                data={"user": result},
            )

        except Exception as e:
            logger.error(f"Failed to get user info: {e}")
            return IntegrationResult(
                success=False,
                error=str(e),
            )

    def _list_guild_members(self, payload: Dict[str, Any]) -> IntegrationResult:
        """Liste les membres d'un serveur."""
        try:
            guild_id = payload.get("guild_id")
            limit = payload.get("limit", 100)
            after = payload.get("after")  # ID de l'utilisateur après lequel commencer

            if not guild_id:
                return IntegrationResult(
                    success=False,
                    error="guild_id is required",
                )

            params = {"limit": limit}
            if after:
                params["after"] = after

            result = self._make_request(
                "GET", f"guilds/{guild_id}/members", params=params
            )

            members = result if isinstance(result, list) else []

            return IntegrationResult(
                success=True,
                data={
                    "members": members,
                    "count": len(members),
                },
            )

        except Exception as e:
            logger.error(f"Failed to list guild members: {e}")
            return IntegrationResult(
                success=False,
                error=str(e),
            )

    def _get_member_info(self, payload: Dict[str, Any]) -> IntegrationResult:
        """Obtient les informations d'un membre dans un serveur."""
        try:
            guild_id = payload.get("guild_id")
            user_id = payload.get("user_id")

            if not guild_id or not user_id:
                return IntegrationResult(
                    success=False,
                    error="guild_id and user_id are required",
                )

            result = self._make_request(
                "GET",
                f"guilds/{guild_id}/members/{user_id}",
            )

            return IntegrationResult(
                success=True,
                data={"member": result},
            )

        except Exception as e:
            logger.error(f"Failed to get member info: {e}")
            return IntegrationResult(
                success=False,
                error=str(e),
            )

    def _list_roles(self, payload: Dict[str, Any]) -> IntegrationResult:
        """Liste les rôles d'un serveur."""
        try:
            guild_id = payload.get("guild_id")

            if not guild_id:
                return IntegrationResult(
                    success=False,
                    error="guild_id is required",
                )

            result = self._make_request(
                "GET",
                f"guilds/{guild_id}/roles",
            )

            roles = result if isinstance(result, list) else []

            return IntegrationResult(
                success=True,
                data={
                    "roles": roles,
                    "count": len(roles),
                },
            )

        except Exception as e:
            logger.error(f"Failed to list roles: {e}")
            return IntegrationResult(
                success=False,
                error=str(e),
            )

    def _create_role(self, payload: Dict[str, Any]) -> IntegrationResult:
        """Crée un nouveau rôle."""
        try:
            guild_id = payload.get("guild_id")
            name = payload.get("name")
            permissions = payload.get("permissions", 0)
            color = payload.get("color")
            hoist = payload.get("hoist", False)
            mentionable = payload.get("mentionable", False)

            if not guild_id or not name:
                return IntegrationResult(
                    success=False,
                    error="guild_id and name are required",
                )

            role_data = {
                "name": name,
                "permissions": permissions,
            }

            if color is not None:
                role_data["color"] = color
            if hoist:
                role_data["hoist"] = hoist
            if mentionable:
                role_data["mentionable"] = mentionable

            result = self._make_request(
                "POST", f"guilds/{guild_id}/roles", json=role_data
            )

            return IntegrationResult(
                success=True,
                data={"role": result},
            )

        except Exception as e:
            logger.error(f"Failed to create role: {e}")
            return IntegrationResult(
                success=False,
                error=str(e),
            )

    def _add_role_to_member(self, payload: Dict[str, Any]) -> IntegrationResult:
        """Ajoute un rôle à un membre."""
        try:
            guild_id = payload.get("guild_id")
            user_id = payload.get("user_id")
            role_id = payload.get("role_id")

            if not guild_id or not user_id or not role_id:
                return IntegrationResult(
                    success=False,
                    error="guild_id, user_id, and role_id are required",
                )

            result = self._make_request(
                "PUT",
                f"guilds/{guild_id}/members/{user_id}/roles/{role_id}",
            )

            return IntegrationResult(
                success=True,
                data={"result": result},
            )

        except Exception as e:
            logger.error(f"Failed to add role to member: {e}")
            return IntegrationResult(
                success=False,
                error=str(e),
            )

    def _remove_role_from_member(self, payload: Dict[str, Any]) -> IntegrationResult:
        """Supprime un rôle d'un membre."""
        try:
            guild_id = payload.get("guild_id")
            user_id = payload.get("user_id")
            role_id = payload.get("role_id")

            if not guild_id or not user_id or not role_id:
                return IntegrationResult(
                    success=False,
                    error="guild_id, user_id, and role_id are required",
                )

            result = self._make_request(
                "DELETE",
                f"guilds/{guild_id}/members/{user_id}/roles/{role_id}",
            )

            return IntegrationResult(
                success=True,
                data={"result": result},
            )

        except Exception as e:
            logger.error(f"Failed to remove role from member: {e}")
            return IntegrationResult(
                success=False,
                error=str(e),
            )

    def _add_reaction(self, payload: Dict[str, Any]) -> IntegrationResult:
        """Ajoute une réaction à un message."""
        try:
            channel_id = payload.get("channel_id")
            message_id = payload.get("message_id")
            emoji = payload.get(
                "emoji"
            )  # Peut être un emoji Unicode ou un emoji personnalisé (format: name:id)

            if not channel_id or not message_id or not emoji:
                return IntegrationResult(
                    success=False,
                    error="channel_id, message_id, and emoji are required",
                )

            # Pour les emojis personnalisés, le format est "nom:id"
            # Pour les emojis Unicode, c'est juste le caractère
            emoji_encoded = emoji
            if ":" in emoji and emoji.count(":") >= 2:
                # C'est probablement un emoji personnalisé
                emoji_encoded = emoji

            # L'API Discord attend l'emoji URL-encoded
            result = self._make_request(
                "PUT",
                f"channels/{channel_id}/messages/{message_id}/reactions/"
                f"{emoji_encoded}/@me",
            )

            return IntegrationResult(
                success=True,
                data={"result": result},
            )

        except Exception as e:
            logger.error(f"Failed to add reaction: {e}")
            return IntegrationResult(
                success=False,
                error=str(e),
            )

    def _remove_reaction(self, payload: Dict[str, Any]) -> IntegrationResult:
        """Supprime une réaction d'un message."""
        try:
            channel_id = payload.get("channel_id")
            message_id = payload.get("message_id")
            emoji = payload.get("emoji")
            user_id = payload.get("user_id")  # Optionnel, par défaut @me

            if not channel_id or not message_id or not emoji:
                return IntegrationResult(
                    success=False,
                    error="channel_id, message_id, and emoji are required",
                )

            user_target = user_id or "@me"

            result = self._make_request(
                "DELETE",
                f"channels/{channel_id}/messages/{message_id}/reactions/"
                f"{emoji}/{user_target}",
            )

            return IntegrationResult(
                success=True,
                data={"result": result},
            )

        except Exception as e:
            logger.error(f"Failed to remove reaction: {e}")
            return IntegrationResult(
                success=False,
                error=str(e),
            )

    def _create_slash_command(self, payload: Dict[str, Any]) -> IntegrationResult:
        """Crée une commande slash personnalisée."""
        try:
            application_id = payload.get(
                "application_id"
            )  # ID de l'application Discord
            name = payload.get("name")
            description = payload.get("description")
            options = payload.get("options", [])
            default_permission = payload.get("default_permission", True)

            if not application_id or not name or not description:
                return IntegrationResult(
                    success=False,
                    error="application_id, name, and description are required",
                )

            command_data = {
                "name": name,
                "description": description,
                "default_permission": default_permission,
            }

            if options:
                command_data["options"] = options

            # L'API des commandes slash utilise une URL différente
            slack_url = (
                f"https://discord.com/api/v{self.api_version}/applications/"
                f"{application_id}/commands"
            )

            headers = self._get_auth_headers()

            response = requests.post(
                slack_url,
                headers=headers,
                json=command_data,
                timeout=30,
            )

            if response.status_code >= 400:
                error_data = response.json() if response.text else {}
                error_msg = error_data.get("message", "Unknown error")
                return IntegrationResult(
                    success=False,
                    error=f"Failed to create slash command: {error_msg}",
                )

            result = response.json()

            return IntegrationResult(
                success=True,
                data={"command": result},
            )

        except Exception as e:
            logger.error(f"Failed to create slash command: {e}")
            return IntegrationResult(
                success=False,
                error=str(e),
            )

    def _list_slash_commands(self, payload: Dict[str, Any]) -> IntegrationResult:
        """Liste les commandes slash de l'application."""
        try:
            application_id = payload.get("application_id")

            if not application_id:
                return IntegrationResult(
                    success=False,
                    error="application_id is required",
                )

            slack_url = (
                f"https://discord.com/api/v{self.api_version}/applications/"
                f"{application_id}/commands"
            )

            headers = self._get_auth_headers()

            response = requests.get(
                slack_url,
                headers=headers,
                timeout=30,
            )

            if response.status_code >= 400:
                error_data = response.json() if response.text else {}
                error_msg = error_data.get("message", "Unknown error")
                return IntegrationResult(
                    success=False,
                    error=f"Failed to list slash commands: {error_msg}",
                )

            result = response.json()
            commands = result if isinstance(result, list) else []

            return IntegrationResult(
                success=True,
                data={
                    "commands": commands,
                    "count": len(commands),
                },
            )

        except Exception as e:
            logger.error(f"Failed to list slash commands: {e}")
            return IntegrationResult(
                success=False,
                error=str(e),
            )

    def _delete_slash_command(self, payload: Dict[str, Any]) -> IntegrationResult:
        """Supprime une commande slash."""
        try:
            application_id = payload.get("application_id")
            command_id = payload.get("command_id")

            if not application_id or not command_id:
                return IntegrationResult(
                    success=False,
                    error="application_id and command_id are required",
                )

            slack_url = (
                f"https://discord.com/api/v{self.api_version}/applications/"
                f"{application_id}/commands/{command_id}"
            )

            headers = self._get_auth_headers()

            response = requests.delete(
                slack_url,
                headers=headers,
                timeout=30,
            )

            if response.status_code >= 400:
                error_data = response.json() if response.text else {}
                error_msg = error_data.get("message", "Unknown error")
                return IntegrationResult(
                    success=False,
                    error=f"Failed to delete slash command: {error_msg}",
                )

            return IntegrationResult(
                success=True,
                data={"deleted": True},
            )

        except Exception as e:
            logger.error(f"Failed to delete slash command: {e}")
            return IntegrationResult(
                success=False,
                error=str(e),
            )

    def _create_webhook(self, payload: Dict[str, Any]) -> IntegrationResult:
        """Crée un webhook dans un salon."""
        try:
            channel_id = payload.get("channel_id")
            name = payload.get("name")
            avatar = payload.get("avatar")  # URL de l'avatar

            if not channel_id or not name:
                return IntegrationResult(
                    success=False,
                    error="channel_id and name are required",
                )

            webhook_data = {
                "name": name,
            }

            if avatar:
                webhook_data["avatar"] = avatar

            result = self._make_request(
                "POST", f"channels/{channel_id}/webhooks", json=webhook_data
            )

            return IntegrationResult(
                success=True,
                data={"webhook": result},
            )

        except Exception as e:
            logger.error(f"Failed to create Discord webhook: {e}")
            return IntegrationResult(
                success=False,
                error=str(e),
            )

    def _list_webhooks(self, payload: Dict[str, Any]) -> IntegrationResult:
        """Liste les webhooks d'un serveur."""
        try:
            guild_id = payload.get("guild_id")

            if not guild_id:
                return IntegrationResult(
                    success=False,
                    error="guild_id is required",
                )

            result = self._make_request(
                "GET",
                f"guilds/{guild_id}/webhooks",
            )

            webhooks = result if isinstance(result, list) else []

            return IntegrationResult(
                success=True,
                data={
                    "webhooks": webhooks,
                    "count": len(webhooks),
                },
            )

        except Exception as e:
            logger.error(f"Failed to list Discord webhooks: {e}")
            return IntegrationResult(
                success=False,
                error=str(e),
            )

    def _execute_webhook(self, payload: Dict[str, Any]) -> IntegrationResult:
        """Exécute un webhook."""
        try:
            webhook_url = payload.get("webhook_url")
            content = payload.get("content")
            embeds = payload.get("embeds")
            username = payload.get("username")
            avatar_url = payload.get("avatar_url")

            if not webhook_url:
                return IntegrationResult(
                    success=False,
                    error="webhook_url is required",
                )

            webhook_data = {}
            if content:
                webhook_data["content"] = content
            if embeds:
                webhook_data["embeds"] = embeds
            if username:
                webhook_data["username"] = username
            if avatar_url:
                webhook_data["avatar_url"] = avatar_url

            # Les webhooks Discord ne nécessitent pas d'authentification
            # Ils utilisent un token dans l'URL
            headers = {
                "Content-Type": "application/json",
                "User-Agent": "AgentWorld/0.5.0",
            }

            response = requests.post(
                webhook_url,
                json=webhook_data,
                headers=headers,
                timeout=30,
            )

            if response.status_code >= 400:
                error_msg = f"Webhook execution failed: {response.status_code}"
                try:
                    error_msg += f" - {response.json()}"
                except Exception:
                    error_msg += f" - {response.text}"
                return IntegrationResult(
                    success=False,
                    error=error_msg,
                )

            return IntegrationResult(
                success=True,
                data={
                    "webhook": "executed",
                    "status_code": response.status_code,
                },
            )

        except Exception as e:
            logger.error(f"Failed to execute Discord webhook: {e}")
            return IntegrationResult(
                success=False,
                error=str(e),
            )

    def get_oauth_scopes(self) -> List[str]:
        """Retourne les scopes OAuth2 requis pour Discord."""
        return [
            "identify",  # Informations basiques de l'utilisateur
            "email",  # Email de l'utilisateur
            "connections",  # Connexions de l'utilisateur à d'autres plateformes
            "guilds",  # Liste des serveurs dont l'utilisateur fait partie
            "guilds.join",  # Permet au bot de rejoindre des serveurs
            "messages.read",  # Lire les messages
            "applications.commands",  # Gérer les commandes slash
            "bot",  # Permet d'utiliser le bot dans les serveurs
        ]

    def get_configuration_schema(self) -> Dict[str, Any]:
        """Retourne le schéma de configuration pour Discord."""
        return {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Nom de l'intégration Discord",
                    "default": "My Discord Integration",
                },
                "description": {
                    "type": "string",
                    "description": "Description de l'intégration",
                    "default": "",
                },
                "settings": {
                    "type": "object",
                    "description": "Paramètres spécifiques Discord",
                    "properties": {
                        "default_channel_id": {
                            "type": "string",
                            "description": (
                                "ID du salon par défaut pour les notifications"
                            ),
                            "default": "",
                        },
                        "command_prefix": {
                            "type": "string",
                            "description": "Préfixe pour les commandes (ex: !)",
                            "default": "!",
                        },
                        "enable_mentions": {
                            "type": "boolean",
                            "description": "Activer les mentions @everyone et @here",
                            "default": False,
                        },
                        "embed_color": {
                            "type": "string",
                            "description": (
                                "Couleur par défaut des embeds (hexadecimal)"
                            ),
                            "default": "#5865F2",
                        },
                        "application_id": {
                            "type": "string",
                            "description": (
                                "ID de l'application Discord pour les commandes slash"
                            ),
                            "default": "",
                        },
                    },
                },
            },
            "required": ["name"],
        }
