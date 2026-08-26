# Tests for Model Registry (Épic 11 - US-071)

"""Unit tests for the ModelRegistry."""

import pytest

from backend.services.model_registry import (
    DEFAULT_MODELS,
    MODEL_ALIASES,
    ModelInfo,
    ModelRegistry,
    get_model_registry,
    reset_model_registry,
)


@pytest.fixture
def registry():
    """Create a fresh registry for each test."""
    return ModelRegistry()


class TestModelRegistry:
    """Tests for ModelRegistry core functionality."""

    def test_default_models_loaded(self, registry):
        """Default models should be pre-loaded."""
        models = registry.list_model_ids()
        assert len(models) >= 15
        assert "mistral-tiny" in models
        assert "gpt-3.5-turbo" in models
        assert "claude-3-haiku-20240307" in models
        assert "llama-3.1-70b-versatile" in models

    def test_get_model(self, registry):
        model = registry.get_model("gpt-4o")
        assert model is not None
        assert model.provider == "openai"
        assert model.display_name == "GPT-4o"
        assert "vision" in model.capabilities

    def test_get_model_returns_none_for_unknown(self, registry):
        assert registry.get_model("nonexistent-model") is None

    def test_resolve_alias(self, registry):
        assert registry.resolve_alias("mistral-small") == "mistral-small-latest"
        assert registry.resolve_alias("claude-3-haiku") == "claude-3-haiku-20240307"
        # Non-alias should return as-is
        assert registry.resolve_alias("gpt-4o") == "gpt-4o"

    def test_register_model(self, registry):
        custom = ModelInfo(
            id="custom-model-1",
            provider="custom",
            display_name="Custom Model",
        )
        registry.register_model(custom)
        assert registry.get_model("custom-model-1") is not None

    def test_unregister_model(self, registry):
        assert registry.unregister_model("mistral-tiny") is True
        assert registry.get_model("mistral-tiny") is None
        # Second call should return False
        assert registry.unregister_model("mistral-tiny") is False

    def test_list_models_filter_by_provider(self, registry):
        openai_models = registry.list_models(provider="openai")
        assert all(m.provider == "openai" for m in openai_models)
        assert len(openai_models) >= 4

    def test_list_models_filter_by_capability(self, registry):
        vision_models = registry.list_models(capability="vision")
        assert all("vision" in m.capabilities for m in vision_models)

    def test_list_models_available_only(self, registry):
        registry.set_availability("gpt-4o", False)
        available = registry.list_models(available_only=True)
        ids = [m.id for m in available]
        assert "gpt-4o" not in ids

    def test_list_models_sorted_by_priority(self, registry):
        models = registry.list_models()
        priorities = [m.priority for m in models]
        assert priorities == sorted(priorities)

    def test_list_providers(self, registry):
        providers = registry.list_providers()
        assert "mistral" in providers
        assert "openai" in providers
        assert "anthropic" in providers
        assert "groq" in providers


class TestModelInfo:
    """Tests for ModelInfo data class."""

    def test_estimate_cost(self):
        model = ModelInfo(
            id="test",
            provider="test",
            display_name="Test",
            cost_per_1k_input=0.01,
            cost_per_1k_output=0.03,
        )
        cost = model.estimate_cost(tokens_input=1000, tokens_output=500)
        expected = (1000 / 1000) * 0.01 + (500 / 1000) * 0.03
        assert cost == pytest.approx(expected, abs=1e-6)

    def test_to_dict(self):
        model = ModelInfo(
            id="test-model",
            provider="test",
            display_name="Test Model",
            capabilities=["chat"],
        )
        d = model.to_dict()
        assert d["id"] == "test-model"
        assert d["provider"] == "test"
        assert d["capabilities"] == ["chat"]


class TestFallbackChain:
    """Tests for fallback chain building."""

    def test_get_fallback_chain(self, registry):
        chain = registry.get_fallback_chain("gpt-4o", max_length=3)
        assert len(chain) <= 3
        assert all(m.id != "gpt-4o" for m in chain)
        # Should prefer different providers first
        if len(chain) >= 2:
            providers = [m.provider for m in chain]
            # First fallback should be from a different provider than openai
            assert providers[0] != "openai" or len(registry.list_providers()) <= 1

    def test_get_fallback_chain_unknown_model(self, registry):
        chain = registry.get_fallback_chain("nonexistent")
        assert chain == []


class TestSingleton:
    """Tests for the module-level singleton."""

    def test_singleton_returns_same_instance(self):
        reset_model_registry()
        r1 = get_model_registry()
        r2 = get_model_registry()
        assert r1 is r2

    def test_reset_clears_singleton(self):
        r1 = get_model_registry()
        reset_model_registry()
        r2 = get_model_registry()
        assert r1 is not r2
