"""Vector-store factory — build the workspace's store from its Connection.

`build_vector_store(provider, values, *, session, workspace_id)` returns a store
implementing `upsert()` + `search()`. The default (and the `pgvector` provider with
a blank DSN) is the platform Postgres store. External vector DBs are brought as
`vector_store` Connections; their adapters register here as they land. Until an
adapter exists for a given provider, the factory falls back to pgvector so
retrieval keeps working — pgvector behavior is unchanged when no connection is set.
"""

from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from ..services.resolve import connection_values, default_connection
from . import chroma, moss, pinecone, qdrant, weaviate
from .pgvector import PgVectorStore

# Provider keys for which a dedicated external adapter is wired. pgvector is always
# available (uses the platform session); the rest are REST-backed BYO vector DBs.
_EXTERNAL_BUILDERS: dict = {
    "pinecone": pinecone.build,
    "qdrant": qdrant.build,
    "weaviate": weaviate.build,
    "chroma": chroma.build,
    "moss": moss.build,
}


def build_vector_store(
    provider: str | None,
    values: dict | None,
    *,
    session: AsyncSession,
    workspace_id: uuid.UUID,
):
    """Construct the vector store for a workspace.

    - `provider` None or "pgvector" → platform Postgres store.
    - any other provider with a registered adapter → that adapter.
    - otherwise → pgvector fallback (keeps retrieval working).
    """
    values = values or {}
    if not provider or provider == "pgvector":
        # A blank DSN means "use the platform DB"; a custom DSN would target an
        # external Postgres, which the platform session does not open here, so we
        # use the platform-backed store either way.
        return PgVectorStore(session)

    builder = _EXTERNAL_BUILDERS.get(provider)
    if builder is not None:
        return builder(values, session=session, workspace_id=workspace_id)

    # No adapter yet for this provider — fall back to pgvector.
    return PgVectorStore(session)


async def resolve_vector_store(session: AsyncSession, workspace_id: uuid.UUID):
    """Build the workspace's vector store from its default `vector_store` connection.

    Defaults to pgvector when no connection exists (behavior unchanged).
    """
    conn = await default_connection(session, workspace_id, "vector_store")
    return build_vector_store(
        conn.provider if conn else None,
        connection_values(conn) if conn else {},
        session=session,
        workspace_id=workspace_id,
    )
