from __future__ import annotations

from .base import AIProvider, ChatRequest


class MockProvider(AIProvider):
    """
    Local-only provider for testing the wiring without external API keys.
    Returns a minimal, valid JSON review payload as plain text.
    """

    name = "mock"

    def __init__(self, default_model: str | None = None):
        self._default_model = default_model or "mock-1"

    def default_model(self) -> str:
        return self._default_model

    def chat(self, req: ChatRequest) -> str:
        # Return valid JSON per AIReviewer expectations
        return (
            '{'
            '"summary":"Mock review: wiring OK (provider=mock).",'
            '"score":8,'
            '"issues":[],'
            '"approval_recommended":true,'
            '"block_merge":false'
            '}'
        )

