"""Connector sync service — fetch documents via a connector and ingest them.

Runs the same parse→chunk→embed→store path as uploads, so crawled/connected
documents are first-class. Bounded by the connector's own limits.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from metavita_runtime import ingest_document
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import get_settings
from ..connectors import default_connector_registry
from ..connectors.base import ConnectorRegistry
from ..factory import ProviderFactory
from ..repositories import (
    AuditRepository,
    ChunkRepository,
    DataSourceRepository,
    DocumentRepository,
)
from .notify import notify


@dataclass(slots=True)
class CrawlResult:
    source_id: str
    documents: int
    chunks: int
    pages: list[str]


async def sync_connector(
    session: AsyncSession,
    *,
    workspace_id: uuid.UUID,
    connector: str,
    config: dict,
    source_name: str | None = None,
    registry: ConnectorRegistry = default_connector_registry,
) -> CrawlResult:
    settings = get_settings()
    adapter = registry.get(connector)  # raises KeyError on unknown connector

    sources = DataSourceRepository(session)
    documents = DocumentRepository(session)
    chunks_repo = ChunkRepository(session)
    audit = AuditRepository(session)

    source = await sources.create(
        workspace_id=workspace_id,
        name=source_name or config.get("url") or connector,
        type="web" if connector == "web" else "connector",
        connector=connector,
        config=config,
    )

    factory = ProviderFactory(settings, session=session, workspace_id=workspace_id)
    embedder, embedding_model = await factory.embedding()

    total_docs = 0
    total_chunks = 0
    pages: list[str] = []
    async for fetched in adapter.fetch(config):
        document = await documents.create(
            workspace_id=workspace_id,
            filename=fetched.filename,
            content_type=fetched.content_type,
            source_id=source.id,
        )
        chunks = await ingest_document(
            fetched.content,
            content_type=fetched.content_type,
            filename=fetched.filename,
            embedder=embedder,
            embedding_model=embedding_model,
        )
        count = await chunks_repo.add_many(
            workspace_id=workspace_id, document_id=document.id, chunks=chunks
        )
        await documents.mark_indexed(document)
        total_docs += 1
        total_chunks += count
        pages.append(fetched.filename)

    await audit.record(
        actor="system",
        action="connector.synced",
        workspace_id=workspace_id,
        resource_type="data_source",
        resource_id=str(source.id),
        detail={"connector": connector, "documents": total_docs, "chunks": total_chunks},
    )
    await notify(
        session, workspace_id=workspace_id, category="ingestion",
        title="Web crawl finished", body=f"{total_docs} page(s) indexed",
        severity="success", link="/knowledge/sources",
    )
    return CrawlResult(
        source_id=str(source.id), documents=total_docs, chunks=total_chunks, pages=pages
    )
