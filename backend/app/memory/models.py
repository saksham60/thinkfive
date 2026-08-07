"""Memory subsystem models."""

from pydantic import BaseModel


class MemoryCandidate(BaseModel):
    """A candidate memory extracted from conversation before policy check."""

    memory_type: str
    memory_key: str | None = None
    content: str | None = None
    structured_value: dict | None = None
    confidence: float = 0.5
