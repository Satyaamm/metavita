"""pgvector adapter — the default vector store (platform Postgres + pgvector).

Implements the pluggable store Port: `upsert()` writes chunk vectors into the
`chunks` table and `search()` runs workspace-scoped cosine similarity. This is a
thin superset of the original runtime VectorStore port (which only needs search),
so existing retrieve paths behave identically.
"""

from __future__ import annotations

import uuid
from collections.abc import Iterable

from metavita_runtime import RetrievedChunk
from metavita_runtime.types import Chunk as RuntimeChunk
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Chunk


class PgVectorStore:
    """Workspace-scoped cosine-similarity store over the `chunks` table."""

    provider = "pgvector"

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def upsert(
        self,
        *,
        workspace_id: str,
        document_id: str,
        chunks: Iterable[RuntimeChunk],
    ) -> int:
        """Insert chunk vectors for a document. Returns the number written."""
        ws = uuid.UUID(workspace_id)
        doc = uuid.UUID(document_id)
        count = 0
        for c in chunks:
            self._session.add(
                Chunk(
                    workspace_id=ws,
                    document_id=doc,
                    chunk_index=c.index,
                    text=c.text,
                    embedding=c.embedding,
                    meta=c.metadata,
                )
            )
            count += 1
        return count

    async def search(
        self,
        query_vector: list[float],
        *,
        k: int,
        workspace_id: str,
        query_text: str | None = None,
    ) -> list[RetrievedChunk]:
        distance = Chunk.embedding.cosine_distance(query_vector)
        stmt = (
            select(Chunk, distance.label("distance"))
            .where(Chunk.workspace_id == uuid.UUID(workspace_id))
            .order_by(distance)
            .limit(k)
        )
        rows = (await self._session.execute(stmt)).all()
        return [
            RetrievedChunk(
                text=chunk.text,
                score=1.0 - float(dist),  # cosine similarity
                metadata=chunk.meta,
                document_id=str(chunk.document_id),
                chunk_index=chunk.chunk_index,
            )
            for chunk, dist in rows
        ]
