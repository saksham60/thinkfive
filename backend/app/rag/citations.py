"""RAG citation helpers - never fabricate, only surface stored metadata."""

from __future__ import annotations

from app.rag.models import RetrievedChunk


def format_citation(chunk: RetrievedChunk) -> str:
    """Format a citation string from a retrieved chunk's real metadata."""
    parts = [f"[{chunk.title}"]
    if chunk.version:
        parts.append(f"v{chunk.version}")
    if chunk.jurisdiction:
        parts.append(chunk.jurisdiction)
    if chunk.section:
        parts.append(f"§{chunk.section}")
    if chunk.page:
        parts.append(f"p.{chunk.page}")
    return " ".join(parts) + f", doc_id={chunk.document_id}]"
