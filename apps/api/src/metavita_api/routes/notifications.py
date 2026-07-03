"""Notifications API — the header bell's inbox (its own store, not the audit log).

Each item is individually read/unread and dismissible. The audit log on the Audit
page is a separate, immutable compliance trail.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import get_session
from ..deps import current_workspace_id
from ..models import Notification
from ..repositories import NotificationRepository

router = APIRouter(prefix="/notifications", tags=["notifications"])


def _item(n: Notification) -> dict:
    return {
        "id": str(n.id),
        "category": n.category,
        "title": n.title,
        "detail": n.body,
        "severity": n.severity,
        "link": n.link,
        "read": n.read,
        "created_at": n.created_at.isoformat() if n.created_at else None,
    }


@router.get("")
async def list_notifications(
    limit: int = Query(default=20, le=100),
    session: AsyncSession = Depends(get_session),
    workspace_id: uuid.UUID = Depends(current_workspace_id),
) -> dict:
    repo = NotificationRepository(session)
    items = await repo.list(workspace_id, limit=limit)
    unread = await repo.unread_count(workspace_id)
    return {"items": [_item(n) for n in items], "unread": unread}


@router.post("/read-all")
async def mark_all_read(
    session: AsyncSession = Depends(get_session),
    workspace_id: uuid.UUID = Depends(current_workspace_id),
) -> dict:
    count = await NotificationRepository(session).mark_all_read(workspace_id)
    await session.commit()
    return {"marked_read": count}


@router.post("/{notif_id}/read")
async def mark_read(
    notif_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    workspace_id: uuid.UUID = Depends(current_workspace_id),
) -> dict:
    repo = NotificationRepository(session)
    notif = await repo.get(notif_id, workspace_id)
    if notif is None:
        raise HTTPException(status_code=404, detail="notification not found")
    await repo.mark_read(notif)
    await session.commit()
    return _item(notif)


@router.delete("/{notif_id}", status_code=204)
async def dismiss(
    notif_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    workspace_id: uuid.UUID = Depends(current_workspace_id),
) -> None:
    repo = NotificationRepository(session)
    notif = await repo.get(notif_id, workspace_id)
    if notif is None:
        raise HTTPException(status_code=404, detail="notification not found")
    await repo.delete(notif)
    await session.commit()


@router.delete("", status_code=204)
async def clear_all(
    session: AsyncSession = Depends(get_session),
    workspace_id: uuid.UUID = Depends(current_workspace_id),
) -> None:
    await NotificationRepository(session).clear(workspace_id)
    await session.commit()
