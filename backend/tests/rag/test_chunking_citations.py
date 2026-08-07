"""RAG chunking and citation tests (no live DB required)."""

from __future__ import annotations

from app.rag.chunking import DocumentChunker
from app.rag.citations import format_citation
from app.rag.models import RetrievedChunk


class TestDocumentChunker:
    def test_chunks_short_text_into_single_chunk(self) -> None:
        chunker = DocumentChunker(chunk_size=1000, chunk_overlap=200)
        chunks = chunker.chunk("short text")
        assert len(chunks) == 1
        assert chunks[0].content == "short text"

    def test_chunks_long_text_into_multiple_overlapping_chunks(self) -> None:
        chunker = DocumentChunker(chunk_size=100, chunk_overlap=20)
        text = "word " * 100
        chunks = chunker.chunk(text)
        assert len(chunks) > 1

    def test_empty_text_produces_no_chunks(self) -> None:
        chunker = DocumentChunker()
        assert chunker.chunk("") == []


class TestCitations:
    def test_citation_includes_real_metadata_only(self) -> None:
        chunk = RetrievedChunk(
            chunk_id="c1",
            document_id="d1",
            title="Fraud Liability Policy",
            version="2.1",
            jurisdiction="US",
            section="3.2",
            content="...",
            score=0.9,
        )
        citation = format_citation(chunk)
        assert "Fraud Liability Policy" in citation
        assert "d1" in citation
        assert "3.2" in citation
