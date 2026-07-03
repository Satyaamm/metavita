"""Retrieve → answer pipeline: grounded QA with inline citations."""

from __future__ import annotations

from collections.abc import AsyncIterator

from metavita_providers import ChatMessage, ChatProvider, EmbeddingProvider

from .types import Answer, Citation, RetrievedChunk, VectorStore

_SYSTEM = (
    "You are MetaVita, a retrieval-augmented assistant. Answer the user's question "
    "using ONLY the numbered context passages provided. Cite the passages you use "
    "with inline markers like [1], [2]. If the context does not contain the answer, "
    "say so plainly — do not invent facts."
)


def _build_prompt(question: str, chunks: list[RetrievedChunk]) -> str:
    blocks = [
        f"[{i + 1}] {c.text}".strip() for i, c in enumerate(chunks)
    ]
    context = "\n\n".join(blocks) if blocks else "(no context retrieved)"
    return f"Context passages:\n\n{context}\n\nQuestion: {question}"


def _citations(chunks: list[RetrievedChunk]) -> list[Citation]:
    return [
        Citation(
            marker=i + 1,
            document_id=c.document_id,
            chunk_index=c.chunk_index,
            snippet=c.text[:240],
        )
        for i, c in enumerate(chunks)
    ]


async def _retrieve(
    question: str,
    *,
    embedder: EmbeddingProvider,
    embedding_model: str,
    store: VectorStore,
    workspace_id: str,
    k: int,
) -> list[RetrievedChunk]:
    emb = await embedder.embed([question], model=embedding_model)
    return await store.search(emb.vectors[0], k=k, workspace_id=workspace_id, query_text=question)


async def answer_question(
    question: str,
    *,
    embedder: EmbeddingProvider,
    embedding_model: str,
    chat: ChatProvider,
    chat_model: str,
    store: VectorStore,
    workspace_id: str,
    k: int = 5,
    max_tokens: int = 1024,
) -> Answer:
    chunks = await _retrieve(
        question,
        embedder=embedder,
        embedding_model=embedding_model,
        store=store,
        workspace_id=workspace_id,
        k=k,
    )
    result = await chat.chat(
        [ChatMessage("user", _build_prompt(question, chunks))],
        model=chat_model,
        max_tokens=max_tokens,
        system=_SYSTEM,
    )
    return Answer(text=result.text, citations=_citations(chunks))


async def stream_answer(
    question: str,
    *,
    embedder: EmbeddingProvider,
    embedding_model: str,
    chat: ChatProvider,
    chat_model: str,
    store: VectorStore,
    workspace_id: str,
    k: int = 5,
    max_tokens: int = 1024,
) -> AsyncIterator[tuple[str, str]]:
    """Yield (event, data) pairs: one ('citations', json) then many ('token', text)."""
    import json

    chunks = await _retrieve(
        question,
        embedder=embedder,
        embedding_model=embedding_model,
        store=store,
        workspace_id=workspace_id,
        k=k,
    )
    citations = _citations(chunks)
    yield "citations", json.dumps(
        [
            {
                "marker": c.marker,
                "document_id": c.document_id,
                "chunk_index": c.chunk_index,
                "snippet": c.snippet,
            }
            for c in citations
        ]
    )
    async for token in chat.chat_stream(
        [ChatMessage("user", _build_prompt(question, chunks))],
        model=chat_model,
        max_tokens=max_tokens,
        system=_SYSTEM,
    ):
        yield "token", token
