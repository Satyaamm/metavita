"""Overview API — real workspace rollups and recent audit activity for the dashboard."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Query
from metavita_providers import CHAT_MODELS
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import get_session
from ..deps import current_workspace_id
from ..repositories import AnalyticsRepository, AuditRepository, OverviewRepository
from ..services.analytics import build_daily_series

router = APIRouter(tags=["overview"])


@router.get("/analytics")
async def analytics(
    days: int = Query(default=14, ge=1, le=90),
    session: AsyncSession = Depends(get_session),
    workspace_id: uuid.UUID = Depends(current_workspace_id),
) -> dict:
    repo = AnalyticsRepository(session)
    totals = await repo.totals(workspace_id)
    by_kind = await repo.by_kind(workspace_id)
    daily = build_daily_series(
        await repo.daily_counts(workspace_id, days=days),
        days=days,
        today=datetime.now(UTC).date(),
    )

    # Display-only cost estimate uses a reference model's public pricing.
    model = CHAT_MODELS.get("claude-opus-4-8")
    est_cost = (
        round(
            totals["tokens_in"] / 1e6 * model.input_price
            + totals["tokens_out"] / 1e6 * model.output_price,
            4,
        )
        if model
        else None
    )
    return {
        "totals": {**totals, "est_cost_usd": est_cost},
        "by_kind": by_kind,
        "daily": daily,
    }


@router.get("/overview/stats")
async def overview_stats(
    session: AsyncSession = Depends(get_session),
    workspace_id: uuid.UUID = Depends(current_workspace_id),
) -> dict:
    return await OverviewRepository(session).stats(workspace_id)


@router.get("/audit")
async def list_audit(
    limit: int = Query(default=20, le=200),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_session),
    workspace_id: uuid.UUID = Depends(current_workspace_id),
) -> dict:
    repo = AuditRepository(session)
    events = await repo.list(workspace_id, limit=limit, offset=offset)
    total = await repo.count(workspace_id)
    return {
        "total": total,
        "items": [
            {
                "id": str(e.id),
                "action": e.action,
                "actor": e.actor,
                "resource_type": e.resource_type,
                "resource_id": e.resource_id,
                "detail": e.detail,
                "created_at": e.created_at.isoformat() if e.created_at else None,
            }
            for e in events
        ]
    }
