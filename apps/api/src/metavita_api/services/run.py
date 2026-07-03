"""RAG run executor — runs embed → retrieve → generate, emitting a span per step.

The `record` callback decouples execution from persistence, so this is unit-testable
with fakes (the route passes a callback that writes spans via RunRepository).
"""

from __future__ import annotations

import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from metavita_providers import ChatMessage, ChatProvider, EmbeddingProvider
from metavita_runtime import RetrievedChunk, VectorStore

SpanRecorder = Callable[..., Awaitable[None]]

_SYSTEM = (
    "You are MetaVita. Answer the question using only the numbered context passages. "
    "Cite passages with inline markers like [1]. If the context lacks the answer, say so."
)


@dataclass(slots=True)
class RunOutput:
    answer: str
    citations: list[dict]
    tokens_in: int
    tokens_out: int


def _ms(started: float) -> int:
    return int((time.perf_counter() - started) * 1000)


def _citations(chunks: list[RetrievedChunk]) -> list[dict]:
    return [
        {
            "marker": i + 1,
            "document_id": c.document_id,
            "chunk_index": c.chunk_index,
            "snippet": c.text[:240],
        }
        for i, c in enumerate(chunks)
    ]


async def execute_rag_run(
    *,
    question: str,
    k: int,
    embedder: EmbeddingProvider,
    embedding_model: str,
    chat: ChatProvider,
    chat_model: str,
    store: VectorStore,
    workspace_id: str,
    record: SpanRecorder,
) -> RunOutput:
    t = time.perf_counter()
    emb = await embedder.embed([question], model=embedding_model)
    await record(
        seq=0,
        name="embed query",
        node_type="embed",
        status="succeeded",
        latency_ms=_ms(t),
        detail={"model": embedding_model},
    )

    t = time.perf_counter()
    chunks = await store.search(emb.vectors[0], k=k, workspace_id=workspace_id, query_text=question)
    await record(
        seq=1,
        name="retrieve",
        node_type="retrieve",
        status="succeeded",
        latency_ms=_ms(t),
        detail={"retrieved": len(chunks), "k": k},
    )

    context = "\n\n".join(f"[{i + 1}] {c.text}" for i, c in enumerate(chunks)) or "(no context)"
    prompt = f"Context passages:\n\n{context}\n\nQuestion: {question}"

    t = time.perf_counter()
    result = await chat.chat(
        [ChatMessage("user", prompt)], model=chat_model, system=_SYSTEM, max_tokens=1024
    )
    await record(
        seq=2,
        name="generate",
        node_type="llm",
        status="succeeded",
        latency_ms=_ms(t),
        detail={"model": chat_model, "tokens_out": result.usage.output_tokens},
    )

    return RunOutput(
        answer=result.text,
        citations=_citations(chunks),
        tokens_in=result.usage.input_tokens,
        tokens_out=result.usage.output_tokens,
    )
