"""Weaviate vector-store adapter (REST objects + GraphQL search).

Config: url, class_name (default "MetaVita"), optional api_key. Vectors are supplied
directly (vectorizer: none). Tenant isolation via a `workspace_id` `where` filter.
"""

from __future__ import annotations

import json
from collections.abc import Iterable

from metavita_runtime import RetrievedChunk
from metavita_runtime.types import Chunk as RuntimeChunk

from . import _rest


class WeaviateVectorStore:
    provider = "weaviate"

    def __init__(self, values: dict) -> None:
        self._url = (values.get("url") or "").rstrip("/")
        self._class = values.get("class_name") or "MetaVita"
        self._key = values.get("api_key") or ""
        if not self._url:
            raise ValueError("weaviate connection requires a 'url'")

    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self._key}"} if self._key else {}

    async def _ensure_class(self) -> None:
        try:
            await _rest.request(
                "GET", f"{self._url}/v1/schema/{self._class}", headers=self._headers()
            )
        except Exception:  # noqa: BLE001 - not found → create
            await _rest.request(
                "POST", f"{self._url}/v1/schema", headers=self._headers(),
                json={
                    "class": self._class,
                    "vectorizer": "none",
                    "properties": [
                        {"name": "text", "dataType": ["text"]},
                        {"name": "workspace_id", "dataType": ["text"]},
                        {"name": "document_id", "dataType": ["text"]},
                        {"name": "chunk_index", "dataType": ["int"]},
                        {"name": "metadata_json", "dataType": ["text"]},
                    ],
                },
            )

    async def upsert(
        self, *, workspace_id: str, document_id: str, chunks: Iterable[RuntimeChunk]
    ) -> int:
        items = _rest.chunks_list(chunks)
        if not items:
            return 0
        await self._ensure_class()
        objects = [
            {
                "class": self._class,
                "id": _rest.point_id(document_id, c.index),
                "vector": c.embedding,
                "properties": {
                    "text": c.text,
                    "workspace_id": workspace_id,
                    "document_id": document_id,
                    "chunk_index": c.index,
                    "metadata_json": json.dumps(c.metadata or {}),
                },
            }
            for c in items
        ]
        await _rest.request("POST", f"{self._url}/v1/batch/objects", headers=self._headers(),
                            json={"objects": objects})
        return len(objects)

    async def search(
        self,
        query_vector: list[float],
        *,
        k: int,
        workspace_id: str,
        query_text: str | None = None,
    ) -> list[RetrievedChunk]:
        vec = ",".join(str(x) for x in query_vector)
        where = (
            f'where:{{path:["workspace_id"],operator:Equal,valueText:"{workspace_id}"}}'
        )
        gql = (
            f"{{ Get {{ {self._class}(nearVector:{{vector:[{vec}]}} limit:{k} {where}) "
            f"{{ text document_id chunk_index metadata_json _additional{{distance}} }} }} }}"
        )
        data = await _rest.request("POST", f"{self._url}/v1/graphql", headers=self._headers(),
                                   json={"query": gql})
        rows = (((data.get("data") or {}).get("Get") or {}).get(self._class)) or []
        out = []
        for r in rows:
            dist = (r.get("_additional") or {}).get("distance", 0.0)
            out.append(
                RetrievedChunk(
                    text=r.get("text", ""),
                    score=1.0 - float(dist),
                    metadata=json.loads(r.get("metadata_json", "{}")),
                    document_id=r.get("document_id"),
                    chunk_index=r.get("chunk_index"),
                )
            )
        return out


def build(values: dict, *, session=None, workspace_id=None) -> WeaviateVectorStore:
    return WeaviateVectorStore(values)
