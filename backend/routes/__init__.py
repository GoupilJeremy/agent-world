# 📡 Agent World Routes
# Description: Définition des routes/endpoints de l'API

"""Routes package for Agent World API."""

from flask import Blueprint

from .agents import register_resources as register_agent_resources
from .auth import register_resources as register_auth_resources
from .compression import compression_bp, register_compression_resources
from .files import register_resources as register_file_resources
from .history import register_history_resources
from .invitations import register_resources as register_invitation_resources
from .notifications import register_resources as register_notification_resources
from .performance import performance_bp, register_performance_resources
from .security import security_bp
from .templates import register_resources as register_template_resources

# Créer un blueprint pour les routes des agents
agents_bp = Blueprint("agents", __name__, url_prefix="/api/agents")


# Importer le blueprint des intégrations de manière lazy pour éviter
# les dépendances circulaires
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
    # Performance resources (Épic 8)
    register_performance_resources(api)
    # Compression resources (Épic 8 - US-058)
    register_compression_resources(api)
    # Security resources (Épic 10)
    from .security import register_resources as register_security_resources

    register_security_resources(api)
    # Enregistrer les intégrations de manière lazy
    register_integration_resources = _get_register_integration_resources()
    register_integration_resources(api)


def get_integrations_bp():
    """Récupère le blueprint des intégrations."""
    return _get_integrations_bp()


def get_performance_bp():
    """Récupère le blueprint des performances."""
    return performance_bp


def get_compression_bp():
    """Récupère le blueprint de compression."""
    return compression_bp


def get_security_bp():
    """Récupère le blueprint de sécurité."""
    return security_bp


__all__ = [
    "agents_bp",
    "register_resources",
    "get_integrations_bp",
    "get_performance_bp",
    "get_compression_bp",
    "get_security_bp",
    "security_bp",
]
