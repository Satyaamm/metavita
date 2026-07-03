"""Pipeline DAG executor — runs an arbitrary graph node-by-node.

Walks the graph in topological order, dispatching each node to a handler in the
node-handler registry. Honors per-node config in `node.data` (retrieve `k`, llm
`model`). Records a span per node via the injected `record` callback. Pure of
persistence; providers + store are injected.
"""

from __future__ import annotations

import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field

from metavita_providers import ChatMessage, ChatProvider, EmbeddingProvider

from .graph import topological_order
from .types import RetrievedChunk, VectorStore

SpanRecorder = Callable[..., Awaitable[None]]

_SYSTEM = (
    "You are MetaVita. Answer using only the numbered context passages and cite them "
    "with markers like [1]. If the context lacks the answer, say so."
)


@dataclass(slots=True)
class PipelineRunOutput:
    answer: str
    citations: list[dict] = field(default_factory=list)
    tokens_in: int = 0
    tokens_out: int = 0


def _ms(t: float) -> int:
    return int((time.perf_counter() - t) * 1000)


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


async def execute_pipeline(
    graph: dict,
    *,
    question: str,
    embedder: EmbeddingProvider,
    embedding_model: str,
    chat: ChatProvider,
    chat_model: str,
    store: VectorStore,
    workspace_id: str,
    record: SpanRecorder,
    k_default: int = 5,
) -> PipelineRunOutput:
    nodes_by_id = {
        n["id"]: n
        for n in graph.get("nodes", [])
        if isinstance(n, dict) and n.get("id")
    }
    order = topological_order(graph)
    ctx: dict = {"question": question, "chunks": [], "answer": "", "tokens_in": 0, "tokens_out": 0}
    seq = 0

    async def span(name: str, node_type: str, t: float, detail: dict) -> None:
        nonlocal seq
        await record(
            seq=seq, name=name, node_type=node_type, status="succeeded",
            latency_ms=_ms(t), detail=detail,
        )
        seq += 1

    async def handle_retrieve(node: dict) -> None:
        k = int(node.get("data", {}).get("k", k_default))
        t = time.perf_counter()
        emb = await embedder.embed([ctx["question"]], model=embedding_model)
        ctx["chunks"] = await store.search(
            emb.vectors[0], k=k, workspace_id=workspace_id, query_text=ctx["question"]
        )
        await span("retrieve", "retrieve", t, {"retrieved": len(ctx["chunks"]), "k": k})

    async def handle_llm(node: dict) -> None:
        model = node.get("data", {}).get("model") or chat_model
        chunks = ctx["chunks"]
        context = "\n\n".join(f"[{i + 1}] {c.text}" for i, c in enumerate(chunks)) or "(no context)"
        prompt = f"Context passages:\n\n{context}\n\nQuestion: {ctx['question']}"
        t = time.perf_counter()
        res = await chat.chat(
            [ChatMessage("user", prompt)], model=model, system=_SYSTEM, max_tokens=1024
        )
        ctx["answer"] = res.text
        ctx["tokens_in"] += res.usage.input_tokens
        ctx["tokens_out"] += res.usage.output_tokens
        await span("generate", "llm", t, {"model": model, "tokens_out": res.usage.output_tokens})

    handlers = {"retrieve": handle_retrieve, "llm": handle_llm}

    executed = False
    for node_id in order:
        node = nodes_by_id.get(node_id)
        if node is None:
            continue
        handler = handlers.get(node.get("type"))
        if handler:
            await handler(node)
            executed = True

    # Fallback for graphs without retrieve/llm nodes (or empty graphs): do a default RAG turn.
    if not executed:
        await handle_retrieve({"data": {}})
        await handle_llm({"data": {}})

    return PipelineRunOutput(
        answer=ctx["answer"],
        citations=_citations(ctx["chunks"]),
        tokens_in=ctx["tokens_in"],
        tokens_out=ctx["tokens_out"],
    )
