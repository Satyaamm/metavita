"""Deployments API — publish a pipeline/agent and manage its serving status."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import get_session
from ..deps import current_workspace_id
from ..models import Deployment
from ..repositories import AgentRepository, DeploymentRepository, PipelineRepository
from ..security.keys import generate_api_key

router = APIRouter(prefix="/deployments", tags=["deployments"])


def _deployment(d: Deployment) -> dict:
    return {
        "id": str(d.id),
        "name": d.name,
        "target_type": d.target_type,
        "target_id": str(d.target_id),
        "status": d.status,
        "key_prefix": d.key_prefix,
        "created_at": d.created_at.isoformat() if d.created_at else None,
        "updated_at": d.updated_at.isoformat() if d.updated_at else None,
    }


class DeploymentCreate(BaseModel):
    name: str
    target_type: str  # pipeline | agent
    target_id: uuid.UUID


@router.post("", status_code=201)
async def create_deployment(
    body: DeploymentCreate,
    session: AsyncSession = Depends(get_session),
    workspace_id: uuid.UUID = Depends(current_workspace_id),
) -> dict:
    if body.target_type not in ("pipeline", "agent"):
        raise HTTPException(status_code=422, detail="target_type must be pipeline or agent")

    # Confirm the target exists in this workspace.
    if body.target_type == "pipeline":
        target = await PipelineRepository(session).get(body.target_id, workspace_id)
    else:
        target = await AgentRepository(session).get(body.target_id, workspace_id)
    if target is None:
        raise HTTPException(status_code=404, detail=f"{body.target_type} not found")

    key, prefix, key_hash = generate_api_key()
    deployment = await DeploymentRepository(session).create(
        workspace_id=workspace_id,
        name=body.name,
        target_type=body.target_type,
        target_id=body.target_id,
        key_prefix=prefix,
        key_hash=key_hash,
    )
    await session.commit()
    # The plaintext API key is returned exactly once, here.
    return {**_deployment(deployment), "api_key": key}


@router.get("")
async def list_deployments(
    limit: int = Query(default=20, le=200),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_session),
    workspace_id: uuid.UUID = Depends(current_workspace_id),
) -> dict:
    repo = DeploymentRepository(session)
    items = await repo.list(workspace_id, limit=limit, offset=offset)
    total = await repo.count(workspace_id)
    return {"items": [_deployment(d) for d in items], "total": total}


@router.get("/{deployment_id}")
async def get_deployment(
    deployment_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    workspace_id: uuid.UUID = Depends(current_workspace_id),
) -> dict:
    deployment = await DeploymentRepository(session).get(deployment_id, workspace_id)
    if deployment is None:
        raise HTTPException(status_code=404, detail="deployment not found")
    return _deployment(deployment)


async def _set_status(
    deployment_id: uuid.UUID, status: str, session: AsyncSession, workspace_id: uuid.UUID
) -> dict:
    repo = DeploymentRepository(session)
    deployment = await repo.get(deployment_id, workspace_id)
    if deployment is None:
        raise HTTPException(status_code=404, detail="deployment not found")
    await repo.set_status(deployment, status)
    await session.commit()
    await session.refresh(deployment)
    return _deployment(deployment)


@router.post("/{deployment_id}/pause")
async def pause_deployment(
    deployment_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    workspace_id: uuid.UUID = Depends(current_workspace_id),
) -> dict:
    return await _set_status(deployment_id, "paused", session, workspace_id)


@router.post("/{deployment_id}/unpause")
async def unpause_deployment(
    deployment_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    workspace_id: uuid.UUID = Depends(current_workspace_id),
) -> dict:
    return await _set_status(deployment_id, "active", session, workspace_id)
