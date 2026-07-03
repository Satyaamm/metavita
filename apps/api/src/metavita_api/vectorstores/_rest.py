"""Shared helpers for REST-backed external vector stores.

Each external adapter (Pinecone/Qdrant/Weaviate/Chroma) talks to its DB over HTTP
via httpx, implementing the same Port as pgvector: `upsert()` + `search()`. Chunk
ids are deterministic (uuid5 of document_id + chunk_index) so re-ingesting a
document overwrites rather than duplicates.
"""

from __future__ import annotations

import uuid
from collections.abc import Iterable

import httpx
from metavita_runtime import RetrievedChunk
from metavita_runtime.types import Chunk as RuntimeChunk

_TIMEOUT = 30.0
_NS = uuid.UUID("00000000-0000-0000-0000-0000000000aa")  # namespace for point ids


def point_id(document_id: str, chunk_index: int) -> str:
    return str(uuid.uuid5(_NS, f"{document_id}:{chunk_index}"))


def payload_for(chunk: RuntimeChunk, *, workspace_id: str, document_id: str) -> dict:
    return {
        "text": chunk.text,
        "workspace_id": workspace_id,
        "document_id": document_id,
        "chunk_index": chunk.index,
        "metadata": chunk.metadata or {},
    }


def to_retrieved(*, text: str, score: float, payload: dict) -> RetrievedChunk:
    return RetrievedChunk(
        text=text,
        score=float(score),
        metadata=payload.get("metadata", {}) if isinstance(payload, dict) else {},
        document_id=payload.get("document_id") if isinstance(payload, dict) else None,
        chunk_index=payload.get("chunk_index") if isinstance(payload, dict) else None,
    )


def chunks_list(chunks: Iterable[RuntimeChunk]) -> list[RuntimeChunk]:
    return list(chunks)


async def request(
    method: str, url: str, *, headers: dict | None = None, json: dict | None = None
) -> dict:
    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        resp = await client.request(method, url, headers=headers or {}, json=json)
        resp.raise_for_status()
        if resp.content:
            return resp.json()
        return {}
