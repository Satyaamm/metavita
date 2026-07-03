"""Moss (usemoss.dev) vector-store adapter — ingestion + retrieval.

Two surfaces, per Moss's design:
- **upsert** uses the Control Plane REST API (`POST /v1/manage`, `addDocs`) — Moss
  embeds the text server-side; we attach workspace/document metadata for filtering.
- **search** uses the Moss Python SDK (`pip install moss`): `load_index()` pulls the
  index into memory once, then `query()` runs in-process (~1-10 ms) and accepts our
  precomputed query embedding. The loaded index + client are cached per (project,
  index) so repeated searches don't reload.
"""

from __future__ import annotations

from collections.abc import Iterable

from metavita_runtime import RetrievedChunk
from metavita_runtime.types import Chunk as RuntimeChunk

from . import _rest

_BASE = "https://service.usemoss.dev/v1"

# Process-wide caches: one client per (project, key); track which indexes are loaded.
_CLIENTS: dict[tuple[str, str], object] = {}
_LOADED: set[tuple[str, str]] = set()


def _sdk():
    """Lazy import so the SDK is only required when Moss retrieval is actually used."""
    try:
        from moss import MossClient, QueryOptions
    except ImportError as exc:  # pragma: no cover - exercised only without the SDK
        raise RuntimeError(
            "Moss retrieval needs the Moss SDK — `pip install moss` in the API/worker."
        ) from exc
    return MossClient, QueryOptions


class MossVectorStore:
    provider = "moss"

    def __init__(self, values: dict) -> None:
        self._project = values.get("project_id") or ""
        self._key = values.get("api_key") or ""
        self._index = values.get("index_name") or "metavita"
        self._base = (values.get("base_url") or _BASE).rstrip("/")
        if not self._project or not self._key:
            raise ValueError("moss connection requires 'project_id' and 'api_key'")

    def _headers(self) -> dict:
        return {
            "x-project-key": self._key,
            "x-service-version": "v1",
            "Content-Type": "application/json",
        }

    async def upsert(
        self, *, workspace_id: str, document_id: str, chunks: Iterable[RuntimeChunk]
    ) -> int:
        items = _rest.chunks_list(chunks)
        if not items:
            return 0
        docs = [
            {
                "id": _rest.point_id(document_id, c.index),
                "text": c.text,
                "metadata": {
                    "workspace_id": workspace_id,
                    "document_id": document_id,
                    "chunk_index": c.index,
                    **(c.metadata or {}),
                },
            }
            for c in items
        ]
        await _rest.request(
            "POST", f"{self._base}/manage", headers=self._headers(),
            json={
                "action": "addDocs",
                "projectId": self._project,
                "indexName": self._index,
                "docs": docs,
                "options": {"upsert": True},
            },
        )
        return len(docs)

    async def _client(self):
        client = _CLIENTS.get((self._project, self._key))
        if client is None:
            moss_client_cls, _ = _sdk()
            client = moss_client_cls(self._project, self._key)
            _CLIENTS[(self._project, self._key)] = client
        if (self._project, self._index) not in _LOADED:
            await client.load_index(self._index)
            _LOADED.add((self._project, self._index))
        return client

    async def search(
        self,
        query_vector: list[float],
        *,
        k: int,
        workspace_id: str,
        query_text: str | None = None,
    ) -> list[RetrievedChunk]:
        _, query_options_cls = _sdk()
        client = await self._client()
        flt = {"workspace_id": workspace_id}
        # Moss embeds documents with its own model on addDocs, so query by TEXT for a
        # consistent vector space; fall back to the precomputed vector only without text.
        if query_text:
            options = query_options_cls(top_k=k, filter=flt)
            result = await client.query(self._index, query_text, options)
        else:
            options = query_options_cls(top_k=k, embedding=query_vector, filter=flt)
            result = await client.query(self._index, "", options)
        docs = getattr(result, "docs", result) or []
        out: list[RetrievedChunk] = []
        for d in docs:
            meta = getattr(d, "metadata", None) or {}
            out.append(
                RetrievedChunk(
                    text=getattr(d, "text", "") or "",
                    score=float(getattr(d, "score", 0.0) or 0.0),
                    metadata=meta,
                    document_id=meta.get("document_id"),
                    chunk_index=meta.get("chunk_index"),
                )
            )
        return out


def build(values: dict, *, session=None, workspace_id=None) -> MossVectorStore:
    return MossVectorStore(values)
