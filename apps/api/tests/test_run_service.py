"""Run executor unit test — verifies span emission and output with fakes."""

from __future__ import annotations

from collections.abc import Sequence

import pytest
from metavita_api.services.run import execute_rag_run
from metavita_providers import ChatMessage, ChatResult, EmbeddingResult, Usage
from metavita_runtime.types import RetrievedChunk


class FakeEmbed:
    name = "fake"

    async def embed(self, texts: Sequence[str], *, model: str) -> EmbeddingResult:
        return EmbeddingResult([[0.1, 0.2, 0.3] for _ in texts], model="fake", dim=3)


class FakeChat:
    name = "fake"

    async def chat(self, messages: Sequence[ChatMessage], *, model, max_tokens=4096, system=None):
        return ChatResult(text="The sky is blue [1].", model=model, usage=Usage(12, 7))

    async def chat_stream(self, messages, *, model, max_tokens=4096, system=None):
        yield "x"


class FakeStore:
    async def search(
        self, query_vector, *, k, workspace_id, query_text=None
    ) -> list[RetrievedChunk]:
        return [RetrievedChunk(text="The sky is blue.", score=0.9, document_id="d1", chunk_index=0)]


@pytest.mark.asyncio
async def test_execute_rag_run_emits_spans_and_output() -> None:
    spans: list[dict] = []

    async def record(**kw) -> None:
        spans.append(kw)

    out = await execute_rag_run(
        question="what color is the sky?",
        k=5,
        embedder=FakeEmbed(),
        embedding_model="fake",
        chat=FakeChat(),
        chat_model="fake",
        store=FakeStore(),
        workspace_id="ws1",
        record=record,
    )

    assert [s["node_type"] for s in spans] == ["embed", "retrieve", "llm"]
    assert spans[1]["detail"]["retrieved"] == 1
    assert out.answer == "The sky is blue [1]."
    assert out.tokens_in == 12 and out.tokens_out == 7
    assert out.citations[0]["document_id"] == "d1"
