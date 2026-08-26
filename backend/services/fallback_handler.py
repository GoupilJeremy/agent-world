# ⚙️ Agent World - Fallback Handler
# Version: 0.8.0 (Épic 11 - US-074)
# Description: Gestion du fallback automatique entre modèles IA

"""
Fallback Handler for Agent World.

Ce module gère le basculement automatique vers un modèle alternatif
lorsqu'un appel échoue (rate limit, timeout, erreur serveur, quota épuisé).
"""

import logging
import time
from typing import Any, Callable, Dict, List, Optional, Tuple

from .connectors.base import (
    BaseConnector,
    ConnectorError,
    ConnectorResponse,
    ProviderUnavailableError,
    RateLimitError,
)
from .model_registry import ModelInfo, ModelRegistry

logger = logging.getLogger(__name__)


class FallbackResult:
    """Result of an execution attempt with fallback information."""

    def __init__(
        self,
        response: ConnectorResponse,
        model_used: str,
        attempts: int,
        fallback_chain_used: List[str],
    ):
        self.response = response
        self.model_used = model_used
        self.attempts = attempts
        self.fallback_chain_used = fallback_chain_used

    @property
    def used_fallback(self) -> bool:
        """True if the primary model failed and a fallback was used."""
        return self.attempts > 1


class FallbackHandler:
    """Manages automatic model fallback on failure.

    When a primary model call fails with a retryable error, the handler
    automatically tries the next model in the fallback chain.

    Attributes:
        registry: The model registry to query for fallback candidates.
        max_retries: Maximum number of fallback attempts (default: 3).
        retry_delay_seconds: Base delay between retries (default: 1.0).
    """

    def __init__(
        self,
        registry: ModelRegistry,
        max_retries: int = 3,
        retry_delay_seconds: float = 1.0,
    ):
        self.registry = registry
        self.max_retries = max_retries
        self.retry_delay_seconds = retry_delay_seconds

    def execute_with_fallback(
        self,
        call_fn: Callable[..., ConnectorResponse],
        primary_model: str,
        fallback_chain: Optional[List[str]] = None,
        **call_kwargs: Any,
    ) -> FallbackResult:
        """Execute a connector call with automatic fallback.

        Args:
            call_fn: A callable that accepts (model=..., **call_kwargs)
                and returns a ConnectorResponse.  Typically a bound method
                like ``connector.chat`` or ``connector.generate``.
            primary_model: The preferred model ID.
            fallback_chain: Optional explicit list of fallback model IDs.
                If not provided, the handler builds one from the registry.
            **call_kwargs: Extra keyword arguments forwarded to *call_fn*.

        Returns:
            FallbackResult with the response and metadata about the attempt.

        Raises:
            ConnectorError: If all models in the chain fail.
        """
        # Build the ordered list of models to try
        models_to_try = self._build_chain(primary_model, fallback_chain)

        attempts = 0
        chain_used: List[str] = []
        last_error: Optional[Exception] = None

        for model_id in models_to_try:
            attempts += 1
            chain_used.append(model_id)

            connector = self.registry.get_connector_for_model(model_id)
            if connector is None:
                logger.warning(
                    "No connector for model '%s', skipping in fallback chain",
                    model_id,
                )
                continue

            try:
                logger.info(
                    "Attempting model '%s' (attempt %d/%d)",
                    model_id,
                    attempts,
                    len(models_to_try),
                )

                response = call_fn(connector=connector, model=model_id, **call_kwargs)

                if attempts > 1:
                    logger.info(
                        "Fallback succeeded with model '%s' after %d attempts",
                        model_id,
                        attempts,
                    )

                return FallbackResult(
                    response=response,
                    model_used=model_id,
                    attempts=attempts,
                    fallback_chain_used=chain_used,
                )

            except ConnectorError as exc:
                last_error = exc
                logger.warning(
                    "Model '%s' failed (%s): %s — retryable=%s",
                    model_id,
                    type(exc).__name__,
                    exc,
                    exc.retryable,
                )

                if not exc.retryable:
                    # Non-retryable errors (e.g. auth) should not trigger
                    # further fallback for the same provider
                    logger.warning(
                        "Non-retryable error from '%s', continuing chain",
                        model_id,
                    )

                # Handle rate-limit specific delay
                if isinstance(exc, RateLimitError) and exc.retry_after:
                    delay = min(exc.retry_after, 10.0)
                    logger.info("Rate limited, waiting %.1fs", delay)
                    time.sleep(delay)
                elif attempts < len(models_to_try):
                    time.sleep(self.retry_delay_seconds)

            except Exception as exc:
                last_error = exc
                logger.error(
                    "Unexpected error from model '%s': %s",
                    model_id,
                    exc,
                )
                if attempts < len(models_to_try):
                    time.sleep(self.retry_delay_seconds)

        # All attempts exhausted
        raise ConnectorError(
            f"All {attempts} model(s) failed. "
            f"Chain tried: {chain_used}. "
            f"Last error: {last_error}",
            provider="fallback",
            retryable=False,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _build_chain(
        self,
        primary_model: str,
        explicit_chain: Optional[List[str]] = None,
    ) -> List[str]:
        """Build the ordered list of models to attempt.

        Always starts with the primary model, then appends explicit
        fallbacks or auto-generated ones from the registry.
        """
        chain = [self.registry.resolve_alias(primary_model)]

        if explicit_chain:
            for m in explicit_chain:
                resolved = self.registry.resolve_alias(m)
                if resolved not in chain:
                    chain.append(resolved)
        else:
            fallbacks = self.registry.get_fallback_chain(
                chain[0], max_length=self.max_retries
            )
            for fb in fallbacks:
                if fb.id not in chain:
                    chain.append(fb.id)

        return chain[: self.max_retries + 1]
