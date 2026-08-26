# 🐙 Agent World - GitHub Integration Adapter
# Version: 0.5.0 (Épic 7 - US-047)
# Description: Adapter pour l'intégration avec GitHub

"""
GitHub Integration Adapter for Agent World.

Ce module implémente l'adapter pour l'intégration avec GitHub.
Il permet aux agents d'interagir avec des repositories GitHub,
de créer des PR, commenter des issues, etc.

Requirements:
    - requests: Pour les requêtes HTTP
    - requests-oauthlib: Pour OAuth2 (optionnel, si on utilise OAuth2)
"""

import base64
import json
import logging
import secrets
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from urllib.parse import urlencode

import requests

import logging

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
# On utilise un import direct pour éviter les problèmes circulaires
from . import register_adapter


@register_adapter
class GitHubIntegrationAdapter(BaseIntegrationAdapter):
    """
    Adapter pour l'intégration avec GitHub.
    
    Cet adapter permet aux agents d'effectuer les actions suivantes :
    - Créer une Pull Request
    - Commenter une issue
    - Créer une issue
    - Lister les repositories
    - Obtenir des informations sur un repository
    - etc.
    
    Authentication:
        - OAuth2 (recommandé)
        - Personal Access Token (PAT)
    """
    
    # Configuration de l'adapter
    type = IntegrationType.GITHUB
    name = "GitHub"
    description = "Intégration avec GitHub pour gérer des repositories, PR et issues"
    auth_type = AuthType.OAUTH2
    icon = "github"
    color = "#24292e"
    
    # Actions supportées
    supported_actions = [
        # Repositories
        "list_repositories",
        "get_repository",
        
        # Pull Requests
        "create_pull_request",
        "get_pull_request",
        "list_pull_requests",
        "comment_pull_request",
        
        # Issues
        "create_issue",
        "get_issue",
        "list_issues",
        "comment_issue",
        "close_issue",
        "open_issue",
        
        # Commits
        "create_commit",
        "list_commits",
        "get_commit",
        
        # Files
        "create_file",
        "update_file",
        "delete_file",
        "get_file",
    ]
    
    # Configuration OAuth2 par défaut pour GitHub
    OAUTH_CONFIG = OAuthConfig(
        client_id="",  # À configurer
        client_secret="",  # À configurer
        redirect_uri="http://localhost:5000/api/integrations/github/callback",
        authorization_url="https://github.com/login/oauth/authorize",
        token_url="https://github.com/login/oauth/access_token",
        userinfo_url="https://api.github.com/user",
        scope=["repo", "user", "notifications"],
    )
    
    def __init__(self, config: Optional[IntegrationConfig] = None):
        """Initialise l'adapter GitHub."""
        # Si une config OAuth globale est fournie, l'utiliser
        if config and config.oauth_config:
            self.oauth_config = config.oauth_config
        else:
            self.oauth_config = self.OAUTH_CONFIG
        
        super().__init__(config)
        self.session = requests.Session()
        
        # Ajouter les headers par défaut
        self.session.headers.update({
            "Accept": "application/vnd.github+json",
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
        
        if credentials.access_token:
            return {"Authorization": f"Bearer {credentials.access_token}"}
        elif credentials.api_key:
            return {"Authorization": f"token {credentials.api_key}"}
        else:
            raise AuthenticationError(
                "No valid credentials found",
                self.type
            )
    
    def _make_request(
        self, 
        method: str, 
        url: str, 
        **kwargs
    ) -> Any:
        """
        Effectue une requête HTTP avec gestion des erreurs.
        
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
                    error_data["response"] = response.json()
                except Exception:
                    error_data["response"] = response.text
                
                logger.error(f"GitHub API error: {error_data}")
                
                if response.status_code == 401:
                    raise AuthenticationError("Invalid or expired token", self.type)
                elif response.status_code == 403:
                    raise ConnectionError("Rate limit exceeded", self.type)
                elif response.status_code == 404:
                    raise ConnectionError(f"Resource not found: {url}", self.type)
                else:
                    raise ConnectionError(
                        f"GitHub API error: {response.status_code}",
                        self.type
                    )
            
            # Retourner la réponse JSON si possible
            try:
                return response.json()
            except ValueError:
                return response.text
                
        except requests.exceptions.RequestException as e:
            logger.error(f"GitHub request failed: {e}")
            raise ConnectionError(str(e), self.type)
    
    def authenticate(
        self, 
        credentials: IntegrationCredentials
    ) -> bool:
        """
        Authentifie l'intégration avec GitHub.
        
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
            logger.error(f"GitHub authentication failed: {e}")
            return False
    
    def get_authentication_url(
        self, 
        state: Optional[str] = None
    ) -> str:
        """
        Génère l'URL d'authentification OAuth2 pour GitHub.
        
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
            "scope": " ".join(self.oauth_config.scope),
            "state": state,
        }
        
        return f"{self.oauth_config.authorization_url}?{urlencode(params)}"
    
    def exchange_code_for_token(
        self, 
        code: str
    ) -> IntegrationCredentials:
        """
        Échange un code d'autorisation OAuth2 contre un token GitHub.
        
        Args:
            code: Code d'autorisation reçu de GitHub
            
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
            access_token = token_data.get("access_token")
            refresh_token = token_data.get("refresh_token")
            expires_in = token_data.get("expires_in", 3600)
            
            if not access_token:
                raise ValueError("No access token received from GitHub")
            
            # Calculer l'expiration
            token_expiry = datetime.utcnow() + timedelta(seconds=expires_in)
            
            return IntegrationCredentials(
                access_token=access_token,
                refresh_token=refresh_token,
                token_expiry=token_expiry,
            )
            
        except requests.exceptions.RequestException as e:
            logger.error(f"GitHub token exchange failed: {e}")
            raise ValueError(f"GitHub token exchange failed: {e}")
    
    def refresh_token(
        self, 
        refresh_token: str
    ) -> IntegrationCredentials:
        """
        Rafraîchit le token d'accès avec un refresh token.
        
        Note: GitHub ne fournit pas toujours de refresh_token dans le flux OAuth2.
        Si aucun refresh_token n'est disponible, il faut redemander l'autorisation.
        
        Args:
            refresh_token: Refresh token à utiliser
            
        Returns:
            IntegrationCredentials avec les nouveaux tokens
            
        Raises:
            NotImplementedError: GitHub ne supporte pas toujours le refresh token
        """
        # GitHub utilise des tokens qui n'expirent pas par défaut
        # ou nécessite une nouvelle autorisation
        raise NotImplementedError(
            "GitHub OAuth2 tokens do not support refresh. "
            "Please re-authenticate."
        )
    
    def test_connection(self) -> IntegrationResult:
        """
        Teste la connexion à GitHub.
        
        Returns:
            IntegrationResult avec le résultat du test
        """
        try:
            # Appeler l'API user pour vérifier l'authentification
            user_data = self._make_request("GET", "https://api.github.com/user")
            
            if user_data and isinstance(user_data, dict) and user_data.get("login"):
                return IntegrationResult(
                    success=True,
                    data={"user": user_data.get("login")},
                )
            else:
                return IntegrationResult(
                    success=False,
                    error="Invalid response from GitHub",
                )
        except Exception as e:
            logger.error(f"GitHub connection test failed: {e}")
            return IntegrationResult(
                success=False,
                error=str(e),
            )
    
    def execute(
        self, 
        action: IntegrationAction
    ) -> IntegrationResult:
        """
        Exécute une action GitHub.
        
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
    
    def _list_repositories(self, payload: Dict[str, Any]) -> IntegrationResult:
        """Liste les repositories de l'utilisateur."""
        try:
            # Par défaut, lister tous les repos de l'utilisateur
            user = payload.get("user", "")
            visibility = payload.get("visibility", "all")  # all, public, private
            sort = payload.get("sort", "updated")
            direction = payload.get("direction", "desc")
            per_page = payload.get("per_page", 30)
            page = payload.get("page", 1)
            
            url = "https://api.github.com/user/repos"
            params = {
                "visibility": visibility,
                "sort": sort,
                "direction": direction,
                "per_page": per_page,
                "page": page,
            }
            
            repos = self._make_request("GET", url, params=params)
            
            return IntegrationResult(
                success=True,
                data={"repositories": repos, "count": len(repos)},
            )
            
        except Exception as e:
            logger.error(f"Failed to list repositories: {e}")
            return IntegrationResult(
                success=False,
                error=str(e),
            )
    
    def _get_repository(self, payload: Dict[str, Any]) -> IntegrationResult:
        """Obtient les informations d'un repository."""
        try:
            owner = payload.get("owner")
            repo_name = payload.get("repo")
            
            if not owner or not repo_name:
                return IntegrationResult(
                    success=False,
                    error="owner and repo are required",
                )
            
            url = f"https://api.github.com/repos/{owner}/{repo_name}"
            repo_data = self._make_request("GET", url)
            
            return IntegrationResult(
                success=True,
                data={"repository": repo_data},
            )
            
        except Exception as e:
            logger.error(f"Failed to get repository: {e}")
            return IntegrationResult(
                success=False,
                error=str(e),
            )
    
    def _create_pull_request(self, payload: Dict[str, Any]) -> IntegrationResult:
        """Crée une Pull Request."""
        try:
            owner = payload.get("owner")
            repo_name = payload.get("repo")
            title = payload.get("title")
            body = payload.get("body", "")
            head = payload.get("head")  # Branch source
            base = payload.get("base")  # Branch destination
            draft = payload.get("draft", False)
            
            if not all([owner, repo_name, title, head, base]):
                return IntegrationResult(
                    success=False,
                    error="owner, repo, title, head, and base are required",
                )
            
            url = f"https://api.github.com/repos/{owner}/{repo_name}/pulls"
            pr_data = {
                "title": title,
                "body": body,
                "head": head,
                "base": base,
                "draft": draft,
            }
            
            response = self._make_request("POST", url, json=pr_data)
            
            return IntegrationResult(
                success=True,
                data={"pull_request": response},
            )
            
        except Exception as e:
            logger.error(f"Failed to create pull request: {e}")
            return IntegrationResult(
                success=False,
                error=str(e),
            )
    
    def _comment_pull_request(
        self, 
        payload: Dict[str, Any]
    ) -> IntegrationResult:
        """Ajoute un commentaire à une Pull Request."""
        try:
            owner = payload.get("owner")
            repo_name = payload.get("repo")
            pr_number = payload.get("pr_number")
            body = payload.get("body")
            
            if not all([owner, repo_name, pr_number, body]):
                return IntegrationResult(
                    success=False,
                    error="owner, repo, pr_number, and body are required",
                )
            
            url = f"https://api.github.com/repos/{owner}/{repo_name}/issues/{pr_number}/comments"
            comment_data = {"body": body}
            
            response = self._make_request("POST", url, json=comment_data)
            
            return IntegrationResult(
                success=True,
                data={"comment": response},
            )
            
        except Exception as e:
            logger.error(f"Failed to comment pull request: {e}")
            return IntegrationResult(
                success=False,
                error=str(e),
            )
    
    def _create_issue(self, payload: Dict[str, Any]) -> IntegrationResult:
        """Crée une issue."""
        try:
            owner = payload.get("owner")
            repo_name = payload.get("repo")
            title = payload.get("title")
            body = payload.get("body", "")
            labels = payload.get("labels", [])
            assignees = payload.get("assignees", [])
            
            if not all([owner, repo_name, title]):
                return IntegrationResult(
                    success=False,
                    error="owner, repo, and title are required",
                )
            
            url = f"https://api.github.com/repos/{owner}/{repo_name}/issues"
            issue_data = {
                "title": title,
                "body": body,
                "labels": labels,
                "assignees": assignees,
            }
            
            response = self._make_request("POST", url, json=issue_data)
            
            return IntegrationResult(
                success=True,
                data={"issue": response},
            )
            
        except Exception as e:
            logger.error(f"Failed to create issue: {e}")
            return IntegrationResult(
                success=False,
                error=str(e),
            )
    
    def _comment_issue(self, payload: Dict[str, Any]) -> IntegrationResult:
        """Ajoute un commentaire à une issue."""
        try:
            owner = payload.get("owner")
            repo_name = payload.get("repo")
            issue_number = payload.get("issue_number")
            body = payload.get("body")
            
            if not all([owner, repo_name, issue_number, body]):
                return IntegrationResult(
                    success=False,
                    error="owner, repo, issue_number, and body are required",
                )
            
            url = f"https://api.github.com/repos/{owner}/{repo_name}/issues/{issue_number}/comments"
            comment_data = {"body": body}
            
            response = self._make_request("POST", url, json=comment_data)
            
            return IntegrationResult(
                success=True,
                data={"comment": response},
            )
            
        except Exception as e:
            logger.error(f"Failed to comment issue: {e}")
            return IntegrationResult(
                success=False,
                error=str(e),
            )
    
    def _create_file(self, payload: Dict[str, Any]) -> IntegrationResult:
        """Crée un fichier dans un repository."""
        try:
            owner = payload.get("owner")
            repo_name = payload.get("repo")
            path = payload.get("path")
            content = payload.get("content")
            message = payload.get("message", "Add file via Agent World")
            branch = payload.get("branch", "main")
            
            if not all([owner, repo_name, path, content]):
                return IntegrationResult(
                    success=False,
                    error="owner, repo, path, and content are required",
                )
            
            url = f"https://api.github.com/repos/{owner}/{repo_name}/contents/{path}"
            
            # Encoder le contenu en base64
            if isinstance(content, str):
                content_encoded = base64.b64encode(content.encode()).decode()
            else:
                content_encoded = base64.b64encode(content).decode()
            
            file_data = {
                "message": message,
                "content": content_encoded,
                "branch": branch,
            }
            
            response = self._make_request("PUT", url, json=file_data)
            
            return IntegrationResult(
                success=True,
                data={"file": response},
            )
            
        except Exception as e:
            logger.error(f"Failed to create file: {e}")
            return IntegrationResult(
                success=False,
                error=str(e),
            )
    
    def _get_file(self, payload: Dict[str, Any]) -> IntegrationResult:
        """Récupère le contenu d'un fichier."""
        try:
            owner = payload.get("owner")
            repo_name = payload.get("repo")
            path = payload.get("path")
            ref = payload.get("ref", "main")
            
            if not all([owner, repo_name, path]):
                return IntegrationResult(
                    success=False,
                    error="owner, repo, and path are required",
                )
            
            url = f"https://api.github.com/repos/{owner}/{repo_name}/contents/{path}"
            params = {"ref": ref}
            
            response = self._make_request("GET", url, params=params)
            
            if response and response.get("content"):
                # Décoder le contenu base64
                content_encoded = response["content"]
                try:
                    content = base64.b64decode(content_encoded).decode()
                    response["content_decoded"] = content
                except Exception:
                    pass
            
            return IntegrationResult(
                success=True,
                data={"file": response},
            )
            
        except Exception as e:
            logger.error(f"Failed to get file: {e}")
            return IntegrationResult(
                success=False,
                error=str(e),
            )
    
    def _list_issues(self, payload: Dict[str, Any]) -> IntegrationResult:
        """Liste les issues d'un repository."""
        try:
            owner = payload.get("owner")
            repo_name = payload.get("repo")
            state = payload.get("state", "open")  # open, closed, all
            labels = payload.get("labels", "")
            assignee = payload.get("assignee", "")
            creator = payload.get("creator", "")
            sort = payload.get("sort", "created")
            direction = payload.get("direction", "desc")
            per_page = payload.get("per_page", 30)
            page = payload.get("page", 1)
            
            if not all([owner, repo_name]):
                return IntegrationResult(
                    success=False,
                    error="owner and repo are required",
                )
            
            url = f"https://api.github.com/repos/{owner}/{repo_name}/issues"
            params = {
                "state": state,
                "labels": labels,
                "assignee": assignee,
                "creator": creator,
                "sort": sort,
                "direction": direction,
                "per_page": per_page,
                "page": page,
            }
            
            issues = self._make_request("GET", url, params=params)
            
            return IntegrationResult(
                success=True,
                data={"issues": issues, "count": len(issues)},
            )
            
        except Exception as e:
            logger.error(f"Failed to list issues: {e}")
            return IntegrationResult(
                success=False,
                error=str(e),
            )
    
    def _list_pull_requests(self, payload: Dict[str, Any]) -> IntegrationResult:
        """Liste les Pull Requests d'un repository."""
        try:
            owner = payload.get("owner")
            repo_name = payload.get("repo")
            state = payload.get("state", "open")  # open, closed, all
            sort = payload.get("sort", "created")
            direction = payload.get("direction", "desc")
            per_page = payload.get("per_page", 30)
            page = payload.get("page", 1)
            
            if not all([owner, repo_name]):
                return IntegrationResult(
                    success=False,
                    error="owner and repo are required",
                )
            
            url = f"https://api.github.com/repos/{owner}/{repo_name}/pulls"
            params = {
                "state": state,
                "sort": sort,
                "direction": direction,
                "per_page": per_page,
                "page": page,
            }
            
            pulls = self._make_request("GET", url, params=params)
            
            return IntegrationResult(
                success=True,
                data={"pull_requests": pulls, "count": len(pulls)},
            )
            
        except Exception as e:
            logger.error(f"Failed to list pull requests: {e}")
            return IntegrationResult(
                success=False,
                error=str(e),
            )
    
    def get_oauth_scopes(self) -> List[str]:
        """Retourne les scopes OAuth2 requis pour GitHub."""
        return [
            "repo",           # Accès complet aux repositories privés
            "user",          # Lire le profil utilisateur
            "notifications", # Gérer les notifications
            "read:org",      # Lire les informations organisation
            "write:discussion",  # Écrire dans les discussions
        ]
    
    def get_configuration_schema(self) -> Dict[str, Any]:
        """Retourne le schéma de configuration pour GitHub."""
        return {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Nom de l'intégration GitHub",
                    "default": "My GitHub Integration",
                },
                "description": {
                    "type": "string",
                    "description": "Description de l'intégration",
                    "default": "",
                },
                "settings": {
                    "type": "object",
                    "description": "Paramètres spécifiques GitHub",
                    "properties": {
                        "default_repository": {
                            "type": "string",
                            "description": "Repository par défaut (format: owner/repo)",
                            "default": "",
                        },
                        "auto_create_pr": {
                            "type": "boolean",
                            "description": "Créer automatiquement des PR pour les modifications",
                            "default": False,
                        },
                        "notify_on_comment": {
                            "type": "boolean",
                            "description": "Notifier lorsque quelqu'un commente",
                            "default": True,
                        },
                    },
                },
            },
            "required": ["name"],
        }
