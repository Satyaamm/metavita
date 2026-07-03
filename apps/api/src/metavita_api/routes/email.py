"""Email API — send mail through the workspace's own email Connection.

The platform sends nothing from its own account: it dispatches through whichever
email provider the workspace connected (SMTP / SendGrid / Mailgun / Postmark /
Resend / SES). `POST /email/send` uses the default `email` connection, or a
specific one via `connection_id`.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import get_session
from ..deps import current_workspace_id
from ..repositories import AuditRepository, ConnectionRepository
from ..services.mailer import build_mailer
from ..services.notify import notify
from ..services.resolve import connection_values, default_connection

router = APIRouter(prefix="/email", tags=["email"])


class EmailSend(BaseModel):
    to: str
    subject: str
    html: str | None = None
    text: str | None = None
    connection_id: uuid.UUID | None = None


@router.post("/send")
async def send_email(
    body: EmailSend,
    session: AsyncSession = Depends(get_session),
    workspace_id: uuid.UUID = Depends(current_workspace_id),
) -> dict:
    repo = ConnectionRepository(session)
    if body.connection_id:
        conn = await repo.get(body.connection_id, workspace_id)
        if conn is None or conn.capability != "email":
            raise HTTPException(status_code=404, detail="email connection not found")
    else:
        conn = await default_connection(session, workspace_id, "email")
        if conn is None:
            raise HTTPException(
                status_code=400,
                detail="No email connection configured — add one in Connections.",
            )

    mailer = build_mailer(conn.provider, connection_values(conn))
    result = await mailer.send(
        to=body.to, subject=body.subject, html=body.html, text=body.text
    )

    await AuditRepository(session).record(
        actor="system",
        action="email.sent" if result.ok else "email.failed",
        workspace_id=workspace_id,
        resource_type="email",
        resource_id=str(conn.id),
        detail={"to": body.to, "subject": body.subject, "provider": conn.provider,
                "ok": result.ok, "detail": result.detail},
    )
    await notify(
        session, workspace_id=workspace_id, category="email",
        title="Email sent" if result.ok else "Email failed",
        body=f"To {body.to}: {body.subject}",
        severity="success" if result.ok else "error",
    )
    await session.commit()

    if not result.ok:
        raise HTTPException(status_code=502, detail=result.detail)
    return {"ok": True, "provider": conn.provider, "detail": result.detail}
