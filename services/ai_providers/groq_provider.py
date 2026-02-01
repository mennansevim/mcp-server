from __future__ import annotations

import os
from typing import Optional

from groq import Groq

from .base import AIProvider, AIProviderError, ChatRequest


class GroqProvider(AIProvider):
    name = "groq"

    def __init__(self, api_key: Optional[str] = None, default_model: Optional[str] = None):
        key = api_key or os.getenv("GROQ_API_KEY")
        if not key:
            raise AIProviderError("GROQ_API_KEY environment variable required")
        self._client = Groq(api_key=key)
        self._default_model = default_model or "llama-3.3-70b-versatile"

    def default_model(self) -> str:
        return self._default_model

    def chat(self, req: ChatRequest) -> str:
        try:
            resp = self._client.chat.completions.create(
                model=req.model,
                messages=[
                    {"role": "system", "content": req.system},
                    {"role": "user", "content": req.user},
                ],
                temperature=req.temperature,
                max_tokens=req.max_tokens,
            )
            return resp.choices[0].message.content or ""
        except Exception as e:
            raise AIProviderError(str(e)) from e

