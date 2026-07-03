"""Pipelines API — versioned RAG graphs (visual builder backing store)."""

from __future__ import annotations

import time
import uuid

from fastapi import APIRouter, Depends, HTTPException
from metavita_runtime import execute_pipeline, validate_graph
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import get_settings
from ..db import get_session
from ..deps import current_workspace_id
from ..factory import ProviderFactory
from ..models import Pipeline
from ..repositories import ConnectionRepository, PipelineRepository, RunRepository
from ..services.resolve import (
    build_chat_from_connection,
    build_embedding_from_connection,
    connection_values,
)
from ..vectorstores import build_vector_store, resolve_vector_store

router = APIRouter(prefix="/pipelines", tags=["pipelines"])


def _pipeline(p: Pipeline) -> dict:
    return {
        "id": str(p.id),
        "name": p.name,
        "graph": p.graph,
        "status": p.status,
        "version": p.version,
        "created_at": p.created_at.isoformat() if p.created_at else None,
        "updated_at": p.updated_at.isoformat() if p.updated_at else None,
    }


class PipelineCreate(BaseModel):
    name: str
    graph: dict | None = None


class PipelineUpdate(BaseModel):
    name: str | None = None
    graph: dict | None = None
    status: str | None = None


class RunRequest(BaseModel):
    question: str
    k: int = 5


def _require_valid(graph: dict | None) -> None:
    if graph is None:
        return
    errors = validate_graph(graph)
    if errors:
        raise HTTPException(status_code=422, detail={"error": "invalid_graph", "issues": errors})


def _slot_connection_id(graph: dict | None, node_type: str) -> str | None:
    """First `connection_id` carried by a node of `node_type` in the graph's JSONB.

    The builder stores the chosen Connection on the node's `data`, so the graph
    needs no schema change — the run path reads it here.
    """
    for node in (graph or {}).get("nodes", []):
        if not isinstance(node, dict) or node.get("type") != node_type:
            continue
        conn_id = (node.get("data") or {}).get("connection_id")
        if conn_id:
            return conn_id
    return None


@router.get("")
async def list_pipelines(
    session: AsyncSession = Depends(get_session),
    workspace_id: uuid.UUID = Depends(current_workspace_id),
) -> dict:
    items = await PipelineRepository(session).list(workspace_id)
    return {"items": [_pipeline(p) for p in items]}


@router.post("", status_code=201)
async def create_pipeline(
    body: PipelineCreate,
    session: AsyncSession = Depends(get_session),
    workspace_id: uuid.UUID = Depends(current_workspace_id),
) -> dict:
    _require_valid(body.graph)
    pipeline = await PipelineRepository(session).create(
        workspace_id=workspace_id, name=body.name, graph=body.graph
    )
    await session.commit()
    return _pipeline(pipeline)


@router.get("/{pipeline_id}")
async def get_pipeline(
    pipeline_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    workspace_id: uuid.UUID = Depends(current_workspace_id),
) -> dict:
    pipeline = await PipelineRepository(session).get(pipeline_id, workspace_id)
    if pipeline is None:
        raise HTTPException(status_code=404, detail="pipeline not found")
    return _pipeline(pipeline)


@router.put("/{pipeline_id}")
async def update_pipeline(
    pipeline_id: uuid.UUID,
    body: PipelineUpdate,
    session: AsyncSession = Depends(get_session),
    workspace_id: uuid.UUID = Depends(current_workspace_id),
) -> dict:
    _require_valid(body.graph)
    repo = PipelineRepository(session)
    pipeline = await repo.get(pipeline_id, workspace_id)
    if pipeline is None:
        raise HTTPException(status_code=404, detail="pipeline not found")
    pipeline = await repo.update(
        pipeline, name=body.name, graph=body.graph, status=body.status
    )
    await session.commit()
    await session.refresh(pipeline)  # reload server-side onupdate timestamp
    return _pipeline(pipeline)


@router.post("/{pipeline_id}/run")
async def run_pipeline(
    pipeline_id: uuid.UUID,
    body: RunRequest,
    session: AsyncSession = Depends(get_session),
    workspace_id: uuid.UUID = Depends(current_workspace_id),
) -> dict:
    pipeline = await PipelineRepository(session).get(pipeline_id, workspace_id)
    if pipeline is None:
        raise HTTPException(status_code=404, detail="pipeline not found")

    factory = ProviderFactory(get_settings(), session=session, workspace_id=workspace_id)
    conns = ConnectionRepository(session)
    graph = pipeline.graph

    async def _slot(node_type: str):
        conn_id = _slot_connection_id(graph, node_type)
        if conn_id is None:
            return None
        try:
            slot_uuid = uuid.UUID(str(conn_id))
        except ValueError as exc:
            raise HTTPException(status_code=422, detail="invalid connection_id on node") from exc
        conn = await conns.get(slot_uuid, workspace_id)
        if conn is None:
            raise HTTPException(status_code=422, detail="node connection not found")
        return conn

    # Each capability-bearing node may pin its own Connection via `data.connection_id`:
    # the `llm` node → LLM, the `embed` node → embeddings, the `retrieve` node →
    # vector store. Unset slots fall back to the workspace defaults.
    llm_conn = await _slot("llm")
    if llm_conn is not None:
        resolved = build_chat_from_connection(llm_conn, default_model="")
        chat, chat_model = resolved.provider, resolved.model
    else:
        chat, chat_model = await factory.chat()

    embed_conn = await _slot("embed")
    if embed_conn is not None:
        emb = build_embedding_from_connection(
            embed_conn, default_model=""
        )
        embedder, embedding_model = emb.provider, emb.model
    else:
        embedder, embedding_model = await factory.embedding()

    retrieve_conn = await _slot("retrieve")
    if retrieve_conn is not None:
        store = build_vector_store(
            retrieve_conn.provider,
            connection_values(retrieve_conn),
            session=session,
            workspace_id=workspace_id,
        )
    else:
        store = await resolve_vector_store(session, workspace_id)
    runs = RunRepository(session)

    run = await runs.start(
        workspace_id=workspace_id,
        pipeline_id=pipeline_id,
        kind="pipeline",
        input={"question": body.question, "k": body.k},
    )
    started = time.perf_counter()

    async def record(**span) -> None:
        await runs.add_span(run, **span)

    try:
        out = await execute_pipeline(
            pipeline.graph,
            question=body.question,
            k_default=body.k,
            embedder=embedder,
            embedding_model=embedding_model,
            chat=chat,
            chat_model=chat_model,
            store=store,
            workspace_id=str(workspace_id),
            record=record,
        )
    except Exception as exc:  # noqa: BLE001 - record failure on the run then surface
        await runs.finish(
            run,
            status="failed",
            output={"error": str(exc)},
            latency_ms=int((time.perf_counter() - started) * 1000),
        )
        await session.commit()
        raise HTTPException(status_code=500, detail="run failed") from exc

    await runs.finish(
        run,
        status="succeeded",
        output={"answer": out.answer, "citations": out.citations},
        latency_ms=int((time.perf_counter() - started) * 1000),
        tokens_in=out.tokens_in,
        tokens_out=out.tokens_out,
    )
    await session.commit()
    return {
        "run_id": str(run.id),
        "status": "succeeded",
        "answer": out.answer,
        "citations": out.citations,
    }
