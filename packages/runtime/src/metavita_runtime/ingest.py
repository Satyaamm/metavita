"""Ingest pipeline: parse → chunk → embed → produce embedded chunks.

Persistence is intentionally left to the caller (the API's pgvector store), so the
runtime stays storage-agnostic and unit-testable with a mock embedder.
"""

from __future__ import annotations

from metavita_providers import EmbeddingProvider

from .chunking import chunk_text
from .parsing import parse
from .types import Chunk


async def ingest_document(
    content: bytes,
    *,
    content_type: str | None,
    filename: str | None,
    embedder: EmbeddingProvider,
    embedding_model: str,
    chunk_size: int = 1200,
    overlap: int = 150,
) -> list[Chunk]:
    text = parse(content, content_type=content_type, filename=filename)
    pieces = chunk_text(text, chunk_size=chunk_size, overlap=overlap)
    if not pieces:
        return []

    result = await embedder.embed(pieces, model=embedding_model)
    return [
        Chunk(
            text=piece,
            index=i,
            metadata={"filename": filename},
            embedding=vector,
        )
        for i, (piece, vector) in enumerate(zip(pieces, result.vectors, strict=True))
    ]
