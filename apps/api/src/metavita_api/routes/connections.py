"""Connections API — bring-your-own integrations.

`GET /connections/catalog` returns the full provider catalog (drives the dynamic
"Add connection" form). Connections store non-secret settings in `config` and
encrypt secret fields. Secrets are never returned — responses expose only which
secret fields are set. `POST /connections/{id}/test` probes live connectivity.
"""

from __future__ import annotations

import json
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import get_session
from ..deps import current_workspace_id
from ..integrations import default_integration_registry as catalog
from ..models import Connection
from ..repositories import AuditRepository, ConnectionRepository
from ..security.encryption import get_secret_box
from ..services.notify import notify

router = APIRouter(prefix="/connections", tags=["connections"])


def _integration_or_404(capability: str, provider: str):
    integ = catalog.get(capability, provider)
    if integ is None:
        raise HTTPException(
            status_code=422, detail=f"unknown integration: {capability}/{provider}"
        )
    return integ


def _decrypt_secrets(conn: Connection) -> dict:
    if not conn.secret_ciphertext:
        return {}
    try:
        return json.loads(get_secret_box().decrypt(conn.secret_ciphertext))
    except Exception:  # noqa: BLE001 - corrupt/rotated key → treat as no secrets
        return {}


def _connection(conn: Connection) -> dict:
    secrets = _decrypt_secrets(conn)
    integ = catalog.get(conn.capability, conn.provider)
    secret_names = integ.secret_fields() if integ else list(secrets.keys())
    return {
        "id": str(conn.id),
        "name": conn.name,
        "capability": conn.capability,
        "provider": conn.provider,
        "provider_label": integ.label if integ else conn.provider,
        "config": conn.config,  # non-secret only
        "secrets_set": [n for n in secret_names if secrets.get(n)],
        "status": conn.status,
        "status_detail": conn.status_detail,
        "last_tested_at": conn.last_tested_at.isoformat() if conn.last_tested_at else None,
        "created_at": conn.created_at.isoformat() if conn.created_at else None,
        "updated_at": conn.updated_at.isoformat() if conn.updated_at else None,
    }


def _split_values(integ, values: dict) -> tuple[dict, dict]:
    """Partition submitted values into non-secret config and secret fields."""
    secret_names = set(integ.secret_fields())
    config = {k: v for k, v in values.items() if k not in secret_names and v is not None}
    secrets = {k: v for k, v in values.items() if k in secret_names and v not in (None, "")}
    return config, secrets


def _encrypt(secrets: dict) -> str | None:
    return get_secret_box().encrypt(json.dumps(secrets)) if secrets else None


class ConnectionCreate(BaseModel):
    name: str
    capability: str
    provider: str
    values: dict = {}  # combined config + secret fields as the user typed them


class ConnectionUpdate(BaseModel):
    name: str | None = None
    values: dict | None = None  # merged; only provided secret fields are re-encrypted


@router.get("/catalog")
async def get_catalog() -> dict:
    return catalog.catalog()


@router.get("")
async def list_connections(
    capability: str | None = Query(default=None),
    session: AsyncSession = Depends(get_session),
    workspace_id: uuid.UUID = Depends(current_workspace_id),
) -> dict:
    items = await ConnectionRepository(session).list(workspace_id, capability=capability)
    return {"items": [_connection(c) for c in items]}


@router.post("", status_code=201)
async def create_connection(
    body: ConnectionCreate,
    session: AsyncSession = Depends(get_session),
    workspace_id: uuid.UUID = Depends(current_workspace_id),
) -> dict:
    integ = _integration_or_404(body.capability, body.provider)
    config, secrets = _split_values(integ, body.values)
    conn = await ConnectionRepository(session).create(
        workspace_id=workspace_id,
        name=body.name,
        capability=body.capability,
        provider=body.provider,
        config=config,
        secret_ciphertext=_encrypt(secrets),
    )
    await AuditRepository(session).record(
        actor="system",
        action="connection.created",
        workspace_id=workspace_id,
        resource_type="connection",
        resource_id=str(conn.id),
        detail={"capability": body.capability, "provider": body.provider},
    )
    await notify(
        session, workspace_id=workspace_id, category="connection",
        title="Connection added", body=f"{conn.name} ({integ.label})",
        severity="success", link="/connections",
    )
    await session.commit()
    return _connection(conn)


@router.get("/{conn_id}")
async def get_connection(
    conn_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    workspace_id: uuid.UUID = Depends(current_workspace_id),
) -> dict:
    conn = await ConnectionRepository(session).get(conn_id, workspace_id)
    if conn is None:
        raise HTTPException(status_code=404, detail="connection not found")
    return _connection(conn)


@router.put("/{conn_id}")
async def update_connection(
    conn_id: uuid.UUID,
    body: ConnectionUpdate,
    session: AsyncSession = Depends(get_session),
    workspace_id: uuid.UUID = Depends(current_workspace_id),
) -> dict:
    repo = ConnectionRepository(session)
    conn = await repo.get(conn_id, workspace_id)
    if conn is None:
        raise HTTPException(status_code=404, detail="connection not found")

    new_config = None
    new_cipher = None
    if body.values is not None:
        integ = _integration_or_404(conn.capability, conn.provider)
        config, secrets = _split_values(integ, body.values)
        new_config = config
        # Merge with existing secrets so blank fields don't wipe stored values.
        existing = _decrypt_secrets(conn)
        existing.update(secrets)
        new_cipher = _encrypt(existing)

    await repo.update(conn, name=body.name, config=new_config, secret_ciphertext=new_cipher)
    await session.commit()
    await session.refresh(conn)
    return _connection(conn)


@router.post("/{conn_id}/test")
async def test_connection(
    conn_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    workspace_id: uuid.UUID = Depends(current_workspace_id),
) -> dict:
    repo = ConnectionRepository(session)
    conn = await repo.get(conn_id, workspace_id)
    if conn is None:
        raise HTTPException(status_code=404, detail="connection not found")
    integ = _integration_or_404(conn.capability, conn.provider)

    values = {**conn.config, **_decrypt_secrets(conn)}
    result = await integ.test(values)
    await repo.set_status(
        conn, status="ok" if result.ok else "error", detail=result.message
    )
    if not result.ok:
        await notify(
            session, workspace_id=workspace_id, category="connection",
            title="Connection test failed", body=f"{conn.name}: {result.message}",
            severity="error", link="/connections",
        )
    await session.commit()
    return {"ok": result.ok, "message": result.message, "status": conn.status}


@router.delete("/{conn_id}", status_code=204)
async def delete_connection(
    conn_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    workspace_id: uuid.UUID = Depends(current_workspace_id),
) -> None:
    repo = ConnectionRepository(session)
    conn = await repo.get(conn_id, workspace_id)
    if conn is None:
        raise HTTPException(status_code=404, detail="connection not found")
    await repo.delete(conn)
    await session.commit()
