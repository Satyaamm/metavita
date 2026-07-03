"""Request dependencies — auth (JWT) + workspace resolution.

A valid bearer token resolves the user and their workspace from the JWT. When no
token is present we fall back to a seeded default workspace (dev convenience), so
local flows keep working before/while signing in.
"""

from __future__ import annotations

import uuid

from fastapi import Depends, Header, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .config import get_settings
from .db import get_session
from .models import Membership, User, Workspace
from .security.tokens import TokenError, decode_token

DEFAULT_WORKSPACE_NAME = "default"


async def get_default_workspace_id(session: AsyncSession) -> uuid.UUID:
    ws = (
        await session.execute(
            select(Workspace).where(Workspace.name == DEFAULT_WORKSPACE_NAME)
        )
    ).scalar_one_or_none()
    if ws is None:
        ws = Workspace(name=DEFAULT_WORKSPACE_NAME, key_policy="platform", allowed_providers=[])
        session.add(ws)
        await session.flush()
    return ws.id


def _claims(authorization: str | None) -> dict | None:
    if not authorization:
        return None
    token = authorization.removeprefix("Bearer ").strip()
    if not token:
        return None
    settings = get_settings()
    try:
        return decode_token(token, secret=settings.jwt_secret, algorithm=settings.jwt_algorithm)
    except TokenError:
        return None


async def current_user(
    session: AsyncSession = Depends(get_session),
    authorization: str | None = Header(default=None),
) -> User | None:
    claims = _claims(authorization)
    if not claims:
        return None
    try:
        user_id = uuid.UUID(claims["sub"])
    except (KeyError, ValueError):
        return None
    return await session.get(User, user_id)


async def require_user(user: User | None = Depends(current_user)) -> User:
    if user is None:
        raise HTTPException(status_code=401, detail="authentication required")
    return user


async def current_workspace_id(
    session: AsyncSession = Depends(get_session),
    authorization: str | None = Header(default=None),
    x_workspace_id: str | None = Header(default=None),
) -> uuid.UUID:
    claims = _claims(authorization)
    if claims and claims.get("ws"):
        try:
            return uuid.UUID(claims["ws"])
        except ValueError:
            pass
    if x_workspace_id:
        try:
            return uuid.UUID(x_workspace_id)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="invalid workspace id") from exc
    return await get_default_workspace_id(session)


# RBAC — ranked roles; a higher rank satisfies the requirement for a lower one.
ROLE_RANK = {"viewer": 0, "editor": 1, "admin": 2, "owner": 3}


def require_role(min_role: str):
    """Dependency factory: 403 unless the authenticated user's workspace role is
    at least `min_role`. With no auth token (local dev) the check is a no-op, so
    dev flows keep working; it is enforced for real authenticated sessions.
    """

    async def _dep(
        session: AsyncSession = Depends(get_session),
        user: User | None = Depends(current_user),
        workspace_id: uuid.UUID = Depends(current_workspace_id),
    ) -> None:
        if user is None:
            return  # dev / unauthenticated → treated as workspace owner
        stmt = select(Membership.role).where(
            Membership.user_id == user.id, Membership.workspace_id == workspace_id
        )
        role = (await session.execute(stmt)).scalar_one_or_none()
        if role is None or ROLE_RANK.get(role, -1) < ROLE_RANK[min_role]:
            raise HTTPException(
                status_code=403,
                detail=f"requires '{min_role}' role or higher in this workspace",
            )

    return _dep
