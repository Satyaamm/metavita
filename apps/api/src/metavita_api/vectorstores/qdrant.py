"""Qdrant vector-store adapter (REST).

Config: url, collection (default "metavita"), optional api_key. The collection is
created on first upsert (Cosine, dim inferred from the first vector). Tenant
isolation is enforced with a `workspace_id` payload filter on search.
"""

from __future__ import annotations

from collections.abc import Iterable

from metavita_runtime import RetrievedChunk
from metavita_runtime.types import Chunk as RuntimeChunk

from . import _rest


class QdrantVectorStore:
    provider = "qdrant"

    def __init__(self, values: dict) -> None:
        self._url = (values.get("url") or "").rstrip("/")
        self._collection = values.get("collection") or "metavita"
        self._key = values.get("api_key") or ""
        if not self._url:
            raise ValueError("qdrant connection requires a 'url'")

    def _headers(self) -> dict:
        return {"api-key": self._key} if self._key else {}

    async def _ensure_collection(self, dim: int) -> None:
        try:
            await _rest.request("GET", f"{self._url}/collections/{self._collection}",
                                headers=self._headers())
        except Exception:  # noqa: BLE001 - not found → create
            await _rest.request(
                "PUT", f"{self._url}/collections/{self._collection}",
                headers=self._headers(),
                json={"vectors": {"size": dim, "distance": "Cosine"}},
            )

    async def upsert(
        self, *, workspace_id: str, document_id: str, chunks: Iterable[RuntimeChunk]
    ) -> int:
        items = _rest.chunks_list(chunks)
        if not items:
            return 0
        await self._ensure_collection(len(items[0].embedding or []))
        points = [
            {
                "id": _rest.point_id(document_id, c.index),
                "vector": c.embedding,
                "payload": _rest.payload_for(c, workspace_id=workspace_id, document_id=document_id),
            }
            for c in items
        ]
        await _rest.request(
            "PUT", f"{self._url}/collections/{self._collection}/points?wait=true",
            headers=self._headers(), json={"points": points},
        )
        return len(points)

    async def search(
        self,
        query_vector: list[float],
        *,
        k: int,
        workspace_id: str,
        query_text: str | None = None,
    ) -> list[RetrievedChunk]:
        body = {
            "vector": query_vector,
            "limit": k,
            "with_payload": True,
            "filter": {"must": [{"key": "workspace_id", "match": {"value": workspace_id}}]},
        }
        data = await _rest.request(
            "POST", f"{self._url}/collections/{self._collection}/points/search",
            headers=self._headers(), json=body,
        )
        out = []
        for hit in data.get("result", []):
            payload = hit.get("payload", {}) or {}
            out.append(
                _rest.to_retrieved(
                    text=payload.get("text", ""), score=hit.get("score", 0.0), payload=payload
                )
            )
        return out


def build(values: dict, *, session=None, workspace_id=None) -> QdrantVectorStore:
    return QdrantVectorStore(values)
