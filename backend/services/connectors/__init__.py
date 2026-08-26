# ⚙️ Agent World - AI Connectors Package
# Description: Connecteurs pour les différents fournisseurs d'IA

"""AI Connectors package for Agent World.

Ce package contient les connecteurs pour interagir avec les différents
fournisseurs de modèles IA (Mistral, OpenAI, Anthropic, etc.).
"""

from .base import BaseConnector, ConnectorResponse, ConnectorError

__all__ = [
    "BaseConnector",
    "ConnectorResponse",
    "ConnectorError",
]
