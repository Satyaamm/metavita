"""Health + readiness probe."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import get_session

router = APIRouter(tags=["health"])


@router.get("/health")
async def health(session: AsyncSession = Depends(get_session)) -> dict:
    db_ok = False
    pgvector_ok = False
    try:
        await session.execute(text("SELECT 1"))
        db_ok = True
        ext = await session.execute(
            text("SELECT 1 FROM pg_extension WHERE extname = 'vector'")
        )
        pgvector_ok = ext.scalar_one_or_none() is not None
    except Exception:  # noqa: BLE001 - health check must never raise
        pass
    status = "ok" if db_ok and pgvector_ok else "degraded"
    return {"status": status, "db": db_ok, "pgvector": pgvector_ok}
