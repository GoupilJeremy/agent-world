# 🎣 Agent World - Webhook Service
# Version: 0.5.0 (Épic 7 - US-053)
# Description: Service pour gérer les webhooks entrants et sortants

"""
Webhook Service for Agent World.

Ce service gère :
- L'enregistrement et la gestion des webhooks sortants
- La réception et le traitement des webhooks entrants
- La validation des signatures
- La distribution des événements aux handlers appropriés
"""

import hashlib
import hmac
import json
import logging
import secrets
from typing import Any, Callable, Dict, List, Optional, Tuple

import requests

from ..integration_types import IntegrationConfig, IntegrationType
from .webhook_types import (
    WebhookEvent,
    WebhookEventType,
    WebhookPayload,
    WebhookResponse,
    WebhookStatus,
    WebhookSubscription,
)

logger = logging.getLogger(__name__)


# Type alias pour les handlers de webhook
WebhookHandler = Callable[[WebhookPayload, IntegrationConfig], WebhookResponse]


class WebhookService:
    """
    Service pour gérer les webhooks.
    
    Ce service permet :
    - D'enregistrer des webhooks sortants
    - De recevoir et traiter des webhooks entrants
    - De valider les signatures
    - De distribuer les événements aux handlers appropriés
    """
    
    def __init__(self):
        """Initialise le service de webhooks."""
        # Abonnements webhooks (webhook_id -> WebhookSubscription)
        self._subscriptions: Dict[str, WebhookSubscription] = {}
        
        # Handlers pour les événements entrants (event_type -> list of handlers)
        self._incoming_handlers: Dict[str, List[WebhookHandler]] = {}
        
        # Handlers pour les événements sortants (integration_type -> handler)
        self._outgoing_handlers: Dict[str, WebhookHandler] = {}
        
        # Secrets pour la signature des webhooks sortants
        self._webhook_secrets: Dict[str, str] = {}
    
    def create_subscription(
        self,
        name: str,
        url: str,
        events: List[str],
        secret: Optional[str] = None,
        integration_type: Optional[IntegrationType] = None,
    ) -> WebhookSubscription:
        """
        Crée un nouvel abonnement webhook.
        
        Args:
            name: Nom de l'abonnement
            url: URL du endpoint webhook
            events: Liste des types d'événements à abonner
            secret: Secret partagé (généré si non fourni)
            integration_type: Type d'intégration associé
            
        Returns:
            WebhookSubscription créé
        """
        # Générer un secret si non fourni
        if not secret:
            secret = secrets.token_urlsafe(32)
        
        # Générer un ID unique
        webhook_id = secrets.token_urlsafe(16)
        
        subscription = WebhookSubscription(
            id=None,  # L'ID sera attribué par la base de données
            name=name,
            url=url,
            events=events,
            secret=secret,
            active=True,
            status=WebhookStatus.ACTIVE,
        )
        
        # Stocker le secret
        self._webhook_secrets[webhook_id] = secret
        
        # Stocker l'abonnement
        self._subscriptions[webhook_id] = subscription
        
        # Si c'est pour une intégration spécifique, enregistrer le handler
        if integration_type:
            self.register_outgoing_handler(
                integration_type.value,
                self._default_integration_handler,
            )
        
        logger.info(f"Created webhook subscription: {name} ({webhook_id})")
        
        return subscription
    
    def get_subscription(self, webhook_id: str) -> Optional[WebhookSubscription]:
        """
        Récupère un abonnement webhook.
        
        Args:
            webhook_id: ID de l'abonnement
            
        Returns:
            WebhookSubscription ou None
        """
        return self._subscriptions.get(webhook_id)
    
    def list_subscriptions(self) -> List[WebhookSubscription]:
        """
        Liste tous les abonnements webhook.
        
        Returns:
            Liste des abonnements
        """
        return list(self._subscriptions.values())
    
    def update_subscription(
        self,
        webhook_id: str,
        **kwargs,
    ) -> Optional[WebhookSubscription]:
        """
        Met à jour un abonnement webhook.
        
        Args:
            webhook_id: ID de l'abonnement
            **kwargs: Attributs à mettre à jour
            
        Returns:
            WebhookSubscription mis à jour ou None
        """
        subscription = self._subscriptions.get(webhook_id)
        
        if not subscription:
            return None
        
        for key, value in kwargs.items():
            if hasattr(subscription, key):
                setattr(subscription, key, value)
        
        subscription.updated_at = datetime.now()
        
        return subscription
    
    def delete_subscription(self, webhook_id: str) -> bool:
        """
        Supprime un abonnement webhook.
        
        Args:
            webhook_id: ID de l'abonnement
            
        Returns:
            True si supprimé, False sinon
        """
        if webhook_id in self._subscriptions:
            del self._subscriptions[webhook_id]
            return True
        return False
    
    def activate_subscription(self, webhook_id: str) -> bool:
        """
        Active un abonnement webhook.
        
        Args:
            webhook_id: ID de l'abonnement
            
        Returns:
            True si activé, False sinon
        """
        subscription = self._subscriptions.get(webhook_id)
        
        if subscription:
            subscription.active = True
            subscription.status = WebhookStatus.ACTIVE
            return True
        return False
    
    def deactivate_subscription(self, webhook_id: str) -> bool:
        """
        Désactive un abonnement webhook.
        
        Args:
            webhook_id: ID de l'abonnement
            
        Returns:
            True si désactivé, False sinon
        """
        subscription = self._subscriptions.get(webhook_id)
        
        if subscription:
            subscription.active = False
            subscription.status = WebhookStatus.INACTIVE
            return True
        return False
    
    def register_incoming_handler(
        self,
        event_type: str,
        handler: WebhookHandler,
    ):
        """
        Enregistre un handler pour les événements entrants.
        
        Args:
            event_type: Type d'événement à gérer
            handler: Fonction handler
        """
        if event_type not in self._incoming_handlers:
            self._incoming_handlers[event_type] = []
        
        self._incoming_handlers[event_type].append(handler)
        logger.debug(f"Registered handler for event: {event_type}")
    
    def register_outgoing_handler(
        self,
        integration_type: str,
        handler: WebhookHandler,
    ):
        """
        Enregistre un handler pour les webhooks sortants.
        
        Args:
            integration_type: Type d'intégration
            handler: Fonction handler
        """
        self._outgoing_handlers[integration_type] = handler
        logger.debug(f"Registered outgoing handler for: {integration_type}")
    
    def unregister_handler(
        self,
        event_type: str,
        handler: WebhookHandler,
    ) -> bool:
        """
        Désenregistre un handler.
        
        Args:
            event_type: Type d'événement
            handler: Fonction handler à supprimer
            
        Returns:
            True si supprimé, False sinon
        """
        if event_type in self._incoming_handlers:
            try:
                self._incoming_handlers[event_type].remove(handler)
                return True
            except ValueError:
                pass
        return False
    
    def emit_event(
        self,
        event: WebhookEvent,
        integration_config: Optional[IntegrationConfig] = None,
    ) -> List[WebhookResponse]:
        """
        Émet un événement vers tous les abonnements concernés.
        
        Args:
            event: Événement à émettre
            integration_config: Configuration d'intégration (optionnelle)
            
        Returns:
            Liste des réponses des webhooks
        """
        responses = []
        
        # Trouver les abonnements intéressés par cet événement
        for subscription in self._subscriptions.values():
            if not subscription.active:
                continue
            
            # Vérifier si l'événement est dans la liste des événements abonnés
            if "*" in subscription.events or event.event_type in subscription.events:
                # Envoyer l'événement au webhook
                response = self._send_webhook(subscription, event, integration_config)
                responses.append(response)
        
        return responses
    
    def emit_to_integration(
        self,
        event: WebhookEvent,
        integration_config: IntegrationConfig,
    ) -> WebhookResponse:
        """
        Émet un événement vers une intégration spécifique.
        
        Args:
            event: Événement à émettre
            integration_config: Configuration de l'intégration
            
        Returns:
            Réponse du webhook
        """
        # Trouver le handler pour ce type d'intégration
        handler = self._outgoing_handlers.get(integration_config.integration_type.value)
        
        if handler:
            # Créer un payload
            payload = WebhookPayload(
                body=event.to_dict(),
                webhook_id=integration_config.credentials.webhook_url,
                webhook_secret=integration_config.credentials.webhook_secret,
            )
            
            return handler(payload, integration_config)
        else:
            # Par défaut, envoyer directement au webhook URL
            return self._send_to_url(
                integration_config.credentials.webhook_url,
                event,
                integration_config.credentials.webhook_secret,
            )
    
    def handle_incoming_webhook(
        self,
        payload: WebhookPayload,
        integration_config: Optional[IntegrationConfig] = None,
    ) -> WebhookResponse:
        """
        Traite un webhook entrant.
        
        Args:
            payload: Payload du webhook
            integration_config: Configuration d'intégration (optionnelle)
            
        Returns:
            Réponse du traitement
        """
        # Extraire le type d'événement
        event_type = payload.body.get("event_type", "custom")
        
        # Trouver les handlers pour ce type d'événement
        handlers = self._incoming_handlers.get(event_type, [])
        
        if not handlers:
            # Essayer avec un wildcard
            handlers = self._incoming_handlers.get("*", [])
        
        if not handlers:
            return WebhookResponse(
                status_code=400,
                success=False,
                error=f"No handler for event type: {event_type}",
            )
        
        # Exécuter tous les handlers
        responses = []
        for handler in handlers:
            try:
                if integration_config:
                    response = handler(payload, integration_config)
                else:
                    # Créer une config vide si nécessaire
                    empty_config = IntegrationConfig()
                    response = handler(payload, empty_config)
                responses.append(response)
            except Exception as e:
                logger.error(f"Webhook handler error: {e}")
                responses.append(WebhookResponse(
                    status_code=500,
                    success=False,
                    error=str(e),
                ))
        
        # Retourner la première réponse réussie, ou la première erreur
        for response in responses:
            if response.success:
                return response
        
        return responses[0] if responses else WebhookResponse(
            status_code=400,
            success=False,
            error="All handlers failed",
        )
    
    def verify_webhook_signature(
        self,
        payload: WebhookPayload,
        secret: str,
        signature_header: Optional[str] = None,
    ) -> bool:
        """
        Vérifie la signature d'un webhook.
        
        Args:
            payload: Payload du webhook
            secret: Secret partagé
            signature_header: En-tête de signature (optionnel)
            
        Returns:
            True si la signature est valide
        """
        # Si une signature est fournie dans les headers
        if signature_header:
            return payload.verify_signature(signature_header, secret)
        
        # Sinon, vérifier avec l'en-tête standard
        signature = payload.headers.get("X-Hub-Signature-256") or \
                   payload.headers.get("X-Hub-Signature") or \
                   payload.headers.get("X-Slack-Signature") or \
                   payload.headers.get("X-Signature")
        
        if signature:
            return payload.verify_signature(signature, secret)
        
        return False
    
    def generate_signature(
        self,
        data: str,
        secret: str,
    ) -> str:
        """
        Génère une signature pour un webhook sortant.
        
        Args:
            data: Données à signer
            secret: Secret partagé
            
        Returns:
            Signature générée
        """
        # Hash SHA256
        computed_hash = hmac.new(
            secret.encode(),
            data.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return f"sha256={computed_hash}"
    
    def _send_webhook(
        self,
        subscription: WebhookSubscription,
        event: WebhookEvent,
        integration_config: Optional[IntegrationConfig] = None,
    ) -> WebhookResponse:
        """
        Envoie un événement à un abonnement webhook.
        
        Args:
            subscription: Abonnement webhook
            event: Événement à envoyer
            integration_config: Configuration d'intégration (optionnelle)
            
        Returns:
            Réponse du webhook
        """
        try:
            # Générer le payload
            payload_data = event.to_dict()
            
            # Ajouter des métadonnées si une config d'intégration est fournie
            if integration_config:
                payload_data["integration"] = {
                    "type": integration_config.integration_type.value,
                    "id": integration_config.id,
                }
            
            # Générer la signature
            secret = subscription.secret or ""
            signature = self.generate_signature(json.dumps(payload_data), secret)
            
            # Envoyer la requête
            headers = {
                "Content-Type": "application/json",
                "User-Agent": "AgentWorld/0.5.0",
                "X-Hub-Signature-256": signature,
            }
            
            response = requests.post(
                subscription.url,
                json=payload_data,
                headers=headers,
                timeout=30,
            )
            
            # Mettre à jour les statistiques
            subscription.calls_count += 1
            subscription.last_called_at = datetime.now()
            
            if response.status_code >= 200 and response.status_code < 300:
                subscription.success_count += 1
                subscription.status = WebhookStatus.ACTIVE
                return WebhookResponse(
                    status_code=response.status_code,
                    success=True,
                    message="Webhook delivered successfully",
                )
            else:
                subscription.error_count += 1
                subscription.last_error = response.text
                subscription.last_error_at = datetime.now()
                subscription.status = WebhookStatus.ERROR
                return WebhookResponse(
                    status_code=response.status_code,
                    success=False,
                    error=response.text,
                )
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send webhook: {e}")
            subscription.error_count += 1
            subscription.last_error = str(e)
            subscription.last_error_at = datetime.now()
            subscription.status = WebhookStatus.ERROR
            return WebhookResponse(
                status_code=500,
                success=False,
                error=str(e),
            )
    
    def _send_to_url(
        self,
        url: str,
        event: WebhookEvent,
        secret: Optional[str] = None,
    ) -> WebhookResponse:
        """
        Envoie un événement à une URL spécifique.
        
        Args:
            url: URL du webhook
            event: Événement à envoyer
            secret: Secret partagé (optionnel)
            
        Returns:
            Réponse du webhook
        """
        try:
            # Générer le payload
            payload_data = event.to_dict()
            
            # Générer la signature si un secret est fourni
            headers = {"Content-Type": "application/json", "User-Agent": "AgentWorld/0.5.0"}
            
            if secret:
                signature = self.generate_signature(json.dumps(payload_data), secret)
                headers["X-Hub-Signature-256"] = signature
            
            response = requests.post(
                url,
                json=payload_data,
                headers=headers,
                timeout=30,
            )
            
            if response.status_code >= 200 and response.status_code < 300:
                return WebhookResponse(
                    status_code=response.status_code,
                    success=True,
                    message="Webhook delivered successfully",
                )
            else:
                return WebhookResponse(
                    status_code=response.status_code,
                    success=False,
                    error=response.text,
                )
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send webhook to URL: {e}")
            return WebhookResponse(
                status_code=500,
                success=False,
                error=str(e),
            )
    
    def _default_integration_handler(
        self,
        payload: WebhookPayload,
        integration_config: IntegrationConfig,
    ) -> WebhookResponse:
        """
        Handler par défaut pour les intégrations.
        
        Args:
            payload: Payload du webhook
            integration_config: Configuration de l'intégration
            
        Returns:
            Réponse du webhook
        """
        # Envoyer directement au webhook URL de l'intégration
        if not integration_config.credentials.webhook_url:
            return WebhookResponse(
                status_code=400,
                success=False,
                error="No webhook URL configured for integration",
            )
        
        return self._send_to_url(
            integration_config.credentials.webhook_url,
            WebhookEvent.from_dict(payload.body),
            integration_config.credentials.webhook_secret,
        )
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Récupère les statistiques des webhooks.
        
        Returns:
            Statistiques des webhooks
        """
        total_subscriptions = len(self._subscriptions)
        active_subscriptions = sum(
            1 for s in self._subscriptions.values() if s.active
        )
        total_calls = sum(s.calls_count for s in self._subscriptions.values())
        total_success = sum(s.success_count for s in self._subscriptions.values())
        total_errors = sum(s.error_count for s in self._subscriptions.values())
        
        return {
            "total_subscriptions": total_subscriptions,
            "active_subscriptions": active_subscriptions,
            "total_calls": total_calls,
            "total_success": total_success,
            "total_errors": total_errors,
            "success_rate": total_success / total_calls if total_calls > 0 else 0,
        }
    
    def cleanup(self):
        """Nettoie les ressources."""
        self._subscriptions.clear()
        self._incoming_handlers.clear()
        self._outgoing_handlers.clear()
        self._webhook_secrets.clear()


# Importer datetime au niveau module pour l'utiliser dans les méthodes
from datetime import datetime
