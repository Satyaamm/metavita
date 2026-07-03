"""Settings API — workspace, members, and BYO provider credentials."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import get_session
from ..deps import current_workspace_id, require_role
from ..models import Membership, ProviderCredential, User, Workspace
from ..repositories import (
    AuthRepository,
    MemberRepository,
    ProviderCredentialRepository,
    WorkspaceRepository,
)
from ..security.encryption import get_secret_box

router = APIRouter(tags=["settings"])


# --- Workspace --------------------------------------------------------------
def _workspace(w: Workspace) -> dict:
    return {
        "id": str(w.id),
        "name": w.name,
        "key_policy": w.key_policy,
        "settings": w.settings,
    }


class WorkspaceUpdate(BaseModel):
    name: str | None = None
    key_policy: str | None = None
    settings: dict | None = None


@router.get("/workspace")
async def get_workspace(
    session: AsyncSession = Depends(get_session),
    workspace_id: uuid.UUID = Depends(current_workspace_id),
) -> dict:
    ws = await WorkspaceRepository(session).get(workspace_id)
    if ws is None:
        raise HTTPException(status_code=404, detail="workspace not found")
    return _workspace(ws)


@router.put("/workspace", dependencies=[Depends(require_role("admin"))])
async def update_workspace(
    body: WorkspaceUpdate,
    session: AsyncSession = Depends(get_session),
    workspace_id: uuid.UUID = Depends(current_workspace_id),
) -> dict:
    repo = WorkspaceRepository(session)
    ws = await repo.get(workspace_id)
    if ws is None:
        raise HTTPException(status_code=404, detail="workspace not found")
    ws = await repo.update(ws, name=body.name, key_policy=body.key_policy, settings=body.settings)
    await session.commit()
    return _workspace(ws)


# --- Members ----------------------------------------------------------------
def _member(m: Membership, u: User) -> dict:
    return {
        "membership_id": str(m.id),
        "role": m.role,
        "user": {"id": str(u.id), "email": u.email, "name": u.name},
    }


class MemberAdd(BaseModel):
    email: str
    role: str = "editor"


@router.get("/workspace/members")
async def list_members(
    session: AsyncSession = Depends(get_session),
    workspace_id: uuid.UUID = Depends(current_workspace_id),
) -> dict:
    rows = await MemberRepository(session).list(workspace_id)
    return {"items": [_member(m, u) for m, u in rows]}


@router.post(
    "/workspace/members", status_code=201, dependencies=[Depends(require_role("admin"))]
)
async def add_member(
    body: MemberAdd,
    session: AsyncSession = Depends(get_session),
    workspace_id: uuid.UUID = Depends(current_workspace_id),
) -> dict:
    auth = AuthRepository(session)
    user = await auth.get_user_by_email(body.email)
    if user is None:
        raise HTTPException(status_code=404, detail="no user with that email")
    if await auth.is_member(user.id, workspace_id):
        raise HTTPException(status_code=409, detail="already a member")
    membership = await MemberRepository(session).add(
        workspace_id=workspace_id, user_id=user.id, role=body.role
    )
    await session.commit()
    return _member(membership, user)


@router.delete(
    "/workspace/members/{membership_id}",
    status_code=204,
    dependencies=[Depends(require_role("admin"))],
)
async def remove_member(
    membership_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    workspace_id: uuid.UUID = Depends(current_workspace_id),
) -> None:
    repo = MemberRepository(session)
    membership = await repo.get(membership_id, workspace_id)
    if membership is None:
        raise HTTPException(status_code=404, detail="membership not found")
    await repo.remove(membership)
    await session.commit()


# --- Provider credentials (BYO keys) ----------------------------------------
def _credential(c: ProviderCredential) -> dict:
    return {
        "id": str(c.id),
        "provider": c.provider,
        "label": c.label,
        "key_prefix": c.key_prefix,
        "created_at": c.created_at.isoformat() if c.created_at else None,
    }


class CredentialCreate(BaseModel):
    provider: str
    label: str
    key: str


@router.get("/provider-credentials")
async def list_credentials(
    session: AsyncSession = Depends(get_session),
    workspace_id: uuid.UUID = Depends(current_workspace_id),
) -> dict:
    creds = await ProviderCredentialRepository(session).list(workspace_id)
    return {"items": [_credential(c) for c in creds]}


@router.post("/provider-credentials", status_code=201)
async def create_credential(
    body: CredentialCreate,
    session: AsyncSession = Depends(get_session),
    workspace_id: uuid.UUID = Depends(current_workspace_id),
) -> dict:
    ciphertext = get_secret_box().encrypt(body.key)
    cred = await ProviderCredentialRepository(session).create(
        workspace_id=workspace_id,
        provider=body.provider,
        label=body.label,
        key_prefix=body.key[:6],
        key_ciphertext=ciphertext,
    )
    await session.commit()
    return _credential(cred)


@router.delete("/provider-credentials/{cred_id}", status_code=204)
async def delete_credential(
    cred_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    workspace_id: uuid.UUID = Depends(current_workspace_id),
) -> None:
    repo = ProviderCredentialRepository(session)
    cred = await repo.get(cred_id, workspace_id)
    if cred is None:
        raise HTTPException(status_code=404, detail="credential not found")
    await repo.delete(cred)
    await session.commit()
