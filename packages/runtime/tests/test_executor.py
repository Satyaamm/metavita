"""DAG executor tests — verifies node-by-node dispatch and span recording."""

from __future__ import annotations

import pytest
from metavita_providers import ChatResult, EmbeddingResult, Usage
from metavita_runtime import execute_pipeline
from metavita_runtime.types import RetrievedChunk


class FakeEmbedder:
    def __init__(self) -> None:
        self.calls = 0

    async def embed(self, texts, *, model):
        self.calls += 1
        return EmbeddingResult(
            vectors=[[0.1, 0.2, 0.3] for _ in texts],
            model=model,
            dim=3,
            usage=Usage(input_tokens=3),
        )


class FakeChat:
    def __init__(self) -> None:
        self.models_seen: list[str] = []

    async def chat(self, messages, *, model, system=None, max_tokens=1024):
        self.models_seen.append(model)
        return ChatResult(
            text="Grounded answer [1].",
            model=model,
            usage=Usage(input_tokens=42, output_tokens=8),
        )


class FakeStore:
    def __init__(self, chunks) -> None:
        self._chunks = chunks
        self.k_seen: int | None = None

    async def search(self, query_vector, *, k, workspace_id, query_text=None):
        self.k_seen = k
        return self._chunks[:k]


def _graph(retrieve_k=None, llm_model=None):
    r_data = {"k": retrieve_k} if retrieve_k else {}
    l_data = {"model": llm_model} if llm_model else {}
    return {
        "nodes": [
            {"id": "r1", "type": "retrieve", "position": {"x": 0, "y": 0}, "data": r_data},
            {"id": "l1", "type": "llm", "position": {"x": 200, "y": 0}, "data": l_data},
        ],
        "edges": [{"id": "e1", "source": "r1", "target": "l1"}],
    }


def _chunks(n):
    return [
        RetrievedChunk(text=f"chunk {i}", score=1.0 - i * 0.1, document_id=f"doc{i}", chunk_index=i)
        for i in range(n)
    ]


@pytest.mark.asyncio
async def test_executor_runs_retrieve_then_llm_and_records_spans():
    embedder, chat, store = FakeEmbedder(), FakeChat(), FakeStore(_chunks(5))
    spans: list[dict] = []

    async def record(**span):
        spans.append(span)

    out = await execute_pipeline(
        _graph(),
        question="what is metavita?",
        embedder=embedder,
        embedding_model="emb-model",
        chat=chat,
        chat_model="chat-model",
        store=store,
        workspace_id="ws-1",
        record=record,
    )

    assert out.answer == "Grounded answer [1]."
    assert out.tokens_in == 42
    assert out.tokens_out == 8
    assert len(out.citations) == 5
    assert out.citations[0]["marker"] == 1
    assert [s["node_type"] for s in spans] == ["retrieve", "llm"]
    assert [s["seq"] for s in spans] == [0, 1]


@pytest.mark.asyncio
async def test_executor_honors_per_node_k_and_model():
    embedder, chat, store = FakeEmbedder(), FakeChat(), FakeStore(_chunks(10))
    out = await execute_pipeline(
        _graph(retrieve_k=3, llm_model="custom-model"),
        question="q",
        embedder=embedder,
        embedding_model="emb-model",
        chat=chat,
        chat_model="default-model",
        store=store,
        workspace_id="ws-1",
        record=_noop,
    )
    assert store.k_seen == 3
    assert len(out.citations) == 3
    assert chat.models_seen == ["custom-model"]


@pytest.mark.asyncio
async def test_executor_falls_back_to_default_turn_for_empty_graph():
    embedder, chat, store = FakeEmbedder(), FakeChat(), FakeStore(_chunks(5))
    out = await execute_pipeline(
        {"nodes": [], "edges": []},
        question="q",
        embedder=embedder,
        embedding_model="emb-model",
        chat=chat,
        chat_model="default-model",
        store=store,
        workspace_id="ws-1",
        record=_noop,
        k_default=5,
    )
    assert embedder.calls == 1
    assert chat.models_seen == ["default-model"]
    assert out.answer == "Grounded answer [1]."


async def _noop(**_span):
    return None
