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
        raise ValueError(f"{adapter_class.__name__} must inherit from BaseIntegrationAdapter")
    
    # Instancier l'adapter sans configuration pour obtenir ses métadonnées
    instance = adapter_class()
    ADAPTER_REGISTRY[instance.type.value] = adapter_class
    
    return adapter_class


# Importer les adapters (ils s'enregistrent automatiquement via @register_adapter)
# Import lazy pour éviter les dépendances circulaires
def __getattr__(name):
    if name == "GitHubIntegrationAdapter":
        from .github_adapter import GitHubIntegrationAdapter
        return GitHubIntegrationAdapter
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "BaseIntegrationAdapter",
    "ADAPTER_REGISTRY",
    "register_adapter",
    "GitHubIntegrationAdapter",
]
