"""RAG service facade."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.rag.models import RetrievedChunk

if TYPE_CHECKING:
    from app.rag.retrieval import HybridRetriever


class RAGService:
    """Facade over ingestion/retrieval used by the Knowledge Agent."""

    def __init__(self, retriever: HybridRetriever) -> None:
        self.retriever = retriever

    async def retrieve(self, query: str, top_k: int = 5) -> list[RetrievedChunk]:
        return await self.retriever.retrieve(query, top_k)
