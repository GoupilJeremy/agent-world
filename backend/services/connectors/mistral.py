# ⚙️ Agent World - Mistral AI Connector
# Version: 0.8.0 (Épic 11 - US-071)
# Description: Connecteur pour les modèles Mistral AI

"""
Mistral AI Connector for Agent World.

Connecteur utilisant le SDK officiel ``mistralai`` pour interagir
avec l'API Mistral.  Supporte les modèles Mistral tiny à large
et les variantes open-source (open-mistral-nemo, codestral).
"""

import os
import logging
from typing import Any, Dict, List, Optional

from .base import (
    AuthenticationError,
    BaseConnector,
    ConnectorError,
    ConnectorResponse,
    ModelNotFoundError,
    ProviderUnavailableError,
    RateLimitError,
)

logger = logging.getLogger(__name__)

# Models supported by Mistral and their display names
MISTRAL_MODELS = {
    "mistral-tiny": "Mistral Tiny",
    "mistral-small-latest": "Mistral Small",
    "mistral-medium-latest": "Mistral Medium",
    "mistral-large-latest": "Mistral Large",
    "open-mistral-nemo": "Open Mistral Nemo",
    "codestral-latest": "Codestral",
    # Legacy aliases
    "mistral-small": "Mistral Small",
    "mistral-medium": "Mistral Medium",
    "mistral-large": "Mistral Large",
}


class MistralConnector(BaseConnector):
    """Connector for Mistral AI models.

    Uses the official ``mistralai`` SDK when available, falling back to
    raw HTTP via ``httpx`` for environments where the SDK is not installed.
    """

    PROVIDER = "mistral"

    def __init__(self, api_key: Optional[str] = None):
        """Initialize the Mistral connector.

        Args:
            api_key: Mistral API key.  Falls back to the
                ``MISTRAL_API_KEY`` environment variable.
        """
        super().__init__()
        self._api_key = api_key or os.environ.get("MISTRAL_API_KEY")
        self._base_url = "https://api.mistral.ai/v1"
        self._client = None

    def _get_client(self):
        """Lazily create the Mistral client."""
        if self._client is not None:
            return self._client

        if not self.is_configured:
            raise AuthenticationError(
                "MISTRAL_API_KEY not configured. "
                "Set the environment variable or pass api_key to the connector.",
                provider=self.PROVIDER,
            )

        try:
            from mistralai import Mistral

            self._client = Mistral(api_key=self._api_key)
        except ImportError:
            # Fallback: use httpx directly
            self._client = None
            self._logger.info(
                "mistralai SDK not installed — using httpx fallback"
            )

        return self._client

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate(
        self,
        prompt: str,
        model: str = "mistral-tiny",
        max_tokens: int = 1000,
        temperature: float = 0.7,
        **kwargs: Any,
    ) -> ConnectorResponse:
        """Generate text using Mistral API.

        Mistral's API only supports the chat/completions endpoint,
        so we wrap the prompt in a single user message.
        """
        messages = [{"role": "user", "content": prompt}]
        return self.chat(
            messages=messages,
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            **kwargs,
        )

    def chat(
        self,
        messages: List[Dict[str, Any]],
        model: str = "mistral-tiny",
        max_tokens: int = 1000,
        temperature: float = 0.7,
        **kwargs: Any,
    ) -> ConnectorResponse:
        """Generate a chat completion using Mistral API."""
        client = self._get_client()

        if client is not None:
            return self._chat_with_sdk(client, messages, model, max_tokens, temperature, **kwargs)
        else:
            return self._chat_with_httpx(messages, model, max_tokens, temperature, **kwargs)

    def list_models(self) -> List[str]:
        """Return supported Mistral model identifiers."""
        return list(MISTRAL_MODELS.keys())

    def health_check(self) -> bool:
        """Check connectivity to Mistral API."""
        if not self.is_configured:
            return False
        try:
            client = self._get_client()
            if client is not None:
                client.models.list()
            return True
        except Exception:
            return False

    # ------------------------------------------------------------------
    # Internal — SDK path
    # ------------------------------------------------------------------

    def _chat_with_sdk(
        self,
        client,
        messages: List[Dict[str, Any]],
        model: str,
        max_tokens: int,
        temperature: float,
        **kwargs: Any,
    ) -> ConnectorResponse:
        """Call Mistral via the official SDK."""
        try:
            (response, latency_ms) = self._timed_call(
                client.chat.complete,
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
            )

            choice = response.choices[0]
            usage = response.usage

            return ConnectorResponse(
                text=choice.message.content,
                message={
                    "role": choice.message.role,
                    "content": choice.message.content,
                },
                tokens_input=usage.prompt_tokens,
                tokens_output=usage.completion_tokens,
                model=response.model,
                finish_reason=choice.finish_reason or "stop",
                latency_ms=latency_ms,
                raw_response=None,
            )

        except Exception as exc:
            self._raise_typed_error(exc)

    # ------------------------------------------------------------------
    # Internal — httpx fallback
    # ------------------------------------------------------------------

    def _chat_with_httpx(
        self,
        messages: List[Dict[str, Any]],
        model: str,
        max_tokens: int,
        temperature: float,
        **kwargs: Any,
    ) -> ConnectorResponse:
        """Call Mistral via raw HTTP (httpx)."""
        import httpx

        url = f"{self._base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        try:
            (resp, latency_ms) = self._timed_call(
                httpx.post, url, headers=headers, json=payload, timeout=60.0
            )

            if resp.status_code == 429:
                retry_after = resp.headers.get("Retry-After")
                raise RateLimitError(
                    "Mistral rate limit exceeded",
                    provider=self.PROVIDER,
                    retry_after=float(retry_after) if retry_after else None,
                )

            if resp.status_code == 401:
                raise AuthenticationError(
                    "Invalid Mistral API key", provider=self.PROVIDER
                )

            if resp.status_code >= 500:
                raise ProviderUnavailableError(
                    f"Mistral server error: {resp.status_code}",
                    provider=self.PROVIDER,
                    status_code=resp.status_code,
                )

            resp.raise_for_status()
            data = resp.json()

            choice = data["choices"][0]
            usage = data.get("usage", {})

            return ConnectorResponse(
                text=choice["message"]["content"],
                message=choice["message"],
                tokens_input=usage.get("prompt_tokens", 0),
                tokens_output=usage.get("completion_tokens", 0),
                model=data.get("model", model),
                finish_reason=choice.get("finish_reason", "stop"),
                latency_ms=latency_ms,
                raw_response=data,
            )

        except (RateLimitError, AuthenticationError, ProviderUnavailableError):
            raise
        except httpx.TimeoutException:
            raise ProviderUnavailableError(
                "Mistral request timed out", provider=self.PROVIDER
            )
        except Exception as exc:
            raise ConnectorError(
                f"Mistral request failed: {exc}",
                provider=self.PROVIDER,
                retryable=True,
            ) from exc

    # ------------------------------------------------------------------
    # Error mapping
    # ------------------------------------------------------------------

    def _raise_typed_error(self, exc: Exception) -> None:
        """Convert SDK/HTTP exceptions into ConnectorError subtypes."""
        msg = str(exc)
        if "rate" in msg.lower() or "429" in msg:
            raise RateLimitError(msg, provider=self.PROVIDER) from exc
        if "auth" in msg.lower() or "401" in msg:
            raise AuthenticationError(msg, provider=self.PROVIDER) from exc
        if "not found" in msg.lower() or "404" in msg:
            raise ModelNotFoundError(msg, provider=self.PROVIDER) from exc
        if "5" in msg[:1] and msg[:3].isdigit():
            raise ProviderUnavailableError(msg, provider=self.PROVIDER) from exc
        raise ConnectorError(msg, provider=self.PROVIDER, retryable=True) from exc
