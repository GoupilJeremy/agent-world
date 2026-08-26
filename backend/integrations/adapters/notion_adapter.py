# 📝 Agent World - Notion Integration Adapter
# Version: 0.5.0 (Épic 7 - US-050)
# Description: Adapter pour l'intégration avec Notion

"""
Notion Integration Adapter for Agent World.

Ce module implémente l'adapter pour l'intégration avec Notion.
Il permet aux agents de synchroniser des données avec des bases de données Notion,
de créer des pages, de mettre à jour du contenu, etc.

Requirements:
    - requests: Pour les requêtes HTTP
    - notion-client: Bibliothèque officielle Notion (optionnelle)
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
class NotionIntegrationAdapter(BaseIntegrationAdapter):
    """
    Adapter pour l'intégration avec Notion.

    Cet adapter permet aux agents d'effectuer les actions suivantes :
    - Lire une base de données Notion
    - Créer une page dans une base de données
    - Mettre à jour une page existante
    - Rechercher des pages
    - Synchroniser des données bidirectionnellement

    Authentication:
        - OAuth2 (recommandé)
        - Internal Integration Token (recommandé pour les intégrations serveurs)

    Documentation Notion API: https://developers.notion.com/docs
    """

    # Configuration de l'adapter
    type = IntegrationType.NOTION
    name = "Notion"
    description = (
        "Intégration avec Notion pour synchroniser des bases de données "
        "et créer des pages"
    )
    auth_type = AuthType.OAUTH2
    icon = "notion"
    color = "#000000"

    # Actions supportées
    supported_actions = [
        # Bases de données
        "list_databases",
        "get_database",
        "query_database",
        # Pages
        "create_page",
        "get_page",
        "update_page",
        "delete_page",
        # Recherche
        "search",
        # Synchronisation
        "sync_database",
        "sync_page",
        # Blocks
        "get_block_children",
        "append_block_children",
        # Utilisateurs
        "get_current_user",
        "list_users",
    ]

    # Configuration OAuth2 par défaut pour Notion
    OAUTH_CONFIG = OAuthConfig(
        client_id="",  # À configurer
        client_secret="",  # À configurer
        redirect_uri="http://localhost:5000/api/integrations/notion/callback",
        authorization_url="https://api.notion.com/v1/oauth/authorize",
        token_url="https://api.notion.com/v1/oauth/token",
        userinfo_url="https://api.notion.com/v1/users/me",
        scope=[
            "read:user",
            "read:page",
            "write:page",
            "read:database",
            "write:database",
        ],
    )

    # Version de l'API Notion
    NOTION_VERSION = "2022-06-28"

    def __init__(self, config: Optional[IntegrationConfig] = None):
        """Initialise l'adapter Notion."""
        # Si une config OAuth globale est fournie, l'utiliser
        if config and config.oauth_config:
            self.oauth_config = config.oauth_config
        else:
            self.oauth_config = self.OAUTH_CONFIG

        super().__init__(config)
        self.session = requests.Session()

        # Ajouter les headers par défaut pour Notion
        self.session.headers.update(
            {
                "Notion-Version": self.NOTION_VERSION,
                "Content-Type": "application/json",
                "User-Agent": "AgentWorld/0.5.0",
            }
        )

    def _get_auth_headers(self) -> Dict[str, str]:
        """
        Obtient les headers d'authentification pour Notion.

        Notion utilise un Bearer token dans le header Authorization.

        Returns:
            Dictionnaire des headers
        """
        if not self.config or not self.config.credentials:
            raise AuthenticationError("No credentials configured for Notion", self.type)

        credentials = self.config.credentials

        # Notion accepte soit un access_token (OAuth2) soit un api_key
        # (Integration Token)
        if credentials.access_token:
            return {"Authorization": f"Bearer {credentials.access_token}"}
        elif credentials.api_key:
            return {"Authorization": f"Bearer {credentials.api_key}"}
        else:
            raise AuthenticationError(
                "No valid credentials found for Notion", self.type
            )

    def _make_request(self, method: str, url: str, **kwargs) -> Any:
        """
        Effectue une requête HTTP à l'API Notion avec gestion des erreurs.

        Args:
            method: Méthode HTTP (GET, POST, etc.)
            url: URL de la requête
            **kwargs: Arguments supplémentaires pour requests

        Returns:
            Réponse JSON ou None

        Raises:
            ConnectionError: En cas d'erreur de connexion
        """
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
                    error_data["response"] = response.json()
                except Exception:
                    error_data["response"] = response.text

                logger.error(f"Notion API error: {error_data}")

                if response.status_code == 401:
                    raise AuthenticationError(
                        "Invalid or expired Notion token", self.type
                    )
                elif response.status_code == 403:
                    raise ConnectionError("Notion rate limit exceeded", self.type)
                elif response.status_code == 404:
                    raise ConnectionError(
                        f"Notion resource not found: {url}", self.type
                    )
                elif response.status_code == 429:
                    raise ConnectionError("Notion API rate limited", self.type)
                else:
                    raise ConnectionError(
                        f"Notion API error: {response.status_code}", self.type
                    )

            # Retourner la réponse JSON si possible
            try:
                return response.json()
            except ValueError:
                return response.text

        except requests.exceptions.RequestException as e:
            logger.error(f"Notion request failed: {e}")
            raise ConnectionError(str(e), self.type)

    def authenticate(self, credentials: IntegrationCredentials) -> bool:
        """
        Authentifie l'intégration avec Notion.

        Args:
            credentials: Identifiants à utiliser

        Returns:
            True si l'authentification réussit
        """
        try:
            # Sauvegarder les credentials actuels
            old_credentials = self.config.credentials if self.config else None

            # Créer une config temporaire
            temp_config = IntegrationConfig(
                integration_type=self.type,
                credentials=credentials,
            )
            self.config = temp_config

            # Tester la connexion en récupérant l'utilisateur courant
            result = self.test_connection()

            # Restaurer les credentials d'origine
            if old_credentials:
                self.config.credentials = old_credentials

            return result.success

        except Exception as e:
            logger.error(f"Notion authentication failed: {e}")
            return False

    def get_authentication_url(self, state: Optional[str] = None) -> str:
        """
        Génère l'URL d'authentification OAuth2 pour Notion.

        Args:
            state: Valeur state pour la sécurité CSRF (générée si non fournie)

        Returns:
            URL d'authentification OAuth2
        """
        if not state:
            state = secrets.token_urlsafe(16)

        # Notion utilise "owner" comme paramètre pour spécifier le type d'intégration
        params = {
            "client_id": self.oauth_config.client_id,
            "redirect_uri": self.oauth_config.redirect_uri,
            "response_type": "code",
            "owner": "user",  # ou "workspace" pour les intégrations workspace
            "scope": " ".join(self.oauth_config.scope),
            "state": state,
        }

        return f"{self.oauth_config.authorization_url}?{urlencode(params)}"

    def exchange_code_for_token(self, code: str) -> IntegrationCredentials:
        """
        Échange un code d'autorisation OAuth2 contre un token Notion.

        Args:
            code: Code d'autorisation reçu de Notion

        Returns:
            IntegrationCredentials avec le token d'accès

        Raises:
            ValueError: Si l'échange échoue
        """
        try:
            data = {
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": self.oauth_config.redirect_uri,
            }

            # Notion nécessite l'authentification Basic Auth avec
            # client_id:client_secret
            auth = (self.oauth_config.client_id, self.oauth_config.client_secret)

            headers = {
                "Content-Type": "application/json",
            }

            response = requests.post(
                self.oauth_config.token_url,
                json=data,
                headers=headers,
                auth=auth,
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
            access_token = token_data.get("access_token")
            refresh_token = token_data.get("refresh_token")
            expires_in = token_data.get("expires_in", 3600)

            if not access_token:
                raise ValueError("No access token received from Notion")

            # Calculer l'expiration
            token_expiry = datetime.utcnow() + timedelta(seconds=expires_in)

            return IntegrationCredentials(
                access_token=access_token,
                refresh_token=refresh_token,
                token_expiry=token_expiry,
            )

        except requests.exceptions.RequestException as e:
            logger.error(f"Notion token exchange failed: {e}")
            raise ValueError(f"Notion token exchange failed: {e}")

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
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
            }

            # Notion nécessite l'authentification Basic Auth
            auth = (self.oauth_config.client_id, self.oauth_config.client_secret)

            headers = {
                "Content-Type": "application/json",
            }

            response = requests.post(
                self.oauth_config.token_url,
                json=data,
                headers=headers,
                auth=auth,
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
            access_token = token_data.get("access_token")
            new_refresh_token = token_data.get("refresh_token", refresh_token)
            expires_in = token_data.get("expires_in", 3600)

            if not access_token:
                raise ValueError("No access token received from Notion")

            # Calculer l'expiration
            token_expiry = datetime.utcnow() + timedelta(seconds=expires_in)

            return IntegrationCredentials(
                access_token=access_token,
                refresh_token=new_refresh_token,
                token_expiry=token_expiry,
            )

        except requests.exceptions.RequestException as e:
            logger.error(f"Notion token refresh failed: {e}")
            raise ValueError(f"Notion token refresh failed: {e}")

    def test_connection(self) -> IntegrationResult:
        """
        Teste la connexion à Notion.

        Returns:
            IntegrationResult avec le résultat du test
        """
        try:
            # Appeler l'API users/me pour vérifier l'authentification
            user_data = self._make_request("GET", "https://api.notion.com/v1/users/me")

            if (
                user_data
                and isinstance(user_data, dict)
                and user_data.get("object") == "user"
            ):
                return IntegrationResult(
                    success=True,
                    data={
                        "user": {
                            "id": user_data.get("id"),
                            "name": user_data.get("name"),
                            "type": user_data.get("type"),
                        }
                    },
                )
            else:
                return IntegrationResult(
                    success=False,
                    error="Invalid response from Notion users endpoint",
                )
        except Exception as e:
            logger.error(f"Notion connection test failed: {e}")
            return IntegrationResult(
                success=False,
                error=str(e),
            )

    def execute(self, action: IntegrationAction) -> IntegrationResult:
        """
        Exécute une action Notion.

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

    def _get_current_user(self, payload: Dict[str, Any]) -> IntegrationResult:
        """Récupère les informations de l'utilisateur courant."""
        try:
            user_data = self._make_request("GET", "https://api.notion.com/v1/users/me")

            if user_data and user_data.get("object") == "user":
                return IntegrationResult(
                    success=True,
                    data={"user": user_data},
                )
            else:
                return IntegrationResult(
                    success=False,
                    error="Invalid user data received",
                )
        except Exception as e:
            logger.error(f"Failed to get current user: {e}")
            return IntegrationResult(success=False, error=str(e))

    def _list_users(self, payload: Dict[str, Any]) -> IntegrationResult:
        """Liste tous les utilisateurs accessibles."""
        try:
            # Notion ne fournit pas d'endpoint pour lister tous les utilisateurs
            # On retourne une erreur car cette action n'est pas supportée
            return IntegrationResult(
                success=False,
                error="Listing all users is not supported by Notion API",
            )
        except Exception as e:
            return IntegrationResult(success=False, error=str(e))

    def _list_databases(self, payload: Dict[str, Any]) -> IntegrationResult:
        """Liste les bases de données accessibles."""
        try:
            # Utiliser l'endpoint search pour trouver les bases de données
            # Notion ne fournit pas d'endpoint direct pour lister les bases de données
            query = payload.get("query", "")

            search_payload = {
                "filter": {
                    "value": "database",
                    "property": "object",
                },
                "query": query,
            }

            results = self._make_request(
                "POST", "https://api.notion.com/v1/search", json=search_payload
            )

            if results and results.get("results"):
                databases = [
                    r for r in results["results"] if r.get("object") == "database"
                ]
                return IntegrationResult(
                    success=True,
                    data={"databases": databases, "count": len(databases)},
                )
            else:
                return IntegrationResult(
                    success=True,
                    data={"databases": [], "count": 0},
                )
        except Exception as e:
            logger.error(f"Failed to list databases: {e}")
            return IntegrationResult(success=False, error=str(e))

    def _get_database(self, payload: Dict[str, Any]) -> IntegrationResult:
        """Récupère les informations d'une base de données."""
        try:
            database_id = payload.get("database_id")

            if not database_id:
                return IntegrationResult(
                    success=False,
                    error="database_id is required",
                )

            # Notion utilise des IDs au format UUID ou préfixés
            # Si l'ID ne contient pas de tirets, on suppose qu'il est déjà complet
            if "-" not in database_id:
                # C'est probablement un ID court, il faut le formater
                database_id = self._format_notion_id(database_id)

            url = f"https://api.notion.com/v1/databases/{database_id}"
            database_data = self._make_request("GET", url)

            if database_data and database_data.get("object") == "database":
                return IntegrationResult(
                    success=True,
                    data={"database": database_data},
                )
            else:
                return IntegrationResult(
                    success=False,
                    error="Invalid database data received",
                )
        except Exception as e:
            logger.error(f"Failed to get database: {e}")
            return IntegrationResult(success=False, error=str(e))

    def _query_database(self, payload: Dict[str, Any]) -> IntegrationResult:
        """Interroge une base de données Notion."""
        try:
            database_id = payload.get("database_id")

            if not database_id:
                return IntegrationResult(
                    success=False,
                    error="database_id is required",
                )

            # Formater l'ID si nécessaire
            if "-" not in database_id:
                database_id = self._format_notion_id(database_id)

            # Construire la requête de filtrage
            filter_expr = payload.get("filter", {})
            sorts = payload.get("sorts", [])
            start_cursor = payload.get("start_cursor")
            page_size = payload.get("page_size", 100)

            query_payload = {
                "filter": filter_expr,
                "sorts": sorts,
            }

            if start_cursor:
                query_payload["start_cursor"] = start_cursor
            if page_size:
                query_payload["page_size"] = page_size

            url = f"https://api.notion.com/v1/databases/{database_id}/query"
            results = self._make_request("POST", url, json=query_payload)

            if results and results.get("results"):
                return IntegrationResult(
                    success=True,
                    data={
                        "results": results["results"],
                        "has_more": results.get("has_more", False),
                        "next_cursor": results.get("next_cursor"),
                        "count": len(results["results"]),
                    },
                )
            else:
                return IntegrationResult(
                    success=True,
                    data={"results": [], "count": 0},
                )
        except Exception as e:
            logger.error(f"Failed to query database: {e}")
            return IntegrationResult(success=False, error=str(e))

    def _create_page(self, payload: Dict[str, Any]) -> IntegrationResult:
        """Crée une nouvelle page dans une base de données."""
        try:
            database_id = payload.get("database_id")
            properties = payload.get("properties", {})
            children = payload.get("children", [])
            icon = payload.get("icon")
            cover = payload.get("cover")

            if not database_id:
                return IntegrationResult(
                    success=False,
                    error="database_id is required",
                )

            # Formater l'ID si nécessaire
            if "-" not in database_id:
                database_id = self._format_notion_id(database_id)

            page_data = {
                "parent": {"database_id": database_id},
                "properties": properties,
            }

            if children:
                page_data["children"] = children
            if icon:
                page_data["icon"] = icon
            if cover:
                page_data["cover"] = cover

            url = "https://api.notion.com/v1/pages"
            response = self._make_request("POST", url, json=page_data)

            if response and response.get("object") == "page":
                return IntegrationResult(
                    success=True,
                    data={"page": response},
                )
            else:
                return IntegrationResult(
                    success=False,
                    error="Invalid page creation response",
                )
        except Exception as e:
            logger.error(f"Failed to create page: {e}")
            return IntegrationResult(success=False, error=str(e))

    def _get_page(self, payload: Dict[str, Any]) -> IntegrationResult:
        """Récupère les informations d'une page."""
        try:
            page_id = payload.get("page_id")

            if not page_id:
                return IntegrationResult(
                    success=False,
                    error="page_id is required",
                )

            # Formater l'ID si nécessaire
            if "-" not in page_id:
                page_id = self._format_notion_id(page_id)

            url = f"https://api.notion.com/v1/pages/{page_id}"
            page_data = self._make_request("GET", url)

            if page_data and page_data.get("object") == "page":
                return IntegrationResult(
                    success=True,
                    data={"page": page_data},
                )
            else:
                return IntegrationResult(
                    success=False,
                    error="Invalid page data received",
                )
        except Exception as e:
            logger.error(f"Failed to get page: {e}")
            return IntegrationResult(success=False, error=str(e))

    def _update_page(self, payload: Dict[str, Any]) -> IntegrationResult:
        """Met à jour une page existante."""
        try:
            page_id = payload.get("page_id")
            properties = payload.get("properties", {})

            if not page_id:
                return IntegrationResult(
                    success=False,
                    error="page_id is required",
                )

            # Formater l'ID si nécessaire
            if "-" not in page_id:
                page_id = self._format_notion_id(page_id)

            # Notion utilise PATCH pour mettre à jour les propriétés
            url = f"https://api.notion.com/v1/pages/{page_id}"
            update_data = {"properties": properties}

            response = self._make_request("PATCH", url, json=update_data)

            if response and response.get("object") == "page":
                return IntegrationResult(
                    success=True,
                    data={"page": response},
                )
            else:
                return IntegrationResult(
                    success=False,
                    error="Invalid page update response",
                )
        except Exception as e:
            logger.error(f"Failed to update page: {e}")
            return IntegrationResult(success=False, error=str(e))

    def _delete_page(self, payload: Dict[str, Any]) -> IntegrationResult:
        """Supprime une page (larchive en réalité, car Notion ne permet pas
        la suppression définitive)."""
        try:
            page_id = payload.get("page_id")

            if not page_id:
                return IntegrationResult(
                    success=False,
                    error="page_id is required",
                )

            # Formater l'ID si nécessaire
            if "-" not in page_id:
                page_id = self._format_notion_id(page_id)

            # Notion n'a pas d'endpoint DELETE pour les pages
            # On utilise PATCH pour archiver la page
            url = f"https://api.notion.com/v1/pages/{page_id}"
            archive_data = {"archived": True}

            response = self._make_request("PATCH", url, json=archive_data)

            if (
                response
                and response.get("object") == "page"
                and response.get("archived") is True
            ):
                return IntegrationResult(
                    success=True,
                    data={"page": response, "archived": True},
                )
            else:
                return IntegrationResult(
                    success=False,
                    error="Failed to archive page",
                )
        except Exception as e:
            logger.error(f"Failed to delete/archive page: {e}")
            return IntegrationResult(success=False, error=str(e))

    def _search(self, payload: Dict[str, Any]) -> IntegrationResult:
        """Recherche des pages, bases de données ou utilisateurs."""
        try:
            query = payload.get("query", "")
            filter_type = payload.get("filter", None)  # page, database, user, etc.

            search_payload = {"query": query}

            if filter_type:
                search_payload["filter"] = {
                    "value": filter_type,
                    "property": "object",
                }

            url = "https://api.notion.com/v1/search"
            results = self._make_request("POST", url, json=search_payload)

            if results and results.get("results"):
                return IntegrationResult(
                    success=True,
                    data={
                        "results": results["results"],
                        "count": len(results["results"]),
                    },
                )
            else:
                return IntegrationResult(
                    success=True,
                    data={"results": [], "count": 0},
                )
        except Exception as e:
            logger.error(f"Failed to search: {e}")
            return IntegrationResult(success=False, error=str(e))

    def _get_block_children(self, payload: Dict[str, Any]) -> IntegrationResult:
        """Récupère les enfants d'un bloc (page, colonne, etc.)."""
        try:
            block_id = payload.get("block_id")
            start_cursor = payload.get("start_cursor")
            page_size = payload.get("page_size", 100)

            if not block_id:
                return IntegrationResult(
                    success=False,
                    error="block_id is required",
                )

            # Formater l'ID si nécessaire
            if "-" not in block_id:
                block_id = self._format_notion_id(block_id)

            url = f"https://api.notion.com/v1/blocks/{block_id}/children"
            params = {}

            if start_cursor:
                params["start_cursor"] = start_cursor
            if page_size:
                params["page_size"] = page_size

            results = self._make_request("GET", url, params=params)

            if results and results.get("results"):
                return IntegrationResult(
                    success=True,
                    data={
                        "results": results["results"],
                        "has_more": results.get("has_more", False),
                        "next_cursor": results.get("next_cursor"),
                        "count": len(results["results"]),
                    },
                )
            else:
                return IntegrationResult(
                    success=True,
                    data={"results": [], "count": 0},
                )
        except Exception as e:
            logger.error(f"Failed to get block children: {e}")
            return IntegrationResult(success=False, error=str(e))

    def _append_block_children(self, payload: Dict[str, Any]) -> IntegrationResult:
        """Ajoute des enfants à un bloc."""
        try:
            block_id = payload.get("block_id")
            children = payload.get("children", [])
            after = payload.get("after")  # ID du bloc après lequel insérer

            if not block_id:
                return IntegrationResult(
                    success=False,
                    error="block_id is required",
                )

            if not children:
                return IntegrationResult(
                    success=False,
                    error="children are required",
                )

            # Formater l'ID si nécessaire
            if "-" not in block_id:
                block_id = self._format_notion_id(block_id)

            url = f"https://api.notion.com/v1/blocks/{block_id}/children"

            append_data = {"children": children}

            if after:
                # Formater l'ID after si nécessaire
                if "-" not in after:
                    after = self._format_notion_id(after)
                append_data["after"] = after

            results = self._make_request("PATCH", url, json=append_data)

            if results and results.get("results"):
                return IntegrationResult(
                    success=True,
                    data={
                        "results": results["results"],
                        "count": len(results["results"]),
                    },
                )
            else:
                return IntegrationResult(
                    success=False,
                    error="Failed to append block children",
                )
        except Exception as e:
            logger.error(f"Failed to append block children: {e}")
            return IntegrationResult(success=False, error=str(e))

    def _sync_database(self, payload: Dict[str, Any]) -> IntegrationResult:
        """Synchronise les données entre une base de données Notion et Agent World."""
        try:
            database_id = payload.get("database_id")
            agent_data = payload.get("data", [])
            sync_direction = payload.get(
                "direction", "to_notion"
            )  # to_notion, from_notion, bidirectional

            if not database_id:
                return IntegrationResult(
                    success=False,
                    error="database_id is required",
                )

            # Formater l'ID si nécessaire
            if "-" not in database_id:
                database_id = self._format_notion_id(database_id)

            if sync_direction == "from_notion":
                # Lire les données depuis Notion
                query_result = self._query_database({"database_id": database_id})
                if query_result.success:
                    return IntegrationResult(
                        success=True,
                        data={
                            "direction": "from_notion",
                            "notion_data": query_result.data.get("results", []),
                            "count": query_result.data.get("count", 0),
                        },
                    )
                else:
                    return query_result

            elif sync_direction == "to_notion":
                # Écrire les données vers Notion
                created_count = 0
                updated_count = 0
                errors = []

                for item in agent_data:
                    try:
                        # Vérifier si la page existe déjà (simplifié)
                        # Dans une implémentation réelle, on utiliserait une
                        # propriété unique
                        # pour identifier les pages existantes

                        # Pour cet exemple, on crée une nouvelle page
                        create_result = self._create_page(
                            {
                                "database_id": database_id,
                                "properties": item.get("properties", {}),
                                "children": item.get("children", []),
                            }
                        )

                        if create_result.success:
                            created_count += 1
                        else:
                            errors.append(create_result.error)
                    except Exception as e:
                        errors.append(str(e))

                return IntegrationResult(
                    success=len(errors) == 0,
                    data={
                        "direction": "to_notion",
                        "created_count": created_count,
                        "updated_count": updated_count,
                        "errors": errors,
                    },
                    error=", ".join(errors) if errors else None,
                )

            elif sync_direction == "bidirectional":
                # Synchronisation bidirectionnelle (simplifiée)
                # 1. Lire les données depuis Notion
                from_notion = self._query_database({"database_id": database_id})

                if not from_notion.success:
                    return from_notion

                notion_data = from_notion.data.get("results", [])

                # 2. Écrire les données depuis Agent World
                to_notion = self._sync_database(
                    {
                        "database_id": database_id,
                        "data": agent_data,
                        "direction": "to_notion",
                    }
                )

                if not to_notion.success:
                    return to_notion

                return IntegrationResult(
                    success=True,
                    data={
                        "direction": "bidirectional",
                        "from_notion": {
                            "data": notion_data,
                            "count": len(notion_data),
                        },
                        "to_notion": to_notion.data,
                    },
                )

            else:
                return IntegrationResult(
                    success=False,
                    error=f"Invalid sync direction: {sync_direction}",
                )

        except Exception as e:
            logger.error(f"Failed to sync database: {e}")
            return IntegrationResult(success=False, error=str(e))

    def _sync_page(self, payload: Dict[str, Any]) -> IntegrationResult:
        """Synchronise une page Notion avec des données d'agent."""
        try:
            page_id = payload.get("page_id")
            agent_data = payload.get("data", {})

            if not page_id:
                return IntegrationResult(
                    success=False,
                    error="page_id is required",
                )

            # Formater l'ID si nécessaire
            if "-" not in page_id:
                page_id = self._format_notion_id(page_id)

            # Mettre à jour la page avec les données de l'agent
            update_result = self._update_page(
                {
                    "page_id": page_id,
                    "properties": agent_data.get("properties", {}),
                }
            )

            if update_result.success:
                # Optionnellement, récupérer la page mise à jour
                get_page_result = self._get_page({"page_id": page_id})
                if get_page_result.success:
                    return IntegrationResult(
                        success=True,
                        data={
                            "page": get_page_result.data["page"],
                            "synced_properties": list(
                                agent_data.get("properties", {}).keys()
                            ),
                        },
                    )
                else:
                    return get_page_result
            else:
                return update_result

        except Exception as e:
            logger.error(f"Failed to sync page: {e}")
            return IntegrationResult(success=False, error=str(e))

    def _format_notion_id(self, id: str) -> str:
        """
        Formate un ID Notion court en ID complet.

        Les IDs Notion peuvent être fournis sous forme courte (sans tirets)
        ou complète (avec tirets). L'API Notion attend toujours la forme complète.

        Args:
            id: ID Notion à formater

        Returns:
            ID Notion formaté
        """
        if not id:
            return id

        # Si l'ID contient déjà des tirets, on suppose qu'il est complet
        if "-" in id:
            return id

        # Les IDs Notion sont des UUID sans les tirets, ou avec un préfixe
        # Exemple: "123e4567-e89b-12d3-a456-426614174000" ou
        # "123e4567e89b12d3a456426614174000"

        # Si la longueur correspond à un UUID sans tirets (32 caractères)
        if len(id) == 32:
            # Insérer les tirets aux positions appropriées
            return f"{id[:8]}-{id[8:12]}-{id[12:16]}-{id[16:20]}-{id[20:]}"

        # Sinon, retourner l'ID tel quel
        return id

    def get_oauth_scopes(self) -> List[str]:
        """Retourne les scopes OAuth2 requis pour Notion."""
        return [
            "read:user",  # Lire le profil utilisateur
            "read:page",  # Lire le contenu des pages
            "write:page",  # Modifier le contenu des pages
            "read:database",  # Lire les bases de données
            "write:database",  # Modifier les bases de données
            "read:block",  # Lire les blocs
            "write:block",  # Modifier les blocs
            "read:comment",  # Lire les commentaires
            "write:comment",  # Créer des commentaires
        ]

    def get_configuration_schema(self) -> Dict[str, Any]:
        """Retourne le schéma de configuration pour Notion."""
        return {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Nom de l'intégration Notion",
                    "default": "My Notion Integration",
                },
                "description": {
                    "type": "string",
                    "description": "Description de l'intégration",
                    "default": "",
                },
                "settings": {
                    "type": "object",
                    "description": "Paramètres spécifiques Notion",
                    "properties": {
                        "default_database_id": {
                            "type": "string",
                            "description": "ID de la base de données par défaut",
                            "default": "",
                        },
                        "auto_sync": {
                            "type": "boolean",
                            "description": "Synchroniser automatiquement avec Notion",
                            "default": False,
                        },
                        "sync_interval_minutes": {
                            "type": "number",
                            "description": (
                                "Intervalle de synchronisation automatique (en minutes)"
                            ),
                            "default": 60,
                            "minimum": 1,
                        },
                        "map_agent_properties": {
                            "type": "object",
                            "description": (
                                "Mappage des propriétés de l'agent vers Notion"
                            ),
                            "default": {},
                        },
                    },
                },
            },
            "required": ["name"],
        }
