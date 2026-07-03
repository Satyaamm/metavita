"""Knowledge API — data sources, documents (+ chunk inspector), and indexes."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from ..connectors import default_connector_registry
from ..db import get_session
from ..deps import current_workspace_id
from ..models import Chunk, DataSource, Document, Index
from ..repositories import DataSourceRepository, DocumentRepository, IndexRepository
from ..services.crawl import sync_connector

router = APIRouter(prefix="/knowledge", tags=["knowledge"])


# --- serializers ------------------------------------------------------------
def _source(s: DataSource, *, document_count: int | None = None) -> dict:
    return {
        "id": str(s.id),
        "name": s.name,
        "type": s.type,
        "connector": s.connector,
        "modality": s.modality,
        "status": s.status,
        "document_count": document_count,
        "created_at": s.created_at.isoformat() if s.created_at else None,
    }


def _document(d: Document, *, chunk_count: int | None = None) -> dict:
    return {
        "id": str(d.id),
        "filename": d.filename,
        "content_type": d.content_type,
        "status": d.status,
        "source_id": str(d.source_id) if d.source_id else None,
        "index_id": str(d.index_id) if d.index_id else None,
        "chunk_count": chunk_count,
        "created_at": d.created_at.isoformat() if d.created_at else None,
    }


def _chunk(c: Chunk) -> dict:
    return {"chunk_index": c.chunk_index, "text": c.text, "meta": c.meta}


def _index(i: Index) -> dict:
    return {
        "id": str(i.id),
        "name": i.name,
        "modality": i.modality,
        "embedding_provider": i.embedding_provider,
        "embedding_model": i.embedding_model,
        "embedding_dim": i.embedding_dim,
        "chunk_size": i.chunk_size,
        "overlap": i.overlap,
        "created_at": i.created_at.isoformat() if i.created_at else None,
    }


# --- request bodies ---------------------------------------------------------
class SourceCreate(BaseModel):
    name: str
    type: str = "upload"
    modality: str = "text"
    connector: str | None = None


class IndexCreate(BaseModel):
    name: str
    modality: str = "text"
    embedding_provider: str = "openai"
    embedding_model: str = "text-embedding-3-small"
    chunk_size: int = 1200
    overlap: int = 150
    embedding_dim: int = 1536  # the user's embedder decides this


class CrawlRequest(BaseModel):
    url: str
    max_pages: int = 1
    same_domain: bool = True
    name: str | None = None


# --- Connectors -------------------------------------------------------------
@router.get("/connectors")
async def list_connectors() -> dict:
    return {"items": default_connector_registry.names()}


@router.post("/crawl", status_code=201)
async def crawl(
    body: CrawlRequest,
    session: AsyncSession = Depends(get_session),
    workspace_id: uuid.UUID = Depends(current_workspace_id),
) -> dict:
    if not body.url.startswith(("http://", "https://")):
        raise HTTPException(status_code=422, detail="url must be http(s)")
    result = await sync_connector(
        session,
        workspace_id=workspace_id,
        connector="web",
        config={"url": body.url, "max_pages": body.max_pages, "same_domain": body.same_domain},
        source_name=body.name,
    )
    await session.commit()
    return {
        "source_id": result.source_id,
        "documents": result.documents,
        "chunks": result.chunks,
        "pages": result.pages,
    }


# --- Data Sources -----------------------------------------------------------
@router.get("/sources")
async def list_sources(
    session: AsyncSession = Depends(get_session),
    workspace_id: uuid.UUID = Depends(current_workspace_id),
) -> dict:
    repo = DataSourceRepository(session)
    sources = await repo.list(workspace_id)
    items = [_source(s, document_count=await repo.document_count(s.id)) for s in sources]
    return {"items": items}


@router.post("/sources", status_code=201)
async def create_source(
    body: SourceCreate,
    session: AsyncSession = Depends(get_session),
    workspace_id: uuid.UUID = Depends(current_workspace_id),
) -> dict:
    source = await DataSourceRepository(session).create(
        workspace_id=workspace_id,
        name=body.name,
        type=body.type,
        modality=body.modality,
        connector=body.connector,
    )
    await session.commit()
    return _source(source, document_count=0)


@router.get("/sources/{source_id}")
async def get_source(
    source_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    workspace_id: uuid.UUID = Depends(current_workspace_id),
) -> dict:
    repo = DataSourceRepository(session)
    source = await repo.get(source_id, workspace_id)
    if source is None:
        raise HTTPException(status_code=404, detail="source not found")
    return _source(source, document_count=await repo.document_count(source.id))


# --- Documents --------------------------------------------------------------
@router.get("/documents")
async def list_documents(
    q: str | None = Query(default=None),
    status: str | None = Query(default=None),
    source_id: uuid.UUID | None = Query(default=None),
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_session),
    workspace_id: uuid.UUID = Depends(current_workspace_id),
) -> dict:
    repo = DocumentRepository(session)
    docs = await repo.list(
        workspace_id, q=q, status=status, source_id=source_id, limit=limit, offset=offset
    )
    total = await repo.count(workspace_id, q=q, status=status, source_id=source_id)
    return {"items": [_document(d) for d in docs], "total": total}


@router.get("/documents/{document_id}")
async def get_document(
    document_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    workspace_id: uuid.UUID = Depends(current_workspace_id),
) -> dict:
    repo = DocumentRepository(session)
    doc = await repo.get(document_id, workspace_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="document not found")
    return _document(doc, chunk_count=await repo.chunk_count(doc.id))


@router.get("/documents/{document_id}/chunks")
async def list_document_chunks(
    document_id: uuid.UUID,
    limit: int = Query(default=100, le=500),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_session),
    workspace_id: uuid.UUID = Depends(current_workspace_id),
) -> dict:
    repo = DocumentRepository(session)
    doc = await repo.get(document_id, workspace_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="document not found")
    chunks = await repo.list_chunks(document_id, workspace_id, limit=limit, offset=offset)
    return {"document": _document(doc), "items": [_chunk(c) for c in chunks]}


# --- Indexes ----------------------------------------------------------------
@router.get("/indexes")
async def list_indexes(
    session: AsyncSession = Depends(get_session),
    workspace_id: uuid.UUID = Depends(current_workspace_id),
) -> dict:
    indexes = await IndexRepository(session).list(workspace_id)
    return {"items": [_index(i) for i in indexes]}


@router.post("/indexes", status_code=201)
async def create_index(
    body: IndexCreate,
    session: AsyncSession = Depends(get_session),
    workspace_id: uuid.UUID = Depends(current_workspace_id),
) -> dict:
    index = await IndexRepository(session).create(
        workspace_id=workspace_id,
        name=body.name,
        modality=body.modality,
        embedding_provider=body.embedding_provider,
        embedding_model=body.embedding_model,
        embedding_dim=body.embedding_dim,
        chunk_size=body.chunk_size,
        overlap=body.overlap,
    )
    await session.commit()
    return _index(index)


@router.get("/indexes/{index_id}")
async def get_index(
    index_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    workspace_id: uuid.UUID = Depends(current_workspace_id),
) -> dict:
    index = await IndexRepository(session).get(index_id, workspace_id)
    if index is None:
        raise HTTPException(status_code=404, detail="index not found")
    return _index(index)
