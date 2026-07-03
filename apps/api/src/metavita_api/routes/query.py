"""Grounded QA over a workspace's indexed documents (streaming + sync)."""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from metavita_runtime import answer_question, stream_answer
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import get_settings
from ..db import get_session
from ..deps import current_workspace_id
from ..factory import ProviderFactory
from ..repositories import AuditRepository
from ..vectorstores import resolve_vector_store

router = APIRouter(tags=["query"])


class QueryRequest(BaseModel):
    question: str
    k: int = 5


def _sse(event: str, data: str) -> str:
    payload = "".join(f"data: {line}\n" for line in data.splitlines() or [""])
    return f"event: {event}\n{payload}\n"


@router.post("/query/stream")
async def query_stream(
    body: QueryRequest,
    session: AsyncSession = Depends(get_session),
    workspace_id: uuid.UUID = Depends(current_workspace_id),
) -> StreamingResponse:
    factory = ProviderFactory(get_settings(), session=session, workspace_id=workspace_id)
    embedder, embedding_model = await factory.embedding()
    chat, chat_model = await factory.chat()
    store = await resolve_vector_store(session, workspace_id)

    await AuditRepository(session).record(
        actor="system",
        action="query.streamed",
        workspace_id=workspace_id,
        detail={"k": body.k},
    )
    await session.commit()

    async def gen() -> AsyncIterator[str]:
        async for event, data in stream_answer(
            body.question,
            embedder=embedder,
            embedding_model=embedding_model,
            chat=chat,
            chat_model=chat_model,
            store=store,
            workspace_id=str(workspace_id),
            k=body.k,
        ):
            yield _sse(event, data)
        yield _sse("done", "")

    return StreamingResponse(gen(), media_type="text/event-stream")


@router.post("/query")
async def query_sync(
    body: QueryRequest,
    session: AsyncSession = Depends(get_session),
    workspace_id: uuid.UUID = Depends(current_workspace_id),
) -> dict:
    factory = ProviderFactory(get_settings(), session=session, workspace_id=workspace_id)
    embedder, embedding_model = await factory.embedding()
    chat, chat_model = await factory.chat()
    store = await resolve_vector_store(session, workspace_id)

    result = await answer_question(
        body.question,
        embedder=embedder,
        embedding_model=embedding_model,
        chat=chat,
        chat_model=chat_model,
        store=store,
        workspace_id=str(workspace_id),
        k=body.k,
    )
    await AuditRepository(session).record(
        actor="system",
        action="query.answered",
        workspace_id=workspace_id,
        detail={"k": body.k},
    )
    await session.commit()

    return {
        "answer": result.text,
        "citations": [
            {
                "marker": c.marker,
                "document_id": c.document_id,
                "chunk_index": c.chunk_index,
                "snippet": c.snippet,
            }
            for c in result.citations
        ],
    }
