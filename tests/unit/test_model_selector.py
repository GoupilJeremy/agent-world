# Tests for Model Selector (Épic 11 - US-073)

"""Unit tests for the ModelSelector."""

import pytest

from backend.services.model_registry import ModelInfo, ModelRegistry
from backend.services.model_selector import ModelSelector, SelectionStrategy


@pytest.fixture
def registry():
    """Create a registry with controlled test models."""
    reg = ModelRegistry()
    # Clear defaults and add specific test models
    reg._models.clear()

    reg.register_model(ModelInfo(
        id="cheap-fast",
        provider="providerA",
        display_name="Cheap Fast",
        cost_per_1k_input=0.0001,
        cost_per_1k_output=0.0003,
        priority=5,
        is_available=True,
    ))
    reg.register_model(ModelInfo(
        id="expensive-quality",
        provider="providerB",
        display_name="Expensive Quality",
        cost_per_1k_input=0.03,
        cost_per_1k_output=0.06,
        priority=80,
        is_available=True,
    ))
    reg.register_model(ModelInfo(
        id="mid-balanced",
        provider="providerA",
        display_name="Mid Balanced",
        cost_per_1k_input=0.005,
        cost_per_1k_output=0.015,
        priority=40,
        is_available=True,
    ))
    reg.register_model(ModelInfo(
        id="unavailable-model",
        provider="providerC",
        display_name="Unavailable",
        cost_per_1k_input=0.001,
        cost_per_1k_output=0.002,
        priority=20,
        is_available=False,
    ))
    reg.register_model(ModelInfo(
        id="vision-model",
        provider="providerB",
        display_name="Vision Model",
        capabilities=["chat", "generate", "vision"],
        cost_per_1k_input=0.01,
        cost_per_1k_output=0.03,
        priority=60,
        is_available=True,
    ))

    return reg


@pytest.fixture
def selector(registry):
    return ModelSelector(registry)


class TestModelSelector:
    """Tests for selection strategies."""

    def test_cheapest_strategy(self, selector):
        result = selector.select(strategy=SelectionStrategy.CHEAPEST)
        assert result is not None
        assert result.id == "cheap-fast"

    def test_fastest_strategy(self, selector):
        result = selector.select(strategy=SelectionStrategy.FASTEST)
        assert result is not None
        # Fastest = lowest priority number in our heuristic
        assert result.id == "cheap-fast"

    def test_best_quality_strategy(self, selector):
        result = selector.select(strategy=SelectionStrategy.BEST_QUALITY)
        assert result is not None
        assert result.id == "expensive-quality"

    def test_balanced_strategy(self, selector):
        result = selector.select(strategy=SelectionStrategy.BALANCED)
        assert result is not None
        # Should return something reasonable, not necessarily any specific one
        assert result.is_available is True

    def test_excludes_unavailable_models(self, selector):
        result = selector.select(strategy=SelectionStrategy.CHEAPEST)
        assert result.id != "unavailable-model"

    def test_filter_by_capability(self, selector):
        result = selector.select(
            strategy=SelectionStrategy.CHEAPEST,
            required_capabilities=["vision"],
        )
        assert result is not None
        assert result.id == "vision-model"

    def test_filter_by_max_cost(self, selector):
        result = selector.select(
            strategy=SelectionStrategy.BEST_QUALITY,
            max_cost_per_1k=0.02,
        )
        assert result is not None
        # Should exclude expensive-quality (0.06) and vision-model (0.03)
        assert result.cost_per_1k_output <= 0.02

    def test_filter_returns_none_when_no_match(self, selector):
        result = selector.select(
            strategy=SelectionStrategy.CHEAPEST,
            required_capabilities=["nonexistent"],
        )
        assert result is None

    def test_preferred_provider(self, selector):
        result = selector.select(
            strategy=SelectionStrategy.BALANCED,
            preferred_provider="providerB",
        )
        assert result is not None
        # Should prefer providerB when score is close
        assert result.provider == "providerB"

    def test_exclude_specific_models(self, selector):
        result = selector.select(
            strategy=SelectionStrategy.CHEAPEST,
            exclude_models=["cheap-fast"],
        )
        assert result is not None
        assert result.id != "cheap-fast"
