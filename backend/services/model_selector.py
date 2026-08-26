# ⚙️ Agent World - Model Selector
# Version: 0.8.0 (Épic 11 - US-073)
# Description: Sélection automatique du meilleur modèle pour une tâche

"""
Model Selector for Agent World.

Ce module implémente des stratégies de sélection automatique de modèle
basées sur le coût, la vitesse, la qualité ou un compromis équilibré.
"""

import logging
from enum import Enum
from typing import Any, Dict, List, Optional

from .model_registry import ModelInfo, ModelRegistry

logger = logging.getLogger(__name__)


class SelectionStrategy(str, Enum):
    """Model selection strategies."""

    CHEAPEST = "cheapest"
    FASTEST = "fastest"
    BEST_QUALITY = "best_quality"
    BALANCED = "balanced"


class ModelSelector:
    """Selects the best model for a given task based on a strategy.

    The selector considers:
    - Model capabilities (does it support the required features?)
    - Cost per token
    - Context window size
    - Priority/quality ranking
    - Availability
    """

    def __init__(self, registry: ModelRegistry):
        self.registry = registry

    def select(
        self,
        strategy: SelectionStrategy = SelectionStrategy.BALANCED,
        required_capabilities: Optional[List[str]] = None,
        max_cost_per_1k: Optional[float] = None,
        min_context_tokens: Optional[int] = None,
        preferred_provider: Optional[str] = None,
        exclude_models: Optional[List[str]] = None,
    ) -> Optional[ModelInfo]:
        """Select the best model according to the given strategy.

        Args:
            strategy: Selection strategy to use
            required_capabilities: Required model capabilities (e.g. ["chat"])
            max_cost_per_1k: Maximum acceptable cost per 1K output tokens
            min_context_tokens: Minimum required context window
            preferred_provider: Prefer models from this provider
            exclude_models: Model IDs to exclude from selection

        Returns:
            The selected ModelInfo or None if no model matches
        """
        candidates = self._filter_candidates(
            required_capabilities=required_capabilities,
            max_cost_per_1k=max_cost_per_1k,
            min_context_tokens=min_context_tokens,
            exclude_models=exclude_models,
        )

        if not candidates:
            logger.warning("No candidate models match the given criteria")
            return None

        if strategy == SelectionStrategy.CHEAPEST:
            selected = self._select_cheapest(candidates)
        elif strategy == SelectionStrategy.FASTEST:
            selected = self._select_fastest(candidates)
        elif strategy == SelectionStrategy.BEST_QUALITY:
            selected = self._select_best_quality(candidates)
        elif strategy == SelectionStrategy.BALANCED:
            selected = self._select_balanced(candidates, preferred_provider)
        else:
            selected = candidates[0]

        logger.info(
            "Selected model '%s' (%s) using strategy '%s' from %d candidates",
            selected.id,
            selected.provider,
            strategy.value,
            len(candidates),
        )
        return selected

    # ------------------------------------------------------------------
    # Filtering
    # ------------------------------------------------------------------

    def _filter_candidates(
        self,
        required_capabilities: Optional[List[str]] = None,
        max_cost_per_1k: Optional[float] = None,
        min_context_tokens: Optional[int] = None,
        exclude_models: Optional[List[str]] = None,
    ) -> List[ModelInfo]:
        """Filter models based on hard constraints."""
        models = self.registry.list_models(available_only=True)

        if required_capabilities:
            models = [
                m
                for m in models
                if all(cap in m.capabilities for cap in required_capabilities)
            ]

        if max_cost_per_1k is not None:
            models = [m for m in models if m.cost_per_1k_output <= max_cost_per_1k]

        if min_context_tokens is not None:
            models = [m for m in models if m.max_context_tokens >= min_context_tokens]

        if exclude_models:
            models = [m for m in models if m.id not in exclude_models]

        return models

    # ------------------------------------------------------------------
    # Strategy implementations
    # ------------------------------------------------------------------

    def _select_cheapest(self, candidates: List[ModelInfo]) -> ModelInfo:
        """Pick the cheapest model (lowest cost per 1K output tokens)."""
        return min(candidates, key=lambda m: m.cost_per_1k_output)

    def _select_fastest(self, candidates: List[ModelInfo]) -> ModelInfo:
        """Pick the fastest model.

        Heuristic: smaller models with lower priority numbers tend to be
        faster.  In a real system this would use latency benchmarks.
        """
        return min(candidates, key=lambda m: m.priority)

    def _select_best_quality(self, candidates: List[ModelInfo]) -> ModelInfo:
        """Pick the highest-quality model (highest priority number = most capable)."""
        return max(candidates, key=lambda m: m.priority)

    def _select_balanced(
        self, candidates: List[ModelInfo], preferred_provider: Optional[str] = None
    ) -> ModelInfo:
        """Pick a balanced model considering cost, quality and preference.

        Scoring formula:
          score = (1 / (cost + epsilon)) * 0.4  +  priority_normalized * 0.4  +  provider_bonus * 0.2

        Lower is better for cost, higher priority = better quality.
        """
        if not candidates:
            return candidates[0]

        max_priority = max(m.priority for m in candidates) or 1
        max_cost = max(m.cost_per_1k_output for m in candidates) or 1.0

        def score(m: ModelInfo) -> float:
            cost_norm = 1.0 - (m.cost_per_1k_output / (max_cost + 1e-9))
            quality_norm = m.priority / max_priority
            provider_bonus = 0.5 if preferred_provider and m.provider == preferred_provider else 0.0
            return cost_norm * 0.4 + quality_norm * 0.4 + provider_bonus * 0.2

        return max(candidates, key=score)
