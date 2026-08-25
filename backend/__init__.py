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

from flask import Flask

from .config import Config


def create_app(config_class: type[Config] = Config) -> Flask:
    """Create the Flask application without initializing it on package import."""

    from .app import create_app as application_factory

    return application_factory(config_class)


__version__ = "0.1.0"
__author__ = "Jeremy Goupil"
__all__ = ["create_app", "Config"]
