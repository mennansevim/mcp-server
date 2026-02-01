from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

import structlog

from .base import AIProvider, AIProviderError, ChatRequest
from .factory import create_provider, default_model_for_provider

logger = structlog.get_logger()


@dataclass(frozen=True)
class SelectedProvider:
    provider_name: str
    model: str


class AIProviderRouter:
    """
    Selects provider/model according to config.

    Backward-compatible with legacy config:
      ai: { provider: "groq", model: "...", temperature: 0.3, max_tokens: 4096 }

    New config (recommended):
      ai:
        temperature: 0.3
        max_tokens: 4096
        providers:
          - name: groq
            model: llama-3.3-70b-versatile
          - name: openai
            model: gpt-4o-mini
        primary: groq
    """

    def __init__(self, ai_config: dict[str, Any]):
        self.ai_config = ai_config or {}

        self.temperature = float(self.ai_config.get("temperature", 0.3))
        self.max_tokens = int(self.ai_config.get("max_tokens", 4096))

        # Normalize providers list
        self.providers_cfg: list[dict[str, Any]] = []
        if isinstance(self.ai_config.get("providers"), list):
            self.providers_cfg = [p for p in self.ai_config["providers"] if isinstance(p, dict) and p.get("name")]
        else:
            legacy_provider = self.ai_config.get("provider", "groq")
            legacy_model = self.ai_config.get("model")
            self.providers_cfg = [{"name": legacy_provider, "model": legacy_model}]

        # Keep it simple: select a single provider.
        self.primary = (self.ai_config.get("primary") or self.providers_cfg[0]["name"]).lower()

        # Cache provider instances (lazy-init on first use)
        self._providers: dict[str, AIProvider] = {}

    def _get_provider_cfg(self, name: str) -> Optional[dict[str, Any]]:
        name_l = (name or "").lower()
        for cfg in self.providers_cfg:
            if (cfg.get("name") or "").lower() == name_l:
                return cfg
        return None

    def _get_or_create_provider(self, name: str) -> AIProvider:
        name_l = (name or "").lower()
        if name_l in self._providers:
            return self._providers[name_l]
        cfg = self._get_provider_cfg(name_l) or {"name": name_l}
        provider = create_provider(name_l, cfg)
        self._providers[name_l] = provider
        return provider

    def resolve(self, provider_override: Optional[str] = None, model_override: Optional[str] = None) -> SelectedProvider:
        """
        Resolve provider+model WITHOUT instantiating provider SDKs.
        This makes selection observable even if API keys are missing.
        """
        provider_name = (provider_override or self.primary).lower()
        cfg = self._get_provider_cfg(provider_name) or {}

        model = model_override or cfg.get("model") or default_model_for_provider(provider_name)
        return SelectedProvider(provider_name=provider_name, model=model)

    def select(
        self,
        provider_override: Optional[str] = None,
        model_override: Optional[str] = None,
    ) -> SelectedProvider:
        """
        Back-compat alias for resolve().
        """
        return self.resolve(provider_override=provider_override, model_override=model_override)

    def chat(
        self,
        system: str,
        user: str,
        provider_override: Optional[str] = None,
        model_override: Optional[str] = None,
    ) -> tuple[str, str, str]:
        """
        Single-provider chat (no fallback). Returns (provider_name, model, response_text).
        """
        selected = self.resolve(provider_override=provider_override, model_override=model_override)
        try:
            provider = self._get_or_create_provider(selected.provider_name)
            text = provider.chat(
                ChatRequest(
                    system=system,
                    user=user,
                    model=selected.model,
                    temperature=self.temperature,
                    max_tokens=self.max_tokens,
                )
            )
            return provider.name, selected.model, text
        except Exception as e:
            logger.warning("ai_provider_call_failed", provider=selected.provider_name, model=selected.model, error=str(e))
            raise AIProviderError(str(e)) from e

