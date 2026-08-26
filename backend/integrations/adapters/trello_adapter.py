# 📋 Agent World - Trello Integration Adapter
# Version: 0.5.0 (Épic 7 - US-052)
# Description: Adapter pour l'intégration avec Trello

"""
Trello Integration Adapter for Agent World.

Ce module implémente l'adapter pour l'intégration avec Trello.
Il permet aux agents de créer et gérer des cartes, listes et tableaux Trello
afin d'automatiser le suivi des tâches.

Requirements:
    - requests: Pour les requêtes HTTP
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
class TrelloIntegrationAdapter(BaseIntegrationAdapter):
    """
    Adapter pour l'intégration avec Trello.
    
    Cet adapter permet aux agents d'effectuer les actions suivantes :
    - Créer des cartes Trello
    - Mettre à jour des cartes (déplacer, ajouter des labels, etc.)
    - Lister les cartes d'un tableau
    - Créer des listes
    - Gérer les tableaux
    - Ajouter des commentaires
    - Attacher des fichiers
    
    Authentication:
        - OAuth2 (recommandé)
        - API Key + Token (méthode plus simple)
    
    Documentation Trello API: https://developer.atlassian.com/cloud/trello/rest/api-group-actions/
    """
    
    # Configuration de l'adapter
    type = IntegrationType.TRELLO
    name = "Trello"
    description = "Intégration avec Trello pour créer et gérer des cartes de tâches"
    auth_type = AuthType.OAUTH2
    icon = "trello"
    color = "#0079BF"
    
    # Actions supportées
    supported_actions = [
        # Tableaux
        "list_boards",
        "get_board",
        "create_board",
        
        # Listes
        "list_lists",
        "get_list",
        "create_list",
        
        # Cartes
        "list_cards",
        "get_card",
        "create_card",
        "update_card",
        "delete_card",
        "move_card",
        
        # Commentaires
        "add_comment",
        "list_comments",
        
        # Labels
        "list_labels",
        "add_label_to_card",
        "remove_label_from_card",
        
        # Checklists
        "add_checklist",
        "add_checklist_item",
        "update_checklist_item",
        
        # Attachements
        "add_attachment",
        "list_attachments",
        
        # Membres
        "list_members",
        "add_member_to_card",
        "remove_member_from_card",
        
        # Webhooks
        "create_webhook",
        "delete_webhook",
    ]
    
    # Configuration OAuth2 par défaut pour Trello
    OAUTH_CONFIG = OAuthConfig(
        client_id="",  # À configurer
        client_secret="",  # À configurer
        redirect_uri="http://localhost:5000/api/integrations/trello/callback",
        authorization_url="https://trello.com/1/OAuthAuthorizeToken",
        token_url="https://trello.com/1/OAuthGetAccessToken",
        userinfo_url="https://api.trello.com/1/members/me",
        scope=["read", "write", "account"],
    )
    
    # Base URL pour l'API Trello
    TRELLO_API_BASE = "https://api.trello.com/1"
    
    def __init__(self, config: Optional[IntegrationConfig] = None):
        """Initialise l'adapter Trello."""
        # Si une config OAuth globale est fournie, l'utiliser
        if config and config.oauth_config:
            self.oauth_config = config.oauth_config
        else:
            self.oauth_config = self.OAUTH_CONFIG
        
        super().__init__(config)
        self.session = requests.Session()
        
        # Ajouter les headers par défaut
        self.session.headers.update({
            "Content-Type": "application/json",
            "User-Agent": "AgentWorld/0.5.0",
        })
    
    def _get_auth_params(self) -> Dict[str, str]:
        """
        Obtient les paramètres d'authentification pour Trello.
        
        Trello utilise une combinaison de API key + token ou OAuth2.
        
        Returns:
            Dictionnaire des paramètres
        """
        if not self.config or not self.config.credentials:
            raise AuthenticationError(
                "No credentials configured for Trello",
                self.type
            )
        
        credentials = self.config.credentials
        
        # Trello accepte plusieurs méthodes d'authentification
        params = {}
        
        # Méthode 1: API Key + Token (la plus simple)
        if credentials.api_key and credentials.client_secret:
            params["key"] = credentials.api_key
            params["token"] = credentials.client_secret
        # Méthode 2: OAuth2 (access_token)
        elif credentials.access_token:
            params["key"] = credentials.client_id or ""
            params["token"] = credentials.access_token
        else:
            raise AuthenticationError(
                "No valid credentials found for Trello",
                self.type
            )
        
        return params
    
    def _make_request(
        self, 
        method: str, 
        endpoint: str,
        **kwargs
    ) -> Any:
        """
        Effectue une requête HTTP à l'API Trello avec gestion des erreurs.
        
        Args:
            method: Méthode HTTP (GET, POST, etc.)
            endpoint: Endpoint de l'API (sans la base URL)
            **kwargs: Arguments supplémentaires pour requests
            
        Returns:
            Réponse JSON ou None
            
        Raises:
            ConnectionError: En cas d'erreur de connexion
        """
        url = f"{self.TRELLO_API_BASE}/{endpoint}"
        
        # Ajouter les paramètres d'authentification
        params = kwargs.pop("params", {})
        auth_params = self._get_auth_params()
        params.update(auth_params)
        
        try:
            response = self.session.request(
                method,
                url,
                params=params,
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
                
                logger.error(f"Trello API error: {error_data}")
                
                if response.status_code == 401:
                    raise AuthenticationError("Invalid or expired Trello credentials", self.type)
                elif response.status_code == 403:
                    raise ConnectionError("Trello permission denied", self.type)
                elif response.status_code == 404:
                    raise ConnectionError(f"Trello resource not found: {endpoint}", self.type)
                elif response.status_code == 429:
                    raise ConnectionError("Trello API rate limited", self.type)
                else:
                    raise ConnectionError(
                        f"Trello API error: {response.status_code}",
                        self.type
                    )
            
            # Retourner la réponse JSON si possible
            try:
                return response.json()
            except ValueError:
                return response.text
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Trello request failed: {e}")
            raise ConnectionError(str(e), self.type)
    
    def authenticate(
        self, 
        credentials: IntegrationCredentials
    ) -> bool:
        """
        Authentifie l'intégration avec Trello.
        
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
            
            # Tester la connexion en récupérant les infos du membre
            result = self.test_connection()
            
            # Restaurer les credentials d'origine
            if old_credentials:
                self.config.credentials = old_credentials
            
            return result.success
            
        except Exception as e:
            logger.error(f"Trello authentication failed: {e}")
            return False
    
    def get_authentication_url(
        self, 
        state: Optional[str] = None,
        scope: Optional[str] = None
    ) -> str:
        """
        Génère l'URL d'authentification OAuth1 pour Trello.
        
        Note: Trello utilise OAuth1, pas OAuth2
        
        Args:
            state: Valeur state pour la sécurité CSRF (générée si non fournie)
            scope: Portée des permissions
            
        Returns:
            URL d'authentification OAuth1
        """
        if not state:
            state = secrets.token_urlsafe(16)
        
        params = {
            "response_type": "token",
            "key": self.oauth_config.client_id,
            "return_url": self.oauth_config.redirect_uri,
            "scope": scope or " ".join(self.oauth_config.scope),
            "expiration": "never",
            "name": "Agent World",
        }
        
        return f"{self.oauth_config.authorization_url}?{urlencode(params)}"
    
    def exchange_code_for_token(
        self, 
        code: str
    ) -> IntegrationCredentials:
        """
        Échange un token OAuth1 pour un access token Trello.
        
        Note: Trello utilise OAuth1. Avec OAuth1, on reçoit directement
        un access token dans le callback.
        
        Args:
            code: Token OAuth1 reçu de Trello
            
        Returns:
            IntegrationCredentials avec le token d'accès
        """
        # Avec OAuth1, le token est déjà fourni dans l'URL de callback
        # Format: https://callback?oauth_token=TOKEN&oauth_verifier=VERIFIER
        # Mais Trello utilise un flux simplifié où on reçoit directement le token
        
        return IntegrationCredentials(
            access_token=code,
            token_expiry=None,  # Les tokens Trello OAuth1 n'expirent pas
        )
    
    def refresh_token(
        self, 
        refresh_token: str
    ) -> IntegrationCredentials:
        """
        Rafraîchit le token d'accès.
        
        Note: Les tokens Trello OAuth1 ne sont pas rafraîchissables.
        Il faut redemander l'autorisation.
        
        Args:
            refresh_token: Non utilisé pour Trello OAuth1
            
        Raises:
            NotImplementedError: Trello OAuth1 tokens cannot be refreshed
        """
        raise NotImplementedError(
            "Trello OAuth1 tokens cannot be refreshed. "
            "Please re-authenticate."
        )
    
    def test_connection(self) -> IntegrationResult:
        """
        Teste la connexion à Trello.
        
        Returns:
            IntegrationResult avec le résultat du test
        """
        try:
            # Appeler l'API members/me pour vérifier l'authentification
            member_data = self._make_request("GET", "members/me")
            
            if member_data and isinstance(member_data, dict) and member_data.get("id"):
                return IntegrationResult(
                    success=True,
                    data={"user": {
                        "id": member_data.get("id"),
                        "username": member_data.get("username"),
                        "full_name": member_data.get("fullName"),
                        "email": member_data.get("email"),
                        "avatar_url": member_data.get("avatarUrl"),
                    }},
                )
            else:
                return IntegrationResult(
                    success=False,
                    error="Invalid response from Trello members endpoint",
                )
        except Exception as e:
            logger.error(f"Trello connection test failed: {e}")
            return IntegrationResult(
                success=False,
                error=str(e),
            )
    
    def execute(
        self, 
        action: IntegrationAction
    ) -> IntegrationResult:
        """
        Exécute une action Trello.
        
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
    
    def _list_boards(self, payload: Dict[str, Any]) -> IntegrationResult:
        """Liste les tableaux accessibles."""
        try:
            # Par défaut, lister les tableaux de l'utilisateur
            member_id = payload.get("member_id", "me")
            
            endpoint = f"members/{member_id}/boards"
            
            boards = self._make_request("GET", endpoint)
            
            if boards and isinstance(boards, list):
                return IntegrationResult(
                    success=True,
                    data={"boards": boards, "count": len(boards)},
                )
            else:
                return IntegrationResult(
                    success=True,
                    data={"boards": [], "count": 0},
                )
        except Exception as e:
            logger.error(f"Failed to list boards: {e}")
            return IntegrationResult(success=False, error=str(e))
    
    def _get_board(self, payload: Dict[str, Any]) -> IntegrationResult:
        """Récupère les informations d'un tableau."""
        try:
            board_id = payload.get("board_id")
            
            if not board_id:
                return IntegrationResult(
                    success=False,
                    error="board_id is required",
                )
            
            endpoint = f"boards/{board_id}"
            board_data = self._make_request("GET", endpoint)
            
            if board_data and board_data.get("id"):
                return IntegrationResult(
                    success=True,
                    data={"board": board_data},
                )
            else:
                return IntegrationResult(
                    success=False,
                    error="Invalid board data received",
                )
        except Exception as e:
            logger.error(f"Failed to get board: {e}")
            return IntegrationResult(success=False, error=str(e))
    
    def _create_board(self, payload: Dict[str, Any]) -> IntegrationResult:
        """Crée un nouveau tableau."""
        try:
            name = payload.get("name")
            default_lists = payload.get("default_lists", True)
            
            if not name:
                return IntegrationResult(
                    success=False,
                    error="name is required",
                )
            
            endpoint = "boards/"
            
            board_data = {
                "name": name,
                "defaultLists": default_lists,
            }
            
            # Paramètres optionnels
            if "description" in payload:
                board_data["desc"] = payload["description"]
            if "organization_id" in payload:
                board_data["idOrganization"] = payload["organization_id"]
            if "permissions" in payload:
                board_data["prefs_permissionLevel"] = payload["permissions"]
            if "visibility" in payload:
                board_data["prefs_visibility"] = payload["visibility"]
            
            response = self._make_request("POST", endpoint, json=board_data)
            
            if response and response.get("id"):
                return IntegrationResult(
                    success=True,
                    data={"board": response},
                )
            else:
                return IntegrationResult(
                    success=False,
                    error="Failed to create board",
                )
        except Exception as e:
            logger.error(f"Failed to create board: {e}")
            return IntegrationResult(success=False, error=str(e))
    
    def _list_lists(self, payload: Dict[str, Any]) -> IntegrationResult:
        """Liste les listes d'un tableau."""
        try:
            board_id = payload.get("board_id")
            
            if not board_id:
                return IntegrationResult(
                    success=False,
                    error="board_id is required",
                )
            
            endpoint = f"boards/{board_id}/lists"
            
            lists = self._make_request("GET", endpoint)
            
            if lists and isinstance(lists, list):
                return IntegrationResult(
                    success=True,
                    data={"lists": lists, "count": len(lists)},
                )
            else:
                return IntegrationResult(
                    success=True,
                    data={"lists": [], "count": 0},
                )
        except Exception as e:
            logger.error(f"Failed to list lists: {e}")
            return IntegrationResult(success=False, error=str(e))
    
    def _get_list(self, payload: Dict[str, Any]) -> IntegrationResult:
        """Récupère les informations d'une liste."""
        try:
            list_id = payload.get("list_id")
            
            if not list_id:
                return IntegrationResult(
                    success=False,
                    error="list_id is required",
                )
            
            endpoint = f"lists/{list_id}"
            list_data = self._make_request("GET", endpoint)
            
            if list_data and list_data.get("id"):
                return IntegrationResult(
                    success=True,
                    data={"list": list_data},
                )
            else:
                return IntegrationResult(
                    success=False,
                    error="Invalid list data received",
                )
        except Exception as e:
            logger.error(f"Failed to get list: {e}")
            return IntegrationResult(success=False, error=str(e))
    
    def _create_list(self, payload: Dict[str, Any]) -> IntegrationResult:
        """Crée une nouvelle liste dans un tableau."""
        try:
            board_id = payload.get("board_id")
            name = payload.get("name")
            position = payload.get("position", "bottom")  # top, bottom, ou un nombre
            
            if not board_id:
                return IntegrationResult(
                    success=False,
                    error="board_id is required",
                )
            
            if not name:
                return IntegrationResult(
                    success=False,
                    error="name is required",
                )
            
            endpoint = "lists"
            
            list_data = {
                "name": name,
                "idBoard": board_id,
                "pos": position,
            }
            
            response = self._make_request("POST", endpoint, json=list_data)
            
            if response and response.get("id"):
                return IntegrationResult(
                    success=True,
                    data={"list": response},
                )
            else:
                return IntegrationResult(
                    success=False,
                    error="Failed to create list",
                )
        except Exception as e:
            logger.error(f"Failed to create list: {e}")
            return IntegrationResult(success=False, error=str(e))
    
    def _list_cards(self, payload: Dict[str, Any]) -> IntegrationResult:
        """Liste les cartes d'une liste ou d'un tableau."""
        try:
            list_id = payload.get("list_id")
            board_id = payload.get("board_id")
            
            if list_id:
                endpoint = f"lists/{list_id}/cards"
            elif board_id:
                endpoint = f"boards/{board_id}/cards"
            else:
                return IntegrationResult(
                    success=False,
                    error="Either list_id or board_id is required",
                )
            
            cards = self._make_request("GET", endpoint)
            
            if cards and isinstance(cards, list):
                return IntegrationResult(
                    success=True,
                    data={"cards": cards, "count": len(cards)},
                )
            else:
                return IntegrationResult(
                    success=True,
                    data={"cards": [], "count": 0},
                )
        except Exception as e:
            logger.error(f"Failed to list cards: {e}")
            return IntegrationResult(success=False, error=str(e))
    
    def _get_card(self, payload: Dict[str, Any]) -> IntegrationResult:
        """Récupère les informations d'une carte."""
        try:
            card_id = payload.get("card_id")
            
            if not card_id:
                return IntegrationResult(
                    success=False,
                    error="card_id is required",
                )
            
            endpoint = f"cards/{card_id}"
            card_data = self._make_request("GET", endpoint)
            
            if card_data and card_data.get("id"):
                return IntegrationResult(
                    success=True,
                    data={"card": card_data},
                )
            else:
                return IntegrationResult(
                    success=False,
                    error="Invalid card data received",
                )
        except Exception as e:
            logger.error(f"Failed to get card: {e}")
            return IntegrationResult(success=False, error=str(e))
    
    def _create_card(self, payload: Dict[str, Any]) -> IntegrationResult:
        """Crée une nouvelle carte dans une liste."""
        try:
            list_id = payload.get("list_id")
            name = payload.get("name")
            
            if not list_id:
                return IntegrationResult(
                    success=False,
                    error="list_id is required",
                )
            
            if not name:
                return IntegrationResult(
                    success=False,
                    error="name is required",
                )
            
            endpoint = "cards"
            
            card_data = {
                "name": name,
                "idList": list_id,
            }
            
            # Champs optionnels
            if "description" in payload:
                card_data["desc"] = payload["description"]
            if "position" in payload:
                card_data["pos"] = payload["position"]
            if "due_date" in payload:
                card_data["due"] = payload["due_date"]
            if "labels" in payload:
                card_data["idLabels"] = payload["labels"]
            if "members" in payload:
                card_data["idMembers"] = payload["members"]
            
            response = self._make_request("POST", endpoint, json=card_data)
            
            if response and response.get("id"):
                return IntegrationResult(
                    success=True,
                    data={"card": response},
                )
            else:
                return IntegrationResult(
                    success=False,
                    error="Failed to create card",
                )
        except Exception as e:
            logger.error(f"Failed to create card: {e}")
            return IntegrationResult(success=False, error=str(e))
    
    def _update_card(self, payload: Dict[str, Any]) -> IntegrationResult:
        """Met à jour une carte existante."""
        try:
            card_id = payload.get("card_id")
            
            if not card_id:
                return IntegrationResult(
                    success=False,
                    error="card_id is required",
                )
            
            endpoint = f"cards/{card_id}"
            
            # Construire les données de mise à jour
            update_data = {}
            
            for key, value in payload.items():
                if key == "card_id":
                    continue
                if key == "name":
                    update_data["name"] = value
                elif key == "description":
                    update_data["desc"] = value
                elif key == "list_id":
                    update_data["idList"] = value
                elif key == "labels":
                    update_data["idLabels"] = value
                elif key == "members":
                    update_data["idMembers"] = value
                elif key == "due_date":
                    update_data["due"] = value
                elif key == "closed":
                    update_data["closed"] = value
                elif key == "archived":
                    update_data["archived"] = value
            
            if not update_data:
                return IntegrationResult(
                    success=False,
                    error="No data to update",
                )
            
            response = self._make_request("PUT", endpoint, json=update_data)
            
            if response and response.get("id"):
                return IntegrationResult(
                    success=True,
                    data={"card": response},
                )
            else:
                return IntegrationResult(
                    success=False,
                    error="Failed to update card",
                )
        except Exception as e:
            logger.error(f"Failed to update card: {e}")
            return IntegrationResult(success=False, error=str(e))
    
    def _delete_card(self, payload: Dict[str, Any]) -> IntegrationResult:
        """Supprime une carte (larchive)."""
        try:
            card_id = payload.get("card_id")
            
            if not card_id:
                return IntegrationResult(
                    success=False,
                    error="card_id is required",
                )
            
            endpoint = f"cards/{card_id}"
            
            # Trello archive plutôt que de supprimer définitivement
            response = self._make_request("DELETE", endpoint)
            
            if response and response.get("id"):
                return IntegrationResult(
                    success=True,
                    data={"card": response, "archived": True},
                )
            else:
                return IntegrationResult(
                    success=True,
                    data={"archived": True, "card_id": card_id},
                )
        except Exception as e:
            logger.error(f"Failed to delete/archive card: {e}")
            return IntegrationResult(success=False, error=str(e))
    
    def _move_card(self, payload: Dict[str, Any]) -> IntegrationResult:
        """Déplace une carte vers une autre liste ou position."""
        try:
            card_id = payload.get("card_id")
            list_id = payload.get("list_id")
            position = payload.get("position")  # top, bottom, ou un nombre
            
            if not card_id:
                return IntegrationResult(
                    success=False,
                    error="card_id is required",
                )
            
            endpoint = f"cards/{card_id}/idList"
            
            if list_id:
                move_data = {"value": list_id}
            elif position:
                # Déplacer vers une position spécifique dans la même liste
                endpoint = f"cards/{card_id}/pos"
                move_data = {"value": position}
            else:
                return IntegrationResult(
                    success=False,
                    error="Either list_id or position is required",
                )
            
            response = self._make_request("PUT", endpoint, json=move_data)
            
            if response and response.get("_value"):
                return IntegrationResult(
                    success=True,
                    data={
                        "card_id": card_id,
                        "moved_to": list_id or position,
                        "new_value": response.get("_value"),
                    },
                )
            else:
                return IntegrationResult(
                    success=True,
                    data={"card_id": card_id, "moved_to": list_id or position},
                )
        except Exception as e:
            logger.error(f"Failed to move card: {e}")
            return IntegrationResult(success=False, error=str(e))
    
    def _add_comment(self, payload: Dict[str, Any]) -> IntegrationResult:
        """Ajoute un commentaire à une carte."""
        try:
            card_id = payload.get("card_id")
            text = payload.get("text")
            
            if not card_id:
                return IntegrationResult(
                    success=False,
                    error="card_id is required",
                )
            
            if not text:
                return IntegrationResult(
                    success=False,
                    error="text is required",
                )
            
            endpoint = f"cards/{card_id}/actions/comments"
            
            comment_data = {
                "text": text,
            }
            
            response = self._make_request("POST", endpoint, json=comment_data)
            
            if response and response.get("id"):
                return IntegrationResult(
                    success=True,
                    data={"comment": response},
                )
            else:
                return IntegrationResult(
                    success=False,
                    error="Failed to add comment",
                )
        except Exception as e:
            logger.error(f"Failed to add comment: {e}")
            return IntegrationResult(success=False, error=str(e))
    
    def _list_comments(self, payload: Dict[str, Any]) -> IntegrationResult:
        """Liste les commentaires d'une carte."""
        try:
            card_id = payload.get("card_id")
            
            if not card_id:
                return IntegrationResult(
                    success=False,
                    error="card_id is required",
                )
            
            endpoint = f"cards/{card_id}/actions"
            
            # Filtrer pour obtenir uniquement les commentaires
            params = {"filter": "commentCard"}
            
            actions = self._make_request("GET", endpoint, params=params)
            
            if actions and isinstance(actions, list):
                comments = [a for a in actions if a.get("type") == "commentCard"]
                return IntegrationResult(
                    success=True,
                    data={"comments": comments, "count": len(comments)},
                )
            else:
                return IntegrationResult(
                    success=True,
                    data={"comments": [], "count": 0},
                )
        except Exception as e:
            logger.error(f"Failed to list comments: {e}")
            return IntegrationResult(success=False, error=str(e))
    
    def _list_labels(self, payload: Dict[str, Any]) -> IntegrationResult:
        """Liste les labels disponibles."""
        try:
            board_id = payload.get("board_id")
            
            if board_id:
                endpoint = f"boards/{board_id}/labels"
            else:
                endpoint = "labels"
            
            labels = self._make_request("GET", endpoint)
            
            if labels and isinstance(labels, list):
                return IntegrationResult(
                    success=True,
                    data={"labels": labels, "count": len(labels)},
                )
            else:
                return IntegrationResult(
                    success=True,
                    data={"labels": [], "count": 0},
                )
        except Exception as e:
            logger.error(f"Failed to list labels: {e}")
            return IntegrationResult(success=False, error=str(e))
    
    def _add_label_to_card(self, payload: Dict[str, Any]) -> IntegrationResult:
        """Ajoute un label à une carte."""
        try:
            card_id = payload.get("card_id")
            label_id = payload.get("label_id")
            label_color = payload.get("label_color")  # green, yellow, orange, red, purple, blue, sky, lime, pink, black
            label_name = payload.get("label_name")
            
            if not card_id:
                return IntegrationResult(
                    success=False,
                    error="card_id is required",
                )
            
            # Soit on utilise un label_id existant, soit on crée un nouveau label
            if label_id:
                endpoint = f"cards/{card_id}/idLabels"
                response = self._make_request(
                    "POST", 
                    endpoint, 
                    json={"value": label_id}
                )
            elif label_name and label_color:
                # Créer un nouveau label
                board_id = payload.get("board_id")
                if not board_id:
                    return IntegrationResult(
                        success=False,
                        error="board_id is required to create a new label",
                    )
                
                # D'abord, vérifier si le label existe déjà
                labels_result = self._list_labels({"board_id": board_id})
                existing_label = None
                if labels_result.success:
                    for label in labels_result.data.get("labels", []):
                        if label.get("name") == label_name:
                            existing_label = label
                            break
                
                if existing_label:
                    # Utiliser le label existant
                    label_id = existing_label.get("id")
                    endpoint = f"cards/{card_id}/idLabels"
                    response = self._make_request(
                        "POST", 
                        endpoint, 
                        json={"value": label_id}
                    )
                else:
                    # Créer un nouveau label
                    endpoint = "labels"
                    label_data = {
                        "name": label_name,
                        "color": label_color,
                        "idBoard": board_id,
                    }
                    create_response = self._make_request("POST", endpoint, json=label_data)
                    
                    if create_response and create_response.get("id"):
                        label_id = create_response.get("id")
                        # Ajouter le label à la carte
                        endpoint = f"cards/{card_id}/idLabels"
                        response = self._make_request(
                            "POST", 
                            endpoint, 
                            json={"value": label_id}
                        )
                    else:
                        return IntegrationResult(
                            success=False,
                            error="Failed to create label",
                        )
            else:
                return IntegrationResult(
                    success=False,
                    error="Either label_id or (label_name and label_color) is required",
                )
            
            if response and response.get("_value"):
                return IntegrationResult(
                    success=True,
                    data={"label_added": label_id or label_name, "card_id": card_id},
                )
            else:
                return IntegrationResult(
                    success=False,
                    error="Failed to add label to card",
                )
        except Exception as e:
            logger.error(f"Failed to add label to card: {e}")
            return IntegrationResult(success=False, error=str(e))
    
    def _remove_label_from_card(self, payload: Dict[str, Any]) -> IntegrationResult:
        """Supprime un label d'une carte."""
        try:
            card_id = payload.get("card_id")
            label_id = payload.get("label_id")
            
            if not card_id:
                return IntegrationResult(
                    success=False,
                    error="card_id is required",
                )
            
            if not label_id:
                return IntegrationResult(
                    success=False,
                    error="label_id is required",
                )
            
            endpoint = f"cards/{card_id}/idLabels/{label_id}"
            
            response = self._make_request("DELETE", endpoint)
            
            # Une réponse vide (200 OK avec contenu vide) indique un succès
            if response is None or response == "":
                return IntegrationResult(
                    success=True,
                    data={"removed": True, "label_id": label_id, "card_id": card_id},
                )
            else:
                return IntegrationResult(
                    success=True,
                    data={"removed": True, "label_id": label_id, "card_id": card_id},
                )
        except Exception as e:
            logger.error(f"Failed to remove label from card: {e}")
            return IntegrationResult(success=False, error=str(e))
    
    def _add_checklist(self, payload: Dict[str, Any]) -> IntegrationResult:
        """Ajoute une checklist à une carte."""
        try:
            card_id = payload.get("card_id")
            name = payload.get("name")
            
            if not card_id:
                return IntegrationResult(
                    success=False,
                    error="card_id is required",
                )
            
            if not name:
                return IntegrationResult(
                    success=False,
                    error="name is required",
                )
            
            endpoint = "checklists"
            
            checklist_data = {
                "name": name,
                "idCard": card_id,
            }
            
            response = self._make_request("POST", endpoint, json=checklist_data)
            
            if response and response.get("id"):
                return IntegrationResult(
                    success=True,
                    data={"checklist": response},
                )
            else:
                return IntegrationResult(
                    success=False,
                    error="Failed to add checklist",
                )
        except Exception as e:
            logger.error(f"Failed to add checklist: {e}")
            return IntegrationResult(success=False, error=str(e))
    
    def _add_checklist_item(self, payload: Dict[str, Any]) -> IntegrationResult:
        """Ajoute un élément à une checklist."""
        try:
            checklist_id = payload.get("checklist_id")
            name = payload.get("name")
            checked = payload.get("checked", False)
            
            if not checklist_id:
                return IntegrationResult(
                    success=False,
                    error="checklist_id is required",
                )
            
            if not name:
                return IntegrationResult(
                    success=False,
                    error="name is required",
                )
            
            endpoint = f"checklists/{checklist_id}/checkItems"
            
            item_data = {
                "name": name,
                "checked": str(checked).lower(),
            }
            
            response = self._make_request("POST", endpoint, json=item_data)
            
            if response and response.get("id"):
                return IntegrationResult(
                    success=True,
                    data={"checklist_item": response},
                )
            else:
                return IntegrationResult(
                    success=False,
                    error="Failed to add checklist item",
                )
        except Exception as e:
            logger.error(f"Failed to add checklist item: {e}")
            return IntegrationResult(success=False, error=str(e))
    
    def _update_checklist_item(self, payload: Dict[str, Any]) -> IntegrationResult:
        """Met à jour un élément de checklist."""
        try:
            item_id = payload.get("item_id")
            checked = payload.get("checked")
            name = payload.get("name")
            
            if not item_id:
                return IntegrationResult(
                    success=False,
                    error="item_id is required",
                )
            
            endpoint = f"checklists/{item_id}"
            
            update_data = {}
            
            if checked is not None:
                update_data["checked"] = str(checked).lower()
            if name:
                update_data["name"] = name
            
            if not update_data:
                return IntegrationResult(
                    success=False,
                    error="No data to update",
                )
            
            response = self._make_request("PUT", endpoint, json=update_data)
            
            if response and response.get("id"):
                return IntegrationResult(
                    success=True,
                    data={"checklist_item": response},
                )
            else:
                return IntegrationResult(
                    success=False,
                    error="Failed to update checklist item",
                )
        except Exception as e:
            logger.error(f"Failed to update checklist item: {e}")
            return IntegrationResult(success=False, error=str(e))
    
    def _add_attachment(self, payload: Dict[str, Any]) -> IntegrationResult:
        """Ajoute une pièce jointe à une carte."""
        try:
            card_id = payload.get("card_id")
            url = payload.get("url")
            file_path = payload.get("file_path")
            name = payload.get("name")
            mime_type = payload.get("mime_type")
            
            if not card_id:
                return IntegrationResult(
                    success=False,
                    error="card_id is required",
                )
            
            if not url and not file_path:
                return IntegrationResult(
                    success=False,
                    error="Either url or file_path is required",
                )
            
            endpoint = f"cards/{card_id}/attachments"
            
            if url:
                # Attacher depuis une URL
                attachment_data = {
                    "url": url,
                }
                if name:
                    attachment_data["name"] = name
                if mime_type:
                    attachment_data["mimeType"] = mime_type
                
                response = self._make_request("POST", endpoint, json=attachment_data)
            elif file_path:
                # Attacher un fichier local
                # Note: Cette implémentation nécessite que le fichier soit accessible
                # Dans une implémentation complète, il faudrait upload le fichier
                return IntegrationResult(
                    success=False,
                    error="Local file attachment not yet implemented",
                )
            else:
                return IntegrationResult(
                    success=False,
                    error="Either url or file_path is required",
                )
            
            if response and response.get("id"):
                return IntegrationResult(
                    success=True,
                    data={"attachment": response},
                )
            else:
                return IntegrationResult(
                    success=False,
                    error="Failed to add attachment",
                )
        except Exception as e:
            logger.error(f"Failed to add attachment: {e}")
            return IntegrationResult(success=False, error=str(e))
    
    def _list_attachments(self, payload: Dict[str, Any]) -> IntegrationResult:
        """Liste les pièces jointes d'une carte."""
        try:
            card_id = payload.get("card_id")
            
            if not card_id:
                return IntegrationResult(
                    success=False,
                    error="card_id is required",
                )
            
            endpoint = f"cards/{card_id}/attachments"
            
            attachments = self._make_request("GET", endpoint)
            
            if attachments and isinstance(attachments, list):
                return IntegrationResult(
                    success=True,
                    data={"attachments": attachments, "count": len(attachments)},
                )
            else:
                return IntegrationResult(
                    success=True,
                    data={"attachments": [], "count": 0},
                )
        except Exception as e:
            logger.error(f"Failed to list attachments: {e}")
            return IntegrationResult(success=False, error=str(e))
    
    def _list_members(self, payload: Dict[str, Any]) -> IntegrationResult:
        """Liste les membres disponibles (pour un tableau ou une organisation)."""
        try:
            board_id = payload.get("board_id")
            organization_id = payload.get("organization_id")
            
            if board_id:
                endpoint = f"boards/{board_id}/members"
            elif organization_id:
                endpoint = f"organizations/{organization_id}/members"
            else:
                endpoint = "members/me"  # Retourne uniquement l'utilisateur courant
            
            members = self._make_request("GET", endpoint)
            
            if members and isinstance(members, list):
                return IntegrationResult(
                    success=True,
                    data={"members": members, "count": len(members)},
                )
            elif members and isinstance(members, dict):
                # Cas où on a récupérer un seul membre
                return IntegrationResult(
                    success=True,
                    data={"members": [members], "count": 1},
                )
            else:
                return IntegrationResult(
                    success=True,
                    data={"members": [], "count": 0},
                )
        except Exception as e:
            logger.error(f"Failed to list members: {e}")
            return IntegrationResult(success=False, error=str(e))
    
    def _add_member_to_card(self, payload: Dict[str, Any]) -> IntegrationResult:
        """Ajoute un membre à une carte."""
        try:
            card_id = payload.get("card_id")
            member_id = payload.get("member_id")
            
            if not card_id:
                return IntegrationResult(
                    success=False,
                    error="card_id is required",
                )
            
            if not member_id:
                return IntegrationResult(
                    success=False,
                    error="member_id is required",
                )
            
            endpoint = f"cards/{card_id}/idMembers"
            
            response = self._make_request(
                "POST", 
                endpoint, 
                json={"value": member_id}
            )
            
            if response and response.get("_value"):
                return IntegrationResult(
                    success=True,
                    data={"member_added": member_id, "card_id": card_id},
                )
            else:
                return IntegrationResult(
                    success=False,
                    error="Failed to add member to card",
                )
        except Exception as e:
            logger.error(f"Failed to add member to card: {e}")
            return IntegrationResult(success=False, error=str(e))
    
    def _remove_member_from_card(self, payload: Dict[str, Any]) -> IntegrationResult:
        """Supprime un membre d'une carte."""
        try:
            card_id = payload.get("card_id")
            member_id = payload.get("member_id")
            
            if not card_id:
                return IntegrationResult(
                    success=False,
                    error="card_id is required",
                )
            
            if not member_id:
                return IntegrationResult(
                    success=False,
                    error="member_id is required",
                )
            
            endpoint = f"cards/{card_id}/idMembers/{member_id}"
            
            response = self._make_request("DELETE", endpoint)
            
            # Une réponse vide indique un succès
            if response is None or response == "":
                return IntegrationResult(
                    success=True,
                    data={"removed": True, "member_id": member_id, "card_id": card_id},
                )
            else:
                return IntegrationResult(
                    success=True,
                    data={"removed": True, "member_id": member_id, "card_id": card_id},
                )
        except Exception as e:
            logger.error(f"Failed to remove member from card: {e}")
            return IntegrationResult(success=False, error=str(e))
    
    def _create_webhook(self, payload: Dict[str, Any]) -> IntegrationResult:
        """Crée un webhook pour un tableau."""
        try:
            board_id = payload.get("board_id")
            callback_url = payload.get("callback_url")
            description = payload.get("description", "Agent World Webhook")
            
            if not board_id:
                return IntegrationResult(
                    success=False,
                    error="board_id is required",
                )
            
            if not callback_url:
                return IntegrationResult(
                    success=False,
                    error="callback_url is required",
                )
            
            endpoint = "webhooks"
            
            webhook_data = {
                "idModel": board_id,
                "description": description,
                "callbackURL": callback_url,
                "active": True,
            }
            
            response = self._make_request("POST", endpoint, json=webhook_data)
            
            if response and response.get("id"):
                return IntegrationResult(
                    success=True,
                    data={"webhook": response},
                )
            else:
                return IntegrationResult(
                    success=False,
                    error="Failed to create webhook",
                )
        except Exception as e:
            logger.error(f"Failed to create webhook: {e}")
            return IntegrationResult(success=False, error=str(e))
    
    def _delete_webhook(self, payload: Dict[str, Any]) -> IntegrationResult:
        """Supprime un webhook."""
        try:
            webhook_id = payload.get("webhook_id")
            
            if not webhook_id:
                return IntegrationResult(
                    success=False,
                    error="webhook_id is required",
                )
            
            endpoint = f"webhooks/{webhook_id}"
            
            response = self._make_request("DELETE", endpoint)
            
            # Une réponse vide indique un succès
            if response is None or response == "":
                return IntegrationResult(
                    success=True,
                    data={"deleted": True, "webhook_id": webhook_id},
                )
            else:
                return IntegrationResult(
                    success=True,
                    data={"deleted": True, "webhook_id": webhook_id},
                )
        except Exception as e:
            logger.error(f"Failed to delete webhook: {e}")
            return IntegrationResult(success=False, error=str(e))
    
    def get_oauth_scopes(self) -> List[str]:
        """Retourne les scopes OAuth1 requis pour Trello."""
        return [
            "read",      # Lecture seule
            "write",     # Lecture et écriture
            "account",   # Accès aux informations de compte
        ]
    
    def get_configuration_schema(self) -> Dict[str, Any]:
        """Retourne le schéma de configuration pour Trello."""
        return {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Nom de l'intégration Trello",
                    "default": "My Trello Integration",
                },
                "description": {
                    "type": "string",
                    "description": "Description de l'intégration",
                    "default": "",
                },
                "settings": {
                    "type": "object",
                    "description": "Paramètres spécifiques Trello",
                    "properties": {
                        "default_board_id": {
                            "type": "string",
                            "description": "ID du tableau par défaut",
                            "default": "",
                        },
                        "default_list_id": {
                            "type": "string",
                            "description": "ID de la liste par défaut",
                            "default": "",
                        },
                        "auto_create_cards": {
                            "type": "boolean",
                            "description": "Créer automatiquement des cartes pour les nouvelles tâches",
                            "default": True,
                        },
                        "card_template": {
                            "type": "object",
                            "description": "Template de carte par défaut",
                            "default": {},
                            "properties": {
                                "labels": {
                                    "type": "array",
                                    "description": "Labels par défaut",
                                    "default": [],
                                },
                                "due_days": {
                                    "type": "number",
                                    "description": "Nombre de jours pour la date d'échéance par défaut",
                                    "default": 7,
                                },
                            },
                        },
                        "notify_on_create": {
                            "type": "boolean",
                            "description": "Notifier les membres quand une carte est créée",
                            "default": True,
                        },
                    },
                },
            },
            "required": ["name"],
        }
