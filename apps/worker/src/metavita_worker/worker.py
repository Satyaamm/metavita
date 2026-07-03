"""Arq worker — processes ingestion jobs off the Redis queue.

Run with:  arq metavita_worker.worker.WorkerSettings

Each `ingest_object` job loads the raw document from object storage, parses,
chunks, embeds, and upserts to pgvector — the same unit-of-work the API uses
inline, but decoupled so heavy ingestion never blocks the request path.
"""

from __future__ import annotations

from arq.connections import RedisSettings
from metavita_api.config import get_settings
from metavita_api.services.ingest_job import run_ingest


async def ingest_object(
    ctx: dict,
    *,
    workspace_id: str,
    document_id: str,
    object_key: str,
    content_type: str | None = None,
    filename: str | None = None,
) -> dict:
    return await run_ingest(
        workspace_id=workspace_id,
        document_id=document_id,
        object_key=object_key,
        content_type=content_type,
        filename=filename,
    )


class WorkerSettings:
    functions = [ingest_object]
    redis_settings = RedisSettings.from_dsn(get_settings().redis_url)
    max_jobs = 10
    job_timeout = 600
