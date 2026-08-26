# 🌐 Agent World - Integration Routes
# Version: 0.5.0 (Épic 7)
# Description: Routes API pour les intégrations externes

"""
Integration Routes for Agent World.

Ce module définit les endpoints RESTful pour gérer les intégrations
avec des services externes (GitHub, Slack, Discord, etc.).
"""

import logging
from datetime import datetime
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Tuple

from flask import Blueprint, current_app, jsonify, request
from flask_restful import Api, Resource

logger = logging.getLogger(__name__)

# Créer le blueprint pour les intégrations
integrations_bp = Blueprint("integrations", __name__, url_prefix="/api/integrations")

# API Flask-RESTful
integrations_api = Api(integrations_bp)


def get_integration_manager():
    """Récupère le IntegrationManager depuis l'application Flask."""
    return _get_integration_manager()


def get_oauth_service():
    """Récupère le OAuthService depuis l'application Flask."""
    return _get_oauth_service()


def get_webhook_service():
    """Récupère le WebhookService depuis l'application Flask."""
    return _get_webhook_service()


# ==================== Décorateurs ====================


def handle_integration_errors(func: Callable) -> Callable:
    """Décorateur pour gérer les erreurs des intégrations."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except IntegrationAdapterError as e:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": str(e),
                        "error_code": e.error_code,
                    }
                ),
                400,
            )
        except AuthenticationError as e:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": str(e),
                        "error_code": "AUTHENTICATION_ERROR",
                    }
                ),
                401,
            )
        except ConnectionError as e:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": str(e),
                        "error_code": "CONNECTION_ERROR",
                    }
                ),
                502,
            )
        except ValueError as e:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": str(e),
                        "error_code": "VALIDATION_ERROR",
                    }
                ),
                400,
            )
        except Exception as e:
            logger.error(f"Unexpected error in integration endpoint: {e}")
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "Internal server error",
                        "error_code": "INTERNAL_ERROR",
                    }
                ),
                500,
            )

    return wrapper


# ==================== Resources RESTful ====================


class IntegrationListResource(Resource):
    """Resource pour lister et créer des intégrations."""

    @handle_integration_errors
    def get(self):
        """Liste toutes les intégrations."""
        manager = get_integration_manager()

        if not manager:
            return {"error": "Integration service not initialized"}, 500

        # Filtrer par paramètres de requête
        user_id = request.args.get("user_id", type=int)
        integration_type = request.args.get("type")
        status = request.args.get("status")

        integrations = manager.list_integrations(
            user_id=user_id,
            integration_type=(
                IntegrationType(integration_type) if integration_type else None
            ),
            status=IntegrationStatus(status) if status else None,
        )

        # Convertir en dictionnaires (sans les secrets)
        result = [config.to_dict(include_secrets=False) for config in integrations]

        return {
            "success": True,
            "count": len(result),
            "integrations": result,
        }

    @handle_integration_errors
    def post(self):
        """Crée une nouvelle intégration."""
        manager = get_integration_manager()

        if not manager:
            return {"error": "Integration service not initialized"}, 500

        data = request.get_json()

        if not data:
            return {"error": "No data provided"}, 400

        # Valider les données requises
        required_fields = ["type", "name"]
        for field in required_fields:
            if field not in data:
                return {"error": f"Missing required field: {field}"}, 400

        # Convertir le type
        try:
            integration_type = IntegrationType(data["type"])
        except ValueError:
            return {"error": f"Invalid integration type: {data['type']}"}, 400

        # Créer la configuration
        config = manager.create_integration(
            integration_type=integration_type,
            name=data["name"],
            user_id=data.get("user_id"),
            description=data.get("description", ""),
            credentials=(
                IntegrationCredentials(**data.get("credentials", {}))
                if data.get("credentials")
                else None
            ),
            settings=data.get("settings", {}),
        )

        return {
            "success": True,
            "integration": config.to_dict(include_secrets=False),
        }


class IntegrationResource(Resource):
    """Resource pour gérer une intégration spécifique."""

    @handle_integration_errors
    def get(self, integration_id):
        """Récupère une intégration."""
        manager = get_integration_manager()

        if not manager:
            return {"error": "Integration service not initialized"}, 500

        config = manager.get_integration(int(integration_id))

        if not config:
            return {"error": f"Integration {integration_id} not found"}, 404

        include_secrets = request.args.get("include_secrets", "false").lower() == "true"

        return {
            "success": True,
            "integration": config.to_dict(include_secrets=include_secrets),
        }

    @handle_integration_errors
    def put(self, integration_id):
        """Met à jour une intégration."""
        manager = get_integration_manager()

        if not manager:
            return {"error": "Integration service not initialized"}, 500

        config = manager.get_integration(int(integration_id))

        if not config:
            return {"error": f"Integration {integration_id} not found"}, 404

        data = request.get_json() or {}

        # Mettre à jour les champs autorisés
        allowed_fields = [
            "name",
            "description",
            "status",
            "settings",
            "oauth_config",
            "webhook_config",
        ]

        update_data = {}
        for field in allowed_fields:
            if field in data:
                update_data[field] = data[field]

        # Mettre à jour les credentials séparément
        if "credentials" in data:
            credentials_data = data["credentials"]
            config.credentials.access_token = credentials_data.get("access_token")
            config.credentials.refresh_token = credentials_data.get("refresh_token")
            config.credentials.api_key = credentials_data.get("api_key")
            config.credentials.webhook_url = credentials_data.get("webhook_url")
            config.credentials.webhook_secret = credentials_data.get("webhook_secret")

        # Mettre à jour
        config = manager.update_integration(int(integration_id), **update_data)

        return {
            "success": True,
            "integration": config.to_dict(include_secrets=False),
        }

    @handle_integration_errors
    def delete(self, integration_id):
        """Supprime une intégration."""
        manager = get_integration_manager()

        if not manager:
            return {"error": "Integration service not initialized"}, 500

        success = manager.delete_integration(int(integration_id))

        if not success:
            return {"error": f"Integration {integration_id} not found"}, 404

        return {"success": True, "message": "Integration deleted"}


class IntegrationActionsResource(Resource):
    """Resource pour exécuter des actions sur une intégration."""

    @handle_integration_errors
    def post(self, integration_id):
        """Exécute une action sur une intégration."""
        manager = get_integration_manager()

        if not manager:
            return {"error": "Integration service not initialized"}, 500

        data = request.get_json()

        if not data:
            return {"error": "No data provided"}, 400

        # Valider les données requises
        if "action_type" not in data:
            return {"error": "Missing required field: action_type"}, 400

        action = IntegrationAction(
            action_type=data["action_type"],
            payload=data.get("payload", {}),
            metadata=data.get("metadata"),
        )

        result = manager.execute_action(int(integration_id), action)

        return {
            "success": result.success,
            "data": result.data,
            "error": result.error,
            "error_code": result.error_code,
            "timestamp": result.timestamp.isoformat(),
            "duration_ms": result.duration_ms,
        }


class IntegrationTestResource(Resource):
    """Resource pour tester une intégration."""

    @handle_integration_errors
    def post(self, integration_id):
        """Teste la connexion d'une intégration."""
        manager = get_integration_manager()

        if not manager:
            return {"error": "Integration service not initialized"}, 500

        adapter = manager.get_adapter(int(integration_id))

        if not adapter:
            return {"error": f"Integration {integration_id} not found"}, 404

        result = adapter.test_connection()

        return {
            "success": result.success,
            "data": result.data,
            "error": result.error,
        }


class IntegrationActivateResource(Resource):
    """Resource pour activer/désactiver une intégration."""

    @handle_integration_errors
    def post(self, integration_id, action):
        """Active ou désactive une intégration."""
        manager = get_integration_manager()

        if not manager:
            return {"error": "Integration service not initialized"}, 500

        if action == "activate":
            success = manager.activate_integration(int(integration_id))
            message = (
                "Integration activated" if success else "Failed to activate integration"
            )
        elif action == "deactivate":
            success = manager.deactivate_integration(int(integration_id))
            message = (
                "Integration deactivated"
                if success
                else "Failed to deactivate integration"
            )
        else:
            return {
                "error": f"Invalid action: {action}. Must be 'activate' or 'deactivate'"
            }, 400

        return {
            "success": success,
            "message": message,
        }


class IntegrationTypesResource(Resource):
    """Resource pour lister les types d'intégrations supportées."""

    @handle_integration_errors
    def get(self):
        """Liste les types d'intégrations supportées."""
        manager = get_integration_manager()

        if not manager:
            return {"error": "Integration service not initialized"}, 500

        supported = manager.get_supported_integrations()

        return {
            "success": True,
            "count": len(supported),
            "supported_integrations": supported,
        }


class IntegrationMetadataResource(Resource):
    """Resource pour obtenir les métadonnées d'une intégration."""

    @handle_integration_errors
    def get(self, integration_type):
        """Obtient les métadonnées d'une intégration."""
        manager = get_integration_manager()

        if not manager:
            return {"error": "Integration service not initialized"}, 500

        try:
            itype = IntegrationType(integration_type)
        except ValueError:
            return {"error": f"Invalid integration type: {integration_type}"}, 400

        metadata = manager.get_integration_metadata(itype)

        return {
            "success": True,
            "metadata": metadata,
        }


class IntegrationActionSchemaResource(Resource):
    """Resource pour obtenir le schéma d'une action."""

    @handle_integration_errors
    def get(self, integration_type, action_type):
        """Obtient le schéma d'une action."""
        manager = get_integration_manager()

        if not manager:
            return {"error": "Integration service not initialized"}, 500

        try:
            itype = IntegrationType(integration_type)
        except ValueError:
            return {"error": f"Invalid integration type: {integration_type}"}, 400

        schema = manager.get_action_schema(itype, action_type)

        return {
            "success": True,
            "schema": schema,
        }


# ==================== OAuth2 Routes ====================


class OAuthAuthorizationResource(Resource):
    """Resource pour démarrer l'authentification OAuth2."""

    @handle_integration_errors
    def get(self, integration_type):
        """Génère une URL d'autorisation OAuth2."""
        manager = get_integration_manager()

        if not manager:
            return {"error": "Integration service not initialized"}, 500

        try:
            itype = IntegrationType(integration_type)
        except ValueError:
            return {"error": f"Invalid integration type: {integration_type}"}, 400

        # Obtenir les paramètres de requête
        state = request.args.get("state")
        user_id = request.args.get("user_id", type=int)
        integration_id = request.args.get("integration_id", type=int)

        # Générer l'URL d'autorisation
        auth_url, state_value = manager.get_oauth_authorization_url(
            integration_type=itype,
            integration_id=integration_id,
            user_id=user_id,
            state=state,
        )

        return {
            "success": True,
            "authorization_url": auth_url,
            "state": state_value,
        }


class OAuthCallbackResource(Resource):
    """Resource pour gérer les callbacks OAuth2."""

    @handle_integration_errors
    def get(self, integration_type):
        """Gère le callback OAuth2."""
        manager = get_integration_manager()

        if not manager:
            return {"error": "Integration service not initialized"}, 500

        try:
            itype = IntegrationType(integration_type)
        except ValueError:
            return {"error": f"Invalid integration type: {integration_type}"}, 400

        # Récupérer les paramètres du callback
        code = request.args.get("code")
        state = request.args.get("state")
        error = request.args.get("error")

        if error:
            return {
                "success": False,
                "error": error,
                "error_description": request.args.get("error_description"),
            }, 400

        if not code:
            return {"error": "Missing authorization code"}, 400

        # Échanger le code contre un token
        credentials = manager.exchange_oauth_code(
            integration_type=itype,
            code=code,
            state=state,
        )

        return {
            "success": True,
            "message": "OAuth authorization successful",
            "credentials": {
                "access_token": (
                    credentials.access_token[:10] + "..."
                    if credentials.access_token
                    else None
                ),
                "token_type": "Bearer",
                "expires_in": (
                    (
                        credentials.token_expiry.timestamp()
                        - datetime.utcnow().timestamp()
                    )
                    if credentials.token_expiry
                    else None
                ),
            },
        }


# ==================== Webhook Routes ====================


class WebhookSubscriptionResource(Resource):
    """Resource pour gérer les abonnements webhook."""

    @handle_integration_errors
    def get(self):
        """Liste tous les abonnements webhook."""
        webhook_service = get_webhook_service()

        if not webhook_service:
            return {"error": "Webhook service not initialized"}, 500

        subscriptions = webhook_service.list_subscriptions()

        return {
            "success": True,
            "count": len(subscriptions),
            "subscriptions": [s.to_dict() for s in subscriptions],
        }

    @handle_integration_errors
    def post(self):
        """Crée un nouvel abonnement webhook."""
        webhook_service = get_webhook_service()

        if not webhook_service:
            return {"error": "Webhook service not initialized"}, 500

        data = request.get_json()

        if not data:
            return {"error": "No data provided"}, 400

        # Valider les données requises
        required_fields = ["name", "url", "events"]
        for field in required_fields:
            if field not in data:
                return {"error": f"Missing required field: {field}"}, 400

        # Créer l'abonnement
        subscription = webhook_service.create_subscription(
            name=data["name"],
            url=data["url"],
            events=data["events"],
            secret=data.get("secret"),
        )

        return {
            "success": True,
            "subscription": subscription.to_dict(include_secret=False),
        }


class WebhookIncomingResource(Resource):
    """Resource pour recevoir les webhooks entrants."""

    @handle_integration_errors
    def post(self):
        """Reçoit et traite un webhook entrant."""
        webhook_service = get_webhook_service()

        if not webhook_service:
            return {"error": "Webhook service not initialized"}, 500

        # Obtenir les données de la requête
        headers = dict(request.headers)
        body = request.get_json() or {}
        query_params = dict(request.args)

        payload = WebhookPayload(
            headers=headers,
            body=body,
            query_params=query_params,
        )

        # Trouver l'ID du webhook (peut être dans les headers ou query params)
        webhook_id = headers.get("X-Webhook-ID") or query_params.get("webhook_id")

        # Traiter le webhook
        response = webhook_service.handle_incoming_webhook(payload)

        return response.to_dict(), response.status_code


class WebhookEmitResource(Resource):
    """Resource pour émettre des événements webhook."""

    @handle_integration_errors
    def post(self):
        """Émet un événement webhook."""
        manager = get_integration_manager()

        if not manager:
            return {"error": "Integration service not initialized"}, 500

        data = request.get_json()

        if not data:
            return {"error": "No data provided"}, 400

        # Créer l'événement
        event = WebhookEvent(
            event_type=data.get("event_type", "custom"),
            source=data.get("source", "unknown"),
            source_id=data.get("source_id"),
            data=data.get("data", {}),
            metadata=data.get("metadata", {}),
        )

        # Obtenir l'ID de l'intégration si fourni
        integration_id = data.get("integration_id")

        # Émettre l'événement
        if integration_id:
            responses = manager.emit_webhook_event(
                event,
                integration_id=int(integration_id),
            )
        else:
            responses = manager.emit_webhook_event(event)

        return {
            "success": True,
            "responses": [r.to_dict() for r in responses],
        }


class WebhookStatisticsResource(Resource):
    """Resource pour obtenir les statistiques des webhooks."""

    @handle_integration_errors
    def get(self):
        """Obtient les statistiques des webhooks."""
        manager = get_integration_manager()

        if not manager:
            return {"error": "Integration service not initialized"}, 500

        stats = manager.get_statistics()

        return {
            "success": True,
            "statistics": stats,
        }


# ==================== Provider-specific Routes ====================


class GitHubIntegrationResource(Resource):
    """Resource pour les opérations spécifiques à GitHub."""

    @handle_integration_errors
    def get(self, integration_id):
        """Obtient des informations spécifiques à GitHub."""
        manager = get_integration_manager()

        if not manager:
            return {"error": "Integration service not initialized"}, 500

        config = manager.get_integration(int(integration_id))

        if not config:
            return {"error": f"Integration {integration_id} not found"}, 404

        if config.integration_type != IntegrationType.GITHUB:
            return {"error": "This endpoint is only for GitHub integrations"}, 400

        adapter = manager.get_adapter(int(integration_id))

        if not adapter:
            return {"error": "Failed to get adapter"}, 500

        # Obtenir les métadonnées
        metadata = adapter.get_metadata()

        return {
            "success": True,
            "integration_type": "github",
            "metadata": metadata,
            "supported_actions": adapter.supported_actions,
            "oauth_scopes": adapter.get_oauth_scopes(),
        }


# ==================== Enregistrement des Resources ====================


def register_integration_resources(api):
    """Enregistre toutes les resources d'intégrations."""

    # Resources principales
    api.add_resource(IntegrationListResource, "/integrations")
    api.add_resource(IntegrationResource, "/integrations/<int:integration_id>")
    api.add_resource(
        IntegrationActionsResource, "/integrations/<int:integration_id>/actions"
    )
    api.add_resource(IntegrationTestResource, "/integrations/<int:integration_id>/test")
    api.add_resource(
        IntegrationActivateResource,
        "/integrations/<int:integration_id>/<string:action>",
    )
    api.add_resource(IntegrationTypesResource, "/integrations/types")
    api.add_resource(
        IntegrationMetadataResource, "/integrations/<string:integration_type>/metadata"
    )
    api.add_resource(
        IntegrationActionSchemaResource,
        "/integrations/<string:integration_type>/actions/<string:action_type>/schema",
    )

    # OAuth2
    api.add_resource(
        OAuthAuthorizationResource,
        "/integrations/<string:integration_type>/oauth/authorize",
    )
    api.add_resource(
        OAuthCallbackResource, "/integrations/<string:integration_type>/oauth/callback"
    )

    # Webhooks
    api.add_resource(WebhookSubscriptionResource, "/integrations/webhooks")
    api.add_resource(WebhookIncomingResource, "/integrations/webhooks/incoming")
    api.add_resource(WebhookEmitResource, "/integrations/webhooks/emit")
    api.add_resource(WebhookStatisticsResource, "/integrations/webhooks/statistics")

    # Spécifiques aux fournisseurs
    api.add_resource(
        GitHubIntegrationResource, "/integrations/github/<int:integration_id>"
    )


def register_resources(api):
    """Enregistre les resources d'intégrations."""
    register_integration_resources(api)
