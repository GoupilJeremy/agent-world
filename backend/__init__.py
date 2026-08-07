# 🚀 Agent World Backend
# Version: 0.1.0 (MVP)
# Description: Backend Flask/FastAPI pour la gestion des agents IA

"""
Agent World Backend Package

Ce package contient toute la logique backend pour la plateforme Agent World.
Il inclut :
- API REST/GraphQL pour la gestion des agents
- Modèles de données et interactions avec la base de données
- Services et connecteurs pour les modèles IA
- Configuration et utilitaires
"""

from .app import create_app
from .config import Config

__version__ = "0.1.0"
__author__ = "Jeremy Goupil"
__all__ = ["create_app", "Config"]
