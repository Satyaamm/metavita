"""Task queue — enqueue heavy ingestion onto Arq (Redis), with an inline fallback.

The API never blocks on a large parse/embed: it stores the raw bytes, creates the
document row, and enqueues `ingest_object`. A separate worker (`apps/worker`) runs
the job. When Redis is unreachable (e.g. a minimal dev box), `enqueue_ingest` runs
the job inline so ingestion still completes — degraded, but never broken.
"""

from __future__ import annotations

from dataclasses import dataclass

from arq import create_pool
from arq.connections import RedisSettings

from .config import get_settings
from .services.ingest_job import run_ingest


@dataclass(slots=True)
class EnqueueResult:
    job_id: str
    mode: str  # "queued" | "inline"


async def enqueue_ingest(
    *,
    workspace_id: str,
    document_id: str,
    object_key: str,
    content_type: str | None,
    filename: str | None,
) -> EnqueueResult:
    payload = {
        "workspace_id": workspace_id,
        "document_id": document_id,
        "object_key": object_key,
        "content_type": content_type,
        "filename": filename,
    }
    settings = get_settings()
    try:
        pool = await create_pool(RedisSettings.from_dsn(settings.redis_url))
        job = await pool.enqueue_job("ingest_object", **payload)
        await pool.aclose()
        if job is not None:
            return EnqueueResult(job_id=job.job_id, mode="queued")
    except Exception:  # noqa: BLE001 - Redis down → run inline so ingestion still happens
        pass

    await run_ingest(**payload)
    return EnqueueResult(job_id=f"inline:{document_id}", mode="inline")
