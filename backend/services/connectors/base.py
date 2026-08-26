# ⚙️ Agent World - Base AI Connector
# Version: 0.8.0 (Épic 11 - Multi-Modèles)
# Description: Classe de base abstraite pour tous les connecteurs IA

"""
Base AI Connector for Agent World.

Ce module définit l'interface commune que tous les connecteurs IA
doivent implémenter, ainsi que les types de données partagés.
"""

import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class ConnectorError(Exception):
    """Base exception for connector errors."""

    def __init__(
        self,
        message: str,
        provider: str = "unknown",
        status_code: Optional[int] = None,
        retryable: bool = False,
    ):
        super().__init__(message)
        self.provider = provider
        self.status_code = status_code
        self.retryable = retryable


class RateLimitError(ConnectorError):
    """Raised when the provider rate limit is exceeded."""

    def __init__(self, message: str, provider: str, retry_after: Optional[float] = None):
        super().__init__(message, provider=provider, status_code=429, retryable=True)
        self.retry_after = retry_after


class AuthenticationError(ConnectorError):
    """Raised when authentication fails."""

    def __init__(self, message: str, provider: str):
        super().__init__(message, provider=provider, status_code=401, retryable=False)


class ModelNotFoundError(ConnectorError):
    """Raised when the requested model is not available."""

    def __init__(self, message: str, provider: str):
        super().__init__(message, provider=provider, status_code=404, retryable=False)


class ProviderUnavailableError(ConnectorError):
    """Raised when the provider is temporarily unavailable."""

    def __init__(self, message: str, provider: str, status_code: int = 503):
        super().__init__(
            message, provider=provider, status_code=status_code, retryable=True
        )


@dataclass
class ConnectorResponse:
    """Standardized response from any AI connector.

    All connectors must return this type, regardless of the provider's
    native response format.
    """

    text: str = ""
    message: Optional[Dict[str, Any]] = None
    tokens_input: int = 0
    tokens_output: int = 0
    model: str = ""
    finish_reason: str = "stop"
    latency_ms: int = 0
    raw_response: Optional[Dict[str, Any]] = None

    @property
    def tokens_total(self) -> int:
        """Total tokens used (input + output)."""
        return self.tokens_input + self.tokens_output


class BaseConnector(ABC):
    """Abstract base class for AI model connectors.

    All provider-specific connectors must inherit from this class and
    implement the abstract methods.
    """

    # Subclasses must set this to their provider name (e.g. "openai")
    PROVIDER: str = "unknown"

    def __init__(self):
        """Initialize the connector."""
        self._api_key: Optional[str] = None
        self._base_url: Optional[str] = None
        self._logger = logging.getLogger(f"{__name__}.{self.PROVIDER}")

    @property
    def is_configured(self) -> bool:
        """Check if the connector has valid credentials."""
        return self._api_key is not None and len(self._api_key) > 0

    @abstractmethod
    def generate(
        self,
        prompt: str,
        model: str,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        **kwargs: Any,
    ) -> ConnectorResponse:
        """Generate text from a prompt.

        Args:
            prompt: Input prompt
            model: Model identifier (provider-specific)
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0-2)
            **kwargs: Additional provider-specific parameters

        Returns:
            ConnectorResponse with generated text and metadata

        Raises:
            ConnectorError: If the request fails
        """

    @abstractmethod
    def chat(
        self,
        messages: List[Dict[str, Any]],
        model: str,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        **kwargs: Any,
    ) -> ConnectorResponse:
        """Generate a chat completion.

        Args:
            messages: List of message dicts with 'role' and 'content' keys
            model: Model identifier (provider-specific)
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0-2)
            **kwargs: Additional provider-specific parameters

        Returns:
            ConnectorResponse with assistant reply and metadata

        Raises:
            ConnectorError: If the request fails
        """

    def health_check(self) -> bool:
        """Check if the connector is operational.

        Default implementation just checks that credentials are configured.
        Subclasses may override to actually ping the provider.

        Returns:
            True if the connector is ready to serve requests
        """
        return self.is_configured

    @abstractmethod
    def list_models(self) -> List[str]:
        """Return a list of model identifiers this connector supports.

        Returns:
            List of model ID strings
        """

    def _timed_call(self, func, *args, **kwargs) -> tuple:
        """Execute *func* and return (result, latency_ms).

        Utility used by subclasses to measure call duration.
        """
        start = time.perf_counter()
        result = func(*args, **kwargs)
        latency_ms = int((time.perf_counter() - start) * 1000)
        return result, latency_ms

    def _handle_error(self, error: Exception) -> ConnectorResponse:
        """Produce a non-fatal error response.

        Use this only when the caller explicitly opts out of exceptions
        (e.g. benchmarks that must not abort on a single failure).
        """
        self._logger.warning("Connector error for %s: %s", self.PROVIDER, error)
        return ConnectorResponse(
            text=f"Error from {self.PROVIDER}: {error}",
            tokens_input=0,
            tokens_output=0,
            model="",
            finish_reason="error",
        )
