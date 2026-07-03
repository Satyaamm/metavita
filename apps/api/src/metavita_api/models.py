"""SQLAlchemy models (M0 slice).

Every tenant-owned row carries `workspace_id` — the isolation boundary enforced
by app-layer scoping today and Postgres RLS as defense-in-depth (see migrations).
`audit_logs` is append-only and hash-chained for SOC 2 / HIPAA evidence.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


def _uuid() -> uuid.UUID:
    return uuid.uuid4()


class Workspace(Base):
    __tablename__ = "workspaces"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(256))
    key_policy: Mapped[str] = mapped_column(String(32), default="platform")  # platform|byo|local
    allowed_providers: Mapped[dict] = mapped_column(JSONB, default=list)
    settings: Mapped[dict] = mapped_column(JSONB, default=dict)  # retention_days, region, …
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ProviderCredential(Base):
    __tablename__ = "provider_credentials"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), index=True
    )
    provider: Mapped[str] = mapped_column(String(64))  # anthropic|openai|azure|…
    label: Mapped[str] = mapped_column(String(256))
    key_prefix: Mapped[str] = mapped_column(String(16))
    key_ciphertext: Mapped[str] = mapped_column(Text)  # encrypted via SecretBox
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(256))
    first_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    last_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(32), nullable=True)
    company: Mapped[str | None] = mapped_column(String(256), nullable=True)
    password_hash: Mapped[str] = mapped_column(String(128))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Membership(Base):
    __tablename__ = "memberships"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), index=True
    )
    role: Mapped[str] = mapped_column(String(32), default="owner")  # owner|admin|editor|viewer
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class DataSource(Base):
    __tablename__ = "data_sources"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(256))
    type: Mapped[str] = mapped_column(String(32), default="upload")  # upload|web|connector
    connector: Mapped[str | None] = mapped_column(String(64), nullable=True)
    modality: Mapped[str] = mapped_column(String(16), default="text")  # text|image|audio|video
    status: Mapped[str] = mapped_column(String(32), default="active")  # active|syncing|error
    config: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Index(Base):
    __tablename__ = "indexes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(256))
    modality: Mapped[str] = mapped_column(String(16), default="text")
    embedding_provider: Mapped[str] = mapped_column(String(64), default="openai")
    embedding_model: Mapped[str] = mapped_column(String(128), default="text-embedding-3-small")
    embedding_dim: Mapped[int] = mapped_column(Integer, default=1536)  # user-set metadata
    chunk_size: Mapped[int] = mapped_column(Integer, default=1200)
    overlap: Mapped[int] = mapped_column(Integer, default=150)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), index=True
    )
    source_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("data_sources.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    index_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("indexes.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    filename: Mapped[str] = mapped_column(String(1024))
    content_type: Mapped[str | None] = mapped_column(String(256), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="pending")  # pending|indexed|error
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    chunks: Mapped[list[Chunk]] = relationship(
        back_populates="document", cascade="all, delete-orphan"
    )


class Chunk(Base):
    __tablename__ = "chunks"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    workspace_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True)
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), index=True
    )
    chunk_index: Mapped[int] = mapped_column(Integer)
    text: Mapped[str] = mapped_column(Text)
    # Dimensionless pgvector column: the user's own embedding model decides the
    # dimension. (A fixed HNSW/IVFFlat index needs a fixed dim, so it's dropped —
    # exact cosine search is used; operators can add an ANN index for their dim.)
    embedding: Mapped[list[float]] = mapped_column(Vector())
    meta: Mapped[dict] = mapped_column(JSONB, default=dict)

    document: Mapped[Document] = relationship(back_populates="chunks")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    workspace_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True, index=True
    )
    actor: Mapped[str] = mapped_column(String(256))
    action: Mapped[str] = mapped_column(String(128))
    resource_type: Mapped[str | None] = mapped_column(String(128), nullable=True)
    resource_id: Mapped[str | None] = mapped_column(String(256), nullable=True)
    detail: Mapped[dict] = mapped_column(JSONB, default=dict)
    prev_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    hash: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


def _empty_graph() -> dict:
    return {"nodes": [], "edges": []}


class Pipeline(Base):
    __tablename__ = "pipelines"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(256))
    graph: Mapped[dict] = mapped_column(JSONB, default=_empty_graph)
    status: Mapped[str] = mapped_column(String(32), default="draft")  # draft|published
    version: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class Agent(Base):
    __tablename__ = "agents"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(256))
    system_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    provider: Mapped[str] = mapped_column(String(64), default="anthropic")
    model: Mapped[str] = mapped_column(String(128), default="claude-opus-4-8")
    tools: Mapped[list] = mapped_column(JSONB, default=list)
    index_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("indexes.id", ondelete="SET NULL"), nullable=True
    )
    # Connection slots — which BYO Connection fills each capability at run time.
    # Null falls back to the workspace's default connection for that capability.
    llm_connection_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("connections.id", ondelete="SET NULL"), nullable=True
    )
    embedding_connection_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("connections.id", ondelete="SET NULL"), nullable=True
    )
    vector_store_connection_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("connections.id", ondelete="SET NULL"), nullable=True
    )
    memory: Mapped[bool] = mapped_column(default=False)
    status: Mapped[str] = mapped_column(String(32), default="draft")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class Deployment(Base):
    __tablename__ = "deployments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(256))
    target_type: Mapped[str] = mapped_column(String(16))  # pipeline|agent
    target_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    status: Mapped[str] = mapped_column(String(32), default="active")  # active|paused
    key_prefix: Mapped[str] = mapped_column(String(16))
    key_hash: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class Run(Base):
    __tablename__ = "runs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), index=True
    )
    pipeline_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("pipelines.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    kind: Mapped[str] = mapped_column(String(32), default="pipeline")  # pipeline|query
    status: Mapped[str] = mapped_column(String(32), default="running")  # running|succeeded|failed
    input: Mapped[dict] = mapped_column(JSONB, default=dict)
    output: Mapped[dict] = mapped_column(JSONB, default=dict)
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    tokens_in: Mapped[int] = mapped_column(Integer, default=0)
    tokens_out: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    spans: Mapped[list[Span]] = relationship(
        back_populates="run", cascade="all, delete-orphan", order_by="Span.seq"
    )


class Span(Base):
    __tablename__ = "spans"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("runs.id", ondelete="CASCADE"), index=True
    )
    seq: Mapped[int] = mapped_column(Integer, default=0)
    name: Mapped[str] = mapped_column(String(128))
    node_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="succeeded")
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    detail: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    run: Mapped[Run] = relationship(back_populates="spans")


class PasswordReset(Base):
    """A single-use token to reset a user's password (delivered by email)."""

    __tablename__ = "password_resets"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    token: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    used: Mapped[bool] = mapped_column(default=False)


class Invitation(Base):
    """A pending invite to join a workspace, delivered by email as a token URL."""

    __tablename__ = "invitations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), index=True
    )
    email: Mapped[str] = mapped_column(String(320), index=True)
    role: Mapped[str] = mapped_column(String(32), default="editor")  # admin|editor|viewer
    token: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    status: Mapped[str] = mapped_column(String(32), default="pending")  # pending|accepted|revoked
    invited_by: Mapped[str] = mapped_column(String(320), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class Notification(Base):
    """User-facing inbox item — curated, read/unread, and dismissible.

    Distinct from `audit_logs` (immutable compliance evidence): notifications are
    only the notable, actionable events surfaced in the header bell, and a user can
    mark them read or dismiss (delete) them without touching the audit trail.
    """

    __tablename__ = "notifications"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), index=True
    )
    category: Mapped[str] = mapped_column(String(64))  # ingestion|connection|email|compliance|…
    title: Mapped[str] = mapped_column(String(256))
    body: Mapped[str] = mapped_column(Text, default="")
    severity: Mapped[str] = mapped_column(String(16), default="info")  # info|success|warning|error
    link: Mapped[str | None] = mapped_column(String(512), nullable=True)
    read: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class EvalDataset(Base):
    __tablename__ = "eval_datasets"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(256))
    items: Mapped[list] = mapped_column(JSONB, default=list)  # [{question, expected?}]
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Connection(Base):
    """A bring-your-own service the workspace connects: an LLM, embeddings model,
    vector DB, video analyzer, reranker, or object store. Non-secret settings live
    in `config`; secret fields are encrypted into `secret_ciphertext` (a JSON blob).
    """

    __tablename__ = "connections"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(256))
    # capability: llm | embeddings | vector_store | video | rerank | object_store
    capability: Mapped[str] = mapped_column(String(32))
    provider: Mapped[str] = mapped_column(String(64))  # openai | pinecone | azure_openai | …
    config: Mapped[dict] = mapped_column(JSONB, default=dict)  # non-secret settings
    secret_ciphertext: Mapped[str | None] = mapped_column(Text, nullable=True)  # encrypted JSON
    status: Mapped[str] = mapped_column(String(32), default="untested")  # untested|ok|error
    status_detail: Mapped[str] = mapped_column(Text, default="")
    last_tested_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class Tool(Base):
    """A callable an agent can invoke: retriever, HTTP, code-exec, or MCP tool."""

    __tablename__ = "tools"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(128))  # tool name exposed to the model (snake_case)
    kind: Mapped[str] = mapped_column(String(32), default="http")  # retriever|http|code|mcp
    description: Mapped[str] = mapped_column(Text, default="")
    input_schema: Mapped[dict] = mapped_column(JSONB, default=dict)  # JSON Schema for params
    config: Mapped[dict] = mapped_column(JSONB, default=dict)  # url/method/headers/server/…
    enabled: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class Prompt(Base):
    """A named, versioned prompt template reusable across agents and pipelines."""

    __tablename__ = "prompts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(256))
    description: Mapped[str] = mapped_column(Text, default="")
    current_version: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    versions: Mapped[list[PromptVersion]] = relationship(
        back_populates="prompt", cascade="all, delete-orphan", order_by="PromptVersion.version"
    )


class PromptVersion(Base):
    """An immutable snapshot of a prompt's content — history is append-only."""

    __tablename__ = "prompt_versions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    prompt_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("prompts.id", ondelete="CASCADE"), index=True
    )
    version: Mapped[int] = mapped_column(Integer)
    content: Mapped[str] = mapped_column(Text)
    notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    prompt: Mapped[Prompt] = relationship(back_populates="versions")


class DataSubjectRequest(Base):
    """GDPR DSAR job — export (portability) or erasure (right-to-be-forgotten)."""

    __tablename__ = "data_subject_requests"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), index=True
    )
    subject: Mapped[str] = mapped_column(String(320))  # email or external subject id
    kind: Mapped[str] = mapped_column(String(16))  # export|erasure
    status: Mapped[str] = mapped_column(String(32), default="pending")  # pending|completed|failed
    result: Mapped[dict] = mapped_column(JSONB, default=dict)  # counts / export payload location
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class EvalRun(Base):
    __tablename__ = "eval_runs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), index=True
    )
    dataset_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("eval_datasets.id", ondelete="CASCADE"), index=True
    )
    pipeline_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("pipelines.id", ondelete="SET NULL"), nullable=True
    )
    status: Mapped[str] = mapped_column(String(32), default="running")
    summary: Mapped[dict] = mapped_column(JSONB, default=dict)
    results: Mapped[list] = mapped_column(JSONB, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
