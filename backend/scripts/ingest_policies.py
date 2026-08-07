"""CLI script to ingest policy documents into the RAG store."""

from __future__ import annotations

import argparse
import asyncio
import logging
from pathlib import Path

from app.core.config import get_settings
from app.infrastructure.database.postgres import PostgresDatabase
from app.infrastructure.embeddings.factory import EmbeddingFactory
from app.rag.chunking import DocumentChunker
from app.rag.ingestion import DocumentIngestionService

logger = logging.getLogger(__name__)


async def ingest_path(path: Path, title: str, jurisdiction: str | None, version: str | None) -> None:
    settings = get_settings()
    db = PostgresDatabase(settings)
    await db.connect()

    try:
        embedding_provider = EmbeddingFactory(settings).create()
        chunker = DocumentChunker(settings.rag_chunk_size, settings.rag_chunk_overlap)
        service = DocumentIngestionService(db, chunker, embedding_provider)

        document_id = await service.ingest(
            path, title=title, jurisdiction=jurisdiction, version=version
        )
        logger.info(f"Ingested {path.name} -> document_id={document_id}")
    finally:
        await db.disconnect()


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest policy documents into RAG store")
    parser.add_argument("path", type=Path, help="Path to PDF/Markdown/TXT file")
    parser.add_argument("--title", required=True)
    parser.add_argument("--jurisdiction", default=None)
    parser.add_argument("--version", default=None)
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)
    asyncio.run(ingest_path(args.path, args.title, args.jurisdiction, args.version))


if __name__ == "__main__":
    main()
