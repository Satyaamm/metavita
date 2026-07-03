"""Core runtime data types shared across ingest and retrieve."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol


@dataclass(slots=True)
class Chunk:
    text: str
    index: int
    metadata: dict = field(default_factory=dict)
    embedding: list[float] | None = None


@dataclass(slots=True)
class RetrievedChunk:
    text: str
    score: float
    metadata: dict = field(default_factory=dict)
    document_id: str | None = None
    chunk_index: int | None = None


@dataclass(slots=True)
class Citation:
    marker: int  # 1-based citation number shown in the answer
    document_id: str | None
    chunk_index: int | None
    snippet: str


@dataclass(slots=True)
class Answer:
    text: str
    citations: list[Citation]


class VectorStore(Protocol):
    """Port implemented by the API layer (pgvector) — keeps the runtime DB-agnostic."""

    async def search(
        self,
        query_vector: list[float],
        *,
        k: int,
        workspace_id: str,
        query_text: str | None = None,
    ) -> list[RetrievedChunk]: ...
