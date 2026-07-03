"""DB-integration test — exercises real Postgres via repositories.

Skipped unless METAVITA_DATABASE_URL points at a live (migrated) database, so the
default unit suite stays DB-free. CI runs migrations first, then this. The test
rolls back, leaving no rows behind.
"""

from __future__ import annotations

import os
import uuid

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

DB_URL = os.environ.get("METAVITA_DATABASE_URL") or os.environ.get("DATABASE_URL")

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(not DB_URL, reason="no METAVITA_DATABASE_URL set"),
]


@pytest.mark.asyncio
async def test_tool_and_prompt_round_trip_against_postgres():
    from metavita_api.models import Workspace
    from metavita_api.repositories import PromptRepository, ToolRepository

    engine = create_async_engine(DB_URL, pool_pre_ping=True)
    Session = async_sessionmaker(engine, expire_on_commit=False)
    try:
        async with Session() as session:
            # Set up a throwaway workspace so FKs + RLS-owner path are exercised.
            ws = Workspace(name=f"itest-{uuid.uuid4().hex[:8]}", allowed_providers=[])
            session.add(ws)
            await session.flush()

            tools = ToolRepository(session)
            tool = await tools.create(
                workspace_id=ws.id, name="web_search", kind="http", config={"url": "https://x"}
            )
            fetched = await tools.get(tool.id, ws.id)
            assert fetched is not None and fetched.name == "web_search"
            assert (await tools.list(ws.id))[0].id == tool.id

            prompts = PromptRepository(session)
            prompt = await prompts.create(
                workspace_id=ws.id, name="sys", description="d", content="v1"
            )
            await prompts.add_version(prompt, content="v2", notes="tweak")
            assert prompt.current_version == 2
            assert await prompts.latest_content(prompt) == "v2"

            await session.rollback()  # leave the database clean
    finally:
        await engine.dispose()
