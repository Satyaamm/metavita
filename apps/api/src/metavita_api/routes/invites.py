"""Invitations API — invite users to a workspace by a token URL, delivered via
the workspace's OWN email Connection.

Two surfaces:
  * Management (`/workspace/invites`) — admin-only (RBAC). Creating an invite REQUIRES
    an email Connection (SMTP / SendGrid / Mailgun / Postmark / Resend / SES); with
    none, it returns 400 and nothing is sent — you literally cannot invite without
    bringing an email provider.
  * Public accept (`/invites/{token}`) — preview + accept (creates the user + membership
    and returns a session). No auth; the unguessable token is the credential.
"""

from __future__ import annotations

import secrets
import uuid
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import get_settings
from ..db import get_session
from ..deps import current_user, current_workspace_id, require_role
from ..models import User
from ..repositories import (
    AuditRepository,
    AuthRepository,
    InvitationRepository,
    WorkspaceRepository,
)
from ..security.passwords import hash_password
from ..security.tokens import create_access_token
from ..services.mailer import build_mailer
from ..services.notify import notify
from ..services.resolve import connection_values, default_connection

VALID_ROLES = {"admin", "editor", "viewer"}
INVITE_TTL_DAYS = 7

# Admin-only management endpoints.
router = APIRouter(tags=["invitations"], dependencies=[Depends(require_role("admin"))])
# Public accept endpoints (token is the credential).
public_router = APIRouter(prefix="/invites", tags=["invitations"])


def _invite(inv, *, base_url: str) -> dict:
    return {
        "id": str(inv.id),
        "email": inv.email,
        "role": inv.role,
        "status": inv.status,
        "invited_by": inv.invited_by,
        "created_at": inv.created_at.isoformat() if inv.created_at else None,
        "expires_at": inv.expires_at.isoformat() if inv.expires_at else None,
        "accept_url": f"{base_url}/invite/{inv.token}",
    }


def _invite_email_html(*, workspace: str, role: str, url: str, inviter: str) -> str:
    who = f"{inviter} has invited" if inviter else "You've been invited"
    return (
        f'<div style="font-family:system-ui,sans-serif;max-width:520px;margin:auto">'
        f"<h2>Join {workspace} on MetaVita</h2>"
        f"<p>{who} you to collaborate in the <b>{workspace}</b> workspace "
        f"as <b>{role}</b>.</p>"
        f'<p><a href="{url}" style="display:inline-block;background:#6d28d9;color:#fff;'
        f'padding:10px 18px;border-radius:8px;text-decoration:none">Accept invitation</a></p>'
        f'<p style="color:#666;font-size:12px">Or paste this link: {url}<br>'
        f"This invite expires in {INVITE_TTL_DAYS} days.</p></div>"
    )


class InviteCreate(BaseModel):
    email: str
    role: str = "editor"


@router.post("/workspace/invites", status_code=201)
async def create_invite(
    body: InviteCreate,
    session: AsyncSession = Depends(get_session),
    workspace_id: uuid.UUID = Depends(current_workspace_id),
    actor: User | None = Depends(current_user),
) -> dict:
    if body.role not in VALID_ROLES:
        raise HTTPException(status_code=422, detail=f"role must be one of {sorted(VALID_ROLES)}")

    auth = AuthRepository(session)
    existing = await auth.get_user_by_email(body.email)
    if existing and await auth.is_member(existing.id, workspace_id):
        raise HTTPException(status_code=409, detail="already a member")

    # HARD GUARD: no email Connection → cannot invite (nothing to deliver through).
    email_conn = await default_connection(session, workspace_id, "email")
    if email_conn is None:
        raise HTTPException(
            status_code=400,
            detail=(
                "Add an email connection (SMTP, Resend, SendGrid, Mailgun, Postmark, "
                "or SES) in Connections before inviting members — invites are sent "
                "through your own email provider."
            ),
        )

    settings = get_settings()
    ws = await WorkspaceRepository(session).get(workspace_id)
    ws_name = ws.name if ws else "workspace"
    token = secrets.token_urlsafe(24)
    invites = InvitationRepository(session)
    inv = await invites.create(
        workspace_id=workspace_id,
        email=body.email,
        role=body.role,
        token=token,
        invited_by=actor.email if actor else "",
        expires_at=datetime.now(UTC) + timedelta(days=INVITE_TTL_DAYS),
    )
    url = f"{settings.app_base_url}/invite/{token}"

    mailer = build_mailer(email_conn.provider, connection_values(email_conn))
    result = await mailer.send(
        to=body.email,
        subject=f"You're invited to {ws_name} on MetaVita",
        html=_invite_email_html(
            workspace=ws_name, role=body.role, url=url,
            inviter=actor.name if actor else "",
        ),
        text=f"You're invited to {ws_name} as {body.role}. Accept: {url}",
    )

    await AuditRepository(session).record(
        actor=actor.email if actor else "system",
        action="invite.sent" if result.ok else "invite.failed",
        workspace_id=workspace_id,
        resource_type="invitation",
        resource_id=str(inv.id),
        detail={"email": body.email, "role": body.role,
                "provider": email_conn.provider, "ok": result.ok, "detail": result.detail},
    )
    await notify(
        session, workspace_id=workspace_id, category="member",
        title="Invitation sent" if result.ok else "Invitation email failed",
        body=f"{body.email} · {body.role}",
        severity="success" if result.ok else "error",
        link="/settings/members",
    )
    await session.commit()

    payload = _invite(inv, base_url=settings.app_base_url)
    if not result.ok:
        # The invite row exists (link is valid), but delivery failed — surface it.
        payload["email_error"] = result.detail
    return payload


@router.get("/workspace/invites")
async def list_invites(
    session: AsyncSession = Depends(get_session),
    workspace_id: uuid.UUID = Depends(current_workspace_id),
) -> dict:
    base = get_settings().app_base_url
    rows = await InvitationRepository(session).list(workspace_id)
    return {"items": [_invite(i, base_url=base) for i in rows]}


@router.post("/workspace/invites/{invite_id}/resend")
async def resend_invite(
    invite_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    workspace_id: uuid.UUID = Depends(current_workspace_id),
) -> dict:
    invites = InvitationRepository(session)
    inv = await invites.get(invite_id, workspace_id)
    if inv is None:
        raise HTTPException(status_code=404, detail="invite not found")
    if inv.status != "pending":
        raise HTTPException(status_code=409, detail=f"invite is {inv.status}")

    email_conn = await default_connection(session, workspace_id, "email")
    if email_conn is None:
        raise HTTPException(
            status_code=400,
            detail="No email connection configured — add one in Connections.",
        )
    settings = get_settings()
    ws = await WorkspaceRepository(session).get(workspace_id)
    url = f"{settings.app_base_url}/invite/{inv.token}"
    mailer = build_mailer(email_conn.provider, connection_values(email_conn))
    result = await mailer.send(
        to=inv.email,
        subject=f"Reminder: you're invited to {ws.name if ws else 'a workspace'} on MetaVita",
        html=_invite_email_html(
            workspace=ws.name if ws else "workspace", role=inv.role, url=url, inviter=""
        ),
        text=f"Accept your invite: {url}",
    )
    await session.commit()
    if not result.ok:
        raise HTTPException(status_code=502, detail=result.detail)
    return {"ok": True}


@router.delete("/workspace/invites/{invite_id}", status_code=204)
async def revoke_invite(
    invite_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    workspace_id: uuid.UUID = Depends(current_workspace_id),
) -> None:
    invites = InvitationRepository(session)
    inv = await invites.get(invite_id, workspace_id)
    if inv is None:
        raise HTTPException(status_code=404, detail="invite not found")
    await invites.revoke(inv)
    await session.commit()


# --- Public accept ----------------------------------------------------------
def _is_expired(inv) -> bool:
    return inv.expires_at is not None and inv.expires_at < datetime.now(UTC)


@public_router.get("/{token}")
async def preview_invite(
    token: str,
    session: AsyncSession = Depends(get_session),
) -> dict:
    inv = await InvitationRepository(session).get_by_token(token)
    if inv is None:
        raise HTTPException(status_code=404, detail="invite not found")
    ws = await WorkspaceRepository(session).get(inv.workspace_id)
    status = "expired" if (inv.status == "pending" and _is_expired(inv)) else inv.status
    existing = await AuthRepository(session).get_user_by_email(inv.email)
    return {
        "email": inv.email,
        "role": inv.role,
        "status": status,
        "workspace": ws.name if ws else "workspace",
        "needs_account": existing is None,
    }


class InviteAccept(BaseModel):
    name: str | None = None
    password: str | None = None


@public_router.post("/{token}/accept")
async def accept_invite(
    token: str,
    body: InviteAccept,
    session: AsyncSession = Depends(get_session),
) -> dict:
    invites = InvitationRepository(session)
    inv = await invites.get_by_token(token)
    if inv is None:
        raise HTTPException(status_code=404, detail="invite not found")
    if inv.status != "pending":
        raise HTTPException(status_code=409, detail=f"invite already {inv.status}")
    if _is_expired(inv):
        raise HTTPException(status_code=410, detail="invite expired")

    auth = AuthRepository(session)
    user = await auth.get_user_by_email(inv.email)
    if user is None:
        if not body.password:
            raise HTTPException(status_code=422, detail="password required to create your account")
        user = await auth.create_user(
            email=inv.email,
            name=body.name or inv.email.split("@")[0],
            password_hash=hash_password(body.password),
        )

    if not await auth.is_member(user.id, inv.workspace_id):
        await auth.add_membership(
            user_id=user.id, workspace_id=inv.workspace_id, role=inv.role
        )
    await invites.mark_accepted(inv)

    ws = await WorkspaceRepository(session).get(inv.workspace_id)
    await AuditRepository(session).record(
        actor=user.email,
        action="invite.accepted",
        workspace_id=inv.workspace_id,
        resource_type="invitation",
        resource_id=str(inv.id),
        detail={"email": inv.email, "role": inv.role},
    )
    await notify(
        session, workspace_id=inv.workspace_id, category="member",
        title="New member joined",
        body=f"{user.email} joined as {inv.role}",
        severity="success", link="/settings/members",
    )
    await session.commit()

    settings = get_settings()
    access = create_access_token(
        subject=str(user.id),
        workspace_id=str(inv.workspace_id),
        secret=settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )
    return {
        "token": access,
        "user": {"id": str(user.id), "email": user.email, "name": user.name},
        "workspace": {"id": str(inv.workspace_id), "name": ws.name if ws else "workspace"},
    }
