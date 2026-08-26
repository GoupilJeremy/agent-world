# 💬 Agent World - Slack Integration Adapter
# Version: 0.5.0 (Épic 7 - US-048)
# Description: Adapter pour l'intégration avec Slack

"""
Slack Integration Adapter for Agent World.

Ce module implémente l'adapter pour l'intégration avec Slack.
Il permet aux agents d'envoyer des messages, de créer des canaux,
de gérer des notifications et d'interagir avec les utilisateurs Slack.

Requirements:
    - requests: Pour les requêtes HTTP
    - requests-oauthlib: Pour OAuth2 (optionnel)
"""

import json
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
from . import register_adapter


@register_adapter
class SlackIntegrationAdapter(BaseIntegrationAdapter):
    """
    Adapter pour l'intégration avec Slack.
    
    Cet adapter permet aux agents d'effectuer les actions suivantes :
    - Envoyer un message à un canal ou un utilisateur
    - Créer un canal
    - Lister les canaux
    - Obtenir des informations sur un utilisateur
    - Réagir à un message
    - Gérer les notifications
    - Exécuter des commandes slash
    
    Authentication:
        - OAuth2 (recommandé)
        - Bot Token
        - Webhook URL (pour les incoming webhooks)
    """
    
    # Configuration de l'adapter
    type = IntegrationType.SLACK
    name = "Slack"
    description = "Intégration avec Slack pour envoyer des messages, notifications et interagir avec les équipes"
    auth_type = AuthType.OAUTH2
    icon = "slack"
    color = "#4A154B"
    
    # Actions supportées
    supported_actions = [
        # Messages
        "send_message",
        "send_ephemeral_message",
        "update_message",
        "delete_message",
        
        # Canaux
        "list_channels",
        "get_channel_info",
        "create_channel",
        "join_channel",
        "leave_channel",
        
        # Utilisateurs
        "get_user_info",
        "list_users",
        "get_user_profile",
        
        # Réactions
        "add_reaction",
        "remove_reaction",
        
        # Notifications
        "send_notification",
        "create_reminder",
        
        # Fichiers
        "upload_file",
        "share_file",
        
        # Conversations
        "open_conversation",
        "close_conversation",
    ]
    
    # Configuration OAuth2 par défaut pour Slack
    OAUTH_CONFIG = OAuthConfig(
        client_id="",  # À configurer
        client_secret="",  # À configurer
        redirect_uri="http://localhost:5000/api/integrations/slack/callback",
        authorization_url="https://slack.com/oauth/v2/authorize",
        token_url="https://slack.com/api/oauth.v2.access",
        userinfo_url="https://slack.com/api/auth.test",
        scope=[
            "chat:write",
            "chat:write.public",
            "channels:read",
            "channels:join",
            "groups:read",
            "im:read",
            "im:write",
            "mpim:read",
            "mpim:write",
            "users:read",
            "users:read.email",
            "files:write",
            "reactions:write",
            "reminders:write",
        ],
    )
    
    def __init__(self, config: Optional[IntegrationConfig] = None):
        """Initialise l'adapter Slack."""
        # Si une config OAuth globale est fournie, l'utiliser
        if config and config.oauth_config:
            self.oauth_config = config.oauth_config
        else:
            self.oauth_config = self.OAUTH_CONFIG
        
        super().__init__(config)
        self.session = requests.Session()
        
        # Ajouter les headers par défaut
        self.session.headers.update({
            "Content-Type": "application/json; charset=utf-8",
            "User-Agent": "AgentWorld/0.5.0",
        })
    
    def _get_auth_headers(self) -> Dict[str, str]:
        """
        Obtient les headers d'authentification.
        
        Returns:
            Dictionnaire des headers
        """
        if not self.config or not self.config.credentials:
            raise AuthenticationError(
                "No credentials configured",
                self.type
            )
        
        credentials = self.config.credentials
        
        # Slack utilise un Bearer token
        if credentials.access_token:
            return {"Authorization": f"Bearer {credentials.access_token}"}
        elif credentials.api_key:
            # Pour les Bot Tokens (xoxb-...)
            if credentials.api_key.startswith("xoxb-"):
                return {"Authorization": f"Bearer {credentials.api_key}"}
            # Pour les User Tokens (xoxp-...)
            elif credentials.api_key.startswith("xoxp-"):
                return {"Authorization": f"Bearer {credentials.api_key}"}
        
        raise AuthenticationError(
            "No valid Slack token found",
            self.type
        )
    
    def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        **kwargs
    ) -> Any:
        """
        Effectue une requête à l'API Slack avec gestion des erreurs.
        
        Args:
            method: Méthode HTTP (GET, POST, etc.)
            endpoint: Endpoint de l'API Slack (sans l'URL de base)
            **kwargs: Arguments supplémentaires pour requests
            
        Returns:
            Réponse JSON ou None
            
        Raises:
            ConnectionError: En cas d'erreur de connexion
        """
        url = f"https://slack.com/api/{endpoint}"
        headers = self._get_auth_headers()
        headers.update(kwargs.pop("headers", {}))
        
        try:
            response = self.session.request(
                method,
                url,
                headers=headers,
                timeout=30,
                **kwargs
            )
            
            # Gérer les erreurs HTTP
            if response.status_code >= 400:
                error_data = {"status_code": response.status_code}
                try:
                    response_json = response.json()
                    error_data["response"] = response_json
                    # Slack retourne un champ 'ok' et 'error'
                    if not response_json.get("ok"):
                        error_data["slack_error"] = response_json.get("error", "Unknown error")
                except Exception:
                    error_data["response"] = response.text
                
                logger.error(f"Slack API error: {error_data}")
                
                if response.status_code == 401:
                    raise AuthenticationError("Invalid or expired Slack token", self.type)
                elif response.status_code == 429:
                    raise ConnectionError("Slack API rate limit exceeded", self.type)
                else:
                    error_msg = response_json.get("error", response.text) if response_json else response.text
                    raise ConnectionError(
                        f"Slack API error: {error_msg}",
                        self.type
                    )
            
            # Retourner la réponse JSON
            try:
                result = response.json()
                # Vérifier si Slack a retourné une erreur
                if isinstance(result, dict) and not result.get("ok"):
                    error_msg = result.get("error", "Unknown Slack error")
                    logger.error(f"Slack API returned error: {error_msg}")
                    # Lancer une exception avec le message d'erreur de Slack
                    raise ConnectionError(f"Slack error: {error_msg}", self.type)
                return result
            except ValueError:
                return response.text
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Slack request failed: {e}")
            raise ConnectionError(str(e), self.type)
    
    def authenticate(
        self, 
        credentials: IntegrationCredentials
    ) -> bool:
        """
        Authentifie l'intégration avec Slack.
        
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
            logger.error(f"Slack authentication failed: {e}")
            return False
    
    def get_authentication_url(
        self, 
        state: Optional[str] = None
    ) -> str:
        """
        Génère l'URL d'authentification OAuth2 pour Slack.
        
        Args:
            state: Valeur state pour la sécurité CSRF (générée si non fournie)
            
        Returns:
            URL d'authentification OAuth2
        """
        if not state:
            state = secrets.token_urlsafe(16)
        
        # Slack utilise user_scope au lieu de scope
        params = {
            "client_id": self.oauth_config.client_id,
            "redirect_uri": self.oauth_config.redirect_uri,
            "user_scope": ",".join(self.oauth_config.scope),
            "state": state,
        }
        
        return f"{self.oauth_config.authorization_url}?{urlencode(params)}"
    
    def exchange_code_for_token(
        self, 
        code: str
    ) -> IntegrationCredentials:
        """
        Échange un code d'autorisation OAuth2 contre un token Slack.
        
        Args:
            code: Code d'autorisation reçu de Slack
            
        Returns:
            IntegrationCredentials avec le token d'accès
            
        Raises:
            ValueError: Si l'échange échoue
        """
        try:
            data = {
                "client_id": self.oauth_config.client_id,
                "client_secret": self.oauth_config.client_secret,
                "code": code,
                "redirect_uri": self.oauth_config.redirect_uri,
            }
            
            headers = {
                "Accept": "application/json",
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
                    error_msg += f" - {response.json()}"
                except Exception:
                    error_msg += f" - {response.text}"
                raise ValueError(error_msg)
            
            token_data = response.json()
            
            if not token_data.get("ok"):
                error_msg = token_data.get("error", "Unknown error")
                raise ValueError(f"Slack OAuth failed: {error_msg}")
            
            access_token = token_data.get("authed_user", {}).get("access_token") or \
                         token_data.get("access_token")
            refresh_token = token_data.get("refresh_token")
            expires_in = token_data.get("expires_in", 3600)
            
            # Slack retourne aussi un bot_token
            bot_token = token_data.get("access_token")  # Le bot token est dans access_token
            
            if not access_token and not bot_token:
                raise ValueError("No access token received from Slack")
            
            # Utiliser le bot token si disponible
            token_to_use = bot_token or access_token
            
            # Calculer l'expiration (Slack tokens n'expirent pas toujours, mais on utilise expires_in si fourni)
            token_expiry = None
            if expires_in:
                token_expiry = datetime.utcnow() + timedelta(seconds=expires_in)
            
            return IntegrationCredentials(
                access_token=token_to_use,
                refresh_token=refresh_token,
                token_expiry=token_expiry,
            )
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Slack token exchange failed: {e}")
            raise ValueError(f"Slack token exchange failed: {e}")
    
    def refresh_token(
        self, 
        refresh_token: str
    ) -> IntegrationCredentials:
        """
        Rafraîchit le token d'accès avec un refresh token.
        
        Note: Slack utilise des refresh tokens pour le flux OAuth2.
        
        Args:
            refresh_token: Refresh token à utiliser
            
        Returns:
            IntegrationCredentials avec les nouveaux tokens
            
        Raises:
            NotImplementedError: Si Slack ne supporte pas le refresh pour ce type de token
            ValueError: Si le rafraîchissement échoue
        """
        try:
            data = {
                "client_id": self.oauth_config.client_id,
                "client_secret": self.oauth_config.client_secret,
                "refresh_token": refresh_token,
                "grant_type": "refresh_token",
            }
            
            headers = {
                "Accept": "application/json",
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
                    error_msg += f" - {response.json()}"
                except Exception:
                    error_msg += f" - {response.text}"
                raise ValueError(error_msg)
            
            token_data = response.json()
            
            if not token_data.get("ok"):
                error_msg = token_data.get("error", "Unknown error")
                raise ValueError(f"Slack token refresh failed: {error_msg}")
            
            access_token = token_data.get("access_token")
            new_refresh_token = token_data.get("refresh_token", refresh_token)  # Garder l'ancien si non fourni
            expires_in = token_data.get("expires_in", 3600)
            
            if not access_token:
                raise ValueError("No new access token received from Slack")
            
            # Calculer l'expiration
            token_expiry = datetime.utcnow() + timedelta(seconds=expires_in)
            
            return IntegrationCredentials(
                access_token=access_token,
                refresh_token=new_refresh_token,
                token_expiry=token_expiry,
            )
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Slack token refresh failed: {e}")
            raise ValueError(f"Slack token refresh failed: {e}")
    
    def test_connection(self) -> IntegrationResult:
        """
        Teste la connexion à Slack.
        
        Returns:
            IntegrationResult avec le résultat du test
        """
        try:
            # Appeler l'API auth.test pour vérifier l'authentification
            result = self._make_request("GET", "auth.test")
            
            if result and isinstance(result, dict) and result.get("ok"):
                user_id = result.get("user_id")
                team_id = result.get("team_id")
                
                return IntegrationResult(
                    success=True,
                    data={
                        "user_id": user_id,
                        "team_id": team_id,
                        "message": "Successfully connected to Slack",
                    },
                )
            else:
                return IntegrationResult(
                    success=False,
                    error="Invalid response from Slack",
                )
        except Exception as e:
            logger.error(f"Slack connection test failed: {e}")
            return IntegrationResult(
                success=False,
                error=str(e),
            )
    
    def execute(
        self, 
        action: IntegrationAction
    ) -> IntegrationResult:
        """
        Exécute une action Slack.
        
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
        """Envoye un message à un canal ou un utilisateur."""
        try:
            channel = payload.get("channel")
            text = payload.get("text")
            blocks = payload.get("blocks")
            attachments = payload.get("attachments")
            thread_ts = payload.get("thread_ts")
            reply_broadcast = payload.get("reply_broadcast", False)
            
            if not channel or not text:
                return IntegrationResult(
                    success=False,
                    error="channel and text are required",
                )
            
            message_data = {
                "channel": channel,
                "text": text,
            }
            
            if blocks:
                message_data["blocks"] = blocks
            if attachments:
                message_data["attachments"] = attachments
            if thread_ts:
                message_data["thread_ts"] = thread_ts
            if reply_broadcast:
                message_data["reply_broadcast"] = reply_broadcast
            
            result = self._make_request("POST", "chat.postMessage", json=message_data)
            
            return IntegrationResult(
                success=True,
                data={
                    "message": result,
                    "channel": channel,
                    "ts": result.get("ts") if result else None,
                },
            )
            
        except Exception as e:
            logger.error(f"Failed to send Slack message: {e}")
            return IntegrationResult(
                success=False,
                error=str(e),
            )
    
    def _send_ephemeral_message(self, payload: Dict[str, Any]) -> IntegrationResult:
        """Envoye un message éphémère (visible seulement par l'utilisateur)."""
        try:
            channel = payload.get("channel")
            text = payload.get("text")
            user = payload.get("user")
            
            if not channel or not text or not user:
                return IntegrationResult(
                    success=False,
                    error="channel, text, and user are required",
                )
            
            message_data = {
                "channel": channel,
                "text": text,
                "user": user,
            }
            
            result = self._make_request("POST", "chat.postEphemeral", json=message_data)
            
            return IntegrationResult(
                success=True,
                data={"message": result},
            )
            
        except Exception as e:
            logger.error(f"Failed to send ephemeral message: {e}")
            return IntegrationResult(
                success=False,
                error=str(e),
            )
    
    def _list_channels(self, payload: Dict[str, Any]) -> IntegrationResult:
        """Liste les canaux disponibles."""
        try:
            cursor = payload.get("cursor")
            limit = payload.get("limit", 100)
            types = payload.get("types", "public_channel,private_channel")
            exclude_archived = payload.get("exclude_archived", True)
            
            params = {
                "limit": limit,
                "types": types,
                "exclude_archived": str(exclude_archived).lower(),
            }
            
            if cursor:
                params["cursor"] = cursor
            
            result = self._make_request("GET", "conversations.list", params=params)
            
            channels = result.get("channels", []) if result else []
            
            return IntegrationResult(
                success=True,
                data={
                    "channels": channels,
                    "count": len(channels),
                    "response_metadata": result.get("response_metadata"),
                },
            )
            
        except Exception as e:
            logger.error(f"Failed to list Slack channels: {e}")
            return IntegrationResult(
                success=False,
                error=str(e),
            )
    
    def _get_channel_info(self, payload: Dict[str, Any]) -> IntegrationResult:
        """Obtient les informations d'un canal."""
        try:
            channel = payload.get("channel")
            
            if not channel:
                return IntegrationResult(
                    success=False,
                    error="channel is required",
                )
            
            result = self._make_request("GET", "conversations.info", params={"channel": channel})
            
            return IntegrationResult(
                success=True,
                data={"channel": result.get("channel") if result else None},
            )
            
        except Exception as e:
            logger.error(f"Failed to get channel info: {e}")
            return IntegrationResult(
                success=False,
                error=str(e),
            )
    
    def _create_channel(self, payload: Dict[str, Any]) -> IntegrationResult:
        """Crée un nouveau canal."""
        try:
            name = payload.get("name")
            is_private = payload.get("is_private", False)
            
            if not name:
                return IntegrationResult(
                    success=False,
                    error="name is required",
                )
            
            channel_data = {
                "name": name,
                "is_private": is_private,
            }
            
            result = self._make_request("POST", "conversations.create", json=channel_data)
            
            return IntegrationResult(
                success=True,
                data={"channel": result.get("channel") if result else None},
            )
            
        except Exception as e:
            logger.error(f"Failed to create channel: {e}")
            return IntegrationResult(
                success=False,
                error=str(e),
            )
    
    def _join_channel(self, payload: Dict[str, Any]) -> IntegrationResult:
        """Rejoint un canal."""
        try:
            channel = payload.get("channel")
            
            if not channel:
                return IntegrationResult(
                    success=False,
                    error="channel is required",
                )
            
            result = self._make_request("POST", "conversations.join", json={"channel": channel})
            
            return IntegrationResult(
                success=True,
                data={"channel": result.get("channel") if result else None},
            )
            
        except Exception as e:
            logger.error(f"Failed to join channel: {e}")
            return IntegrationResult(
                success=False,
                error=str(e),
            )
    
    def _leave_channel(self, payload: Dict[str, Any]) -> IntegrationResult:
        """Quitte un canal."""
        try:
            channel = payload.get("channel")
            
            if not channel:
                return IntegrationResult(
                    success=False,
                    error="channel is required",
                )
            
            result = self._make_request("POST", "conversations.leave", json={"channel": channel})
            
            return IntegrationResult(
                success=True,
                data={"result": result},
            )
            
        except Exception as e:
            logger.error(f"Failed to leave channel: {e}")
            return IntegrationResult(
                success=False,
                error=str(e),
            )
    
    def _get_user_info(self, payload: Dict[str, Any]) -> IntegrationResult:
        """Obtient les informations d'un utilisateur."""
        try:
            user = payload.get("user")
            
            if not user:
                return IntegrationResult(
                    success=False,
                    error="user is required",
                )
            
            result = self._make_request("GET", "users.info", params={"user": user})
            
            return IntegrationResult(
                success=True,
                data={"user": result.get("user") if result else None},
            )
            
        except Exception as e:
            logger.error(f"Failed to get user info: {e}")
            return IntegrationResult(
                success=False,
                error=str(e),
            )
    
    def _list_users(self, payload: Dict[str, Any]) -> IntegrationResult:
        """Liste les utilisateurs."""
        try:
            cursor = payload.get("cursor")
            limit = payload.get("limit", 100)
            
            params = {"limit": limit}
            if cursor:
                params["cursor"] = cursor
            
            result = self._make_request("GET", "users.list", params=params)
            
            users = result.get("members", []) if result else []
            
            return IntegrationResult(
                success=True,
                data={
                    "users": users,
                    "count": len(users),
                    "response_metadata": result.get("response_metadata"),
                },
            )
            
        except Exception as e:
            logger.error(f"Failed to list users: {e}")
            return IntegrationResult(
                success=False,
                error=str(e),
            )
    
    def _add_reaction(self, payload: Dict[str, Any]) -> IntegrationResult:
        """Ajoute une réaction à un message."""
        try:
            channel = payload.get("channel")
            timestamp = payload.get("timestamp")
            name = payload.get("name")
            
            if not all([channel, timestamp, name]):
                return IntegrationResult(
                    success=False,
                    error="channel, timestamp, and name are required",
                )
            
            result = self._make_request(
                "POST", 
                "reactions.add",
                json={"channel": channel, "timestamp": timestamp, "name": name}
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
            channel = payload.get("channel")
            timestamp = payload.get("timestamp")
            name = payload.get("name")
            
            if not all([channel, timestamp, name]):
                return IntegrationResult(
                    success=False,
                    error="channel, timestamp, and name are required",
                )
            
            result = self._make_request(
                "POST", 
                "reactions.remove",
                json={"channel": channel, "timestamp": timestamp, "name": name}
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
    
    def _upload_file(self, payload: Dict[str, Any]) -> IntegrationResult:
        """Télécharge un fichier."""
        try:
            # Pour l'instant, on retourne une erreur car l'upload de fichier
            # nécessite un traitement spécial avec multipart/form-data
            return IntegrationResult(
                success=False,
                error="File upload not yet implemented - requires multipart/form-data",
            )
            
        except Exception as e:
            logger.error(f"Failed to upload file: {e}")
            return IntegrationResult(
                success=False,
                error=str(e),
            )
    
    def _open_conversation(self, payload: Dict[str, Any]) -> IntegrationResult:
        """Ouvre une conversation avec un utilisateur ou un groupe."""
        try:
            users = payload.get("users")  # Liste des IDs utilisateurs
            
            if not users or not isinstance(users, list):
                return IntegrationResult(
                    success=False,
                    error="users (list) is required",
                )
            
            result = self._make_request(
                "POST",
                "conversations.open",
                json={"users": users}
            )
            
            return IntegrationResult(
                success=True,
                data={"conversation": result.get("channel") if result else None},
            )
            
        except Exception as e:
            logger.error(f"Failed to open conversation: {e}")
            return IntegrationResult(
                success=False,
                error=str(e),
            )
    
    def get_oauth_scopes(self) -> List[str]:
        """Retourne les scopes OAuth2 requis pour Slack."""
        return [
            "chat:write",           # Envoyer des messages
            "chat:write.public",   # Envoyer des messages dans les canaux publics
            "channels:read",       # Lister les canaux publics
            "channels:join",       # Rejoindre des canaux publics
            "groups:read",         # Lister les canaux privés
            "im:read",             # Lister les messages directs
            "im:write",            # Envoyer des messages directs
            "mpim:read",           # Lister les conversations multi-utilisateurs
            "mpim:write",          # Envoyer des messages multi-utilisateurs
            "users:read",          # Lire les informations utilisateurs
            "users:read.email",    # Lire les emails des utilisateurs
            "files:write",         # Télécharger des fichiers
            "reactions:write",     # Ajouter des réactions
            "reminders:write",     # Créer des rappels
        ]
    
    def get_configuration_schema(self) -> Dict[str, Any]:
        """Retourne le schéma de configuration pour Slack."""
        return {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Nom de l'intégration Slack",
                    "default": "My Slack Integration",
                },
                "description": {
                    "type": "string",
                    "description": "Description de l'intégration",
                    "default": "",
                },
                "settings": {
                    "type": "object",
                    "description": "Paramètres spécifiques Slack",
                    "properties": {
                        "default_channel": {
                            "type": "string",
                            "description": "Canal par défaut pour les notifications",
                            "default": "",
                        },
                        "notify_on_mention": {
                            "type": "boolean",
                            "description": "Notifier lorsque quelqu'un est mentionné",
                            "default": True,
                        },
                        "use_thread_for_replies": {
                            "type": "boolean",
                            "description": "Utiliser les threads pour les réponses",
                            "default": True,
                        },
                        "auto_unfurl_links": {
                            "type": "boolean",
                            "description": "Développer automatiquement les liens",
                            "default": True,
                        },
                    },
                },
            },
            "required": ["name"],
        }
