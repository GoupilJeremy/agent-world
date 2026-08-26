# 🔗 Agent World - Integrations Package
# Version: 0.5.0 (Épic 7)
# Description: Package pour les intégrations externes

"""
Integrations package for Agent World.

Ce package contient toutes les intégrations avec des services externes
(GitHub, Slack, Discord, Notion, Google Drive, Trello) ainsi que
la gestion des webhooks personnalisés.
"""

# Registre des intégrations disponibles
INTEGRATION_REGISTRY = {}

__all__ = [
    "INTEGRATION_REGISTRY",
]
