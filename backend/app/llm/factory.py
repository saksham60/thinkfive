"""LLM provider factory (Factory pattern)."""

from __future__ import annotations

from app.core.config import Settings
from app.llm.models import LLMConfig
from app.llm.port import LLMProvider
from app.llm.providers.openai import OpenAICompatibleProvider


class LLMFactory:
    """Factory for constructing configured LLM providers."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def create(
        self,
        provider_name: str | None = None,
        model: str | None = None,
        temperature: float = 0.0,
    ) -> LLMProvider:
        """Create an LLM provider instance.

        Both ``openai`` and ``gemini`` route through the same LiteLLM
        OpenAI-compatible gateway, differing only by the configured model.
        """
        provider_name = provider_name or self.settings.llm_provider

        if provider_name == "gemini":
            config = LLMConfig(
                provider="gemini",
                model=model or self.settings.gemini_model,
                base_url=self.settings.litellm_base_url,
                temperature=temperature,
            )
            return OpenAICompatibleProvider(config, self.settings.litellm_api_key.get_secret_value())

        # default: openai (LiteLLM gateway)
        config = LLMConfig(
            provider="openai",
            model=model or self.settings.openai_model,
            base_url=self.settings.openai_base_url,
            temperature=temperature,
        )
        return OpenAICompatibleProvider(config, self.settings.openai_api_key.get_secret_value())
