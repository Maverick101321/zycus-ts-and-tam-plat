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

    def __repr__(self) -> str:
        return f"NotImplementedProvider(provider_name={self.provider_name!r})"

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

    def __repr__(self) -> str:
        return f"OpenRouterClient(model={self.model!r})"

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
        if not response.ok:
            raise RuntimeError(
                f"OpenRouter API error ({response.status_code}): {response.text}"
            )
        data = response.json()

        choices = data.get("choices")
        if not choices or not isinstance(choices, list):
            raise ValueError(f"Unexpected response payload structure from OpenRouter: {data}")

        content = choices[0].get("message", {}).get("content")
        if content is None:
            raise ValueError(f"Empty or missing message content in OpenRouter response: {data}")

        return content


class GroqClient(LLMClient):
    """Concrete LLM client for Groq API."""

    GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

    def __init__(
        self,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: float = 30.0,
    ):
        self.model = model or config.GROQ_MODEL
        self.api_key = api_key if api_key is not None else config.GROQ_API_KEY
        self.timeout = timeout

    def __repr__(self) -> str:
        return f"GroqClient(model={self.model!r})"

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
                "Groq API key is missing. Please set GROQ_API_KEY in your .env file."
            )
        if not self.model:
            raise ValueError(
                "Groq model is missing. Please set GROQ_MODEL in your .env file."
            )

        temp = temperature if temperature is not None else config.DEFAULT_TEMPERATURE
        model_seed = seed if seed is not None else config.DEFAULT_SEED

        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        headers = {
            "Authorization": f"Bearer {self.api_key}",
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
            self.GROQ_URL,
            headers=headers,
            json=payload,
            timeout=self.timeout,
        )
        if not response.ok:
            raise RuntimeError(
                f"Groq API error ({response.status_code}): {response.text}"
            )
        data = response.json()

        choices = data.get("choices")
        if not choices or not isinstance(choices, list):
            raise ValueError(f"Unexpected response payload structure from Groq: {data}")

        content = choices[0].get("message", {}).get("content")
        if content is None:
            raise ValueError(f"Empty or missing message content in Groq response: {data}")

        return content


class FallbackLLMClient(LLMClient):
    """Wrapper that tries a list of pre-configured LLMClient instances sequentially."""

    def __init__(self, clients: List[LLMClient]):
        if not clients:
            raise ValueError(
                "FallbackLLMClient requires at least one LLMClient instance in the clients list."
            )
        self.clients = clients

    def __repr__(self) -> str:
        return f"FallbackLLMClient(clients={self.clients!r})"

    def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: Optional[float] = None,
        seed: Optional[int] = None,
        json_mode: bool = False,
    ) -> str:
        last_error: Optional[Exception] = None
        attempted_clients: List[str] = []

        for client in self.clients:
            client_repr = repr(client)
            attempted_clients.append(client_repr)
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
                    "Client %s failed during generation: %s. Retrying with next client in fallback chain...",
                    client_repr,
                    exc,
                )

        raise RuntimeError(
            f"All attempted clients {attempted_clients} failed. Last error: {last_error}"
        ) from last_error


def get_llm_client() -> LLMClient:
    """Factory helper to retrieve the configured LLM client instance."""
    provider = (config.LLM_PROVIDER or "").strip().lower()

    if provider == "openrouter":
        openrouter_models = config.OPENROUTER_MODELS
        if not openrouter_models:
            openrouter_models = [
                "nvidia/nemotron-3-ultra-550b-a55b:free",
                "z-ai/glm-5.2:free",
            ]
        clients: List[LLMClient] = [
            OpenRouterClient(model=model) for model in openrouter_models
        ]
        clients.append(GroqClient(model=config.GROQ_MODEL))
        return FallbackLLMClient(clients=clients)

    return NotImplementedProvider(provider_name=config.LLM_PROVIDER)
