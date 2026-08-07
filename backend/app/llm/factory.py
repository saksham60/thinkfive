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
        """Create the selected OpenAI-compatible LLM provider."""
        provider_name = provider_name or self.settings.llm_provider

        if provider_name == "gemini":
            if self.settings.gemini_api_key is None:
                raise ValueError("GEMINI_API_KEY is required when LLM_PROVIDER=gemini")
            config = LLMConfig(
                provider="gemini",
                model=model or self.settings.gemini_model,
                base_url=self.settings.gemini_base_url,
                temperature=temperature,
            )
            return OpenAICompatibleProvider(config, self.settings.gemini_api_key.get_secret_value())

        # ``openai`` is the legacy name used by earlier deployments for the
        # OpenAI-compatible LiteLLM gateway.
        if provider_name not in {"litellm", "openai"}:
            raise ValueError(f"Unsupported LLM provider: {provider_name}")
        if self.settings.litellm_api_key is None or not self.settings.litellm_base_url:
            raise ValueError(
                "LITELLM_API_KEY and LITELLM_BASE_URL are required when LLM_PROVIDER=litellm"
            )

        default_headers = {}
        if self.settings.litellm_team_id:
            default_headers["x-litellm-team-id"] = self.settings.litellm_team_id
        config = LLMConfig(
            provider="litellm",
            model=model or self.settings.litellm_model,
            base_url=self.settings.litellm_base_url,
            temperature=temperature,
            default_headers=default_headers,
        )
        return OpenAICompatibleProvider(config, self.settings.litellm_api_key.get_secret_value())
