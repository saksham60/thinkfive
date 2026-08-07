"""RAG ingestion pipeline: checksum -> extract -> chunk -> embed -> store."""

from __future__ import annotations

import hashlib
import logging
from pathlib import Path
from typing import TYPE_CHECKING
from uuid import uuid4

from app.rag.chunking import DocumentChunker

if TYPE_CHECKING:
    from app.infrastructure.database.postgres import PostgresDatabase
    from app.infrastructure.embeddings.factory import EmbeddingProvider

logger = logging.getLogger(__name__)


class DocumentIngestionService:
    """Ingests PDF/Markdown/TXT policy documents into policy_documents/policy_chunks."""

    def __init__(
        self,
        db: PostgresDatabase,
        chunker: DocumentChunker,
        embedding_provider: EmbeddingProvider,
    ) -> None:
        self.db = db
        self.chunker = chunker
        self.embedding_provider = embedding_provider

    def extract_text(self, file_path: Path) -> str:
        """Extract raw text from PDF/Markdown/TXT."""
        suffix = file_path.suffix.lower()
        if suffix == ".pdf":
            from pypdf import PdfReader

            reader = PdfReader(str(file_path))
            return "\n".join(page.extract_text() or "" for page in reader.pages)
        # markdown / txt - read as plain text
        return file_path.read_text(encoding="utf-8")

    async def ingest(
        self,
        file_path: Path,
        title: str,
        document_type: str = "policy",
        version: str | None = None,
        jurisdiction: str | None = None,
    ) -> str:
        """Ingest a document: idempotent based on content checksum."""
        content = self.extract_text(file_path)
        content_hash = hashlib.sha256(content.encode()).hexdigest()

        existing = await self.db.fetchrow(
            "SELECT document_id FROM policy_documents WHERE content_hash = $1", content_hash
        )
        if existing:
            logger.info(f"Document already ingested (checksum match): {title}")
            return str(existing["document_id"])

        document_id = uuid4()
        await self.db.execute(
            """
            INSERT INTO policy_documents
                (document_id, title, filename, document_type, version, jurisdiction, content, content_hash)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            """,
            document_id,
            title,
            file_path.name,
            document_type,
            version,
            jurisdiction,
            content,
            content_hash,
        )

        chunks = self.chunker.chunk(content)
        for chunk in chunks:
            embedding = await self.embedding_provider.embed(chunk.content)
            await self.db.execute(
                """
                INSERT INTO policy_chunks (chunk_id, document_id, chunk_index, content, embedding)
                VALUES ($1, $2, $3, $4, $5)
                """,
                uuid4(),
                document_id,
                chunk.index,
                chunk.content,
                str(embedding),
            )

        await self.db.execute(
            "UPDATE policy_documents SET chunk_count = $2 WHERE document_id = $1",
            document_id,
            len(chunks),
        )

        logger.info(f"Ingested document '{title}' with {len(chunks)} chunks")
        return str(document_id)
