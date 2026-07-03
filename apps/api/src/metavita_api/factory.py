"""ProviderFactory — constructs chat/embedding providers from the workspace's Connections.

Pure BYO, NO fallback: the provider and model come entirely from the workspace's
default Connection for the capability (llm / embeddings). If no Connection exists,
construction raises a clear 400 directing the user to add one in Connections — the
platform never uses a key of its own. HIPAA/BAA gating is enforced against the
connection's provider.
"""

from __future__ import annotations

import uuid

from fastapi import HTTPException
from metavita_providers import (
    ChatProvider,
    EmbeddingProvider,
    ProviderRegistry,
    default_provider_registry,
)
from sqlalchemy.ext.asyncio import AsyncSession

from .config import Settings
from .repositories import WorkspaceRepository
from .services.resolve import (
    build_chat_from_connection,
    build_embedding_from_connection,
    default_connection,
)


class ProviderFactory:
    def __init__(
        self,
        settings: Settings,
        *,
        session: AsyncSession | None = None,
        workspace_id: uuid.UUID | None = None,
        registry: ProviderRegistry = default_provider_registry,
    ) -> None:
        self._settings = settings
        self._session = session
        self._workspace_id = workspace_id
        self._registry = registry

    async def _workspace_allowed(self) -> set[str] | None:
        """BAA gating: in HIPAA mode, restrict to the workspace's allow-listed providers."""
        if self._session is None or self._workspace_id is None:
            return None
        ws = await WorkspaceRepository(self._session).get(self._workspace_id)
        if ws is None:
            return None
        if bool((ws.settings or {}).get("hipaa", False)) and (ws.allowed_providers or []):
            return set(ws.allowed_providers)
        return None

    async def _require_connection(self, capability: str):
        if self._session is None or self._workspace_id is None:
            raise HTTPException(
                status_code=400,
                detail=f"No {capability} connection configured — add one in Connections",
            )
        conn = await default_connection(self._session, self._workspace_id, capability)
        if conn is None:
            raise HTTPException(
                status_code=400,
                detail=f"No {capability} connection configured — add one in Connections",
            )
        allowed = await self._workspace_allowed()
        if allowed is not None and conn.provider not in allowed:
            raise HTTPException(
                status_code=403,
                detail=(
                    f"provider '{conn.provider}' is not permitted for this "
                    "workspace (HIPAA/BAA)"
                ),
            )
        return conn

    async def chat(
        self,
        *,
        provider: str | None = None,  # noqa: ARG002 - the connection decides the provider
        model: str | None = None,
        allowed: set[str] | None = None,  # noqa: ARG002 - HIPAA gate is computed internally
    ) -> tuple[ChatProvider, str]:
        conn = await self._require_connection("llm")
        resolved = build_chat_from_connection(
            conn, registry=self._registry, default_model=model or ""
        )
        return resolved.provider, resolved.model

    async def embedding(
        self,
        *,
        provider: str | None = None,  # noqa: ARG002
        model: str | None = None,
        allowed: set[str] | None = None,  # noqa: ARG002
    ) -> tuple[EmbeddingProvider, str]:
        conn = await self._require_connection("embeddings")
        resolved = build_embedding_from_connection(
            conn, registry=self._registry, default_model=model or ""
        )
        return resolved.provider, resolved.model
