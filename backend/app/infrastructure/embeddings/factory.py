"""Embedding provider factory (Strategy pattern for embedding models)."""

from __future__ import annotations

from typing import Protocol

from openai import AsyncOpenAI


class EmbeddingProvider(Protocol):
    """Protocol for embedding provider strategies."""

    async def embed(self, text: str) -> list[float]:
        """Embed a single text into a vector."""
        ...


class OpenAIEmbeddingProvider:
    """OpenAI-compatible embedding provider (via LiteLLM gateway)."""

    def __init__(self, api_key: str, base_url: str, model: str = "text-embedding-3-small") -> None:
        self.client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        self.model = model

    async def embed(self, text: str) -> list[float]:
        response = await self.client.embeddings.create(model=self.model, input=text)
        return response.data[0].embedding


class EmbeddingFactory:
    """Factory for embedding providers."""

    def __init__(self, settings: object) -> None:
        self.settings = settings

    def create(self) -> EmbeddingProvider:
        s = self.settings
        return OpenAIEmbeddingProvider(
            api_key=s.openai_api_key.get_secret_value(),  # type: ignore[attr-defined]
            base_url=s.openai_base_url,  # type: ignore[attr-defined]
            model=s.embedding_model,  # type: ignore[attr-defined]
        )
