# 📡 Agent World Routes
# Description: Définition des routes/endpoints de l'API

"""Routes package for Agent World API."""

from flask import Blueprint
from .agents import register_resources

# Créer un blueprint pour les routes des agents
agents_bp = Blueprint("agents", __name__, url_prefix="/api/agents")

__all__ = ["agents_bp", "register_resources"]
