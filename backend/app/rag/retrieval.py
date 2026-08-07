"""RAG hybrid retrieval - vector similarity + PostgreSQL full-text search."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from app.rag.models import RetrievedChunk

if TYPE_CHECKING:
    from app.infrastructure.database.postgres import PostgresDatabase
    from app.infrastructure.embeddings.factory import EmbeddingProvider

logger = logging.getLogger(__name__)


class HybridRetriever:
    """Combines pgvector cosine similarity with PostgreSQL full-text search."""

    def __init__(
        self,
        db: PostgresDatabase,
        embedding_provider: EmbeddingProvider,
        similarity_threshold: float = 0.7,
    ) -> None:
        self.db = db
        self.embedding_provider = embedding_provider
        self.similarity_threshold = similarity_threshold

    async def retrieve(self, query: str, top_k: int = 5) -> list[RetrievedChunk]:
        """Retrieve top-k chunks combining vector and keyword search."""
        query_embedding = await self.embedding_provider.embed(query)

        rows = await self.db.fetch(
            """
            SELECT
                pc.chunk_id, pc.document_id, pc.content, pc.page_number, pc.section_title,
                pd.title, pd.version, pd.jurisdiction,
                1 - (pc.embedding <=> $1::vector) AS vector_score,
                ts_rank_cd(to_tsvector('english', pc.content), plainto_tsquery('english', $2)) AS text_score
            FROM policy_chunks pc
            JOIN policy_documents pd ON pd.document_id = pc.document_id
            ORDER BY (1 - (pc.embedding <=> $1::vector)) * 0.7
                   + ts_rank_cd(to_tsvector('english', pc.content), plainto_tsquery('english', $2)) * 0.3
                   DESC
            LIMIT $3
            """,
            str(query_embedding),
            query,
            top_k,
        )

        results = []
        for row in rows:
            if row["vector_score"] < self.similarity_threshold and row["text_score"] == 0:
                continue
            results.append(
                RetrievedChunk(
                    chunk_id=str(row["chunk_id"]),
                    document_id=str(row["document_id"]),
                    title=row["title"],
                    version=row["version"],
                    jurisdiction=row["jurisdiction"],
                    page=row["page_number"],
                    section=row["section_title"],
                    content=row["content"],
                    score=float(row["vector_score"]),
                )
            )
        return results
