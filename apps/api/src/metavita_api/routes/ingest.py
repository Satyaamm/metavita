"""Document ingestion: upload → parse → chunk → embed → store."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from metavita_runtime import ingest_document
from metavita_runtime.types import Chunk as RuntimeChunk
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import get_settings
from ..db import get_session
from ..deps import current_workspace_id
from ..factory import ProviderFactory
from ..repositories import (
    AuditRepository,
    DataSourceRepository,
    DocumentRepository,
)
from ..security import build_file_safety
from ..services.notify import notify
from ..services.resolve import connection_values, default_connection
from ..services.video import build_video_embedder
from ..storage import build_object_store, object_key
from ..tasks import enqueue_ingest
from ..vectorstores import resolve_vector_store

router = APIRouter(tags=["ingest"])


class VideoIngestRequest(BaseModel):
    url: str
    name: str | None = None
    index_id: str | None = None


@router.post("/ingest/video", status_code=201)
async def ingest_video(
    body: VideoIngestRequest,
    session: AsyncSession = Depends(get_session),
    workspace_id: uuid.UUID = Depends(current_workspace_id),
) -> dict:
    """Multimodal ingestion: embed a video via the Azure video embedder and store it.

    The video is referenced by URL; its embedding (whole-video vector) is stored as a
    single chunk so it's retrievable alongside text. A dedicated video index pins the
    `azure_video` provider.
    """
    if not body.url.startswith(("http://", "https://")):
        raise HTTPException(status_code=422, detail="url must be http(s)")

    sources = DataSourceRepository(session)
    documents = DocumentRepository(session)
    audit = AuditRepository(session)

    source = await sources.create(
        workspace_id=workspace_id,
        name=body.name or body.url,
        type="upload",
        modality="video",
        config={"url": body.url},
    )
    document = await documents.create(
        workspace_id=workspace_id,
        filename=body.name or body.url,
        content_type="video/*",
        source_id=source.id,
        index_id=uuid.UUID(body.index_id) if body.index_id else None,
    )

    # Pure BYO: use the workspace's `video` connection (fallback: offline azure_video).
    video_conn = await default_connection(session, workspace_id, "video")
    embedder = build_video_embedder(
        video_conn.provider if video_conn else None,
        connection_values(video_conn) if video_conn else {},
    )
    result = await embedder.embed([body.url], model="")

    store = await resolve_vector_store(session, workspace_id)
    count = await store.upsert(
        workspace_id=str(workspace_id),
        document_id=str(document.id),
        chunks=[
            RuntimeChunk(
                text=f"Video: {body.url}",
                index=0,
                metadata={"url": body.url, "modality": "video"},
                embedding=result.vectors[0],
            )
        ],
    )
    await documents.mark_indexed(document)
    await audit.record(
        actor="system",
        action="video.ingested",
        workspace_id=workspace_id,
        resource_type="document",
        resource_id=str(document.id),
        detail={"url": body.url, "chunks": count},
    )
    await notify(
        session, workspace_id=workspace_id, category="ingestion",
        title="Video indexed", body=body.url, severity="success",
        link="/knowledge/sources",
    )
    await session.commit()
    return {
        "document_id": str(document.id),
        "source_id": str(source.id),
        "filename": document.filename,
        "chunks": count,
        "status": document.status,
        "modality": "video",
    }


@router.post("/ingest")
async def ingest(
    file: UploadFile = File(...),
    source_id: str | None = Form(default=None),
    index_id: str | None = Form(default=None),
    session: AsyncSession = Depends(get_session),
    workspace_id: uuid.UUID = Depends(current_workspace_id),
) -> dict:
    settings = get_settings()
    documents = DocumentRepository(session)
    sources = DataSourceRepository(session)
    audit = AuditRepository(session)

    content = await file.read()

    # Defense-in-depth: size cap → magic-byte type check → antivirus scan.
    verdict = await build_file_safety(settings).check(
        content, filename=file.filename, declared_content_type=file.content_type
    )
    if not verdict.ok:
        await audit.record(
            actor="system",
            action="upload.rejected",
            workspace_id=workspace_id,
            resource_type="upload",
            resource_id=None,
            detail={
                "filename": file.filename,
                "reason": verdict.reason,
                "signature": verdict.signature,
                "detected_type": verdict.detected_type,
            },
        )
        await session.commit()
        raise HTTPException(
            status_code=422,
            detail={"error": verdict.reason, "signature": verdict.signature},
        )

    # Attach to the chosen source, or the workspace's default "Uploads" source.
    if source_id:
        resolved_source_id = uuid.UUID(source_id)
    else:
        resolved_source_id = (await sources.ensure_default_upload(workspace_id)).id
    resolved_index_id = uuid.UUID(index_id) if index_id else None

    document = await documents.create(
        workspace_id=workspace_id,
        filename=file.filename or "upload",
        content_type=file.content_type,
        source_id=resolved_source_id,
        index_id=resolved_index_id,
    )

    factory = ProviderFactory(settings, session=session, workspace_id=workspace_id)
    embedder, embedding_model = await factory.embedding()
    chunks = await ingest_document(
        content,
        content_type=file.content_type,
        filename=file.filename,
        embedder=embedder,
        embedding_model=embedding_model,
    )

    store = await resolve_vector_store(session, workspace_id)
    count = await store.upsert(
        workspace_id=str(workspace_id), document_id=str(document.id), chunks=chunks
    )
    await documents.mark_indexed(document)

    await audit.record(
        actor="system",
        action="document.ingested",
        workspace_id=workspace_id,
        resource_type="document",
        resource_id=str(document.id),
        detail={"filename": document.filename, "chunks": count},
    )
    await notify(
        session, workspace_id=workspace_id, category="ingestion",
        title="Document indexed", body=document.filename, severity="success",
        link="/knowledge/documents",
    )
    await session.commit()

    return {
        "document_id": str(document.id),
        "filename": document.filename,
        "chunks": count,
        "status": document.status,
    }


@router.post("/ingest/async", status_code=202)
async def ingest_async(
    file: UploadFile = File(...),
    source_id: str | None = Form(default=None),
    index_id: str | None = Form(default=None),
    session: AsyncSession = Depends(get_session),
    workspace_id: uuid.UUID = Depends(current_workspace_id),
) -> dict:
    """Store the raw file in object storage and enqueue ingestion on the worker.

    Returns immediately with a job id; the document stays `pending` until the
    worker indexes it. Falls back to inline processing if Redis is unavailable.
    """
    settings = get_settings()
    documents = DocumentRepository(session)
    sources = DataSourceRepository(session)
    audit = AuditRepository(session)

    content = await file.read()

    verdict = await build_file_safety(settings).check(
        content, filename=file.filename, declared_content_type=file.content_type
    )
    if not verdict.ok:
        await audit.record(
            actor="system",
            action="upload.rejected",
            workspace_id=workspace_id,
            resource_type="upload",
            resource_id=None,
            detail={"filename": file.filename, "reason": verdict.reason},
        )
        await session.commit()
        raise HTTPException(
            status_code=422, detail={"error": verdict.reason, "signature": verdict.signature}
        )

    if source_id:
        resolved_source_id = uuid.UUID(source_id)
    else:
        resolved_source_id = (await sources.ensure_default_upload(workspace_id)).id

    document = await documents.create(
        workspace_id=workspace_id,
        filename=file.filename or "upload",
        content_type=file.content_type,
        source_id=resolved_source_id,
        index_id=uuid.UUID(index_id) if index_id else None,
    )
    await session.commit()  # persist the pending document before the worker picks it up

    key = object_key(str(workspace_id), f"{document.id}/{file.filename or 'upload'}")
    await build_object_store(settings).put(key, content, content_type=file.content_type)

    result = await enqueue_ingest(
        workspace_id=str(workspace_id),
        document_id=str(document.id),
        object_key=key,
        content_type=file.content_type,
        filename=file.filename,
    )

    return {
        "document_id": str(document.id),
        "filename": document.filename,
        "job_id": result.job_id,
        "mode": result.mode,
        "status": "queued",
    }
