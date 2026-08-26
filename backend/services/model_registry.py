# ⚙️ Agent World - Model Registry
# Version: 0.8.0 (Épic 11 - US-071)
# Description: Registre central des modèles IA disponibles

"""
Model Registry for Agent World.

Le registre maintient un catalogue de tous les modèles IA disponibles
avec leurs métadonnées (provider, pricing, capabilities, limites).
Il est la source de vérité pour la sélection de modèle, le fallback
et le calcul des coûts.
"""

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .connectors.base import BaseConnector

logger = logging.getLogger(__name__)


@dataclass
class ModelInfo:
    """Metadata for a single AI model.

    Attributes:
        id: Unique model identifier (e.g. "gpt-4-turbo")
        provider: Provider name (e.g. "openai")
        display_name: Human-readable name
        capabilities: List of supported features ("chat", "generate", etc.)
        max_context_tokens: Maximum context window size
        cost_per_1k_input: USD per 1K input tokens
        cost_per_1k_output: USD per 1K output tokens
        is_available: Whether the model is currently operational
        priority: Fallback priority (lower = preferred)
    """

    id: str
    provider: str
    display_name: str
    capabilities: List[str] = field(default_factory=lambda: ["chat", "generate"])
    max_context_tokens: int = 4096
    cost_per_1k_input: float = 0.0
    cost_per_1k_output: float = 0.0
    is_available: bool = True
    priority: int = 100

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to a dictionary for API responses."""
        return {
            "id": self.id,
            "provider": self.provider,
            "display_name": self.display_name,
            "capabilities": self.capabilities,
            "max_context_tokens": self.max_context_tokens,
            "cost_per_1k_input": self.cost_per_1k_input,
            "cost_per_1k_output": self.cost_per_1k_output,
            "is_available": self.is_available,
            "priority": self.priority,
        }

    def estimate_cost(self, tokens_input: int, tokens_output: int) -> float:
        """Estimate the cost of a request in USD."""
        input_cost = (tokens_input / 1000) * self.cost_per_1k_input
        output_cost = (tokens_output / 1000) * self.cost_per_1k_output
        return round(input_cost + output_cost, 6)


# -----------------------------------------------------------------------
# Default model catalog
# -----------------------------------------------------------------------

DEFAULT_MODELS: List[ModelInfo] = [
    # --- Mistral ---
    ModelInfo(
        id="mistral-tiny",
        provider="mistral",
        display_name="Mistral Tiny",
        max_context_tokens=32_000,
        cost_per_1k_input=0.00025,
        cost_per_1k_output=0.00025,
        priority=10,
    ),
    ModelInfo(
        id="mistral-small-latest",
        provider="mistral",
        display_name="Mistral Small",
        max_context_tokens=32_000,
        cost_per_1k_input=0.001,
        cost_per_1k_output=0.003,
        priority=20,
    ),
    ModelInfo(
        id="mistral-medium-latest",
        provider="mistral",
        display_name="Mistral Medium",
        max_context_tokens=32_000,
        cost_per_1k_input=0.0027,
        cost_per_1k_output=0.0081,
        priority=30,
    ),
    ModelInfo(
        id="mistral-large-latest",
        provider="mistral",
        display_name="Mistral Large",
        max_context_tokens=128_000,
        cost_per_1k_input=0.004,
        cost_per_1k_output=0.012,
        priority=40,
    ),
    ModelInfo(
        id="open-mistral-nemo",
        provider="mistral",
        display_name="Open Mistral Nemo",
        max_context_tokens=128_000,
        cost_per_1k_input=0.0003,
        cost_per_1k_output=0.0003,
        priority=15,
    ),
    # --- OpenAI ---
    ModelInfo(
        id="gpt-3.5-turbo",
        provider="openai",
        display_name="GPT-3.5 Turbo",
        max_context_tokens=16_384,
        cost_per_1k_input=0.0005,
        cost_per_1k_output=0.0015,
        priority=12,
    ),
    ModelInfo(
        id="gpt-4",
        provider="openai",
        display_name="GPT-4",
        max_context_tokens=8_192,
        cost_per_1k_input=0.03,
        cost_per_1k_output=0.06,
        priority=50,
    ),
    ModelInfo(
        id="gpt-4-turbo",
        provider="openai",
        display_name="GPT-4 Turbo",
        max_context_tokens=128_000,
        cost_per_1k_input=0.01,
        cost_per_1k_output=0.03,
        priority=45,
    ),
    ModelInfo(
        id="gpt-4o",
        provider="openai",
        display_name="GPT-4o",
        capabilities=["chat", "generate", "vision"],
        max_context_tokens=128_000,
        cost_per_1k_input=0.005,
        cost_per_1k_output=0.015,
        priority=35,
    ),
    ModelInfo(
        id="gpt-4o-mini",
        provider="openai",
        display_name="GPT-4o Mini",
        max_context_tokens=128_000,
        cost_per_1k_input=0.00015,
        cost_per_1k_output=0.0006,
        priority=8,
    ),
    # --- Anthropic ---
    ModelInfo(
        id="claude-3-haiku-20240307",
        provider="anthropic",
        display_name="Claude 3 Haiku",
        max_context_tokens=200_000,
        cost_per_1k_input=0.00025,
        cost_per_1k_output=0.00125,
        priority=9,
    ),
    ModelInfo(
        id="claude-3-sonnet-20240229",
        provider="anthropic",
        display_name="Claude 3 Sonnet",
        max_context_tokens=200_000,
        cost_per_1k_input=0.003,
        cost_per_1k_output=0.015,
        priority=30,
    ),
    ModelInfo(
        id="claude-3-opus-20240229",
        provider="anthropic",
        display_name="Claude 3 Opus",
        max_context_tokens=200_000,
        cost_per_1k_input=0.015,
        cost_per_1k_output=0.075,
        priority=60,
    ),
    ModelInfo(
        id="claude-3-5-sonnet-20240620",
        provider="anthropic",
        display_name="Claude 3.5 Sonnet",
        max_context_tokens=200_000,
        cost_per_1k_input=0.003,
        cost_per_1k_output=0.015,
        priority=32,
    ),
    # --- Groq (Llama / Gemma) ---
    ModelInfo(
        id="llama-3.1-70b-versatile",
        provider="groq",
        display_name="Llama 3.1 70B (Groq)",
        max_context_tokens=131_072,
        cost_per_1k_input=0.00059,
        cost_per_1k_output=0.00079,
        priority=18,
    ),
    ModelInfo(
        id="llama-3.1-8b-instant",
        provider="groq",
        display_name="Llama 3.1 8B (Groq)",
        max_context_tokens=131_072,
        cost_per_1k_input=0.00005,
        cost_per_1k_output=0.00008,
        priority=5,
    ),
    ModelInfo(
        id="gemma2-9b-it",
        provider="groq",
        display_name="Gemma 2 9B (Groq)",
        max_context_tokens=8_192,
        cost_per_1k_input=0.0002,
        cost_per_1k_output=0.0002,
        priority=11,
    ),
]

# Model alias mapping (legacy identifiers → canonical IDs)
MODEL_ALIASES: Dict[str, str] = {
    "mistral-small": "mistral-small-latest",
    "mistral-medium": "mistral-medium-latest",
    "mistral-large": "mistral-large-latest",
    "claude-3-haiku": "claude-3-haiku-20240307",
    "claude-3-sonnet": "claude-3-sonnet-20240229",
    "claude-3-opus": "claude-3-opus-20240229",
    "claude-3.5-sonnet": "claude-3-5-sonnet-20240620",
}


class ModelRegistry:
    """Central registry of all available AI models.

    Provides lookup, filtering, and availability management.
    """

    def __init__(self):
        """Initialize with the default model catalog."""
        self._models: Dict[str, ModelInfo] = {}
        self._connectors: Dict[str, BaseConnector] = {}

        # Load default models
        for model in DEFAULT_MODELS:
            self._models[model.id] = model

    # ------------------------------------------------------------------
    # Connector management
    # ------------------------------------------------------------------

    def register_connector(self, provider: str, connector: BaseConnector) -> None:
        """Register a connector for a provider.

        Args:
            provider: Provider name (must match ModelInfo.provider)
            connector: Connector instance
        """
        self._connectors[provider] = connector
        logger.info("Registered connector for provider: %s", provider)

    def get_connector(self, provider: str) -> Optional[BaseConnector]:
        """Get the connector for a specific provider."""
        return self._connectors.get(provider)

    def get_connector_for_model(self, model_id: str) -> Optional[BaseConnector]:
        """Get the connector that can serve a specific model."""
        model_id = self.resolve_alias(model_id)
        model_info = self._models.get(model_id)
        if not model_info:
            return None
        return self._connectors.get(model_info.provider)

    # ------------------------------------------------------------------
    # Model management
    # ------------------------------------------------------------------

    def register_model(self, model: ModelInfo) -> None:
        """Add or update a model in the registry."""
        self._models[model.id] = model

    def unregister_model(self, model_id: str) -> bool:
        """Remove a model from the registry."""
        return self._models.pop(model_id, None) is not None

    def get_model(self, model_id: str) -> Optional[ModelInfo]:
        """Look up a model by ID (resolves aliases)."""
        model_id = self.resolve_alias(model_id)
        return self._models.get(model_id)

    def resolve_alias(self, model_id: str) -> str:
        """Resolve a legacy alias to the canonical model ID."""
        return MODEL_ALIASES.get(model_id, model_id)

    # ------------------------------------------------------------------
    # Listing / filtering
    # ------------------------------------------------------------------

    def list_models(
        self,
        provider: Optional[str] = None,
        capability: Optional[str] = None,
        available_only: bool = False,
    ) -> List[ModelInfo]:
        """List models with optional filters.

        Args:
            provider: Filter by provider name
            capability: Filter by required capability
            available_only: Only return models marked as available

        Returns:
            List of matching ModelInfo, sorted by priority (ascending)
        """
        models = list(self._models.values())

        if provider:
            models = [m for m in models if m.provider == provider]

        if capability:
            models = [m for m in models if capability in m.capabilities]

        if available_only:
            models = [m for m in models if m.is_available]

        return sorted(models, key=lambda m: m.priority)

    def list_model_ids(self) -> List[str]:
        """Return all registered model IDs."""
        return list(self._models.keys())

    def list_providers(self) -> List[str]:
        """Return unique provider names."""
        return sorted(set(m.provider for m in self._models.values()))

    # ------------------------------------------------------------------
    # Availability
    # ------------------------------------------------------------------

    def set_availability(self, model_id: str, available: bool) -> None:
        """Mark a model as available or unavailable."""
        model = self.get_model(model_id)
        if model:
            model.is_available = available

    def refresh_availability(self) -> Dict[str, bool]:
        """Run health checks on all registered connectors and update model
        availability accordingly.

        Returns:
            Mapping of provider → health status
        """
        results: Dict[str, bool] = {}
        for provider, connector in self._connectors.items():
            try:
                healthy = connector.health_check()
            except Exception:
                healthy = False
            results[provider] = healthy

            # Update all models for this provider
            for model in self._models.values():
                if model.provider == provider:
                    model.is_available = healthy

        return results

    # ------------------------------------------------------------------
    # Fallback chain
    # ------------------------------------------------------------------

    def get_fallback_chain(
        self, primary_model_id: str, max_length: int = 3
    ) -> List[ModelInfo]:
        """Build a fallback chain starting from the given model.

        Returns models sorted by priority (excluding the primary),
        preferring models from different providers for resilience.

        Args:
            primary_model_id: The primary model to build fallbacks for
            max_length: Maximum number of fallback models

        Returns:
            Ordered list of fallback ModelInfo objects
        """
        primary = self.get_model(primary_model_id)
        if not primary:
            return []

        candidates = [
            m
            for m in self._models.values()
            if m.id != primary.id
            and m.is_available
            and "chat" in m.capabilities
        ]

        # Sort by: different provider first, then by priority
        def sort_key(m: ModelInfo) -> tuple:
            same_provider = 1 if m.provider == primary.provider else 0
            return (same_provider, m.priority)

        candidates.sort(key=sort_key)
        return candidates[:max_length]

    # ------------------------------------------------------------------
    # Cost estimation
    # ------------------------------------------------------------------

    def estimate_cost(
        self, model_id: str, tokens_input: int, tokens_output: int
    ) -> float:
        """Estimate the cost for a given model and token counts."""
        model = self.get_model(model_id)
        if not model:
            return 0.0
        return model.estimate_cost(tokens_input, tokens_output)


# -----------------------------------------------------------------------
# Module-level singleton
# -----------------------------------------------------------------------

_registry_instance: Optional[ModelRegistry] = None


def get_model_registry() -> ModelRegistry:
    """Return the global ModelRegistry singleton."""
    global _registry_instance
    if _registry_instance is None:
        _registry_instance = ModelRegistry()
    return _registry_instance


def reset_model_registry() -> None:
    """Reset the singleton (useful for tests)."""
    global _registry_instance
    _registry_instance = None
