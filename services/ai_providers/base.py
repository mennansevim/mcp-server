"""
Provider-agnostic AI client interface.

This module exists to keep services/ai_reviewer.py and services/rule_generator.py
decoupled from specific SDKs (OpenAI/Anthropic/Groq/etc.).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


class AIProviderError(RuntimeError):
    """Raised when an AI provider call fails."""


@dataclass(frozen=True)
class ChatRequest:
    system: str
    user: str
    model: str
    temperature: float = 0.3
    max_tokens: int = 4096


class AIProvider(ABC):
    """Abstract base class for AI providers."""

    name: str

    @abstractmethod
    def default_model(self) -> str:
        """Return provider default model name."""

    @abstractmethod
    def chat(self, req: ChatRequest) -> str:
        """Run a chat completion and return plain text."""

    def resolve_model(self, model: Optional[str]) -> str:
        return model or self.default_model()

