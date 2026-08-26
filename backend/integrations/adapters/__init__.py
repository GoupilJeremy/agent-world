# 🔌 Agent World - Integration Adapters
# Version: 0.5.0 (Épic 7)
# Description: Package pour les adapters d'intégration

"""
Integration Adapters package for Agent World.

Ce package contient les implémentations concrètes des adapters
pour chaque service externe (GitHub, Slack, Discord, etc.).
"""

from ..base_adapter import BaseIntegrationAdapter

# Registre des adapters disponibles
ADAPTER_REGISTRY = {}


def register_adapter(adapter_class: type) -> type:
    """
    Décorateur pour enregistrer un adapter dans le registre.

    Args:
        adapter_class: Classe de l'adapter à enregistrer

    Returns:
        La classe de l'adapter (inchangée)
    """
    if not issubclass(adapter_class, BaseIntegrationAdapter):
        raise ValueError(
            f"{adapter_class.__name__} must inherit from BaseIntegrationAdapter"
        )

    # Instancier l'adapter sans configuration pour obtenir ses métadonnées
    instance = adapter_class()
    ADAPTER_REGISTRY[instance.type.value] = adapter_class

    return adapter_class


from .discord_adapter import DiscordIntegrationAdapter  # noqa: F401, E402

# Importer les adapters (ils s'enregistrent automatiquement via @register_adapter)
# Import direct pour enregistrer les adapters dans le registre
from .github_adapter import GitHubIntegrationAdapter  # noqa: F401, E402
from .google_drive_adapter import GoogleDriveIntegrationAdapter  # noqa: F401, E402
from .notion_adapter import NotionIntegrationAdapter  # noqa: F401, E402
from .slack_adapter import SlackIntegrationAdapter  # noqa: F401, E402
from .trello_adapter import TrelloIntegrationAdapter  # noqa: F401, E402


# Import lazy pour éviter les dépendances circulaires supplémentaires
def __getattr__(name):
    # Ces adapters sont déjà importés ci-dessus, mais on garde la
    # fonction pour compatibilité
    if name == "GitHubIntegrationAdapter":
        return GitHubIntegrationAdapter
    if name == "SlackIntegrationAdapter":
        return SlackIntegrationAdapter
    if name == "DiscordIntegrationAdapter":
        return DiscordIntegrationAdapter
    if name == "NotionIntegrationAdapter":
        return NotionIntegrationAdapter
    if name == "GoogleDriveIntegrationAdapter":
        return GoogleDriveIntegrationAdapter
    if name == "TrelloIntegrationAdapter":
        return TrelloIntegrationAdapter
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "BaseIntegrationAdapter",
    "ADAPTER_REGISTRY",
    "register_adapter",
    "GitHubIntegrationAdapter",
    "SlackIntegrationAdapter",
    "DiscordIntegrationAdapter",
    "NotionIntegrationAdapter",
    "GoogleDriveIntegrationAdapter",
    "TrelloIntegrationAdapter",
]
