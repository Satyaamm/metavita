"""Runs / traces API — execution records with their span trees."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import get_session
from ..deps import current_workspace_id
from ..models import Run, Span
from ..repositories import RunRepository

router = APIRouter(prefix="/runs", tags=["runs"])


def _run(r: Run, *, with_spans: bool = False) -> dict:
    data = {
        "id": str(r.id),
        "pipeline_id": str(r.pipeline_id) if r.pipeline_id else None,
        "kind": r.kind,
        "status": r.status,
        "input": r.input,
        "latency_ms": r.latency_ms,
        "tokens_in": r.tokens_in,
        "tokens_out": r.tokens_out,
        "created_at": r.created_at.isoformat() if r.created_at else None,
        "finished_at": r.finished_at.isoformat() if r.finished_at else None,
    }
    if with_spans:
        data["output"] = r.output
        data["spans"] = [_span(s) for s in r.spans]
    return data


def _span(s: Span) -> dict:
    return {
        "seq": s.seq,
        "name": s.name,
        "node_type": s.node_type,
        "status": s.status,
        "latency_ms": s.latency_ms,
        "detail": s.detail,
    }


@router.get("")
async def list_runs(
    limit: int = Query(default=20, le=200),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_session),
    workspace_id: uuid.UUID = Depends(current_workspace_id),
) -> dict:
    repo = RunRepository(session)
    runs = await repo.list(workspace_id, limit=limit, offset=offset)
    total = await repo.count(workspace_id)
    return {"items": [_run(r) for r in runs], "total": total}


@router.get("/{run_id}")
async def get_run(
    run_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    workspace_id: uuid.UUID = Depends(current_workspace_id),
) -> dict:
    run = await RunRepository(session).get(run_id, workspace_id)
    if run is None:
        raise HTTPException(status_code=404, detail="run not found")
    return _run(run, with_spans=True)
