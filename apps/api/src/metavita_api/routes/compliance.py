"""Compliance API — GDPR DSAR (export / erasure) + retention policy.

A DSAR is created in `pending`, then `process` runs the export (data portability)
or erasure (right-to-be-forgotten, crypto-shred via hard delete). Every action is
written to the hash-chained audit log for SOC 2 / HIPAA evidence.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import get_session
from ..deps import current_workspace_id
from ..models import DataSubjectRequest
from ..repositories import AuditRepository, DataSubjectRequestRepository, WorkspaceRepository
from ..services.notify import notify

router = APIRouter(prefix="/compliance", tags=["compliance"])

KINDS = {"export", "erasure"}


def _dsar(d: DataSubjectRequest) -> dict:
    return {
        "id": str(d.id),
        "subject": d.subject,
        "kind": d.kind,
        "status": d.status,
        "result": d.result,
        "created_at": d.created_at.isoformat() if d.created_at else None,
        "finished_at": d.finished_at.isoformat() if d.finished_at else None,
    }


class DSARCreate(BaseModel):
    subject: str
    kind: str  # export | erasure


class RetentionUpdate(BaseModel):
    retention_days: int | None = None
    region: str | None = None
    hipaa: bool | None = None


@router.get("/requests")
async def list_requests(
    session: AsyncSession = Depends(get_session),
    workspace_id: uuid.UUID = Depends(current_workspace_id),
) -> dict:
    items = await DataSubjectRequestRepository(session).list(workspace_id)
    return {"items": [_dsar(d) for d in items]}


@router.post("/requests", status_code=201)
async def create_request(
    body: DSARCreate,
    session: AsyncSession = Depends(get_session),
    workspace_id: uuid.UUID = Depends(current_workspace_id),
) -> dict:
    if body.kind not in KINDS:
        raise HTTPException(status_code=422, detail=f"kind must be one of {sorted(KINDS)}")
    repo = DataSubjectRequestRepository(session)
    dsar = await repo.create(workspace_id=workspace_id, subject=body.subject, kind=body.kind)
    await AuditRepository(session).record(
        actor="system",
        action="dsar.created",
        workspace_id=workspace_id,
        resource_type="data_subject_request",
        resource_id=str(dsar.id),
        detail={"subject": body.subject, "kind": body.kind},
    )
    await session.commit()
    return _dsar(dsar)


@router.post("/requests/{dsar_id}/process")
async def process_request(
    dsar_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    workspace_id: uuid.UUID = Depends(current_workspace_id),
) -> dict:
    repo = DataSubjectRequestRepository(session)
    dsar = await repo.get(dsar_id, workspace_id)
    if dsar is None:
        raise HTTPException(status_code=404, detail="request not found")
    if dsar.status == "completed":
        raise HTTPException(status_code=409, detail="request already completed")

    if dsar.kind == "export":
        await repo.export(dsar)
        action = "dsar.exported"
    else:
        await repo.erase(dsar)
        action = "dsar.erased"

    await AuditRepository(session).record(
        actor="system",
        action=action,
        workspace_id=workspace_id,
        resource_type="data_subject_request",
        resource_id=str(dsar.id),
        detail={"subject": dsar.subject, "result": dsar.result},
    )
    await notify(
        session, workspace_id=workspace_id, category="compliance",
        title="Data export ready" if dsar.kind == "export" else "Data erased",
        body=dsar.subject, severity="success", link="/settings/compliance",
    )
    await session.commit()
    await session.refresh(dsar)
    return _dsar(dsar)


@router.get("/retention")
async def get_retention(
    session: AsyncSession = Depends(get_session),
    workspace_id: uuid.UUID = Depends(current_workspace_id),
) -> dict:
    ws = await WorkspaceRepository(session).get(workspace_id)
    if ws is None:
        raise HTTPException(status_code=404, detail="workspace not found")
    s = ws.settings or {}
    return {
        "retention_days": s.get("retention_days"),
        "region": s.get("region", "global"),
        "hipaa": bool(s.get("hipaa", False)),
        "allowed_providers": ws.allowed_providers or [],
    }


@router.put("/retention")
async def update_retention(
    body: RetentionUpdate,
    session: AsyncSession = Depends(get_session),
    workspace_id: uuid.UUID = Depends(current_workspace_id),
) -> dict:
    repo = WorkspaceRepository(session)
    ws = await repo.get(workspace_id)
    if ws is None:
        raise HTTPException(status_code=404, detail="workspace not found")
    settings = dict(ws.settings or {})
    if body.retention_days is not None:
        settings["retention_days"] = body.retention_days
    if body.region is not None:
        settings["region"] = body.region
    if body.hipaa is not None:
        settings["hipaa"] = body.hipaa
    await repo.update(ws, settings=settings)
    await AuditRepository(session).record(
        actor="system",
        action="retention.updated",
        workspace_id=workspace_id,
        resource_type="workspace",
        resource_id=str(workspace_id),
        detail=settings,
    )
    await session.commit()
    await session.refresh(ws)
    s = ws.settings or {}
    return {
        "retention_days": s.get("retention_days"),
        "region": s.get("region", "global"),
        "hipaa": bool(s.get("hipaa", False)),
        "allowed_providers": ws.allowed_providers or [],
    }
