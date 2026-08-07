"""LLM provider port (Strategy pattern interface)."""

from __future__ import annotations

from typing import Any, Protocol


class LLMProvider(Protocol):
    """Protocol for LLM provider strategies."""

    def get_llm(self, temperature: float = 0.0, **kwargs: Any) -> Any:
        """Get a configured chat model instance."""
        ...

    @property
    def model_name(self) -> str:
        """Get the underlying model name."""
        ...

    @property
    def provider_name(self) -> str:
        """Get the provider name (litellm, gemini)."""
        ...
