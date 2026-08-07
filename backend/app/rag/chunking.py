"""Document chunking for RAG ingestion."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Chunk:
    """A text chunk ready for embedding."""

    index: int
    content: str
    page_number: int | None = None
    section_title: str | None = None


class DocumentChunker:
    """Splits document text into overlapping chunks."""

    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200) -> None:
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk(self, text: str) -> list[Chunk]:
        """Split text into overlapping chunks by character count."""
        chunks: list[Chunk] = []
        start = 0
        index = 0
        text_length = len(text)

        while start < text_length:
            end = min(start + self.chunk_size, text_length)
            content = text[start:end].strip()
            if content:
                chunks.append(Chunk(index=index, content=content))
                index += 1
            if end >= text_length:
                break
            start = end - self.chunk_overlap

        return chunks
