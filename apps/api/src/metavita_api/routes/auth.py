"""Auth API — signup, login, and the current user (JWT)."""

from __future__ import annotations

import secrets
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import get_settings
from ..db import get_session
from ..deps import require_user
from ..models import User, Workspace
from ..repositories import AuthRepository
from ..security.passwords import hash_password, verify_password
from ..security.tokens import create_access_token
from ..services.mailer import build_mailer
from ..services.resolve import connection_values, default_connection

router = APIRouter(prefix="/auth", tags=["auth"])


class SignupRequest(BaseModel):
    email: str
    password: str
    first_name: str
    last_name: str
    phone: str | None = None
    company: str | None = None
    # Back-compat: a single `name` may be sent instead of first/last.
    name: str | None = None


class LoginRequest(BaseModel):
    email: str
    password: str


def _token(user: User, workspace_id: str) -> str:
    settings = get_settings()
    return create_access_token(
        subject=str(user.id),
        workspace_id=workspace_id,
        secret=settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )


def _session_payload(user: User, workspace_id: str, workspace_name: str, token: str) -> dict:
    return {
        "token": token,
        "user": {"id": str(user.id), "email": user.email, "name": user.name},
        "workspace": {"id": workspace_id, "name": workspace_name},
    }


@router.post("/signup", status_code=201)
async def signup(
    body: SignupRequest,
    session: AsyncSession = Depends(get_session),
) -> dict:
    repo = AuthRepository(session)
    if await repo.get_user_by_email(body.email):
        raise HTTPException(status_code=409, detail="email already registered")

    full_name = (
        f"{body.first_name} {body.last_name}".strip()
        if (body.first_name or body.last_name)
        else (body.name or body.email.split("@")[0])
    )
    user = await repo.create_user(
        email=body.email,
        name=full_name,
        password_hash=hash_password(body.password),
        first_name=body.first_name,
        last_name=body.last_name,
        phone=body.phone,
        company=body.company,
    )
    first = body.first_name or full_name
    workspace = await repo.create_workspace(name=f"{first}'s workspace")
    await repo.add_membership(user_id=user.id, workspace_id=workspace.id, role="owner")
    await session.commit()

    token = _token(user, str(workspace.id))
    return _session_payload(user, str(workspace.id), workspace.name, token)


@router.post("/login")
async def login(
    body: LoginRequest,
    session: AsyncSession = Depends(get_session),
) -> dict:
    repo = AuthRepository(session)
    user = await repo.get_user_by_email(body.email)
    if user is None or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="invalid email or password")

    membership = await repo.primary_membership(user.id)
    if membership is None:
        raise HTTPException(status_code=403, detail="no workspace for user")
    ws = await session.get(Workspace, membership.workspace_id)
    token = _token(user, str(membership.workspace_id))
    return _session_payload(
        user, str(membership.workspace_id), ws.name if ws else "workspace", token
    )


@router.get("/me")
async def me(
    user: User = Depends(require_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    repo = AuthRepository(session)
    membership = await repo.primary_membership(user.id)
    ws = await session.get(Workspace, membership.workspace_id) if membership else None
    return {
        "user": {"id": str(user.id), "email": user.email, "name": user.name},
        "workspace": {"id": str(ws.id), "name": ws.name} if ws else None,
    }


# --- Password reset (delivered via the user's workspace email Connection) ----
_GENERIC_FORGOT = {
    "ok": True,
    "message": "If an account exists and an email provider is connected, a reset link was sent.",
}


class ForgotRequest(BaseModel):
    email: str


class ResetRequest(BaseModel):
    token: str
    password: str


@router.post("/forgot")
async def forgot_password(
    body: ForgotRequest,
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Email a reset link — through the user's own workspace email Connection.

    Always returns the same generic response (never reveals whether the account
    exists). In pure-BYO, delivery only happens if that workspace has connected an
    email provider; otherwise there is simply nothing to send through.
    """
    repo = AuthRepository(session)
    user = await repo.get_user_by_email(body.email)
    if user is None:
        return _GENERIC_FORGOT
    membership = await repo.primary_membership(user.id)
    if membership is None:
        return _GENERIC_FORGOT
    email_conn = await default_connection(session, membership.workspace_id, "email")
    if email_conn is None:
        return _GENERIC_FORGOT

    token = secrets.token_urlsafe(24)
    await repo.create_password_reset(
        user_id=user.id, token=token, expires_at=datetime.now(UTC) + timedelta(hours=2)
    )
    url = f"{get_settings().app_base_url}/reset/{token}"
    mailer = build_mailer(email_conn.provider, connection_values(email_conn))
    await mailer.send(
        to=user.email,
        subject="Reset your MetaVita password",
        html=(
            '<div style="font-family:system-ui,sans-serif;max-width:520px;margin:auto">'
            "<h2>Reset your password</h2>"
            "<p>Use the link below to set a new password. It expires in 2 hours. "
            "If you didn't request this, you can ignore this email.</p>"
            f'<p><a href="{url}" style="display:inline-block;background:#6d28d9;color:#fff;'
            'padding:10px 18px;border-radius:8px;text-decoration:none">Set a new password</a></p>'
            f'<p style="color:#666;font-size:12px">Or paste this link: {url}</p></div>'
        ),
        text=f"Reset your MetaVita password (expires in 2h): {url}",
    )
    await session.commit()
    return _GENERIC_FORGOT


@router.post("/reset")
async def reset_password(
    body: ResetRequest,
    session: AsyncSession = Depends(get_session),
) -> dict:
    if len(body.password) < 8:
        raise HTTPException(status_code=422, detail="password must be at least 8 characters")
    repo = AuthRepository(session)
    pr = await repo.get_password_reset(body.token)
    if pr is None or pr.used:
        raise HTTPException(status_code=400, detail="invalid or already-used reset link")
    if pr.expires_at and pr.expires_at < datetime.now(UTC):
        raise HTTPException(status_code=410, detail="reset link expired")
    user = await repo.get_user(pr.user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="user not found")
    await repo.set_password(user, hash_password(body.password))
    await repo.mark_reset_used(pr)
    await session.commit()
    return {"ok": True}
