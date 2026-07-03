"""Agents API — agent configurations (builder backing store)."""

from __future__ import annotations

import time
import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import get_settings
from ..db import get_session
from ..deps import current_workspace_id
from ..factory import ProviderFactory
from ..models import Agent
from ..repositories import AgentRepository, ConnectionRepository, RunRepository
from ..services.agent import DEFAULT_SYSTEM, build_tools, make_tool_executor, run_agent
from ..services.resolve import (
    build_chat_from_connection,
    build_embedding_from_connection,
    connection_values,
)
from ..vectorstores import build_vector_store, resolve_vector_store

router = APIRouter(prefix="/agents", tags=["agents"])


def _agent(a: Agent) -> dict:
    return {
        "id": str(a.id),
        "name": a.name,
        "system_prompt": a.system_prompt,
        "provider": a.provider,
        "model": a.model,
        "tools": a.tools,
        "index_id": str(a.index_id) if a.index_id else None,
        "llm_connection_id": str(a.llm_connection_id) if a.llm_connection_id else None,
        "embedding_connection_id": (
            str(a.embedding_connection_id) if a.embedding_connection_id else None
        ),
        "vector_store_connection_id": (
            str(a.vector_store_connection_id) if a.vector_store_connection_id else None
        ),
        "memory": a.memory,
        "status": a.status,
        "created_at": a.created_at.isoformat() if a.created_at else None,
        "updated_at": a.updated_at.isoformat() if a.updated_at else None,
    }


class AgentCreate(BaseModel):
    name: str
    system_prompt: str | None = None
    provider: str = "anthropic"
    model: str = "claude-opus-4-8"
    tools: list = []
    index_id: uuid.UUID | None = None
    llm_connection_id: uuid.UUID | None = None
    embedding_connection_id: uuid.UUID | None = None
    vector_store_connection_id: uuid.UUID | None = None
    memory: bool = False


class AgentRunRequest(BaseModel):
    message: str
    k: int = 5


class AgentUpdate(BaseModel):
    name: str | None = None
    system_prompt: str | None = None
    provider: str | None = None
    model: str | None = None
    tools: list | None = None
    index_id: uuid.UUID | None = None
    llm_connection_id: uuid.UUID | None = None
    embedding_connection_id: uuid.UUID | None = None
    vector_store_connection_id: uuid.UUID | None = None
    memory: bool | None = None
    status: str | None = None


@router.get("")
async def list_agents(
    session: AsyncSession = Depends(get_session),
    workspace_id: uuid.UUID = Depends(current_workspace_id),
) -> dict:
    items = await AgentRepository(session).list(workspace_id)
    return {"items": [_agent(a) for a in items]}


@router.post("", status_code=201)
async def create_agent(
    body: AgentCreate,
    session: AsyncSession = Depends(get_session),
    workspace_id: uuid.UUID = Depends(current_workspace_id),
) -> dict:
    agent = await AgentRepository(session).create(
        workspace_id=workspace_id,
        name=body.name,
        system_prompt=body.system_prompt,
        provider=body.provider,
        model=body.model,
        tools=body.tools,
        index_id=body.index_id,
        llm_connection_id=body.llm_connection_id,
        embedding_connection_id=body.embedding_connection_id,
        vector_store_connection_id=body.vector_store_connection_id,
        memory=body.memory,
    )
    await session.commit()
    return _agent(agent)


@router.post("/{agent_id}/run")
async def run_agent_route(
    agent_id: uuid.UUID,
    body: AgentRunRequest,
    session: AsyncSession = Depends(get_session),
    workspace_id: uuid.UUID = Depends(current_workspace_id),
) -> dict:
    agent = await AgentRepository(session).get(agent_id, workspace_id)
    if agent is None:
        raise HTTPException(status_code=404, detail="agent not found")

    factory = ProviderFactory(get_settings(), session=session, workspace_id=workspace_id)
    conns = ConnectionRepository(session)

    # Connection slots override the workspace defaults when set on the agent.
    if agent.llm_connection_id is not None:
        slot = await conns.get(agent.llm_connection_id, workspace_id)
        if slot is None:
            raise HTTPException(status_code=422, detail="llm connection not found")
        resolved = build_chat_from_connection(slot, default_model=agent.model)
        chat, _default_model = resolved.provider, resolved.model
    else:
        chat, _default_model = await factory.chat(provider=agent.provider, model=agent.model)

    if agent.embedding_connection_id is not None:
        slot = await conns.get(agent.embedding_connection_id, workspace_id)
        if slot is None:
            raise HTTPException(status_code=422, detail="embedding connection not found")
        emb = build_embedding_from_connection(slot, default_model="")
        embedder, embedding_model = emb.provider, emb.model
    else:
        embedder, embedding_model = await factory.embedding()

    if agent.vector_store_connection_id is not None:
        slot = await conns.get(agent.vector_store_connection_id, workspace_id)
        if slot is None:
            raise HTTPException(status_code=422, detail="vector store connection not found")
        store = build_vector_store(
            slot.provider,
            connection_values(slot),
            session=session,
            workspace_id=workspace_id,
        )
    else:
        store = await resolve_vector_store(session, workspace_id)
    runs = RunRepository(session)

    run = await runs.start(
        workspace_id=workspace_id,
        pipeline_id=None,
        kind="agent",
        input={"message": body.message, "agent_id": str(agent_id)},
    )
    started = time.perf_counter()

    async def record(**span) -> None:
        await runs.add_span(run, **span)

    execute = make_tool_executor(
        embedder=embedder,
        embedding_model=embedding_model,
        store=store,
        workspace_id=str(workspace_id),
        k=body.k,
    )
    try:
        answer = await run_agent(
            system=agent.system_prompt or DEFAULT_SYSTEM,
            message=body.message,
            chat=chat,
            chat_model=agent.model,
            tools=build_tools(agent.tools),
            execute=execute,
            record=record,
        )
    except Exception as exc:  # noqa: BLE001
        await runs.finish(
            run,
            status="failed",
            output={"error": str(exc)},
            latency_ms=int((time.perf_counter() - started) * 1000),
        )
        await session.commit()
        raise HTTPException(status_code=500, detail="agent run failed") from exc

    await runs.finish(
        run,
        status="succeeded",
        output={"answer": answer},
        latency_ms=int((time.perf_counter() - started) * 1000),
    )
    await session.commit()
    return {"run_id": str(run.id), "status": "succeeded", "answer": answer}


@router.get("/{agent_id}")
async def get_agent(
    agent_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    workspace_id: uuid.UUID = Depends(current_workspace_id),
) -> dict:
    agent = await AgentRepository(session).get(agent_id, workspace_id)
    if agent is None:
        raise HTTPException(status_code=404, detail="agent not found")
    return _agent(agent)


@router.put("/{agent_id}")
async def update_agent(
    agent_id: uuid.UUID,
    body: AgentUpdate,
    session: AsyncSession = Depends(get_session),
    workspace_id: uuid.UUID = Depends(current_workspace_id),
) -> dict:
    repo = AgentRepository(session)
    agent = await repo.get(agent_id, workspace_id)
    if agent is None:
        raise HTTPException(status_code=404, detail="agent not found")
    # memory is a bool — pass through explicitly so False isn't dropped by the None filter.
    agent = await repo.update(
        agent,
        name=body.name,
        system_prompt=body.system_prompt,
        provider=body.provider,
        model=body.model,
        tools=body.tools,
        index_id=body.index_id,
        status=body.status,
    )
    if body.memory is not None:
        agent.memory = body.memory
        await session.flush()
    # Connection slots are nullable: only touch a slot the caller actually sent, but
    # honor an explicit null (unset) — repo.update drops None, so set them here.
    sent = body.model_fields_set
    for slot in ("llm_connection_id", "embedding_connection_id", "vector_store_connection_id"):
        if slot in sent:
            setattr(agent, slot, getattr(body, slot))
            await session.flush()
    await session.commit()
    await session.refresh(agent)  # reload server-side onupdate timestamp
    return _agent(agent)
