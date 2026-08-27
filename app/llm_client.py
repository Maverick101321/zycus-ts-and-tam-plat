import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
import requests

from app import config

logger = logging.getLogger(__name__)


class LLMClient(ABC):
    """Abstract interface for LLM client providers."""

    @abstractmethod
    def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: Optional[float] = None,
        seed: Optional[int] = None,
        json_mode: bool = False,
    ) -> str:
        """Generate a text response from the LLM given a prompt and optional configuration."""
        raise NotImplementedError


class NotImplementedProvider(LLMClient):
    """Stub provider that alerts the user to configure an LLM provider."""

    def __init__(self, provider_name: Optional[str] = None):
        self.provider_name = provider_name or config.LLM_PROVIDER or "None"

    def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: Optional[float] = None,
        seed: Optional[int] = None,
        json_mode: bool = False,
    ) -> str:
        raise NotImplementedError(
            f"LLM Provider '{self.provider_name}' is not configured or not implemented. "
            "Please configure a valid provider and credentials in your .env file."
        )


class OpenRouterClient(LLMClient):
    """Concrete LLM client for OpenRouter API."""

    OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

    def __init__(
        self,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: float = 30.0,
        referer: str = "https://github.com",
        title: str = "Support-TAM-AI-Tooling",
    ):
        self.model = model or config.LLM_MODEL
        self.api_key = api_key if api_key is not None else config.LLM_API_KEY
        self.timeout = timeout
        self.referer = referer
        self.title = title

    def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: Optional[float] = None,
        seed: Optional[int] = None,
        json_mode: bool = False,
    ) -> str:
        if not self.api_key:
            raise ValueError(
                "OpenRouter API key is missing. Please set LLM_API_KEY in your .env file."
            )
        if not self.model:
            raise ValueError(
                "OpenRouter model is missing. Please set LLM_MODEL or OPENROUTER_MODELS in your .env file."
            )

        temp = temperature if temperature is not None else config.DEFAULT_TEMPERATURE
        model_seed = seed if seed is not None else config.DEFAULT_SEED

        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": self.referer,
            "X-Title": self.title,
            "Content-Type": "application/json",
        }

        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": temp,
        }

        if model_seed is not None:
            payload["seed"] = model_seed

        if json_mode:
            payload["response_format"] = {"type": "json_object"}

        response = requests.post(
            self.OPENROUTER_URL,
            headers=headers,
            json=payload,
            timeout=self.timeout,
        )
        response.raise_for_status()
        data = response.json()

        choices = data.get("choices")
        if not choices or not isinstance(choices, list):
            raise ValueError(f"Unexpected response payload structure from OpenRouter: {data}")

        content = choices[0].get("message", {}).get("content")
        if content is None:
            raise ValueError(f"Empty or missing message content in OpenRouter response: {data}")

        return content


class FallbackLLMClient(LLMClient):
    """Wrapper that tries a list of models sequentially if requests fail or timeout."""

    def __init__(
        self,
        models: List[str],
        api_key: Optional[str] = None,
        timeout: float = 30.0,
    ):
        if not models:
            raise ValueError("FallbackLLMClient requires at least one model in the models list.")
        self.models = models
        self.api_key = api_key if api_key is not None else config.LLM_API_KEY
        self.timeout = timeout

    def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: Optional[float] = None,
        seed: Optional[int] = None,
        json_mode: bool = False,
    ) -> str:
        last_error: Optional[Exception] = None
        attempted_models: List[str] = []

        for model in self.models:
            attempted_models.append(model)
            client = OpenRouterClient(
                model=model,
                api_key=self.api_key,
                timeout=self.timeout,
            )
            try:
                return client.generate(
                    prompt=prompt,
                    system=system,
                    temperature=temperature,
                    seed=seed,
                    json_mode=json_mode,
                )
            except Exception as exc:
                last_error = exc
                logger.warning(
                    "Model '%s' failed during generation: %s. Retrying with fallback model if available.",
                    model,
                    exc,
                )

        raise RuntimeError(
            f"All attempted models {attempted_models} failed. Last error: {last_error}"
        ) from last_error


def get_llm_client() -> LLMClient:
    """Factory helper to retrieve the configured LLM client instance."""
    provider = (config.LLM_PROVIDER or "").strip().lower()

    if provider == "openrouter":
        models = config.OPENROUTER_MODELS
        if not models:
            if config.LLM_MODEL:
                models = [config.LLM_MODEL]
            else:
                models = [
                    "nvidia/nemotron-3-ultra-550b-a55b:free",
                    "z-ai/glm-5.2:free",
                ]
        return FallbackLLMClient(models=models)

    return NotImplementedProvider(provider_name=config.LLM_PROVIDER)
