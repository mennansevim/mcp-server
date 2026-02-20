from __future__ import annotations

import os
from typing import Optional

from anthropic import Anthropic

from .base import AIProvider, AIProviderError, ChatRequest


class AnthropicProvider(AIProvider):
    name = "anthropic"

    def __init__(self, api_key: Optional[str] = None, default_model: Optional[str] = None):
        key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not key:
            raise AIProviderError("ANTHROPIC_API_KEY environment variable required")
        self._client = Anthropic(api_key=key)
        self._default_model = default_model or "claude-3-5-sonnet-20241022"

    def default_model(self) -> str:
        return self._default_model

    def chat(self, req: ChatRequest) -> str:
        try:
            msg = self._client.messages.create(
                model=req.model,
                max_tokens=req.max_tokens,
                temperature=req.temperature,
                messages=[{"role": "user", "content": req.user}],
                system=req.system,
            )
            # anthropic SDK returns content list
            if not msg.content:
                return ""
            return getattr(msg.content[0], "text", "") or ""
        except Exception as e:
            raise AIProviderError(str(e)) from e

