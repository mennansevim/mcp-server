from __future__ import annotations

from typing import Any, Optional

from .base import AIProvider, AIProviderError
from .anthropic_provider import AnthropicProvider
from .groq_provider import GroqProvider
from .openai_provider import OpenAIProvider
from .mock_provider import MockProvider


def default_model_for_provider(name: str) -> str:
    name_l = (name or "").lower()
    if name_l == "openai":
        return "gpt-4-turbo-preview"
    if name_l == "anthropic":
        return "claude-3-5-sonnet-20241022"
    if name_l == "groq":
        return "llama-3.3-70b-versatile"
    if name_l == "mock":
        return "mock-1"
    raise AIProviderError(f"Unsupported AI provider: {name}")


def create_provider(name: str, provider_cfg: Optional[dict[str, Any]] = None) -> AIProvider:
    """
    Factory for supported providers.

    provider_cfg keys (optional):
    - model: str
    - api_key: str (discouraged; prefer env)
    """
    cfg = provider_cfg or {}
    name_l = (name or "").lower()
    model = cfg.get("model")
    api_key = cfg.get("api_key")

    if name_l == "openai":
        return OpenAIProvider(api_key=api_key, default_model=model)
    if name_l == "anthropic":
        return AnthropicProvider(api_key=api_key, default_model=model)
    if name_l == "groq":
        return GroqProvider(api_key=api_key, default_model=model)
    if name_l == "mock":
        return MockProvider(default_model=model)

    raise AIProviderError(f"Unsupported AI provider: {name}")

