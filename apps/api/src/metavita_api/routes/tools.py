"""Tools API — the registry of callables agents can invoke.

Each tool has a `kind` (retriever|http|code|mcp) and a JSON-Schema `input_schema`
the model fills in. The agent loop reads enabled tools from here.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import get_session
from ..deps import current_workspace_id
from ..models import Tool
from ..repositories import ToolRepository

router = APIRouter(prefix="/tools", tags=["tools"])

KINDS = {"retriever", "http", "code", "mcp"}


def _tool(t: Tool) -> dict:
    return {
        "id": str(t.id),
        "name": t.name,
        "kind": t.kind,
        "description": t.description,
        "input_schema": t.input_schema,
        "config": t.config,
        "enabled": t.enabled,
        "created_at": t.created_at.isoformat() if t.created_at else None,
        "updated_at": t.updated_at.isoformat() if t.updated_at else None,
    }


class ToolCreate(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    kind: str = "http"
    description: str = ""
    input_schema: dict = Field(default_factory=dict)
    config: dict = Field(default_factory=dict)
    enabled: bool = True


class ToolUpdate(BaseModel):
    name: str | None = None
    kind: str | None = None
    description: str | None = None
    input_schema: dict | None = None
    config: dict | None = None
    enabled: bool | None = None


def _validate_kind(kind: str | None) -> None:
    if kind is not None and kind not in KINDS:
        raise HTTPException(status_code=422, detail=f"kind must be one of {sorted(KINDS)}")


@router.get("")
async def list_tools(
    session: AsyncSession = Depends(get_session),
    workspace_id: uuid.UUID = Depends(current_workspace_id),
) -> dict:
    items = await ToolRepository(session).list(workspace_id)
    return {"items": [_tool(t) for t in items]}


@router.post("", status_code=201)
async def create_tool(
    body: ToolCreate,
    session: AsyncSession = Depends(get_session),
    workspace_id: uuid.UUID = Depends(current_workspace_id),
) -> dict:
    _validate_kind(body.kind)
    tool = await ToolRepository(session).create(
        workspace_id=workspace_id,
        name=body.name,
        kind=body.kind,
        description=body.description,
        input_schema=body.input_schema,
        config=body.config,
        enabled=body.enabled,
    )
    await session.commit()
    return _tool(tool)


@router.get("/{tool_id}")
async def get_tool(
    tool_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    workspace_id: uuid.UUID = Depends(current_workspace_id),
) -> dict:
    tool = await ToolRepository(session).get(tool_id, workspace_id)
    if tool is None:
        raise HTTPException(status_code=404, detail="tool not found")
    return _tool(tool)


@router.put("/{tool_id}")
async def update_tool(
    tool_id: uuid.UUID,
    body: ToolUpdate,
    session: AsyncSession = Depends(get_session),
    workspace_id: uuid.UUID = Depends(current_workspace_id),
) -> dict:
    _validate_kind(body.kind)
    repo = ToolRepository(session)
    tool = await repo.get(tool_id, workspace_id)
    if tool is None:
        raise HTTPException(status_code=404, detail="tool not found")
    tool = await repo.update(
        tool,
        name=body.name,
        kind=body.kind,
        description=body.description,
        input_schema=body.input_schema,
        config=body.config,
    )
    if body.enabled is not None:  # bool — pass through so False isn't dropped
        tool.enabled = body.enabled
        await session.flush()
    await session.commit()
    await session.refresh(tool)
    return _tool(tool)


@router.delete("/{tool_id}", status_code=204)
async def delete_tool(
    tool_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    workspace_id: uuid.UUID = Depends(current_workspace_id),
) -> None:
    repo = ToolRepository(session)
    tool = await repo.get(tool_id, workspace_id)
    if tool is None:
        raise HTTPException(status_code=404, detail="tool not found")
    await repo.delete(tool)
    await session.commit()
