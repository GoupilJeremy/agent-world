# 🤖 Agent World - AI Service
# Version: 0.8.0 (Épic 11 - Multi-Modèles)
# Description: Service unifié pour l'interaction avec les modèles IA

"""
AI Service for Agent World.

Ce service fournit une interface unifiée pour interagir avec les différents
modèles IA via le registre de modèles et les connecteurs.  Il supporte
le fallback automatique, le suivi des coûts et la sélection de modèle.
"""

import logging
import os
import time
from typing import Any, Dict, List, Optional

from .connectors.anthropic_connector import AnthropicConnector
from .connectors.base import BaseConnector, ConnectorError, ConnectorResponse
from .connectors.mistral import MistralConnector
from .connectors.openai_compatible import OpenAICompatibleConnector
from .connectors.openai_connector import OpenAIConnector
from .model_registry import ModelInfo, ModelRegistry, get_model_registry

logger = logging.getLogger(__name__)


class AIService:
    """Service class for interacting with AI models.

    This service provides a unified interface for different AI model providers.
    It handles authentication, request formatting, response parsing, and
    delegates to the correct connector via the model registry.
    """

    def __init__(self, registry: Optional[ModelRegistry] = None):
        """Initialize the AIService.

        Args:
            registry: Optional model registry.  Uses the global singleton
                if not provided.
        """
        self.registry = registry or get_model_registry()
        self.default_model = os.environ.get("DEFAULT_AI_MODEL", "mistral-tiny")

        # Register all connectors with the registry
        self._register_connectors()

    def _register_connectors(self) -> None:
        """Create and register connectors for all known providers."""
        connectors: Dict[str, BaseConnector] = {
            "mistral": MistralConnector(),
            "openai": OpenAIConnector(),
            "anthropic": AnthropicConnector(),
            "groq": OpenAICompatibleConnector(provider_name="groq"),
            "together": OpenAICompatibleConnector(provider_name="together"),
            "ollama": OpenAICompatibleConnector(provider_name="ollama"),
        }

        for provider, connector in connectors.items():
            self.registry.register_connector(provider, connector)

        # Log which providers are configured
        configured = [p for p, c in connectors.items() if c.is_configured]
        logger.info(
            "AI Service initialized with %d/%d providers configured: %s",
            len(configured),
            len(connectors),
            ", ".join(configured) if configured else "(none)",
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        configuration: Optional[Dict[str, Any]] = None,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        stream: bool = False,
    ) -> Dict[str, Any]:
        """Generate text using the specified AI model.

        Args:
            prompt: The input prompt for the model
            model: Model identifier (default: self.default_model)
            configuration: Optional model configuration overrides
            max_tokens: Maximum number of tokens to generate (default: 1000)
            temperature: Sampling temperature (0-2, default: 0.7)
            stream: Whether to stream the response (default: False)

        Returns:
            Dictionary containing the generated text and metadata

        Raises:
            ValueError: If model is not supported or configuration is invalid
            ConnectorError: If the API call fails
        """
        model = model or self.default_model
        resolved_model = self.registry.resolve_alias(model)

        connector = self.registry.get_connector_for_model(resolved_model)
        if connector is None:
            raise ValueError(
                f"No connector available for model '{model}'. "
                f"Available models: {self.get_available_models()}"
            )

        # Build kwargs from configuration
        kwargs: Dict[str, Any] = {}
        if configuration:
            kwargs.update(configuration)

        response = connector.generate(
            prompt=prompt,
            model=resolved_model,
            max_tokens=max_tokens,
            temperature=temperature,
            **kwargs,
        )

        model_info = self.registry.get_model(resolved_model)
        cost = 0.0
        if model_info:
            cost = model_info.estimate_cost(
                response.tokens_input, response.tokens_output
            )

        return self._format_response(response, model, cost)

    def chat(
        self,
        messages: List[Dict[str, Any]],
        model: Optional[str] = None,
        configuration: Optional[Dict[str, Any]] = None,
        max_tokens: int = 1000,
        temperature: float = 0.7,
    ) -> Dict[str, Any]:
        """Generate a chat completion using the specified AI model.

        Args:
            messages: List of message dictionaries
                (role: 'user', 'assistant', or 'system'; content: str)
            model: Model identifier (default: self.default_model)
            configuration: Optional model configuration overrides
            max_tokens: Maximum number of tokens to generate (default: 1000)
            temperature: Sampling temperature (0-2, default: 0.7)

        Returns:
            Dictionary containing the assistant's response and metadata
        """
        model = model or self.default_model
        resolved_model = self.registry.resolve_alias(model)

        connector = self.registry.get_connector_for_model(resolved_model)
        if connector is None:
            raise ValueError(
                f"No connector available for model '{model}'. "
                f"Available models: {self.get_available_models()}"
            )

        kwargs: Dict[str, Any] = {}
        if configuration:
            kwargs.update(configuration)

        response = connector.chat(
            messages=messages,
            model=resolved_model,
            max_tokens=max_tokens,
            temperature=temperature,
            **kwargs,
        )

        model_info = self.registry.get_model(resolved_model)
        cost = 0.0
        if model_info:
            cost = model_info.estimate_cost(
                response.tokens_input, response.tokens_output
            )

        return self._format_chat_response(response, model, messages, cost)

    def get_available_models(self) -> List[str]:
        """Get a list of all available model identifiers.

        Returns:
            List of available model identifiers
        """
        return self.registry.list_model_ids()

    def get_models_info(
        self,
        provider: Optional[str] = None,
        available_only: bool = False,
    ) -> List[Dict[str, Any]]:
        """Get detailed info for all models.

        Args:
            provider: Optional filter by provider
            available_only: If True, only return available models

        Returns:
            List of model info dictionaries
        """
        models = self.registry.list_models(
            provider=provider, available_only=available_only
        )
        return [m.to_dict() for m in models]

    def validate_model(self, model: str) -> bool:
        """Validate if a model is supported.

        Args:
            model: Model identifier to validate

        Returns:
            True if model is supported, False otherwise
        """
        resolved = self.registry.resolve_alias(model)
        return self.registry.get_model(resolved) is not None

    def get_model_info(self, model: str) -> Optional[Dict[str, Any]]:
        """Get info for a single model.

        Args:
            model: Model identifier

        Returns:
            Model info dictionary or None
        """
        resolved = self.registry.resolve_alias(model)
        model_info = self.registry.get_model(resolved)
        return model_info.to_dict() if model_info else None

    def health_check(self) -> Dict[str, bool]:
        """Run health checks on all providers.

        Returns:
            Mapping of provider name → healthy status
        """
        return self.registry.refresh_availability()

    # ------------------------------------------------------------------
    # Response formatting
    # ------------------------------------------------------------------

    def _format_response(
        self, response: ConnectorResponse, model: str, cost_usd: float
    ) -> Dict[str, Any]:
        """Format a generate() response into the API output dict."""
        model_info = self.registry.get_model(
            self.registry.resolve_alias(model)
        )
        return {
            "model": model,
            "model_type": model_info.provider if model_info else "unknown",
            "prompt": "",  # callers can add this themselves
            "generated_text": response.text,
            "tokens_used": response.tokens_total,
            "tokens_input": response.tokens_input,
            "tokens_output": response.tokens_output,
            "duration_seconds": response.latency_ms / 1000.0,
            "latency_ms": response.latency_ms,
            "finish_reason": response.finish_reason,
            "cost_usd": cost_usd,
        }

    def _format_chat_response(
        self,
        response: ConnectorResponse,
        model: str,
        messages: List[Dict[str, Any]],
        cost_usd: float,
    ) -> Dict[str, Any]:
        """Format a chat() response into the API output dict."""
        model_info = self.registry.get_model(
            self.registry.resolve_alias(model)
        )
        return {
            "model": model,
            "model_type": model_info.provider if model_info else "unknown",
            "messages": messages,
            "response": response.message or {"role": "assistant", "content": response.text},
            "tokens_used": response.tokens_total,
            "tokens_input": response.tokens_input,
            "tokens_output": response.tokens_output,
            "duration_seconds": response.latency_ms / 1000.0,
            "latency_ms": response.latency_ms,
            "cost_usd": cost_usd,
        }


# -----------------------------------------------------------------------
# Legacy compatibility
# -----------------------------------------------------------------------
# The old AIModelType enum and BaseAIConnector class are kept below so
# that any existing code that imports them still works.  New code should
# use the connectors package and ModelRegistry directly.

from enum import Enum


class AIModelType(str, Enum):
    """Types of supported AI models (legacy, kept for backward compat)."""

    MISTRAL = "mistral"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    LLAMA = "llama"
    GEMMA = "gemma"
    GROQ = "groq"
