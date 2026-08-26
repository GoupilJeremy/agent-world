# 🔌 Agent World - Base Integration Adapter
# Version: 0.5.0 (Épic 7)
# Description: Classe de base pour tous les adapters d'intégration

"""
Base Integration Adapter for Agent World.

Ce module définit la classe de base abstraite que tous les adapters
d'intégration doivent implémenter. Cela permet une interface standardisée
pour toutes les intégrations externes.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from .integration_types import (
    AuthType,
    IntegrationAction,
    IntegrationConfig,
    IntegrationCredentials,
    IntegrationResult,
    IntegrationType,
)


class BaseIntegrationAdapter(ABC):
    """
    Classe de base abstraite pour les adapters d'intégration.

    Chaque intégration externe (GitHub, Slack, etc.) doit implémenter
    cette classe en fournissant ses propres implémentations des méthodes
    abstraites.

    Attributes:
        type: Type d'intégration (ex: IntegrationType.GITHUB)
        name: Nom affiché de l'intégration
        description: Description de l'intégration
        auth_type: Type d'authentification requis
        supported_actions: Liste des actions supportées
    """

    # Type d'intégration (à redéfinir dans les classes filles)
    type: IntegrationType = IntegrationType.WEBHOOK

    # Nom affiché
    name: str = "Base Integration"

    # Description
    description: str = "Description de base"

    # Type d'authentification
    auth_type: AuthType = AuthType.NONE

    # Actions supportées
    supported_actions: List[str] = []

    # Icone (optionnel, pour l'UI)
    icon: Optional[str] = None

    # Couleur (optionnel, pour l'UI)
    color: Optional[str] = None

    def __init__(self, config: Optional[IntegrationConfig] = None):
        """
        Initialise l'adapter.

        Args:
            config: Configuration de l'intégration (optionnelle)
        """
        self.config = config
        self._initialized = False

        if config:
            self._validate_config(config)

    def _validate_config(self, config: IntegrationConfig) -> bool:
        """
        Valide la configuration de l'intégration.

        Args:
            config: Configuration à valider

        Returns:
            True si la configuration est valide

        Raises:
            ValueError: Si la configuration est invalide
        """
        if config.integration_type != self.type:
            raise ValueError(
                f"Integration type mismatch: expected {self.type.value}, "
                f"got {config.integration_type.value}"
            )

        # Vérifier que les identifiants sont valides si l'intégration est active
        if config.status.value == "active":
            if not config.credentials.is_valid():
                raise ValueError("Invalid or expired credentials")

        return True

    @abstractmethod
    def authenticate(self, credentials: IntegrationCredentials) -> bool:
        """
        Authentifie l'intégration avec les identifiants fournis.

        Args:
            credentials: Identifiants à utiliser pour l'authentification

        Returns:
            True si l'authentification réussit, False sinon
        """
        pass

    @abstractmethod
    def get_authentication_url(self, state: Optional[str] = None) -> str:
        """
        Génère l'URL d'authentification OAuth2 (si applicable).

        Args:
            state: Valeur state pour la sécurité CSRF

        Returns:
            URL d'authentification OAuth2

        Raises:
            NotImplementedError: Si l'intégration n'utilise pas OAuth2
        """
        pass

    @abstractmethod
    def exchange_code_for_token(self, code: str) -> IntegrationCredentials:
        """
        Échange un code d'autorisation OAuth2 contre un token.

        Args:
            code: Code d'autorisation reçu du fournisseur OAuth2

        Returns:
            IntegrationCredentials contenant le token d'accès

        Raises:
            NotImplementedError: Si l'intégration n'utilise pas OAuth2
            ValueError: Si l'échange échoue
        """
        pass

    @abstractmethod
    def refresh_token(self, refresh_token: str) -> IntegrationCredentials:
        """
        Rafraîchit le token d'accès avec un refresh token.

        Args:
            refresh_token: Refresh token à utiliser

        Returns:
            IntegrationCredentials avec les nouveaux tokens

        Raises:
            NotImplementedError: Si l'intégration n'utilise pas OAuth2
            ValueError: Si le rafraîchissement échoue
        """
        pass

    @abstractmethod
    def test_connection(self) -> IntegrationResult:
        """
        Teste la connexion à l'intégration.

        Returns:
            IntegrationResult avec le résultat du test
        """
        pass

    @abstractmethod
    def execute(self, action: IntegrationAction) -> IntegrationResult:
        """
        Exécute une action sur l'intégration.

        Args:
            action: Action à exécuter

        Returns:
            IntegrationResult avec le résultat de l'action

        Raises:
            ValueError: Si l'action n'est pas supportée
        """
        pass

    def is_action_supported(self, action_type: str) -> bool:
        """
        Vérifie si une action est supportée par cette intégration.

        Args:
            action_type: Type d'action à vérifier

        Returns:
            True si l'action est supportée
        """
        return action_type in self.supported_actions

    def get_action_schema(self, action_type: str) -> Dict[str, Any]:
        """
        Retourne le schéma de validation pour une action.

        Args:
            action_type: Type d'action

        Returns:
            Schéma de validation (dictionnaire)

        Raises:
            ValueError: Si l'action n'est pas supportée
        """
        if not self.is_action_supported(action_type):
            raise ValueError(f"Action '{action_type}' is not supported by {self.name}")

        # Par défaut, retourne un schéma vide
        # Les classes filles doivent redéfinir cette méthode
        return {"type": "object", "properties": {}}

    def get_oauth_scopes(self) -> List[str]:
        """
        Retourne les scopes OAuth2 requis pour cette intégration.

        Returns:
            Liste des scopes requis
        """
        return []

    def get_configuration_schema(self) -> Dict[str, Any]:
        """
        Retourne le schéma de configuration pour cette intégration.

        Returns:
            Schéma de configuration
        """
        return {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Nom de l'intégration"},
                "description": {"type": "string", "description": "Description"},
                "settings": {
                    "type": "object",
                    "description": "Paramètres spécifiques à l'intégration",
                    "properties": {},
                },
            },
            "required": ["name"],
        }

    def get_metadata(self) -> Dict[str, Any]:
        """
        Retourne les métadonnées de l'intégration.

        Returns:
            Dictionnaire contenant les métadonnées
        """
        return {
            "type": self.type.value,
            "name": self.name,
            "description": self.description,
            "auth_type": self.auth_type.value,
            "supported_actions": self.supported_actions,
            "icon": self.icon,
            "color": self.color,
        }

    def __repr__(self) -> str:
        """Représentation texte de l'adapter."""
        return f"<{self.__class__.__name__}(type={self.type.value}, name={self.name})>"

    def __str__(self) -> str:
        """Représentation string de l'adapter."""
        return self.name


class IntegrationAdapterError(Exception):
    """Exception levée par les adapters d'intégration."""

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        integration_type: Optional[IntegrationType] = None,
        action_type: Optional[str] = None,
    ):
        """
        Initialise l'exception.

        Args:
            message: Message d'erreur
            error_code: Code d'erreur (optionnel)
            integration_type: Type d'intégration concernée
            action_type: Type d'action concernée
        """
        super().__init__(message)
        self.error_code = error_code
        self.integration_type = integration_type
        self.action_type = action_type

    def to_dict(self) -> Dict[str, Any]:
        """Convertit l'exception en dictionnaire."""
        return {
            "error": str(self),
            "error_code": self.error_code,
            "integration_type": (
                self.integration_type.value if self.integration_type else None
            ),
            "action_type": self.action_type,
        }


class AuthenticationError(IntegrationAdapterError):
    """Exception levée en cas d'erreur d'authentification."""

    def __init__(
        self,
        message: str = "Authentication failed",
        integration_type: Optional[IntegrationType] = None,
    ):
        """Initialise l'exception d'authentification."""
        super().__init__(
            message=message,
            error_code="AUTHENTICATION_ERROR",
            integration_type=integration_type,
        )


class ActionNotSupportedError(IntegrationAdapterError):
    """Exception levée lorsqu'une action n'est pas supportée."""

    def __init__(self, action_type: str, integration_type: IntegrationType):
        """Initialise l'exception."""
        message = f"Action '{action_type}' is not supported by {integration_type.value}"
        super().__init__(
            message=message,
            error_code="ACTION_NOT_SUPPORTED",
            integration_type=integration_type,
            action_type=action_type,
        )


class ConnectionError(IntegrationAdapterError):
    """Exception levée en cas d'erreur de connexion."""

    def __init__(
        self,
        message: str = "Connection failed",
        integration_type: Optional[IntegrationType] = None,
    ):
        """Initialise l'exception de connexion."""
        super().__init__(
            message=message,
            error_code="CONNECTION_ERROR",
            integration_type=integration_type,
        )
