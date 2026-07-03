"""Alembic async migration environment."""

from __future__ import annotations

import asyncio

from alembic import context
from metavita_api import models  # noqa: F401 - ensure models are imported for metadata
from metavita_api.config import get_settings
from metavita_api.db import Base
from sqlalchemy.ext.asyncio import create_async_engine

target_metadata = Base.metadata


def _run_sync(connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def _run_async() -> None:
    engine = create_async_engine(get_settings().database_url)
    async with engine.connect() as connection:
        await connection.run_sync(_run_sync)
    await engine.dispose()


def run_migrations_offline() -> None:
    context.configure(
        url=get_settings().database_url,
        target_metadata=target_metadata,
        literal_binds=True,
    )
    with context.begin_transaction():
        context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(_run_async())
