"""MetaVita API gateway entrypoint."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from .config import get_settings
from .db import SessionLocal, engine
from .deps import get_default_workspace_id
from .routes import (
    agents,
    auth,
    compliance,
    connections,
    deployments,
    email,
    evals,
    health,
    ingest,
    invites,
    knowledge,
    notifications,
    overview,
    pipelines,
    prompts,
    query,
    runs,
    serve,
    tools,
    widget,
)
from .routes import (
    settings as settings_routes,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure pgvector is available and seed the default workspace (M0 dev convenience).
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
    async with SessionLocal() as session:
        await get_default_workspace_id(session)
        await session.commit()
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="MetaVita API", version="0.0.0", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(agents.router)
    app.include_router(auth.router)
    app.include_router(compliance.router)
    app.include_router(connections.router)
    app.include_router(deployments.router)
    app.include_router(email.router)
    app.include_router(evals.router)
    app.include_router(health.router)
    app.include_router(ingest.router)
    app.include_router(invites.router)
    app.include_router(invites.public_router)
    app.include_router(knowledge.router)
    app.include_router(notifications.router)
    app.include_router(overview.router)
    app.include_router(pipelines.router)
    app.include_router(prompts.router)
    app.include_router(query.router)
    app.include_router(runs.router)
    app.include_router(serve.router)
    app.include_router(settings_routes.router)
    app.include_router(tools.router)
    app.include_router(widget.router)
    return app


app = create_app()
