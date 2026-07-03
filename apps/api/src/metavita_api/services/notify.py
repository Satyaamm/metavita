"""notify() — emit a user-facing notification at a notable lifecycle event.

A thin helper over NotificationRepository so routes can drop a one-liner where
something worth surfacing happens (ingestion finished, connection test failed,
email failed, data export ready…). Does NOT commit — the caller owns the
transaction. This is separate from the audit log: audit records *everything* for
compliance; notifications are the curated, dismissible inbox.
"""

from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from ..repositories import NotificationRepository


async def notify(
    session: AsyncSession,
    *,
    workspace_id: uuid.UUID,
    category: str,
    title: str,
    body: str = "",
    severity: str = "info",
    link: str | None = None,
) -> None:
    await NotificationRepository(session).create(
        workspace_id=workspace_id,
        category=category,
        title=title,
        body=body,
        severity=severity,
        link=link,
    )
