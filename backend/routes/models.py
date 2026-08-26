# 📡 Agent World - Models & Quotas Routes
# Version: 0.8.0 (Épic 11 - US-071, US-075)
# Description: Endpoints REST pour la gestion des modèles IA et des quotas

"""
Models and Quotas Routes for Agent World API.

Endpoints pour lister les modèles disponibles, vérifier leur état de santé,
gérer les quotas utilisateur, et consulter l'historique d'utilisation.
"""

from flask import Blueprint, current_app, request
from flask_restful import Resource

models_bp = Blueprint("models", __name__, url_prefix="/api")


class ModelListResource(Resource):
    """GET /api/models — List all available AI models."""

    def get(self):
        from ..services.ai_service import AIService

        ai_service: AIService = current_app.extensions.get("ai_service")
        if not ai_service:
            ai_service = AIService()

        provider = request.args.get("provider")
        available_only = request.args.get("available_only", "false").lower() in {
            "true",
            "1",
            "yes",
        }

        models = ai_service.get_models_info(
            provider=provider, available_only=available_only
        )

        return {
            "models": models,
            "total": len(models),
            "providers": ai_service.registry.list_providers(),
        }, 200


class ModelDetailResource(Resource):
    """GET /api/models/<model_id> — Get details for a specific model."""

    def get(self, model_id: str):
        from ..services.ai_service import AIService

        ai_service: AIService = current_app.extensions.get("ai_service")
        if not ai_service:
            ai_service = AIService()

        info = ai_service.get_model_info(model_id)
        if not info:
            return {"error": f"Model '{model_id}' not found"}, 404

        return info, 200


class ModelHealthResource(Resource):
    """GET /api/models/health — Health check all providers."""

    def get(self):
        from ..services.ai_service import AIService

        ai_service: AIService = current_app.extensions.get("ai_service")
        if not ai_service:
            ai_service = AIService()

        health = ai_service.health_check()

        return {
            "providers": health,
            "all_healthy": all(health.values()),
        }, 200


class QuotaListResource(Resource):
    """GET /api/quotas — Get all quotas for the current user."""

    def get(self):
        from ..services.quota_service import QuotaService

        user_id = request.args.get("user_id", type=int)
        if not user_id:
            return {"error": "user_id query parameter is required"}, 400

        quota_service = QuotaService()
        quotas = quota_service.get_all_quotas(user_id)

        return {"quotas": quotas, "total": len(quotas)}, 200


class QuotaDetailResource(Resource):
    """PUT /api/quotas/<model_id> — Set or update a quota."""

    def put(self, model_id: str):
        from ..services.quota_service import QuotaService

        data = request.get_json(silent=True) or {}
        user_id = data.get("user_id")
        if not user_id:
            return {"error": "user_id is required"}, 400

        quota_service = QuotaService()
        quota = quota_service.set_quota_limit(
            user_id=user_id,
            model_id=model_id,
            max_tokens_per_month=data.get("max_tokens_per_month"),
            max_cost_per_month=data.get("max_cost_per_month"),
        )

        return quota.to_dict(), 200

    def get(self, model_id: str):
        from ..services.quota_service import QuotaService

        user_id = request.args.get("user_id", type=int)
        if not user_id:
            return {"error": "user_id query parameter is required"}, 400

        quota_service = QuotaService()
        status = quota_service.check_quota(user_id, model_id)

        return status.to_dict(), 200


class UsageSummaryResource(Resource):
    """GET /api/usage — Get usage summary for a user."""

    def get(self):
        from ..services.quota_service import QuotaService

        user_id = request.args.get("user_id", type=int)
        if not user_id:
            return {"error": "user_id query parameter is required"}, 400

        period = request.args.get("period", "month")
        if period not in ("day", "week", "month"):
            return {"error": "period must be 'day', 'week', or 'month'"}, 400

        quota_service = QuotaService()
        summary = quota_service.get_usage_summary(user_id, period)

        return summary.to_dict(), 200


class UsageHistoryResource(Resource):
    """GET /api/usage/history — Get detailed usage history."""

    def get(self):
        from ..services.quota_service import QuotaService

        user_id = request.args.get("user_id", type=int)
        if not user_id:
            return {"error": "user_id query parameter is required"}, 400

        limit = request.args.get("limit", 100, type=int)

        quota_service = QuotaService()
        history = quota_service.get_usage_history(user_id, limit=limit)

        return {"history": history, "total": len(history)}, 200


def register_model_resources(api):
    """Register model and quota resources with the Flask-RESTful API."""
    api.add_resource(ModelListResource, "/models")
    api.add_resource(ModelHealthResource, "/models/health")
    api.add_resource(ModelDetailResource, "/models/<string:model_id>")
    api.add_resource(QuotaListResource, "/quotas")
    api.add_resource(QuotaDetailResource, "/quotas/<string:model_id>")
    api.add_resource(UsageSummaryResource, "/usage")
    api.add_resource(UsageHistoryResource, "/usage/history")
