"""Prompts API — a versioned library of reusable prompts.

Editing a prompt's content appends a new immutable version; history is never
mutated. `current_version` points at the latest snapshot.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import get_session
from ..deps import current_workspace_id
from ..models import Prompt
from ..repositories import PromptRepository

router = APIRouter(prefix="/prompts", tags=["prompts"])


def _prompt(p: Prompt, *, content: str | None = None) -> dict:
    out = {
        "id": str(p.id),
        "name": p.name,
        "description": p.description,
        "current_version": p.current_version,
        "created_at": p.created_at.isoformat() if p.created_at else None,
        "updated_at": p.updated_at.isoformat() if p.updated_at else None,
    }
    if content is not None:
        out["content"] = content
    return out


def _version(v) -> dict:
    return {
        "version": v.version,
        "content": v.content,
        "notes": v.notes,
        "created_at": v.created_at.isoformat() if v.created_at else None,
    }


class PromptCreate(BaseModel):
    name: str = Field(min_length=1, max_length=256)
    description: str = ""
    content: str = ""


class PromptUpdate(BaseModel):
    name: str | None = None
    description: str | None = None


class PromptVersionCreate(BaseModel):
    content: str
    notes: str = ""


@router.get("")
async def list_prompts(
    session: AsyncSession = Depends(get_session),
    workspace_id: uuid.UUID = Depends(current_workspace_id),
) -> dict:
    items = await PromptRepository(session).list(workspace_id)
    return {"items": [_prompt(p) for p in items]}


@router.post("", status_code=201)
async def create_prompt(
    body: PromptCreate,
    session: AsyncSession = Depends(get_session),
    workspace_id: uuid.UUID = Depends(current_workspace_id),
) -> dict:
    prompt = await PromptRepository(session).create(
        workspace_id=workspace_id,
        name=body.name,
        description=body.description,
        content=body.content,
    )
    await session.commit()
    return _prompt(prompt, content=body.content)


@router.get("/{prompt_id}")
async def get_prompt(
    prompt_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    workspace_id: uuid.UUID = Depends(current_workspace_id),
) -> dict:
    repo = PromptRepository(session)
    prompt = await repo.get(prompt_id, workspace_id)
    if prompt is None:
        raise HTTPException(status_code=404, detail="prompt not found")
    out = _prompt(prompt, content=await repo.latest_content(prompt))
    out["versions"] = [_version(v) for v in sorted(prompt.versions, key=lambda v: -v.version)]
    return out


@router.put("/{prompt_id}")
async def update_prompt(
    prompt_id: uuid.UUID,
    body: PromptUpdate,
    session: AsyncSession = Depends(get_session),
    workspace_id: uuid.UUID = Depends(current_workspace_id),
) -> dict:
    repo = PromptRepository(session)
    prompt = await repo.get(prompt_id, workspace_id)
    if prompt is None:
        raise HTTPException(status_code=404, detail="prompt not found")
    prompt = await repo.update_meta(prompt, name=body.name, description=body.description)
    await session.commit()
    await session.refresh(prompt)
    return _prompt(prompt, content=await repo.latest_content(prompt))


@router.post("/{prompt_id}/versions", status_code=201)
async def add_prompt_version(
    prompt_id: uuid.UUID,
    body: PromptVersionCreate,
    session: AsyncSession = Depends(get_session),
    workspace_id: uuid.UUID = Depends(current_workspace_id),
) -> dict:
    repo = PromptRepository(session)
    prompt = await repo.get(prompt_id, workspace_id)
    if prompt is None:
        raise HTTPException(status_code=404, detail="prompt not found")
    version = await repo.add_version(prompt, content=body.content, notes=body.notes)
    await session.commit()
    return _version(version)


@router.delete("/{prompt_id}", status_code=204)
async def delete_prompt(
    prompt_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    workspace_id: uuid.UUID = Depends(current_workspace_id),
) -> None:
    repo = PromptRepository(session)
    prompt = await repo.get(prompt_id, workspace_id)
    if prompt is None:
        raise HTTPException(status_code=404, detail="prompt not found")
    await repo.delete(prompt)
    await session.commit()
