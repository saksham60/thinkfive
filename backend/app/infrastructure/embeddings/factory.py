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
    """Embedding provider using an OpenAI-compatible endpoint."""

    def __init__(
        self,
        api_key: str,
        base_url: str,
        model: str = "text-embedding-3-small",
        dimensions: int | None = None,
    ) -> None:
        self.client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        self.model = model
        self.dimensions = dimensions

    async def embed(self, text: str) -> list[float]:
        kwargs = {"model": self.model, "input": text}
        if self.dimensions is not None:
            kwargs["dimensions"] = self.dimensions
        response = await self.client.embeddings.create(**kwargs)
        return response.data[0].embedding


class EmbeddingFactory:
    """Factory for embedding providers."""

    def __init__(self, settings: object) -> None:
        self.settings = settings

    def create(self) -> EmbeddingProvider:
        s = self.settings
        if s.embedding_provider == "gemini":  # type: ignore[attr-defined]
            if s.gemini_api_key is None:  # type: ignore[attr-defined]
                raise ValueError("GEMINI_API_KEY is required when EMBEDDING_PROVIDER=gemini")
            return OpenAIEmbeddingProvider(
                api_key=s.gemini_api_key.get_secret_value(),  # type: ignore[attr-defined]
                base_url=s.gemini_base_url,  # type: ignore[attr-defined]
                model=s.gemini_embedding_model,  # type: ignore[attr-defined]
                dimensions=s.embedding_dimensions,  # type: ignore[attr-defined]
            )

        if s.embedding_provider != "litellm":  # type: ignore[attr-defined]
            raise ValueError(f"Unsupported embedding provider: {s.embedding_provider}")  # type: ignore[attr-defined]
        if s.litellm_api_key is None or not s.litellm_base_url:  # type: ignore[attr-defined]
            raise ValueError(
                "LITELLM_API_KEY and LITELLM_BASE_URL are required when EMBEDDING_PROVIDER=litellm"
            )
        return OpenAIEmbeddingProvider(
            api_key=s.litellm_api_key.get_secret_value(),  # type: ignore[attr-defined]
            base_url=s.litellm_base_url,  # type: ignore[attr-defined]
            model=s.litellm_embedding_model,  # type: ignore[attr-defined]
            dimensions=s.embedding_dimensions,  # type: ignore[attr-defined]
        )
