# 📡 Agent World Routes
# Description: Définition des routes/endpoints de l'API

"""Routes package for Agent World API."""

from flask import Blueprint

from .agents import register_resources as register_agent_resources
from .auth import register_resources as register_auth_resources
from .files import register_resources as register_file_resources

# Créer un blueprint pour les routes des agents
agents_bp = Blueprint("agents", __name__, url_prefix="/api/agents")


def register_resources(api):
    """Register all REST resources on the application API."""

    register_agent_resources(api)
    register_auth_resources(api)
    register_file_resources(api)


__all__ = ["agents_bp", "register_resources"]
