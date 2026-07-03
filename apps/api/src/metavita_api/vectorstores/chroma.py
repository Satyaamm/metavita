"""Chroma vector-store adapter (REST, API v1).

Config: url, collection (default "metavita"). Chroma metadata must be flat scalars,
so chunk metadata is JSON-encoded into a `metadata_json` field. Tenant isolation via
a `workspace_id` `where` filter.
"""

from __future__ import annotations

import json
from collections.abc import Iterable

from metavita_runtime import RetrievedChunk
from metavita_runtime.types import Chunk as RuntimeChunk

from . import _rest


class ChromaVectorStore:
    provider = "chroma"

    def __init__(self, values: dict) -> None:
        self._url = (values.get("url") or "").rstrip("/")
        self._collection = values.get("collection") or "metavita"
        if not self._url:
            raise ValueError("chroma connection requires a 'url'")

    async def _collection_id(self) -> str:
        data = await _rest.request(
            "POST", f"{self._url}/api/v1/collections",
            json={"name": self._collection, "get_or_create": True},
        )
        return data.get("id", self._collection)

    async def upsert(
        self, *, workspace_id: str, document_id: str, chunks: Iterable[RuntimeChunk]
    ) -> int:
        items = _rest.chunks_list(chunks)
        if not items:
            return 0
        cid = await self._collection_id()
        body = {
            "ids": [_rest.point_id(document_id, c.index) for c in items],
            "embeddings": [c.embedding for c in items],
            "documents": [c.text for c in items],
            "metadatas": [
                {
                    "workspace_id": workspace_id,
                    "document_id": document_id,
                    "chunk_index": c.index,
                    "metadata_json": json.dumps(c.metadata or {}),
                }
                for c in items
            ],
        }
        await _rest.request("POST", f"{self._url}/api/v1/collections/{cid}/upsert", json=body)
        return len(items)

    async def search(
        self,
        query_vector: list[float],
        *,
        k: int,
        workspace_id: str,
        query_text: str | None = None,
    ) -> list[RetrievedChunk]:
        cid = await self._collection_id()
        body = {
            "query_embeddings": [query_vector],
            "n_results": k,
            "where": {"workspace_id": workspace_id},
            "include": ["metadatas", "documents", "distances"],
        }
        data = await _rest.request("POST", f"{self._url}/api/v1/collections/{cid}/query", json=body)
        docs = (data.get("documents") or [[]])[0]
        metas = (data.get("metadatas") or [[]])[0]
        dists = (data.get("distances") or [[]])[0]
        out = []
        for text, meta, dist in zip(docs, metas, dists, strict=False):
            meta = meta or {}
            out.append(
                RetrievedChunk(
                    text=text or "",
                    score=1.0 - float(dist),  # cosine distance → similarity
                    metadata=json.loads(meta.get("metadata_json", "{}")),
                    document_id=meta.get("document_id"),
                    chunk_index=meta.get("chunk_index"),
                )
            )
        return out


def build(values: dict, *, session=None, workspace_id=None) -> ChromaVectorStore:
    return ChromaVectorStore(values)
