"""Ingestion unit-of-work — load raw bytes from object storage, then index.

Shared by the inline path and the Arq worker: both call `run_ingest`. It opens
its own session (the worker has no request scope) so it's safe to run detached.
"""

from __future__ import annotations

import uuid

from metavita_runtime import ingest_document

from ..config import get_settings
from ..db import SessionLocal
from ..factory import ProviderFactory
from ..repositories import AuditRepository, ChunkRepository, DocumentRepository
from ..storage import build_object_store


async def run_ingest(
    *,
    workspace_id: str,
    document_id: str,
    object_key: str,
    content_type: str | None,
    filename: str | None,
) -> dict:
    settings = get_settings()
    store = build_object_store(settings)
    content = await store.get(object_key)

    ws_id = uuid.UUID(workspace_id)
    doc_id = uuid.UUID(document_id)

    async with SessionLocal() as session:
        documents = DocumentRepository(session)
        chunks_repo = ChunkRepository(session)
        audit = AuditRepository(session)

        document = await documents.get(doc_id, ws_id)
        if document is None:
            return {"status": "missing", "document_id": document_id}

        factory = ProviderFactory(settings, session=session, workspace_id=ws_id)
        embedder, embedding_model = await factory.embedding()
        chunks = await ingest_document(
            content,
            content_type=content_type,
            filename=filename,
            embedder=embedder,
            embedding_model=embedding_model,
        )
        count = await chunks_repo.add_many(
            workspace_id=ws_id, document_id=doc_id, chunks=chunks
        )
        await documents.mark_indexed(document)
        await audit.record(
            actor="worker",
            action="document.ingested",
            workspace_id=ws_id,
            resource_type="document",
            resource_id=document_id,
            detail={"filename": filename, "chunks": count, "object_key": object_key},
        )
        await session.commit()
    return {"status": "indexed", "document_id": document_id, "chunks": count}
