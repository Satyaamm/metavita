"""Pinecone vector-store adapter (serverless data plane, REST).

Config: api_key, index_host (the index's data-plane host), optional namespace.
Tenant isolation via a `workspace_id` metadata filter on query.
"""

from __future__ import annotations

from collections.abc import Iterable

from metavita_runtime import RetrievedChunk
from metavita_runtime.types import Chunk as RuntimeChunk

from . import _rest


class PineconeVectorStore:
    provider = "pinecone"

    def __init__(self, values: dict) -> None:
        host = (values.get("index_host") or "").replace("https://", "")
        host = host.replace("http://", "").rstrip("/")
        if not host or not values.get("api_key"):
            raise ValueError("pinecone connection requires 'api_key' and 'index_host'")
        self._base = f"https://{host}"
        self._key = values["api_key"]
        self._namespace = values.get("namespace") or ""

    def _headers(self) -> dict:
        return {"Api-Key": self._key, "Content-Type": "application/json"}

    async def upsert(
        self, *, workspace_id: str, document_id: str, chunks: Iterable[RuntimeChunk]
    ) -> int:
        items = _rest.chunks_list(chunks)
        if not items:
            return 0
        vectors = [
            {
                "id": _rest.point_id(document_id, c.index),
                "values": c.embedding,
                "metadata": _rest.payload_for(
                    c, workspace_id=workspace_id, document_id=document_id
                ),
            }
            for c in items
        ]
        await _rest.request(
            "POST", f"{self._base}/vectors/upsert",
            headers=self._headers(), json={"namespace": self._namespace, "vectors": vectors},
        )
        return len(vectors)

    async def search(
        self,
        query_vector: list[float],
        *,
        k: int,
        workspace_id: str,
        query_text: str | None = None,
    ) -> list[RetrievedChunk]:
        body = {
            "namespace": self._namespace,
            "vector": query_vector,
            "topK": k,
            "includeMetadata": True,
            "filter": {"workspace_id": {"$eq": workspace_id}},
        }
        data = await _rest.request(
            "POST", f"{self._base}/query", headers=self._headers(), json=body
        )
        out = []
        for m in data.get("matches", []):
            meta = m.get("metadata", {}) or {}
            out.append(
                _rest.to_retrieved(
                    text=meta.get("text", ""), score=m.get("score", 0.0), payload=meta
                )
            )
        return out


def build(values: dict, *, session=None, workspace_id=None) -> PineconeVectorStore:
    return PineconeVectorStore(values)
