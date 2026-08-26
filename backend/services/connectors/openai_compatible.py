# ⚙️ Agent World - OpenAI-Compatible Connector
# Version: 0.8.0 (Épic 11 - US-071)
# Description: Connecteur générique pour endpoints compatibles OpenAI

"""
OpenAI-Compatible Connector for Agent World.

Connecteur générique réutilisant le protocole OpenAI chat/completions
pour des providers tiers : Groq (Llama, Gemma), Together AI, Ollama (local).
"""

import os
import logging
from typing import Any, Dict, List, Optional

from .base import (
    AuthenticationError,
    BaseConnector,
    ConnectorError,
    ConnectorResponse,
    ProviderUnavailableError,
    RateLimitError,
)

logger = logging.getLogger(__name__)


# Pre-configured provider profiles
PROVIDER_PROFILES: Dict[str, Dict[str, Any]] = {
    "groq": {
        "base_url": "https://api.groq.com/openai/v1",
        "env_key": "GROQ_API_KEY",
        "models": {
            "llama-3.1-70b-versatile": "Llama 3.1 70B (Groq)",
            "llama-3.1-8b-instant": "Llama 3.1 8B (Groq)",
            "gemma2-9b-it": "Gemma 2 9B (Groq)",
            "mixtral-8x7b-32768": "Mixtral 8x7B (Groq)",
        },
    },
    "together": {
        "base_url": "https://api.together.xyz/v1",
        "env_key": "TOGETHER_API_KEY",
        "models": {
            "meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo": "Llama 3.1 70B (Together)",
            "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo": "Llama 3.1 8B (Together)",
            "google/gemma-2-27b-it": "Gemma 2 27B (Together)",
        },
    },
    "ollama": {
        "base_url": "http://localhost:11434/v1",
        "env_key": None,  # No API key for local Ollama
        "models": {
            "llama3.1": "Llama 3.1 (Ollama)",
            "gemma2": "Gemma 2 (Ollama)",
            "mistral": "Mistral (Ollama)",
            "codellama": "Code Llama (Ollama)",
        },
    },
}


class OpenAICompatibleConnector(BaseConnector):
    """Generic connector for any OpenAI-compatible API.

    This allows Groq, Together AI, Ollama, and other services that
    implement the OpenAI ``/v1/chat/completions`` endpoint to be used
    seamlessly within Agent World.
    """

    PROVIDER = "openai_compatible"

    def __init__(
        self,
        provider_name: str = "groq",
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        """Initialize the connector.

        Args:
            provider_name: Name of the provider profile (groq, together, ollama).
            api_key: API key override.
            base_url: Base URL override.
        """
        super().__init__()
        self._provider_name = provider_name
        self.PROVIDER = provider_name

        profile = PROVIDER_PROFILES.get(provider_name, {})

        self._base_url = base_url or os.environ.get(
            f"{provider_name.upper()}_BASE_URL",
            profile.get("base_url", ""),
        )

        env_key = profile.get("env_key")
        if api_key:
            self._api_key = api_key
        elif env_key:
            self._api_key = os.environ.get(env_key)
        else:
            # Ollama — no key needed
            self._api_key = "ollama"

        self._models = profile.get("models", {})
        self._client = None

    @property
    def is_configured(self) -> bool:
        """Ollama doesn't need an API key, other providers do."""
        if self._provider_name == "ollama":
            return bool(self._base_url)
        return self._api_key is not None and len(self._api_key) > 0

    def _get_client(self):
        if self._client is not None:
            return self._client

        if not self.is_configured:
            raise AuthenticationError(
                f"{self._provider_name.upper()} not configured.",
                provider=self.PROVIDER,
            )

        try:
            from openai import OpenAI

            self._client = OpenAI(
                api_key=self._api_key,
                base_url=self._base_url,
            )
        except ImportError:
            self._client = None
            self._logger.info(
                "openai SDK not installed — using httpx fallback for %s",
                self._provider_name,
            )

        return self._client

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate(
        self,
        prompt: str,
        model: str = "",
        max_tokens: int = 1000,
        temperature: float = 0.7,
        **kwargs: Any,
    ) -> ConnectorResponse:
        messages = [{"role": "user", "content": prompt}]
        model = model or self._default_model()
        return self.chat(messages, model, max_tokens, temperature, **kwargs)

    def chat(
        self,
        messages: List[Dict[str, Any]],
        model: str = "",
        max_tokens: int = 1000,
        temperature: float = 0.7,
        **kwargs: Any,
    ) -> ConnectorResponse:
        model = model or self._default_model()
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
        return list(self._models.keys())

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
        headers = {"Content-Type": "application/json"}
        if self._api_key and self._api_key != "ollama":
            headers["Authorization"] = f"Bearer {self._api_key}"

        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        try:
            (resp, latency_ms) = self._timed_call(
                httpx.post, url, headers=headers, json=payload, timeout=120.0
            )

            if resp.status_code == 429:
                raise RateLimitError(
                    f"{self._provider_name} rate limit exceeded",
                    provider=self.PROVIDER,
                )
            if resp.status_code == 401:
                raise AuthenticationError(
                    f"Invalid {self._provider_name} API key",
                    provider=self.PROVIDER,
                )
            if resp.status_code >= 500:
                raise ProviderUnavailableError(
                    f"{self._provider_name} server error: {resp.status_code}",
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
                f"{self._provider_name} request timed out",
                provider=self.PROVIDER,
            )
        except Exception as exc:
            raise ConnectorError(
                f"{self._provider_name} request failed: {exc}",
                provider=self.PROVIDER,
                retryable=True,
            ) from exc

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _default_model(self) -> str:
        models = self.list_models()
        return models[0] if models else ""

    def _raise_typed_error(self, exc: Exception) -> None:
        msg = str(exc)
        exc_type = type(exc).__name__
        if "RateLimitError" in exc_type or "429" in msg:
            raise RateLimitError(msg, provider=self.PROVIDER) from exc
        if "AuthenticationError" in exc_type or "401" in msg:
            raise AuthenticationError(msg, provider=self.PROVIDER) from exc
        if "5" in msg[:1] and msg[:3].isdigit():
            raise ProviderUnavailableError(msg, provider=self.PROVIDER) from exc
        raise ConnectorError(msg, provider=self.PROVIDER, retryable=True) from exc
