"""LLM model configuration."""

from pydantic import BaseModel


class LLMConfig(BaseModel):
    """Configuration for an LLM provider instance."""

    provider: str
    model: str
    base_url: str | None = None
    temperature: float = 0.0
    max_tokens: int | None = None
