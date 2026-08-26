# 📡 Agent World Routes
# Description: Définition des routes/endpoints de l'API

"""Routes package for Agent World API."""

from flask import Blueprint

from .agents import register_resources as register_agent_resources
from .auth import register_resources as register_auth_resources
from .files import register_resources as register_file_resources
from .history import register_history_resources
from .invitations import register_resources as register_invitation_resources
from .notifications import register_resources as register_notification_resources
from .templates import register_resources as register_template_resources

# Créer un blueprint pour les routes des agents
agents_bp = Blueprint("agents", __name__, url_prefix="/api/agents")

# Importer le blueprint des intégrations de manière lazy pour éviter les dépendances circulaires
def _get_integrations_bp():
    from .integrations import integrations_bp
    return integrations_bp

# Importer la fonction d'enregistrement des ressources d'intégrations de manière lazy
def _get_register_integration_resources():
    from .integrations import register_resources
    return register_resources


def register_resources(api):
    """Register all REST resources on the application API."""

    register_agent_resources(api)
    register_auth_resources(api)
    register_file_resources(api)
    register_history_resources(api)
    register_invitation_resources(api)
    register_notification_resources(api)
    register_template_resources(api)
    # Enregistrer les intégrations de manière lazy
    register_integration_resources = _get_register_integration_resources()
    register_integration_resources(api)


def get_integrations_bp():
    """Récupère le blueprint des intégrations."""
    return _get_integrations_bp()


__all__ = ["agents_bp", "register_resources", "get_integrations_bp"]
