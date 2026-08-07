"""OpenAI-compatible LLM provider (used for LiteLLM gateway + Gemini via OpenAI SDK)."""

from __future__ import annotations

from typing import Any

from langchain_openai import ChatOpenAI

from app.llm.models import LLMConfig


class OpenAICompatibleProvider:
    """LLM provider using an OpenAI-compatible endpoint (LiteLLM gateway).

    Both ``openai`` and ``gemini`` strategy names resolve through this
    provider because the deployed gateway (LiteLLM) exposes an
    OpenAI-compatible ``/v1`` API for both underlying models.
    """

    def __init__(self, config: LLMConfig, api_key: str) -> None:
        self.config = config
        self.api_key = api_key

    def get_llm(self, temperature: float = 0.0, **kwargs: Any) -> ChatOpenAI:
        return ChatOpenAI(
            model=self.config.model,
            base_url=self.config.base_url,
            api_key=self.api_key,  # type: ignore[arg-type]
            temperature=temperature,
            **kwargs,  # type: ignore[arg-type]
        )

    @property
    def model_name(self) -> str:
        return self.config.model

    @property
    def provider_name(self) -> str:
        return self.config.provider
