"""Vector-store adapter tests — factory selection + REST request/response shaping.

REST calls are intercepted by monkeypatching the shared `_rest.request`, so adapters
are verified offline (no live Pinecone/Qdrant/etc needed).
"""

from __future__ import annotations

import pytest
from metavita_api.vectorstores import _rest, factory
from metavita_api.vectorstores.chroma import ChromaVectorStore
from metavita_api.vectorstores.moss import MossVectorStore
from metavita_api.vectorstores.pgvector import PgVectorStore
from metavita_api.vectorstores.pinecone import PineconeVectorStore
from metavita_api.vectorstores.qdrant import QdrantVectorStore
from metavita_runtime.types import Chunk as RuntimeChunk


def _chunks(n=2):
    return [
        RuntimeChunk(text=f"chunk {i}", index=i, metadata={"k": i}, embedding=[0.1, 0.2, 0.3])
        for i in range(n)
    ]


class FakeRest:
    """Records requests; returns canned responses keyed by a URL substring."""

    def __init__(self, responses: dict[str, dict]):
        self.calls: list[tuple[str, str, dict | None]] = []
        self._responses = responses

    async def __call__(self, method, url, *, headers=None, json=None):
        self.calls.append((method, url, json))
        for frag, resp in self._responses.items():
            if frag in url:
                return resp
        return {}


def test_factory_defaults_to_pgvector():
    store = factory.build_vector_store(None, {}, session="S", workspace_id="ws")
    assert isinstance(store, PgVectorStore)
    store2 = factory.build_vector_store("pgvector", {}, session="S", workspace_id="ws")
    assert isinstance(store2, PgVectorStore)


def test_factory_builds_external_adapters():
    q = factory.build_vector_store(
        "qdrant", {"url": "http://q:6333"}, session=None, workspace_id="ws"
    )
    assert isinstance(q, QdrantVectorStore)
    p = factory.build_vector_store(
        "pinecone", {"api_key": "k", "index_host": "h.pinecone.io"}, session=None, workspace_id="ws"
    )
    assert isinstance(p, PineconeVectorStore)
    c = factory.build_vector_store(
        "chroma", {"url": "http://c:8000"}, session=None, workspace_id="ws"
    )
    assert isinstance(c, ChromaVectorStore)


def test_unknown_provider_falls_back_to_pgvector():
    store = factory.build_vector_store("milvus", {}, session="S", workspace_id="ws")
    assert isinstance(store, PgVectorStore)


@pytest.mark.asyncio
async def test_qdrant_upsert_and_search(monkeypatch):
    fake = FakeRest({
        "/points/search": {
            "result": [
                {
                    "score": 0.91,
                    "payload": {
                        "text": "hit", "document_id": "d1",
                        "chunk_index": 0, "metadata": {"k": 0},
                    },
                }
            ]
        },
    })
    monkeypatch.setattr(_rest, "request", fake)
    store = QdrantVectorStore({"url": "http://q:6333", "collection": "c"})

    n = await store.upsert(workspace_id="ws", document_id="d1", chunks=_chunks(2))
    assert n == 2
    # the points PUT carries vectors + workspace_id payload for isolation
    put = [c for c in fake.calls if c[0] == "PUT" and "/points" in c[1]][-1]
    assert put[2]["points"][0]["payload"]["workspace_id"] == "ws"

    res = await store.search([0.1, 0.2, 0.3], k=3, workspace_id="ws")
    assert len(res) == 1 and res[0].text == "hit" and res[0].document_id == "d1"


@pytest.mark.asyncio
async def test_pinecone_search_uses_workspace_filter(monkeypatch):
    fake = FakeRest({
        "/query": {
            "matches": [
                {
                    "score": 0.8,
                    "metadata": {
                        "text": "p", "document_id": "d2",
                        "chunk_index": 1, "metadata": {},
                    },
                }
            ]
        }
    })
    monkeypatch.setattr(_rest, "request", fake)
    store = PineconeVectorStore(
        {"api_key": "k", "index_host": "h.pinecone.io", "namespace": "n"}
    )
    res = await store.search([0.1, 0.2, 0.3], k=5, workspace_id="ws")
    query = [c for c in fake.calls if "/query" in c[1]][-1]
    assert query[2]["filter"] == {"workspace_id": {"$eq": "ws"}}
    assert res[0].text == "p"


def test_factory_builds_moss():
    m = factory.build_vector_store(
        "moss", {"project_id": "p", "api_key": "moss_access_key_x"}, session=None, workspace_id="ws"
    )
    assert isinstance(m, MossVectorStore)


@pytest.mark.asyncio
async def test_moss_upsert_calls_adddocs(monkeypatch):
    fake = FakeRest({"/manage": {"jobId": "j1", "status": "queued"}})
    monkeypatch.setattr(_rest, "request", fake)
    store = MossVectorStore({"project_id": "p", "api_key": "k", "index_name": "ix"})
    n = await store.upsert(workspace_id="ws", document_id="d1", chunks=_chunks(2))
    assert n == 2
    body = [c for c in fake.calls if "/manage" in c[1]][-1][2]
    assert body["action"] == "addDocs" and body["indexName"] == "ix"
    assert body["docs"][0]["text"] == "chunk 0" and "id" in body["docs"][0]


@pytest.mark.asyncio
async def test_moss_search_uses_sdk_with_precomputed_embedding(monkeypatch):
    import metavita_api.vectorstores.moss as mossmod

    mossmod._CLIENTS.clear()
    mossmod._LOADED.clear()
    seen: dict = {}

    class FakeOptions:
        def __init__(self, **kw):
            seen["opts"] = kw

    class FakeDoc:
        def __init__(self, text, score, meta):
            self.text, self.score, self.metadata = text, score, meta

    class FakeResult:
        def __init__(self, docs):
            self.docs = docs

    class FakeClient:
        def __init__(self, project, key):
            seen["init"] = (project, key)

        async def load_index(self, name, **kw):
            seen["loaded"] = name

        async def query(self, name, q, options):
            seen["query"] = (name, q)
            return FakeResult([FakeDoc("hit", 0.9, {"document_id": "d1", "chunk_index": 2})])

    monkeypatch.setattr(mossmod, "_sdk", lambda: (FakeClient, FakeOptions))
    store = mossmod.MossVectorStore({"project_id": "p", "api_key": "k", "index_name": "ix"})

    # Production path: query by TEXT (consistent with Moss's own doc embeddings).
    res = await store.search([0.1, 0.2], k=4, workspace_id="ws", query_text="what is x?")
    assert seen["loaded"] == "ix" and seen["init"] == ("p", "k")
    assert seen["query"] == ("ix", "what is x?")  # queried by text, not ""
    assert "embedding" not in seen["opts"] and seen["opts"]["top_k"] == 4
    assert seen["opts"]["filter"] == {"workspace_id": "ws"}
    assert res[0].text == "hit" and res[0].document_id == "d1" and res[0].chunk_index == 2

    # Fallback path: no text → query by the precomputed embedding.
    mossmod._LOADED.clear()
    await store.search([0.3, 0.4], k=2, workspace_id="ws")
    assert seen["opts"]["embedding"] == [0.3, 0.4] and seen["query"][1] == ""
