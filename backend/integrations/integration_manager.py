# 🎯 Agent World - Integration Manager
# Version: 0.5.0 (Épic 7)
# Description: Service central pour gérer toutes les intégrations

"""
Integration Manager for Agent World.

Ce service est le point central pour gérer toutes les intégrations externes.
Il permet de :
- Créer, lister, mettre à jour et supprimer des configurations d'intégration
- Exécuter des actions sur les intégrations
- Gérer l'authentification OAuth2
- Distribuer les événements aux intégrations appropriées
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Type

from .adapters import ADAPTER_REGISTRY, BaseIntegrationAdapter

# Importer les adapters pour qu'ils s'enregistrent
try:
    from .adapters import GitHubIntegrationAdapter  # noqa: F401
except ImportError:
    pass

try:
    from .adapters import SlackIntegrationAdapter  # noqa: F401
except ImportError:
    pass

try:
    from .adapters import DiscordIntegrationAdapter  # noqa: F401
except ImportError:
    pass

from .base_adapter import (
    AuthenticationError,
    ConnectionError,
    IntegrationAdapterError,
)
from .integration_types import (
    IntegrationAction,
    IntegrationConfig,
    IntegrationCredentials,
    IntegrationResult,
    IntegrationStatus,
    IntegrationType,
)
from .oauth.oauth_service import OAuthService
from .oauth.oauth_types import OAuthProvider, OAuthTokenData
from .webhooks.webhook_service import WebhookService
from .webhooks.webhook_types import WebhookEvent

logger = logging.getLogger(__name__)


class IntegrationManager:
    """
    Gestionnaire central pour toutes les intégrations externes.
    
    Ce service fournit une interface unifiée pour interagir avec
    toutes les intégrations supportées (GitHub, Slack, Discord, etc.).
    """
    
    def __init__(
        self,
        oauth_service: Optional[OAuthService] = None,
        webhook_service: Optional[WebhookService] = None,
    ):
        """
        Initialise le gestionnaire d'intégrations.
        
        Args:
            oauth_service: Service OAuth2 (si None, un nouveau sera créé)
            webhook_service: Service Webhook (si None, un nouveau sera créé)
        """
        self.oauth_service = oauth_service or OAuthService()
        self.webhook_service = webhook_service or WebhookService()
        
        # Cache des adapters instanciés (integration_id -> adapter)
        self._adapter_cache: Dict[int, BaseIntegrationAdapter] = {}
        
        # Registre des configurations (integration_id -> IntegrationConfig)
        self._configurations: Dict[int, IntegrationConfig] = {}
        
        # ID auto-incrémenté pour les intégrations (en mémoire)
        self._next_integration_id = 1
    
    # ==================== Configuration Management ====================
    
    def create_integration(
        self,
        integration_type: IntegrationType,
        name: str,
        user_id: Optional[int] = None,
        description: str = "",
        credentials: Optional[IntegrationCredentials] = None,
        settings: Optional[Dict[str, Any]] = None,
    ) -> IntegrationConfig:
        """
        Crée une nouvelle configuration d'intégration.
        
        Args:
            integration_type: Type d'intégration
            name: Nom de l'intégration
            user_id: ID de l'utilisateur propriétaire (optionnel)
            description: Description de l'intégration
            credentials: Identifiants de connexion (optionnel)
            settings: Paramètres spécifiques (optionnel)
            
        Returns:
            IntegrationConfig créée
        """
        integration_id = self._next_integration_id
        self._next_integration_id += 1
        
        config = IntegrationConfig(
            id=integration_id,
            user_id=user_id,
            integration_type=integration_type,
            name=name,
            description=description,
            credentials=credentials or IntegrationCredentials(),
            settings=settings or {},
            status=IntegrationStatus.INACTIVE,
        )
        
        # Si des credentials sont fournis, tester la connexion
        if config.credentials.is_valid():
            try:
                adapter = self._get_adapter(integration_type, config)
                test_result = adapter.test_connection()
                if test_result.success:
                    config.status = IntegrationStatus.ACTIVE
            except Exception as e:
                logger.warning(f"Failed to test connection for {name}: {e}")
                config.status = IntegrationStatus.ERROR
        
        self._configurations[integration_id] = config
        
        logger.info(f"Created integration: {name} (ID: {integration_id}, Type: {integration_type.value})")
        
        return config
    
    def get_integration(self, integration_id: int) -> Optional[IntegrationConfig]:
        """
        Récupère une configuration d'intégration.
        
        Args:
            integration_id: ID de l'intégration
            
        Returns:
            IntegrationConfig ou None
        """
        return self._configurations.get(integration_id)
    
    def list_integrations(
        self,
        user_id: Optional[int] = None,
        integration_type: Optional[IntegrationType] = None,
        status: Optional[IntegrationStatus] = None,
    ) -> List[IntegrationConfig]:
        """
        Liste les configurations d'intégration.
        
        Args:
            user_id: ID de l'utilisateur pour filtrer (optionnel)
            integration_type: Type d'intégration pour filtrer (optionnel)
            status: Statut pour filtrer (optionnel)
            
        Returns:
            Liste des configurations
        """
        result = []
        
        for config in self._configurations.values():
            # Filtrer par utilisateur
            if user_id is not None and config.user_id != user_id:
                continue
            
            # Filtrer par type
            if integration_type is not None and config.integration_type != integration_type:
                continue
            
            # Filtrer par statut
            if status is not None and config.status != status:
                continue
            
            result.append(config)
        
        return result
    
    def update_integration(
        self,
        integration_id: int,
        **kwargs,
    ) -> Optional[IntegrationConfig]:
        """
        Met à jour une configuration d'intégration.
        
        Args:
            integration_id: ID de l'intégration
            **kwargs: Attributs à mettre à jour
            
        Returns:
            IntegrationConfig mise à jour ou None
        """
        config = self._configurations.get(integration_id)
        
        if not config:
            return None
        
        for key, value in kwargs.items():
            if hasattr(config, key):
                setattr(config, key, value)
        
        config.updated_at = datetime.utcnow()
        
        # Nettoyer le cache de l'adapter
        if integration_id in self._adapter_cache:
            del self._adapter_cache[integration_id]
        
        return config
    
    def delete_integration(self, integration_id: int) -> bool:
        """
        Supprime une configuration d'intégration.
        
        Args:
            integration_id: ID de l'intégration
            
        Returns:
            True si supprimée, False sinon
        """
        if integration_id in self._configurations:
            del self._configurations[integration_id]
            
            # Nettoyer le cache de l'adapter
            if integration_id in self._adapter_cache:
                del self._adapter_cache[integration_id]
            
            logger.info(f"Deleted integration: {integration_id}")
            return True
        return False
    
    def activate_integration(self, integration_id: int) -> bool:
        """
        Active une intégration.
        
        Args:
            integration_id: ID de l'intégration
            
        Returns:
            True si activée, False sinon
        """
        config = self._configurations.get(integration_id)
        
        if config:
            # Tester la connexion avant d'activer
            try:
                adapter = self._get_adapter(config.integration_type, config)
                test_result = adapter.test_connection()
                
                if test_result.success:
                    config.status = IntegrationStatus.ACTIVE
                    config.last_used_at = datetime.utcnow()
                    return True
                else:
                    config.status = IntegrationStatus.ERROR
                    logger.warning(f"Failed to activate integration {integration_id}: {test_result.error}")
            except Exception as e:
                config.status = IntegrationStatus.ERROR
                logger.error(f"Failed to activate integration {integration_id}: {e}")
        
        return False
    
    def deactivate_integration(self, integration_id: int) -> bool:
        """
        Désactive une intégration.
        
        Args:
            integration_id: ID de l'intégration
            
        Returns:
            True si désactivée, False sinon
        """
        config = self._configurations.get(integration_id)
        
        if config:
            config.status = IntegrationStatus.INACTIVE
            return True
        return False
    
    # ==================== Adapter Management ====================
    
    def get_adapter(
        self,
        integration_id: int,
    ) -> Optional[BaseIntegrationAdapter]:
        """
        Récupère l'adapter pour une intégration.
        
        Args:
            integration_id: ID de l'intégration
            
        Returns:
            Adapter ou None
        """
        config = self._configurations.get(integration_id)
        
        if not config:
            return None
        
        return self._get_adapter(config.integration_type, config)
    
    def _get_adapter(
        self,
        integration_type: IntegrationType,
        config: IntegrationConfig,
    ) -> BaseIntegrationAdapter:
        """
        Récupère ou crée un adapter pour une intégration.
        
        Args:
            integration_type: Type d'intégration
            config: Configuration de l'intégration
            
        Returns:
            Adapter
        """
        # Vérifier le cache
        if config.id in self._adapter_cache:
            return self._adapter_cache[config.id]
        
        # Obtenir la classe de l'adapter depuis le registre
        adapter_class = ADAPTER_REGISTRY.get(integration_type.value)
        
        if not adapter_class:
            raise ValueError(f"No adapter registered for integration type: {integration_type.value}")
        
        # Créer une nouvelle instance
        adapter = adapter_class(config)
        
        # Mettre en cache
        if config.id:
            self._adapter_cache[config.id] = adapter
        
        return adapter
    
    # ==================== Action Execution ====================
    
    def execute_action(
        self,
        integration_id: int,
        action: IntegrationAction,
    ) -> IntegrationResult:
        """
        Exécute une action sur une intégration.
        
        Args:
            integration_id: ID de l'intégration
            action: Action à exécuter
            
        Returns:
            IntegrationResult avec le résultat de l'action
        """
        adapter = self.get_adapter(integration_id)
        
        if not adapter:
            return IntegrationResult(
                success=False,
                error=f"Integration {integration_id} not found",
            )
        
        config = self._configurations.get(integration_id)
        
        try:
            # Exécuter l'action
            result = adapter.execute(action)
            
            # Mettre à jour les statistiques
            if config:
                config.usage_count += 1
                config.last_used_at = datetime.utcnow()
            
            return result
            
        except IntegrationAdapterError as e:
            logger.error(f"Integration error: {e}")
            if config:
                config.error_count += 1
            return IntegrationResult(
                success=False,
                error=str(e),
                error_code=e.error_code,
            )
        except Exception as e:
            logger.error(f"Unexpected error executing action: {e}")
            if config:
                config.error_count += 1
            return IntegrationResult(
                success=False,
                error=str(e),
                error_code="INTERNAL_ERROR",
            )
    
    # ==================== OAuth2 Management ====================
    
    def get_oauth_authorization_url(
        self,
        integration_type: IntegrationType,
        integration_id: Optional[int] = None,
        user_id: Optional[int] = None,
        state: Optional[str] = None,
        scope: Optional[List[str]] = None,
    ) -> Tuple[str, str]:
        """
        Génère une URL d'autorisation OAuth2 pour une intégration.
        
        Args:
            integration_type: Type d'intégration
            integration_id: ID de l'intégration (optionnel)
            user_id: ID de l'utilisateur (optionnel)
            state: État CSRF (généré si non fourni)
            scope: Scopes à demander (optionnel)
            
        Returns:
            Tuple contenant (URL d'autorisation, valeur de l'état)
        """
        # Mapper le type d'intégration au fournisseur OAuth
        provider_mapping = {
            IntegrationType.GITHUB: OAuthProvider.GITHUB,
            IntegrationType.SLACK: OAuthProvider.SLACK,
            IntegrationType.DISCORD: OAuthProvider.DISCORD,
            IntegrationType.NOTION: OAuthProvider.NOTION,
            IntegrationType.GOOGLE_DRIVE: OAuthProvider.GOOGLE,
            IntegrationType.TRELLO: OAuthProvider.TRELLO,
        }
        
        provider = provider_mapping.get(integration_type)
        
        if not provider:
            raise ValueError(f"No OAuth provider mapping for {integration_type.value}")
        
        redirect_path = f"/api/integrations/{integration_type.value}/callback"
        
        return self.oauth_service.get_authorization_url(
            provider=provider,
            redirect_path=redirect_path,
            user_id=user_id,
            integration_id=integration_id,
            scope=scope,
            state=state,
        )
    
    def exchange_oauth_code(
        self,
        integration_type: IntegrationType,
        code: str,
        state: Optional[str] = None,
    ) -> IntegrationCredentials:
        """
        Échange un code OAuth2 contre des credentials.
        
        Args:
            integration_type: Type d'intégration
            code: Code d'autorisation
            state: État CSRF
            
        Returns:
            IntegrationCredentials avec les tokens
        """
        # Mapper le type d'intégration au fournisseur OAuth
        provider_mapping = {
            IntegrationType.GITHUB: OAuthProvider.GITHUB,
            IntegrationType.SLACK: OAuthProvider.SLACK,
            IntegrationType.DISCORD: OAuthProvider.DISCORD,
            IntegrationType.NOTION: OAuthProvider.NOTION,
            IntegrationType.GOOGLE_DRIVE: OAuthProvider.GOOGLE,
            IntegrationType.TRELLO: OAuthProvider.TRELLO,
        }
        
        provider = provider_mapping.get(integration_type)
        
        if not provider:
            raise ValueError(f"No OAuth provider mapping for {integration_type.value}")
        
        token_data = self.oauth_service.exchange_code_for_token(
            provider=provider,
            code=code,
            state=state,
        )
        
        return IntegrationCredentials(
            access_token=token_data.access_token,
            refresh_token=token_data.refresh_token,
            token_expiry=token_data.expiry,
        )
    
    def refresh_oauth_token(
        self,
        integration_id: int,
    ) -> bool:
        """
        Rafraîchit le token OAuth2 d'une intégration.
        
        Args:
            integration_id: ID de l'intégration
            
        Returns:
            True si rafraîchi avec succès
        """
        config = self._configurations.get(integration_id)
        
        if not config or not config.credentials.refresh_token:
            return False
        
        try:
            # Mapper le type d'intégration au fournisseur OAuth
            provider_mapping = {
                IntegrationType.GITHUB: OAuthProvider.GITHUB,
                IntegrationType.SLACK: OAuthProvider.SLACK,
                IntegrationType.DISCORD: OAuthProvider.DISCORD,
                IntegrationType.NOTION: OAuthProvider.NOTION,
                IntegrationType.GOOGLE_DRIVE: OAuthProvider.GOOGLE,
                IntegrationType.TRELLO: OAuthProvider.TRELLO,
            }
            
            provider = provider_mapping.get(config.integration_type)
            
            if not provider:
                return False
            
            token_data = self.oauth_service.refresh_access_token(
                provider=provider,
                refresh_token=config.credentials.refresh_token,
            )
            
            # Mettre à jour les credentials
            config.credentials.access_token = token_data.access_token
            config.credentials.refresh_token = token_data.refresh_token
            config.credentials.token_expiry = token_data.expiry
            config.updated_at = datetime.utcnow()
            
            logger.info(f"Refreshed OAuth token for integration {integration_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to refresh OAuth token: {e}")
            return False
    
    # ==================== Webhook Management ====================
    
    def emit_webhook_event(
        self,
        event: WebhookEvent,
        integration_id: Optional[int] = None,
    ) -> List[Any]:
        """
        Émet un événement webhook.
        
        Args:
            event: Événement à émettre
            integration_id: ID de l'intégration (optionnel)
            
        Returns:
            Liste des réponses
        """
        if integration_id:
            config = self._configurations.get(integration_id)
            if config:
                # Émettre vers une intégration spécifique
                response = self.webhook_service.emit_to_integration(event, config)
                return [response]
        else:
            # Émettre vers tous les abonnements concernés
            return self.webhook_service.emit_event(event)
    
    def register_webhook_handler(
        self,
        event_type: str,
        handler: Any,
    ):
        """
        Enregistre un handler pour un type d'événement webhook.
        
        Args:
            event_type: Type d'événement
            handler: Fonction handler
        """
        self.webhook_service.register_incoming_handler(event_type, handler)
    
    # ==================== Integration Discovery ====================
    
    def get_supported_integrations(self) -> List[Dict[str, Any]]:
        """
        Récupère la liste des intégrations supportées.
        
        Returns:
            Liste des informations sur les intégrations supportées
        """
        supported = []
        
        for integration_type in IntegrationType:
            adapter_class = ADAPTER_REGISTRY.get(integration_type.value)
            
            if adapter_class:
                # Créer une instance temporaire pour obtenir les métadonnées
                try:
                    temp_adapter = adapter_class()
                    supported.append({
                        "type": integration_type.value,
                        "name": temp_adapter.name,
                        "description": temp_adapter.description,
                        "auth_type": temp_adapter.auth_type.value,
                        "icon": temp_adapter.icon,
                        "color": temp_adapter.color,
                        "supported_actions": temp_adapter.supported_actions,
                    })
                except Exception as e:
                    logger.warning(f"Failed to get metadata for {integration_type.value}: {e}")
                    supported.append({
                        "type": integration_type.value,
                        "name": integration_type.value.title(),
                        "description": f"Integration with {integration_type.value}",
                        "auth_type": "unknown",
                        "supported_actions": [],
                    })
        
        return supported
    
    def get_integration_metadata(
        self,
        integration_type: IntegrationType,
    ) -> Dict[str, Any]:
        """
        Récupère les métadonnées d'une intégration.
        
        Args:
            integration_type: Type d'intégration
            
        Returns:
            Métadonnées de l'intégration
        """
        adapter_class = ADAPTER_REGISTRY.get(integration_type.value)
        
        if not adapter_class:
            return {
                "error": f"Unknown integration type: {integration_type.value}",
            }
        
        try:
            temp_adapter = adapter_class()
            return {
                "type": integration_type.value,
                "name": temp_adapter.name,
                "description": temp_adapter.description,
                "auth_type": temp_adapter.auth_type.value,
                "icon": temp_adapter.icon,
                "color": temp_adapter.color,
                "supported_actions": temp_adapter.supported_actions,
                "configuration_schema": temp_adapter.get_configuration_schema(),
                "oauth_scopes": temp_adapter.get_oauth_scopes(),
            }
        except Exception as e:
            logger.error(f"Failed to get metadata for {integration_type.value}: {e}")
            return {
                "error": str(e),
            }
    
    def get_action_schema(
        self,
        integration_type: IntegrationType,
        action_type: str,
    ) -> Dict[str, Any]:
        """
        Récupère le schéma d'une action pour une intégration.
        
        Args:
            integration_type: Type d'intégration
            action_type: Type d'action
            
        Returns:
            Schéma de l'action
        """
        adapter_class = ADAPTER_REGISTRY.get(integration_type.value)
        
        if not adapter_class:
            return {"error": f"Unknown integration type: {integration_type.value}"}
        
        try:
            temp_adapter = adapter_class()
            return temp_adapter.get_action_schema(action_type)
        except Exception as e:
            return {"error": str(e)}
    
    # ==================== Statistics ====================
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Récupère les statistiques des intégrations.
        
        Returns:
            Statistiques des intégrations
        """
        total_integrations = len(self._configurations)
        active_integrations = sum(
            1 for c in self._configurations.values()
            if c.status == IntegrationStatus.ACTIVE
        )
        total_actions = sum(
            c.usage_count for c in self._configurations.values()
        )
        total_errors = sum(
            c.error_count for c in self._configurations.values()
        )
        
        return {
            "total_integrations": total_integrations,
            "active_integrations": active_integrations,
            "total_actions": total_actions,
            "total_errors": total_errors,
            "success_rate": total_actions / (total_actions + total_errors) if (total_actions + total_errors) > 0 else 0,
            "webhook_stats": self.webhook_service.get_statistics(),
        }
    
    def cleanup(self):
        """Nettoie les ressources."""
        self._adapter_cache.clear()
        self._configurations.clear()
        self.oauth_service.cleanup()
        self.webhook_service.cleanup()


# Importer datetime au niveau module
from datetime import datetime
