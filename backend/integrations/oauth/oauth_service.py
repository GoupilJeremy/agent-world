# 🔐 Agent World - OAuth Service
# Version: 0.5.0 (Épic 7)
# Description: Service centralisé pour la gestion OAuth2

"""
OAuth Service for Agent World.

Ce service gère de manière centralisée tous les flux OAuth2 pour les
intégrations externes. Il fournit des méthodes pour :
- Générer des URLs d'authentification
- Échanger des codes contre des tokens
- Rafraîchir des tokens
- Valider des tokens
- Stocker et récupérer des états OAuth
"""

import logging
import secrets
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import requests

from ..oauth.oauth_types import (
    DEFAULT_PROVIDER_CONFIGS,
    OAuthProvider,
    OAuthProviderConfig,
    OAuthState,
    OAuthTokenData,
)

logger = logging.getLogger(__name__)


class OAuthStateStore:
    """
    Magasin de stockage pour les états OAuth2.

    Ce magasin stocke les états OAuth générés pour prévenir les attaques CSRF.
    En production, cela devrait utiliser une base de données ou Redis.
    """

    def __init__(self):
        """Initialise le magasin d'états."""
        self._states: Dict[str, OAuthState] = {}
        self._ttl_seconds = 300  # 5 minutes

    def generate_state(
        self,
        provider: OAuthProvider,
        redirect_path: str,
        user_id: Optional[int] = None,
        integration_id: Optional[int] = None,
    ) -> OAuthState:
        """
        Génère un nouvel état OAuth.

        Args:
            provider: Fournisseur OAuth
            redirect_path: Chemin de redirection après authentification
            user_id: ID de l'utilisateur (optionnel)
            integration_id: ID de l'intégration (optionnel)

        Returns:
            Nouveau OAuthState
        """
        state = OAuthState(
            state=secrets.token_urlsafe(32),
            provider=provider,
            redirect_path=redirect_path,
            user_id=user_id,
            integration_id=integration_id,
        )

        self._states[state.state] = state

        # Nettoyer les états expirés
        self._cleanup_expired()

        return state

    def get_state(self, state: str) -> Optional[OAuthState]:
        """
        Récupère un état OAuth.

        Args:
            state: Valeur de l'état à récupérer

        Returns:
            OAuthState si trouvé et valide, None sinon
        """
        stored_state = self._states.get(state)

        if stored_state and stored_state.is_valid(self._ttl_seconds):
            return stored_state

        # Supprimer l'état invalide ou expiré
        if state in self._states:
            del self._states[state]

        return None

    def validate_state(
        self,
        state: str,
        provider: Optional[OAuthProvider] = None,
    ) -> bool:
        """
        Valide un état OAuth.

        Args:
            state: Valeur de l'état à valider
            provider: Fournisseur OAuth attendu (optionnel)

        Returns:
            True si l'état est valide, False sinon
        """
        stored_state = self.get_state(state)

        if stored_state is None:
            return False

        if provider and stored_state.provider != provider:
            return False

        return True

    def remove_state(self, state: str) -> bool:
        """
        Supprime un état OAuth.

        Args:
            state: Valeur de l'état à supprimer

        Returns:
            True si l'état a été supprimé, False s'il n'existait pas
        """
        if state in self._states:
            del self._states[state]
            return True
        return False

    def _cleanup_expired(self):
        """Nettoie les états expirés."""
        now = datetime.utcnow()
        expired_states = [
            state
            for state, oauth_state in self._states.items()
            if (now - oauth_state.created_at).total_seconds() > self._ttl_seconds
        ]

        for state in expired_states:
            del self._states[state]

        if expired_states:
            logger.debug(f"Cleaned up {len(expired_states)} expired OAuth states")

    def clear(self):
        """Efface tous les états."""
        self._states.clear()


class OAuthService:
    """
    Service centralisé pour la gestion OAuth2.

    Ce service gère tous les aspects de l'authentification OAuth2
    pour les intégrations externes.
    """

    def __init__(
        self,
        state_store: Optional[OAuthStateStore] = None,
        provider_configs: Optional[Dict[OAuthProvider, OAuthProviderConfig]] = None,
    ):
        """
        Initialise le service OAuth.

        Args:
            state_store: Magasin d'états (si None, un nouveau sera créé)
            provider_configs: Configuration des fournisseurs (optionnel)
        """
        self.state_store = state_store or OAuthStateStore()
        self.provider_configs = provider_configs or {}
        self._token_cache: Dict[str, OAuthTokenData] = {}

    def get_provider_config(
        self,
        provider: OAuthProvider,
    ) -> OAuthProviderConfig:
        """
        Récupère la configuration d'un fournisseur.

        Args:
            provider: Fournisseur OAuth

        Returns:
            Configuration du fournisseur

        Raises:
            ValueError: Si le fournisseur n'est pas configuré
        """
        # Vérifier d'abord les configurations personnalisées
        if provider in self.provider_configs:
            return self.provider_configs[provider]

        # Sinon, utiliser les configurations par défaut
        if provider in DEFAULT_PROVIDER_CONFIGS:
            return DEFAULT_PROVIDER_CONFIGS[provider]

        raise ValueError(f"Unknown OAuth provider: {provider.value}")

    def set_provider_config(
        self,
        provider: OAuthProvider,
        config: OAuthProviderConfig,
    ):
        """
        Définit la configuration pour un fournisseur.

        Args:
            provider: Fournisseur OAuth
            config: Configuration à appliquer
        """
        self.provider_configs[provider] = config

    def get_authorization_url(
        self,
        provider: OAuthProvider,
        redirect_path: str,
        user_id: Optional[int] = None,
        integration_id: Optional[int] = None,
        scope: Optional[List[str]] = None,
        state: Optional[str] = None,
    ) -> Tuple[str, str]:
        """
        Génère une URL d'autorisation OAuth2.

        Args:
            provider: Fournisseur OAuth
            redirect_path: Chemin de redirection après authentification
            user_id: ID de l'utilisateur (optionnel)
            integration_id: ID de l'intégration (optionnel)
            scope: Scopes à demander (remplace ceux par défaut)
            state: État à utiliser (généré si non fourni)

        Returns:
            Tuple contenant (URL d'autorisation, valeur de l'état)
        """
        config = self.get_provider_config(provider)

        # Utiliser les scopes fournis ou ceux par défaut
        scopes = scope or config.scope

        # Générer un état si non fourni
        if not state:
            oauth_state = self.state_store.generate_state(
                provider=provider,
                redirect_path=redirect_path,
                user_id=user_id,
                integration_id=integration_id,
            )
            state = oauth_state.state
        else:
            # Si un état est fourni, le stocker
            self.state_store.generate_state(
                provider=provider,
                redirect_path=redirect_path,
                user_id=user_id,
                integration_id=integration_id,
            )

        # Construire l'URL d'autorisation
        params = {
            "client_id": config.client_id,
            "redirect_uri": config.redirect_uri,
            "response_type": "code",
            "scope": " ".join(scopes),
            "state": state,
        }

        # Ajouter PKCE si activé
        if config.pkce_enabled:
            code_verifier = secrets.token_urlsafe(64)
            code_challenge = self._generate_pkce_challenge(code_verifier)
            params["code_challenge"] = code_challenge
            params["code_challenge_method"] = "S256"
            # Stocker le code_verifier pour plus tard
            # (En production, utiliser un cache sécurisé)

        # Construire l'URL
        from urllib.parse import urlencode

        authorization_url = f"{config.authorization_url}?{urlencode(params)}"

        return authorization_url, state

    def exchange_code_for_token(
        self,
        provider: OAuthProvider,
        code: str,
        redirect_uri: Optional[str] = None,
        state: Optional[str] = None,
    ) -> OAuthTokenData:
        """
        Échange un code d'autorisation contre un token.

        Args:
            provider: Fournisseur OAuth
            code: Code d'autorisation reçu
            redirect_uri: URI de redirection (optionnel, utilise celle de la config)
            state: État reçu (pour validation CSRF)

        Returns:
            OAuthTokenData avec le token

        Raises:
            ValueError: Si l'échange échoue ou si l'état est invalide
        """
        # Valider l'état si fourni
        if state:
            if not self.state_store.validate_state(state, provider):
                raise ValueError("Invalid OAuth state - possible CSRF attack")
            # Supprimer l'état après utilisation
            self.state_store.remove_state(state)

        config = self.get_provider_config(provider)

        # Utiliser l'URI de redirection de la config si non fourni
        use_redirect_uri = redirect_uri or config.redirect_uri

        # Échanger le code contre un token
        data = {
            "client_id": config.client_id,
            "client_secret": config.client_secret,
            "code": code,
            "redirect_uri": use_redirect_uri,
            "grant_type": "authorization_code",
        }

        try:
            response = requests.post(
                config.token_url,
                data=data,
                headers={"Accept": "application/json"},
                timeout=30,
            )

            if response.status_code != 200:
                error_msg = f"OAuth token exchange failed: {response.status_code}"
                try:
                    error_msg += f" - {response.json()}"
                except Exception:
                    error_msg += f" - {response.text}"
                raise ValueError(error_msg)

            token_data = response.json()

            # Extraire les informations du token
            access_token = token_data.get("access_token")
            if not access_token:
                raise ValueError("No access token received")

            return OAuthTokenData(
                access_token=access_token,
                token_type=token_data.get("token_type", "Bearer"),
                expires_in=token_data.get("expires_in"),
                refresh_token=token_data.get("refresh_token"),
                scope=token_data.get("scope"),
            )

        except requests.exceptions.RequestException as e:
            logger.error(f"OAuth token exchange failed: {e}")
            raise ValueError(f"OAuth token exchange failed: {e}")

    def refresh_access_token(
        self,
        provider: OAuthProvider,
        refresh_token: str,
    ) -> OAuthTokenData:
        """
        Rafraîchit un token d'accès avec un refresh token.

        Args:
            provider: Fournisseur OAuth
            refresh_token: Refresh token à utiliser

        Returns:
            OAuthTokenData avec les nouveaux tokens

        Raises:
            ValueError: Si le rafraîchissement échoue
            NotImplementedError: Si le fournisseur ne supporte pas le refresh
        """
        config = self.get_provider_config(provider)

        if not config.refresh_token_enabled:
            raise NotImplementedError(
                f"Provider {provider.value} does not support token refresh"
            )

        data = {
            "client_id": config.client_id,
            "client_secret": config.client_secret,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        }

        try:
            response = requests.post(
                config.token_url,
                data=data,
                headers={"Accept": "application/json"},
                timeout=30,
            )

            if response.status_code != 200:
                error_msg = f"Token refresh failed: {response.status_code}"
                try:
                    error_msg += f" - {response.json()}"
                except Exception:
                    error_msg += f" - {response.text}"
                raise ValueError(error_msg)

            token_data = response.json()

            access_token = token_data.get("access_token")
            if not access_token:
                raise ValueError("No access token received on refresh")

            return OAuthTokenData(
                access_token=access_token,
                token_type=token_data.get("token_type", "Bearer"),
                expires_in=token_data.get("expires_in"),
                refresh_token=token_data.get("refresh_token", refresh_token),
                scope=token_data.get("scope"),
            )

        except requests.exceptions.RequestException as e:
            logger.error(f"Token refresh failed: {e}")
            raise ValueError(f"Token refresh failed: {e}")

    def get_user_info(
        self,
        provider: OAuthProvider,
        access_token: str,
    ) -> Dict[str, Any]:
        """
        Récupère les informations utilisateur d'un fournisseur.

        Args:
            provider: Fournisseur OAuth
            access_token: Token d'accès

        Returns:
            Informations utilisateur

        Raises:
            ValueError: Si la récupération échoue
        """
        config = self.get_provider_config(provider)

        if not config.userinfo_url:
            raise ValueError(f"Provider {provider.value} does not support user info")

        try:
            response = requests.get(
                config.userinfo_url,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/json",
                },
                timeout=30,
            )

            if response.status_code != 200:
                error_msg = f"Failed to get user info: {response.status_code}"
                try:
                    error_msg += f" - {response.json()}"
                except Exception:
                    error_msg += f" - {response.text}"
                raise ValueError(error_msg)

            return response.json()

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get user info: {e}")
            raise ValueError(f"Failed to get user info: {e}")

    def validate_token(
        self,
        provider: OAuthProvider,
        access_token: str,
    ) -> bool:
        """
        Valide un token d'accès.

        Args:
            provider: Fournisseur OAuth
            access_token: Token à valider

        Returns:
            True si le token est valide
        """
        try:
            self.get_user_info(provider, access_token)
            return True
        except Exception:
            return False

    @staticmethod
    def _generate_pkce_challenge(code_verifier: str) -> str:
        """
        Génère un code challenge PKCE à partir d'un code verifier.

        Args:
            code_verifier: Code verifier PKCE

        Returns:
            Code challenge base64 URL-safe
        """
        import hashlib

        # Hash SHA256 du code verifier
        sha256 = hashlib.sha256(code_verifier.encode()).digest()

        # Encoder en base64 URL-safe (sans padding)
        import base64

        challenge = base64.urlsafe_b64encode(sha256).decode()
        return challenge.rstrip("=")

    def get_all_providers(self) -> List[OAuthProvider]:
        """
        Récupère tous les fournisseurs OAuth configurés.

        Returns:
            Liste des fournisseurs OAuth
        """
        all_providers = []

        # Ajouter les fournisseurs avec configuration personnalisée
        for provider in self.provider_configs.keys():
            if provider not in all_providers:
                all_providers.append(provider)

        # Ajouter les fournisseurs par défaut non encore ajoutés
        for provider in DEFAULT_PROVIDER_CONFIGS.keys():
            if provider not in all_providers:
                all_providers.append(provider)

        return all_providers

    def get_provider_metadata(self, provider: OAuthProvider) -> Dict[str, Any]:
        """
        Récupère les métadonnées d'un fournisseur.

        Args:
            provider: Fournisseur OAuth

        Returns:
            Dictionnaire des métadonnées
        """
        config = self.get_provider_config(provider)

        return {
            "provider": provider.value,
            "name": provider.value.title(),
            "authorization_url": config.authorization_url,
            "token_url": config.token_url,
            "scopes": config.scope,
            "refresh_token_supported": config.refresh_token_enabled,
        }
