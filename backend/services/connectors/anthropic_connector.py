# ⚙️ Agent World - Anthropic Connector
# Version: 0.8.0 (Épic 11 - US-071)
# Description: Connecteur pour les modèles Anthropic (Claude)

"""
Anthropic Connector for Agent World.

Connecteur utilisant le SDK officiel ``anthropic`` pour interagir
avec l'API Anthropic.  Supporte les modèles Claude 3 et 3.5.
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

ANTHROPIC_MODELS = {
    "claude-3-haiku-20240307": "Claude 3 Haiku",
    "claude-3-sonnet-20240229": "Claude 3 Sonnet",
    "claude-3-opus-20240229": "Claude 3 Opus",
    "claude-3-5-sonnet-20240620": "Claude 3.5 Sonnet",
    # Short aliases
    "claude-3-haiku": "Claude 3 Haiku",
    "claude-3-sonnet": "Claude 3 Sonnet",
    "claude-3-opus": "Claude 3 Opus",
    "claude-3.5-sonnet": "Claude 3.5 Sonnet",
}


class AnthropicConnector(BaseConnector):
    """Connector for Anthropic Claude models.

    Uses the official ``anthropic`` SDK when available, falling back to
    raw HTTP via ``httpx``.
    """

    PROVIDER = "anthropic"

    def __init__(self, api_key: Optional[str] = None):
        super().__init__()
        self._api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        self._base_url = "https://api.anthropic.com/v1"
        self._client = None

    def _get_client(self):
        if self._client is not None:
            return self._client

        if not self.is_configured:
            raise AuthenticationError(
                "ANTHROPIC_API_KEY not configured. "
                "Set the environment variable or pass api_key to the connector.",
                provider=self.PROVIDER,
            )

        try:
            from anthropic import Anthropic

            self._client = Anthropic(api_key=self._api_key)
        except ImportError:
            self._client = None
            self._logger.info("anthropic SDK not installed — using httpx fallback")

        return self._client

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate(
        self,
        prompt: str,
        model: str = "claude-3-haiku-20240307",
        max_tokens: int = 1000,
        temperature: float = 0.7,
        **kwargs: Any,
    ) -> ConnectorResponse:
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
        model: str = "claude-3-haiku-20240307",
        max_tokens: int = 1000,
        temperature: float = 0.7,
        **kwargs: Any,
    ) -> ConnectorResponse:
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
        return list(ANTHROPIC_MODELS.keys())

    def health_check(self) -> bool:
        # Anthropic doesn't have a list-models endpoint, so just check creds.
        return self.is_configured

    # ------------------------------------------------------------------
    # Internal — SDK
    # ------------------------------------------------------------------

    def _chat_with_sdk(
        self, client, messages, model, max_tokens, temperature, **kwargs
    ) -> ConnectorResponse:
        try:
            # Anthropic requires separating system messages
            system_msg = None
            chat_messages = []
            for m in messages:
                if m["role"] == "system":
                    system_msg = m["content"]
                else:
                    chat_messages.append(m)

            create_kwargs = dict(
                model=model,
                messages=chat_messages,
                max_tokens=max_tokens,
                temperature=temperature,
            )
            if system_msg:
                create_kwargs["system"] = system_msg

            (response, latency_ms) = self._timed_call(
                client.messages.create, **create_kwargs
            )

            text = ""
            if response.content:
                text = response.content[0].text

            return ConnectorResponse(
                text=text,
                message={"role": "assistant", "content": text},
                tokens_input=response.usage.input_tokens,
                tokens_output=response.usage.output_tokens,
                model=response.model,
                finish_reason=response.stop_reason or "end_turn",
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

        url = f"{self._base_url}/messages"

        # Separate system message
        system_msg = None
        chat_messages = []
        for m in messages:
            if m["role"] == "system":
                system_msg = m["content"]
            else:
                chat_messages.append(m)

        headers = {
            "x-api-key": self._api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }
        payload = {
            "model": model,
            "messages": chat_messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        if system_msg:
            payload["system"] = system_msg

        try:
            (resp, latency_ms) = self._timed_call(
                httpx.post, url, headers=headers, json=payload, timeout=60.0
            )

            if resp.status_code == 429:
                retry_after = resp.headers.get("Retry-After")
                raise RateLimitError(
                    "Anthropic rate limit exceeded",
                    provider=self.PROVIDER,
                    retry_after=float(retry_after) if retry_after else None,
                )
            if resp.status_code == 401:
                raise AuthenticationError(
                    "Invalid Anthropic API key", provider=self.PROVIDER
                )
            if resp.status_code >= 500:
                raise ProviderUnavailableError(
                    f"Anthropic server error: {resp.status_code}",
                    provider=self.PROVIDER,
                    status_code=resp.status_code,
                )

            resp.raise_for_status()
            data = resp.json()

            text = ""
            if data.get("content"):
                text = data["content"][0].get("text", "")

            usage = data.get("usage", {})

            return ConnectorResponse(
                text=text,
                message={"role": "assistant", "content": text},
                tokens_input=usage.get("input_tokens", 0),
                tokens_output=usage.get("output_tokens", 0),
                model=data.get("model", model),
                finish_reason=data.get("stop_reason", "end_turn"),
                latency_ms=latency_ms,
                raw_response=data,
            )

        except (RateLimitError, AuthenticationError, ProviderUnavailableError):
            raise
        except httpx.TimeoutException:
            raise ProviderUnavailableError(
                "Anthropic request timed out", provider=self.PROVIDER
            )
        except Exception as exc:
            raise ConnectorError(
                f"Anthropic request failed: {exc}",
                provider=self.PROVIDER,
                retryable=True,
            ) from exc

    def _raise_typed_error(self, exc: Exception) -> None:
        msg = str(exc)
        exc_type = type(exc).__name__
        if "RateLimitError" in exc_type or "429" in msg:
            raise RateLimitError(msg, provider=self.PROVIDER) from exc
        if "AuthenticationError" in exc_type or "401" in msg:
            raise AuthenticationError(msg, provider=self.PROVIDER) from exc
        if "NotFoundError" in exc_type or "404" in msg:
            raise ModelNotFoundError(msg, provider=self.PROVIDER) from exc
        if "APIStatusError" in exc_type:
            raise ProviderUnavailableError(msg, provider=self.PROVIDER) from exc
        raise ConnectorError(msg, provider=self.PROVIDER, retryable=True) from exc
