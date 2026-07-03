"""Ingest → retrieve → answer pipeline test with mocked providers (no network)."""

from __future__ import annotations

from collections.abc import Sequence

import pytest
from metavita_providers import ChatMessage, ChatResult, EmbeddingResult, Usage
from metavita_runtime import answer_question, chunk_text, ingest_document
from metavita_runtime.types import RetrievedChunk


class FakeEmbedder:
    name = "fake"

    async def embed(self, texts: Sequence[str], *, model: str) -> EmbeddingResult:
        # Deterministic 3-dim vectors derived from text length.
        vectors = [[float(len(t) % 7), 1.0, 0.0] for t in texts]
        return EmbeddingResult(vectors=vectors, model=model, dim=3)


class FakeChat:
    name = "fake"

    async def chat(self, messages: Sequence[ChatMessage], *, model, max_tokens=4096, system=None):
        # Echo that it saw the context, citing [1].
        return ChatResult(text="Per the context, the sky is blue [1].", model=model, usage=Usage())

    async def chat_stream(self, messages, *, model, max_tokens=4096, system=None):
        for tok in ["Per ", "the ", "context [1]."]:
            yield tok


class FakeStore:
    def __init__(self, chunks: list[RetrievedChunk]) -> None:
        self._chunks = chunks

    async def search(
        self, query_vector, *, k, workspace_id, query_text=None
    ) -> list[RetrievedChunk]:
        return self._chunks[:k]


def test_chunking_overlap() -> None:
    text = "para one.\n\npara two is here.\n\npara three closes it out."
    chunks = chunk_text(text, chunk_size=20, overlap=5)
    assert len(chunks) >= 2
    assert all(c.strip() for c in chunks)


@pytest.mark.asyncio
async def test_ingest_produces_embedded_chunks() -> None:
    content = b"The sky is blue. " * 50
    chunks = await ingest_document(
        content,
        content_type="text/plain",
        filename="sky.txt",
        embedder=FakeEmbedder(),
        embedding_model="fake",
        chunk_size=120,
        overlap=20,
    )
    assert chunks
    assert all(c.embedding is not None and len(c.embedding) == 3 for c in chunks)
    assert chunks[0].metadata["filename"] == "sky.txt"


@pytest.mark.asyncio
async def test_answer_cites_context() -> None:
    store = FakeStore(
        [RetrievedChunk(text="The sky is blue.", score=0.9, document_id="doc1", chunk_index=0)]
    )
    result = await answer_question(
        "What color is the sky?",
        embedder=FakeEmbedder(),
        embedding_model="fake",
        chat=FakeChat(),
        chat_model="fake",
        store=store,
        workspace_id="ws1",
        k=5,
    )
    assert "[1]" in result.text
    assert len(result.citations) == 1
    assert result.citations[0].document_id == "doc1"
