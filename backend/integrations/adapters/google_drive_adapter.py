# 💾 Agent World - Google Drive Integration Adapter
# Version: 0.5.0 (Épic 7 - US-051)
# Description: Adapter pour l'intégration avec Google Drive

"""
Google Drive Integration Adapter for Agent World.

Ce module implémente l'adapter pour l'intégration avec Google Drive.
Il permet aux agents de stocker, récupérer, lister et gérer des fichiers
sur Google Drive.

Requirements:
    - requests: Pour les requêtes HTTP
    - google-auth: Pour l'authentification OAuth2 (optionnelle)
    - google-api-python-client: Client officiel Google (optionnelle)
"""

import base64
import json
import logging
import mimetypes
import secrets
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from urllib.parse import urlencode, urlparse

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
class GoogleDriveIntegrationAdapter(BaseIntegrationAdapter):
    """
    Adapter pour l'intégration avec Google Drive.

    Cet adapter permet aux agents d'effectuer les actions suivantes :
    - Lister les fichiers et dossiers
    - Télécharger des fichiers
    - Upload des fichiers
    - Créer des dossiers
    - Supprimer des fichiers
    - Gérer les permissions
    - Rechercher des fichiers

    Authentication:
        - OAuth2 (recommandé)
        - Service Account (pour les applications serveurs)

    Documentation Google Drive API: https://developers.google.com/drive/api
    """

    # Configuration de l'adapter
    type = IntegrationType.GOOGLE_DRIVE
    name = "Google Drive"
    description = "Intégration avec Google Drive pour stocker et gérer des fichiers"
    auth_type = AuthType.OAUTH2
    icon = "google-drive"
    color = "#4285F4"

    # Actions supportées
    supported_actions = [
        # Fichiers
        "list_files",
        "get_file",
        "upload_file",
        "download_file",
        "delete_file",
        "copy_file",
        "move_file",
        # Dossiers
        "create_folder",
        "list_folders",
        "get_folder",
        # Recherche
        "search_files",
        # Permissions
        "get_permissions",
        "add_permission",
        "remove_permission",
        # Métadonnées
        "get_file_metadata",
        "update_file_metadata",
        # Espace disque
        "get_quota",
    ]

    # Configuration OAuth2 par défaut pour Google Drive
    OAUTH_CONFIG = OAuthConfig(
        client_id="",  # À configurer
        client_secret="",  # À configurer
        redirect_uri="http://localhost:5000/api/integrations/google-drive/callback",
        authorization_url="https://accounts.google.com/o/oauth2/v2/auth",
        token_url="https://oauth2.googleapis.com/token",
        userinfo_url="https://www.googleapis.com/oauth2/v3/userinfo",
        scope=[
            "https://www.googleapis.com/auth/drive",
            "https://www.googleapis.com/auth/drive.file",
            "https://www.googleapis.com/auth/drive.metadata",
            "https://www.googleapis.com/auth/drive.readonly",
        ],
    )

    # Base URL pour l'API Google Drive
    DRIVE_API_BASE = "https://www.googleapis.com/drive/v3"
    UPLOAD_API_BASE = "https://www.googleapis.com/upload/drive/v3"

    def __init__(self, config: Optional[IntegrationConfig] = None):
        """Initialise l'adapter Google Drive."""
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
                "User-Agent": "AgentWorld/0.5.0",
            }
        )

    def _get_auth_headers(self) -> Dict[str, str]:
        """
        Obtient les headers d'authentification pour Google Drive.

        Returns:
            Dictionnaire des headers
        """
        if not self.config or not self.config.credentials:
            raise AuthenticationError(
                "No credentials configured for Google Drive", self.type
            )

        credentials = self.config.credentials

        # Google Drive accepte un Bearer token
        if credentials.access_token:
            return {"Authorization": f"Bearer {credentials.access_token}"}
        elif credentials.api_key:
            return {"Authorization": f"Bearer {credentials.api_key}"}
        else:
            raise AuthenticationError(
                "No valid credentials found for Google Drive", self.type
            )

    def _make_request(self, method: str, url: str, **kwargs) -> Any:
        """
        Effectue une requête HTTP à l'API Google Drive avec gestion des erreurs.

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

                logger.error(f"Google Drive API error: {error_data}")

                if response.status_code == 401:
                    raise AuthenticationError(
                        "Invalid or expired Google token", self.type
                    )
                elif response.status_code == 403:
                    # Vérifier si c'est une erreur de permission ou de quota
                    error_json = error_data.get("response", {})
                    error_reason = (
                        error_json.get("error", {})
                        .get("errors", [{}])[0]
                        .get("reason", "")
                    )

                    if error_reason == "rateLimitExceeded":
                        raise ConnectionError(
                            "Google Drive rate limit exceeded", self.type
                        )
                    elif error_reason == "dailyLimitExceeded":
                        raise ConnectionError(
                            "Google Drive daily quota exceeded", self.type
                        )
                    elif error_reason == "userRateLimitExceeded":
                        raise ConnectionError(
                            "Google Drive user rate limit exceeded", self.type
                        )
                    else:
                        raise ConnectionError(
                            f"Google Drive permission denied: {error_reason}", self.type
                        )
                elif response.status_code == 404:
                    raise ConnectionError(
                        f"Google Drive resource not found: {url}", self.type
                    )
                else:
                    raise ConnectionError(
                        f"Google Drive API error: {response.status_code}", self.type
                    )

            # Retourner la réponse JSON si possible
            try:
                return response.json()
            except ValueError:
                return response.text

        except requests.exceptions.RequestException as e:
            logger.error(f"Google Drive request failed: {e}")
            raise ConnectionError(str(e), self.type)

    def authenticate(self, credentials: IntegrationCredentials) -> bool:
        """
        Authentifie l'intégration avec Google Drive.

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

            # Tester la connexion en récupérant les infos utilisateur
            result = self.test_connection()

            # Restaurer les credentials d'origine
            if old_credentials:
                self.config.credentials = old_credentials

            return result.success

        except Exception as e:
            logger.error(f"Google Drive authentication failed: {e}")
            return False

    def get_authentication_url(self, state: Optional[str] = None) -> str:
        """
        Génère l'URL d'authentification OAuth2 pour Google Drive.

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
            "access_type": "offline",  # Pour obtenir un refresh token
            "prompt": "consent",  # Pour forcer l'autorisation et obtenir un refresh token
            "state": state,
        }

        return f"{self.oauth_config.authorization_url}?{urlencode(params)}"

    def exchange_code_for_token(self, code: str) -> IntegrationCredentials:
        """
        Échange un code d'autorisation OAuth2 contre un token Google.

        Args:
            code: Code d'autorisation reçu de Google

        Returns:
            IntegrationCredentials avec le token d'accès

        Raises:
            ValueError: Si l'échange échoue
        """
        try:
            data = {
                "code": code,
                "client_id": self.oauth_config.client_id,
                "client_secret": self.oauth_config.client_secret,
                "redirect_uri": self.oauth_config.redirect_uri,
                "grant_type": "authorization_code",
            }

            headers = {
                "Content-Type": "application/x-www-form-urlencoded",
            }

            response = requests.post(
                self.oauth_config.token_url,
                data=urlencode(data),
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
            access_token = token_data.get("access_token")
            refresh_token = token_data.get("refresh_token")
            expires_in = token_data.get("expires_in", 3600)

            if not access_token:
                raise ValueError("No access token received from Google")

            # Calculer l'expiration
            token_expiry = datetime.utcnow() + timedelta(seconds=expires_in)

            return IntegrationCredentials(
                access_token=access_token,
                refresh_token=refresh_token,
                token_expiry=token_expiry,
            )

        except requests.exceptions.RequestException as e:
            logger.error(f"Google token exchange failed: {e}")
            raise ValueError(f"Google token exchange failed: {e}")

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
                "refresh_token": refresh_token,
                "grant_type": "refresh_token",
            }

            headers = {
                "Content-Type": "application/x-www-form-urlencoded",
            }

            response = requests.post(
                self.oauth_config.token_url,
                data=urlencode(data),
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
            access_token = token_data.get("access_token")
            new_refresh_token = token_data.get("refresh_token", refresh_token)
            expires_in = token_data.get("expires_in", 3600)

            if not access_token:
                raise ValueError("No access token received from Google")

            # Calculer l'expiration
            token_expiry = datetime.utcnow() + timedelta(seconds=expires_in)

            return IntegrationCredentials(
                access_token=access_token,
                refresh_token=new_refresh_token,
                token_expiry=token_expiry,
            )

        except requests.exceptions.RequestException as e:
            logger.error(f"Google token refresh failed: {e}")
            raise ValueError(f"Google token refresh failed: {e}")

    def test_connection(self) -> IntegrationResult:
        """
        Teste la connexion à Google Drive.

        Returns:
            IntegrationResult avec le résultat du test
        """
        try:
            # Appeler l'API userinfo pour vérifier l'authentification
            user_data = self._make_request("GET", self.oauth_config.userinfo_url)

            if user_data and isinstance(user_data, dict) and user_data.get("sub"):
                return IntegrationResult(
                    success=True,
                    data={
                        "user": {
                            "id": user_data.get("sub"),
                            "email": user_data.get("email"),
                            "name": user_data.get("name"),
                            "picture": user_data.get("picture"),
                        }
                    },
                )
            else:
                return IntegrationResult(
                    success=False,
                    error="Invalid response from Google userinfo endpoint",
                )
        except Exception as e:
            logger.error(f"Google Drive connection test failed: {e}")
            return IntegrationResult(
                success=False,
                error=str(e),
            )

    def execute(self, action: IntegrationAction) -> IntegrationResult:
        """
        Exécute une action Google Drive.

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

    def _get_quota(self, payload: Dict[str, Any]) -> IntegrationResult:
        """Récupère les informations sur le quota d'espace disque."""
        try:
            url = f"{self.DRIVE_API_BASE}/about"
            fields = "storageQuota"

            response = self._make_request("GET", url, params={"fields": fields})

            if response and "storageQuota" in response:
                quota = response["storageQuota"]
                return IntegrationResult(
                    success=True,
                    data={
                        "quota": {
                            "limit": quota.get("limit", 0),
                            "usage": quota.get("usage", 0),
                            "usage_in_drive": quota.get("usageInDrive", 0),
                            "usage_in_drive_trash": quota.get("usageInDriveTrash", 0),
                        },
                        "percentage_used": (
                            (quota.get("usage", 0) / quota.get("limit", 1)) * 100
                            if quota.get("limit", 0) > 0
                            else 0
                        ),
                    },
                )
            else:
                return IntegrationResult(
                    success=False,
                    error="Failed to get quota information",
                )
        except Exception as e:
            logger.error(f"Failed to get quota: {e}")
            return IntegrationResult(success=False, error=str(e))

    def _list_files(self, payload: Dict[str, Any]) -> IntegrationResult:
        """Liste les fichiers et dossiers dans Google Drive."""
        try:
            folder_id = payload.get("folder_id", "root")
            query = payload.get("query", "")
            page_size = payload.get("page_size", 100)
            page_token = payload.get("page_token")
            fields = payload.get(
                "fields",
                "files(id, name, mimeType, size, createdTime, modifiedTime, parents, webViewLink)",
            )
            order_by = payload.get("order_by", "modifiedTime desc")

            params = {
                "q": self._build_search_query(folder_id, query),
                "pageSize": page_size,
                "fields": f"nextPageToken, files({fields})",
                "orderBy": order_by,
            }

            if page_token:
                params["pageToken"] = page_token

            url = f"{self.DRIVE_API_BASE}/files"
            response = self._make_request("GET", url, params=params)

            if response and "files" in response:
                files = response.get("files", [])
                return IntegrationResult(
                    success=True,
                    data={
                        "files": files,
                        "count": len(files),
                        "next_page_token": response.get("nextPageToken"),
                    },
                )
            else:
                return IntegrationResult(
                    success=True,
                    data={"files": [], "count": 0},
                )
        except Exception as e:
            logger.error(f"Failed to list files: {e}")
            return IntegrationResult(success=False, error=str(e))

    def _search_files(self, payload: Dict[str, Any]) -> IntegrationResult:
        """Recherche des fichiers dans Google Drive."""
        try:
            query = payload.get("query", "")
            page_size = payload.get("page_size", 100)
            page_token = payload.get("page_token")

            params = {
                "q": query,
                "pageSize": page_size,
                "fields": "nextPageToken, files(id, name, mimeType, size)",
            }

            if page_token:
                params["pageToken"] = page_token

            url = f"{self.DRIVE_API_BASE}/files"
            response = self._make_request("GET", url, params=params)

            if response and "files" in response:
                files = response.get("files", [])
                return IntegrationResult(
                    success=True,
                    data={
                        "files": files,
                        "count": len(files),
                        "next_page_token": response.get("nextPageToken"),
                        "query": query,
                    },
                )
            else:
                return IntegrationResult(
                    success=True,
                    data={"files": [], "count": 0, "query": query},
                )
        except Exception as e:
            logger.error(f"Failed to search files: {e}")
            return IntegrationResult(success=False, error=str(e))

    def _build_search_query(self, folder_id: str, custom_query: str = "") -> str:
        """
        Construit une requête de recherche pour Google Drive.

        Args:
            folder_id: ID du dossier parent
            custom_query: Requête personnalisée

        Returns:
            Requête de recherche formatée
        """
        conditions = []

        if folder_id and folder_id != "root":
            conditions.append(f"'{folder_id}' in parents")

        if custom_query:
            conditions.append(custom_query)

        # Ne pas inclure la corbeille
        conditions.append("trashed = false")

        return " and ".join(conditions) if conditions else "trashed = false"

    def _get_file_metadata(self, payload: Dict[str, Any]) -> IntegrationResult:
        """Récupère les métadonnées d'un fichier."""
        try:
            file_id = payload.get("file_id")
            fields = payload.get(
                "fields",
                "id, name, mimeType, size, createdTime, modifiedTime, parents, "
                "webViewLink, webContentLink, owners, permissions, md5Checksum",
            )

            if not file_id:
                return IntegrationResult(
                    success=False,
                    error="file_id is required",
                )

            url = f"{self.DRIVE_API_BASE}/files/{file_id}"
            response = self._make_request("GET", url, params={"fields": fields})

            if response:
                return IntegrationResult(
                    success=True,
                    data={"metadata": response},
                )
            else:
                return IntegrationResult(
                    success=False,
                    error="Failed to get file metadata",
                )
        except Exception as e:
            logger.error(f"Failed to get file metadata: {e}")
            return IntegrationResult(success=False, error=str(e))

    def _get_file(self, payload: Dict[str, Any]) -> IntegrationResult:
        """Télécharge un fichier depuis Google Drive."""
        try:
            file_id = payload.get("file_id")

            if not file_id:
                return IntegrationResult(
                    success=False,
                    error="file_id is required",
                )

            # D'abord, obtenir les métadonnées pour vérifier que le fichier existe
            metadata_result = self._get_file_metadata({"file_id": file_id})

            if not metadata_result.success:
                return metadata_result

            metadata = metadata_result.data["metadata"]

            # Utiliser l'endpoint de téléchargement direct
            url = f"{self.DRIVE_API_BASE}/files/{file_id}?alt=media"

            response = self._make_request("GET", url)

            if response is not None:
                # Le response est le contenu binaire du fichier
                import io

                file_content = response
                if isinstance(response, bytes):
                    content = response
                elif isinstance(response, str):
                    content = response.encode()
                else:
                    # Si c'est un JSON (ce qui ne devrait pas arriver pour alt=media)
                    content = str(response).encode()

                return IntegrationResult(
                    success=True,
                    data={
                        "content": base64.b64encode(content).decode(),
                        "content_type": mimetypes.guess_type(metadata.get("name", ""))[
                            0
                        ],
                        "metadata": metadata,
                    },
                )
            else:
                return IntegrationResult(
                    success=False,
                    error="Failed to download file",
                )
        except Exception as e:
            logger.error(f"Failed to get file content: {e}")
            return IntegrationResult(success=False, error=str(e))

    def _get_folder(self, payload: Dict[str, Any]) -> IntegrationResult:
        """Récupère les informations d'un dossier."""
        try:
            folder_id = payload.get("folder_id")

            if not folder_id:
                return IntegrationResult(
                    success=False,
                    error="folder_id is required",
                )

            url = f"{self.DRIVE_API_BASE}/files/{folder_id}"
            fields = "id, name, mimeType, createdTime, modifiedTime, parents, size"

            response = self._make_request("GET", url, params={"fields": fields})

            if response:
                return IntegrationResult(
                    success=True,
                    data={"folder": response},
                )
            else:
                return IntegrationResult(
                    success=False,
                    error="Failed to get folder information",
                )
        except Exception as e:
            logger.error(f"Failed to get folder: {e}")
            return IntegrationResult(success=False, error=str(e))

    def _list_folders(self, payload: Dict[str, Any]) -> IntegrationResult:
        """Liste les dossiers dans Google Drive."""
        try:
            parent_id = payload.get("parent_id", "root")
            page_size = payload.get("page_size", 100)
            page_token = payload.get("page_token")

            # Rechercher uniquement les dossiers (mimeType = application/vnd.google-apps.folder)
            params = {
                "q": f"'{parent_id}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false",
                "pageSize": page_size,
                "fields": "nextPageToken, files(id, name, mimeType, createdTime, modifiedTime)",
            }

            if page_token:
                params["pageToken"] = page_token

            url = f"{self.DRIVE_API_BASE}/files"
            response = self._make_request("GET", url, params=params)

            if response and "files" in response:
                folders = response.get("files", [])
                return IntegrationResult(
                    success=True,
                    data={
                        "folders": folders,
                        "count": len(folders),
                        "next_page_token": response.get("nextPageToken"),
                    },
                )
            else:
                return IntegrationResult(
                    success=True,
                    data={"folders": [], "count": 0},
                )
        except Exception as e:
            logger.error(f"Failed to list folders: {e}")
            return IntegrationResult(success=False, error=str(e))

    def _create_folder(self, payload: Dict[str, Any]) -> IntegrationResult:
        """Crée un nouveau dossier dans Google Drive."""
        try:
            name = payload.get("name")
            parent_id = payload.get("parent_id", "root")

            if not name:
                return IntegrationResult(
                    success=False,
                    error="name is required",
                )

            url = f"{self.DRIVE_API_BASE}/files"

            folder_metadata = {
                "name": name,
                "mimeType": "application/vnd.google-apps.folder",
                "parents": [parent_id] if parent_id != "root" else [],
            }

            fields = "id, name, mimeType, parents, webViewLink"

            response = self._make_request(
                "POST", url, json=folder_metadata, params={"fields": fields}
            )

            if response and "id" in response:
                return IntegrationResult(
                    success=True,
                    data={"folder": response},
                )
            else:
                return IntegrationResult(
                    success=False,
                    error="Failed to create folder",
                )
        except Exception as e:
            logger.error(f"Failed to create folder: {e}")
            return IntegrationResult(success=False, error=str(e))

    def _upload_file(self, payload: Dict[str, Any]) -> IntegrationResult:
        """Upload un fichier vers Google Drive."""
        try:
            file_name = payload.get("name")
            content = payload.get("content")
            content_type = payload.get("content_type", "text/plain")
            parent_id = payload.get("parent_id", "root")
            overwrite = payload.get("overwrite", False)

            if not file_name:
                return IntegrationResult(
                    success=False,
                    error="name is required",
                )

            if not content:
                return IntegrationResult(
                    success=False,
                    error="content is required",
                )

            # Décoder le contenu si c'est du base64
            if isinstance(content, str) and content.startswith("data:"):
                # Format: data:[<mediatype>][;base64],<data>
                content = content.split(",")[1]
                import base64

                content_bytes = base64.b64decode(content)
            elif isinstance(content, str):
                content_bytes = content.encode()
            else:
                content_bytes = content

            # Déterminer le type de contenu si non spécifié
            if content_type == "text/plain":
                content_type = mimetypes.guess_type(file_name)[0] or "text/plain"

            # Construire les métadonnées
            metadata = {
                "name": file_name,
                "parents": [parent_id] if parent_id != "root" else [],
            }

            # Utiliser l'endpoint d'upload simple
            url = f"{self.UPLOAD_API_BASE}/files?uploadType=media"

            headers = {
                "Content-Type": content_type,
            }

            # Si on veut écraser un fichier existant, on a besoin de son ID
            if overwrite:
                existing_file_id = payload.get("file_id")
                if existing_file_id:
                    url = f"{self.UPLOAD_API_BASE}/files/{existing_file_id}?uploadType=media"
                    metadata = {}  # Pas besoin de metadata pour l'update

            response = self._make_request(
                "POST" if not overwrite or not payload.get("file_id") else "PUT",
                url,
                data=content_bytes,
                headers=headers,
                params={"name": file_name} if metadata else None,
            )

            if response and "id" in response:
                return IntegrationResult(
                    success=True,
                    data={
                        "file": response,
                        "uploaded": True,
                        "size": len(content_bytes),
                    },
                )
            else:
                return IntegrationResult(
                    success=False,
                    error="Failed to upload file",
                )
        except Exception as e:
            logger.error(f"Failed to upload file: {e}")
            return IntegrationResult(success=False, error=str(e))

    def _download_file(self, payload: Dict[str, Any]) -> IntegrationResult:
        """Télécharge un fichier depuis Google Drive."""
        # Alias pour _get_file
        return self._get_file(payload)

    def _delete_file(self, payload: Dict[str, Any]) -> IntegrationResult:
        """Supprime un fichier de Google Drive."""
        try:
            file_id = payload.get("file_id")

            if not file_id:
                return IntegrationResult(
                    success=False,
                    error="file_id is required",
                )

            url = f"{self.DRIVE_API_BASE}/files/{file_id}"

            response = self._make_request("DELETE", url)

            # Une réponse vide (204) indique un succès
            if response is None or response == "":
                return IntegrationResult(
                    success=True,
                    data={"deleted": True, "file_id": file_id},
                )
            else:
                return IntegrationResult(
                    success=False,
                    error="Failed to delete file",
                )
        except Exception as e:
            logger.error(f"Failed to delete file: {e}")
            return IntegrationResult(success=False, error=str(e))

    def _copy_file(self, payload: Dict[str, Any]) -> IntegrationResult:
        """Copie un fichier dans Google Drive."""
        try:
            file_id = payload.get("file_id")
            new_name = payload.get("name")
            parent_id = payload.get("parent_id")

            if not file_id:
                return IntegrationResult(
                    success=False,
                    error="file_id is required",
                )

            url = f"{self.DRIVE_API_BASE}/files/{file_id}/copy"

            copy_metadata = {}
            if new_name:
                copy_metadata["name"] = new_name
            if parent_id:
                copy_metadata["parents"] = [parent_id]

            fields = "id, name, mimeType, parents"

            response = self._make_request(
                "POST",
                url,
                json=copy_metadata,
                params={"fields": fields},
            )

            if response and "id" in response:
                return IntegrationResult(
                    success=True,
                    data={"file": response, "copied_from": file_id},
                )
            else:
                return IntegrationResult(
                    success=False,
                    error="Failed to copy file",
                )
        except Exception as e:
            logger.error(f"Failed to copy file: {e}")
            return IntegrationResult(success=False, error=str(e))

    def _move_file(self, payload: Dict[str, Any]) -> IntegrationResult:
        """Déplace un fichier vers un autre dossier."""
        try:
            file_id = payload.get("file_id")
            new_parent_id = payload.get("new_parent_id")

            if not file_id:
                return IntegrationResult(
                    success=False,
                    error="file_id is required",
                )

            if not new_parent_id:
                return IntegrationResult(
                    success=False,
                    error="new_parent_id is required",
                )

            url = f"{self.DRIVE_API_BASE}/files/{file_id}"

            # Pour déplacer un fichier, on met à jour ses parents
            update_data = {
                "addParents": new_parent_id,
            }

            # Optionnellement, on peut supprimer les anciens parents
            remove_old_parents = payload.get("remove_old_parents", True)
            if remove_old_parents:
                # On peut obtenir les parents actuels d'abord
                metadata = self._get_file_metadata({"file_id": file_id})
                if metadata.success and "parents" in metadata.data["metadata"]:
                    current_parents = metadata.data["metadata"].get("parents", [])
                    if current_parents:
                        update_data["removeParents"] = ",".join(current_parents)

            fields = "id, name, parents"

            response = self._make_request(
                "PATCH",
                url,
                json=update_data,
                params={"fields": fields},
            )

            if response and "id" in response:
                return IntegrationResult(
                    success=True,
                    data={"file": response, "moved_to": new_parent_id},
                )
            else:
                return IntegrationResult(
                    success=False,
                    error="Failed to move file",
                )
        except Exception as e:
            logger.error(f"Failed to move file: {e}")
            return IntegrationResult(success=False, error=str(e))

    def _update_file_metadata(self, payload: Dict[str, Any]) -> IntegrationResult:
        """Met à jour les métadonnées d'un fichier."""
        try:
            file_id = payload.get("file_id")
            metadata = payload.get("metadata", {})

            if not file_id:
                return IntegrationResult(
                    success=False,
                    error="file_id is required",
                )

            if not metadata:
                return IntegrationResult(
                    success=False,
                    error="metadata is required",
                )

            url = f"{self.DRIVE_API_BASE}/files/{file_id}"

            # Filtrer les champs valides pour la mise à jour
            valid_fields = {"name", "description", "mimeType", "starred", "trashed"}
            update_data = {k: v for k, v in metadata.items() if k in valid_fields}

            if not update_data:
                return IntegrationResult(
                    success=False,
                    error="No valid metadata fields to update",
                )

            fields = ",".join(f"{k}" for k in update_data.keys())

            response = self._make_request(
                "PATCH",
                url,
                json=update_data,
                params={"fields": fields},
            )

            if response and "id" in response:
                return IntegrationResult(
                    success=True,
                    data={"file": response, "updated_fields": list(update_data.keys())},
                )
            else:
                return IntegrationResult(
                    success=False,
                    error="Failed to update file metadata",
                )
        except Exception as e:
            logger.error(f"Failed to update file metadata: {e}")
            return IntegrationResult(success=False, error=str(e))

    def _get_permissions(self, payload: Dict[str, Any]) -> IntegrationResult:
        """Récupère les permissions d'un fichier."""
        try:
            file_id = payload.get("file_id")

            if not file_id:
                return IntegrationResult(
                    success=False,
                    error="file_id is required",
                )

            url = f"{self.DRIVE_API_BASE}/files/{file_id}/permissions"

            fields = "permissions(id, type, role, emailAddress, displayName)"

            response = self._make_request("GET", url, params={"fields": fields})

            if response and "permissions" in response:
                permissions = response.get("permissions", [])
                return IntegrationResult(
                    success=True,
                    data={
                        "permissions": permissions,
                        "count": len(permissions),
                    },
                )
            else:
                return IntegrationResult(
                    success=True,
                    data={"permissions": [], "count": 0},
                )
        except Exception as e:
            logger.error(f"Failed to get permissions: {e}")
            return IntegrationResult(success=False, error=str(e))

    def _add_permission(self, payload: Dict[str, Any]) -> IntegrationResult:
        """Ajoute une permission à un fichier."""
        try:
            file_id = payload.get("file_id")
            email = payload.get("email")
            role = payload.get("role", "reader")  # reader, writer, owner
            permission_type = payload.get("type", "user")  # user, group, domain, anyone

            if not file_id:
                return IntegrationResult(
                    success=False,
                    error="file_id is required",
                )

            if permission_type == "user" and not email:
                return IntegrationResult(
                    success=False,
                    error="email is required for user permission",
                )

            url = f"{self.DRIVE_API_BASE}/files/{file_id}/permissions"

            permission_data = {
                "type": permission_type,
                "role": role,
            }

            if permission_type == "user":
                permission_data["emailAddress"] = email
            elif permission_type == "group":
                permission_data["groupKey"] = email  # Pour les groupes Google
            elif permission_type == "domain":
                permission_data["domain"] = email  # Pour les domaines

            # Paramètres pour éviter les notifications
            params = {
                "sendNotificationEmail": str(
                    payload.get("send_notification", False)
                ).lower(),
            }

            response = self._make_request(
                "POST",
                url,
                json=permission_data,
                params=params,
            )

            if response and "id" in response:
                return IntegrationResult(
                    success=True,
                    data={"permission": response},
                )
            else:
                return IntegrationResult(
                    success=False,
                    error="Failed to add permission",
                )
        except Exception as e:
            logger.error(f"Failed to add permission: {e}")
            return IntegrationResult(success=False, error=str(e))

    def _remove_permission(self, payload: Dict[str, Any]) -> IntegrationResult:
        """Supprime une permission d'un fichier."""
        try:
            file_id = payload.get("file_id")
            permission_id = payload.get("permission_id")

            if not file_id:
                return IntegrationResult(
                    success=False,
                    error="file_id is required",
                )

            if not permission_id:
                return IntegrationResult(
                    success=False,
                    error="permission_id is required",
                )

            url = f"{self.DRIVE_API_BASE}/files/{file_id}/permissions/{permission_id}"

            response = self._make_request("DELETE", url)

            # Une réponse vide (204) indique un succès
            if response is None or response == "":
                return IntegrationResult(
                    success=True,
                    data={"removed": True, "permission_id": permission_id},
                )
            else:
                return IntegrationResult(
                    success=False,
                    error="Failed to remove permission",
                )
        except Exception as e:
            logger.error(f"Failed to remove permission: {e}")
            return IntegrationResult(success=False, error=str(e))

    def get_oauth_scopes(self) -> List[str]:
        """Retourne les scopes OAuth2 requis pour Google Drive."""
        return [
            "https://www.googleapis.com/auth/drive",  # Accès complet à Drive
            "https://www.googleapis.com/auth/drive.file",  # Accès aux fichiers créés par l'app
            "https://www.googleapis.com/auth/drive.metadata",  # Métadonnées seulement
            "https://www.googleapis.com/auth/drive.readonly",  # Lecture seule
            "https://www.googleapis.com/auth/drive.apps",  # Accès aux données de l'app dans Drive
            "https://www.googleapis.com/auth/drive.scripts",  # Accès aux scripts Apps
        ]

    def get_configuration_schema(self) -> Dict[str, Any]:
        """Retourne le schéma de configuration pour Google Drive."""
        return {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Nom de l'intégration Google Drive",
                    "default": "My Google Drive Integration",
                },
                "description": {
                    "type": "string",
                    "description": "Description de l'intégration",
                    "default": "",
                },
                "settings": {
                    "type": "object",
                    "description": "Paramètres spécifiques Google Drive",
                    "properties": {
                        "root_folder_id": {
                            "type": "string",
                            "description": "ID du dossier racine par défaut",
                            "default": "root",
                        },
                        "auto_organize": {
                            "type": "boolean",
                            "description": "Organiser automatiquement les fichiers par date",
                            "default": False,
                        },
                        "date_format": {
                            "type": "string",
                            "description": "Format des dossiers de date (ex: YYYY/MM/DD)",
                            "default": "YYYY/MM",
                        },
                        "max_file_size_mb": {
                            "type": "number",
                            "description": "Taille maximale des fichiers à uploader (en Mo)",
                            "default": 50,
                            "minimum": 1,
                            "maximum": 1024,
                        },
                        "share_uploaded_files": {
                            "type": "boolean",
                            "description": "Partager automatiquement les fichiers uploadés",
                            "default": False,
                        },
                    },
                },
            },
            "required": ["name"],
        }
