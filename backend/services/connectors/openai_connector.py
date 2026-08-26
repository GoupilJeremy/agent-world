# ⚙️ Agent World - OpenAI Connector
# Version: 0.8.0 (Épic 11 - US-071)
# Description: Connecteur pour les modèles OpenAI

"""
OpenAI Connector for Agent World.

Connecteur utilisant le SDK officiel ``openai`` pour interagir
avec l'API OpenAI.  Supporte GPT-3.5, GPT-4, GPT-4o et leurs variantes.
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

OPENAI_MODELS = {
    "gpt-3.5-turbo": "GPT-3.5 Turbo",
    "gpt-4": "GPT-4",
    "gpt-4-turbo": "GPT-4 Turbo",
    "gpt-4o": "GPT-4o",
    "gpt-4o-mini": "GPT-4o Mini",
}


class OpenAIConnector(BaseConnector):
    """Connector for OpenAI models.

    Uses the official ``openai`` SDK when available, falling back to
    raw HTTP via ``httpx``.
    """

    PROVIDER = "openai"

    def __init__(self, api_key: Optional[str] = None):
        super().__init__()
        self._api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self._base_url = "https://api.openai.com/v1"
        self._client = None

    def _get_client(self):
        """Lazily create the OpenAI client."""
        if self._client is not None:
            return self._client

        if not self.is_configured:
            raise AuthenticationError(
                "OPENAI_API_KEY not configured. "
                "Set the environment variable or pass api_key to the connector.",
                provider=self.PROVIDER,
            )

        try:
            from openai import OpenAI

            self._client = OpenAI(api_key=self._api_key)
        except ImportError:
            self._client = None
            self._logger.info("openai SDK not installed — using httpx fallback")

        return self._client

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate(
        self,
        prompt: str,
        model: str = "gpt-3.5-turbo",
        max_tokens: int = 1000,
        temperature: float = 0.7,
        **kwargs: Any,
    ) -> ConnectorResponse:
        """Generate text using OpenAI.  Wraps prompt into a chat request."""
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
        model: str = "gpt-3.5-turbo",
        max_tokens: int = 1000,
        temperature: float = 0.7,
        **kwargs: Any,
    ) -> ConnectorResponse:
        """Generate a chat completion using OpenAI API."""
        client = self._get_client()

        if client is not None:
            return self._chat_with_sdk(
                client, messages, model, max_tokens, temperature, **kwargs
            )
        else:
            return self._chat_with_httpx(
                messages, model, max_tokens, temperature, **kwargs
            )

    def list_models(self) -> List[str]:
        return list(OPENAI_MODELS.keys())

    def health_check(self) -> bool:
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
    # Internal — SDK
    # ------------------------------------------------------------------

    def _chat_with_sdk(
        self, client, messages, model, max_tokens, temperature, **kwargs
    ) -> ConnectorResponse:
        try:
            (response, latency_ms) = self._timed_call(
                client.chat.completions.create,
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
            )

            choice = response.choices[0]
            usage = response.usage

            return ConnectorResponse(
                text=choice.message.content or "",
                message={
                    "role": choice.message.role,
                    "content": choice.message.content or "",
                },
                tokens_input=usage.prompt_tokens if usage else 0,
                tokens_output=usage.completion_tokens if usage else 0,
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
        self, messages, model, max_tokens, temperature, **kwargs
    ) -> ConnectorResponse:
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
                    "OpenAI rate limit exceeded",
                    provider=self.PROVIDER,
                    retry_after=float(retry_after) if retry_after else None,
                )
            if resp.status_code == 401:
                raise AuthenticationError(
                    "Invalid OpenAI API key", provider=self.PROVIDER
                )
            if resp.status_code >= 500:
                raise ProviderUnavailableError(
                    f"OpenAI server error: {resp.status_code}",
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
                "OpenAI request timed out", provider=self.PROVIDER
            )
        except Exception as exc:
            raise ConnectorError(
                f"OpenAI request failed: {exc}",
                provider=self.PROVIDER,
                retryable=True,
            ) from exc

    # ------------------------------------------------------------------
    # Error mapping
    # ------------------------------------------------------------------

    def _raise_typed_error(self, exc: Exception) -> None:
        msg = str(exc)
        exc_type = type(exc).__name__

        # Check for openai SDK-specific exceptions
        if "RateLimitError" in exc_type or "429" in msg:
            raise RateLimitError(msg, provider=self.PROVIDER) from exc
        if "AuthenticationError" in exc_type or "401" in msg:
            raise AuthenticationError(msg, provider=self.PROVIDER) from exc
        if "NotFoundError" in exc_type or "404" in msg:
            raise ModelNotFoundError(msg, provider=self.PROVIDER) from exc
        if "APIStatusError" in exc_type and ("5" in msg[:3]):
            raise ProviderUnavailableError(msg, provider=self.PROVIDER) from exc
        raise ConnectorError(msg, provider=self.PROVIDER, retryable=True) from exc
