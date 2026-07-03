"""pgvector implementation of the runtime VectorStore port."""

from __future__ import annotations

import uuid

from metavita_runtime import RetrievedChunk
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import Chunk


class PgVectorStore:
    """Workspace-scoped cosine-similarity search over the `chunks` table."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

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
