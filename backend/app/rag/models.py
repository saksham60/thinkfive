"""RAG models."""

from pydantic import BaseModel


class RetrievedChunk(BaseModel):
    """A retrieved policy chunk with citation metadata."""

    chunk_id: str
    document_id: str
    title: str
    version: str | None = None
    jurisdiction: str | None = None
    page: int | None = None
    section: str | None = None
    content: str
    score: float
