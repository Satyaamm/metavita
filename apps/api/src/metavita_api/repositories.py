"""Repository layer — encapsulates SQLAlchemy persistence per aggregate.

Routes depend on these repositories, not on the ORM directly (single-responsibility +
dependency-inversion). Each repository is constructed with an AsyncSession and exposes
intent-revealing methods. The hash-chained AuditRepository preserves tamper-evidence.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from collections.abc import Iterable
from datetime import UTC, datetime, timedelta

from metavita_runtime import Chunk as RuntimeChunk
from sqlalchemy import Date, case, cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from .models import (
    Agent,
    AuditLog,
    Chunk,
    Connection,
    DataSource,
    DataSubjectRequest,
    Deployment,
    Document,
    EvalDataset,
    EvalRun,
    Index,
    Invitation,
    Membership,
    Notification,
    PasswordReset,
    Pipeline,
    Prompt,
    PromptVersion,
    ProviderCredential,
    Run,
    Span,
    Tool,
    User,
    Workspace,
)


class DataSourceRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        workspace_id: uuid.UUID,
        name: str,
        type: str = "upload",
        modality: str = "text",
        connector: str | None = None,
        config: dict | None = None,
    ) -> DataSource:
        source = DataSource(
            workspace_id=workspace_id,
            name=name,
            type=type,
            modality=modality,
            connector=connector,
            config=config or {},
        )
        self._session.add(source)
        await self._session.flush()
        return source

    async def list(self, workspace_id: uuid.UUID) -> list[DataSource]:
        stmt = (
            select(DataSource)
            .where(DataSource.workspace_id == workspace_id)
            .order_by(DataSource.created_at.desc())
        )
        return list((await self._session.execute(stmt)).scalars())

    async def get(self, source_id: uuid.UUID, workspace_id: uuid.UUID) -> DataSource | None:
        stmt = select(DataSource).where(
            DataSource.id == source_id, DataSource.workspace_id == workspace_id
        )
        return (await self._session.execute(stmt)).scalar_one_or_none()

    async def ensure_default_upload(self, workspace_id: uuid.UUID) -> DataSource:
        stmt = select(DataSource).where(
            DataSource.workspace_id == workspace_id,
            DataSource.type == "upload",
            DataSource.name == "Uploads",
        )
        existing = (await self._session.execute(stmt)).scalar_one_or_none()
        if existing:
            return existing
        return await self.create(workspace_id=workspace_id, name="Uploads", type="upload")

    async def document_count(self, source_id: uuid.UUID) -> int:
        stmt = select(func.count(Document.id)).where(Document.source_id == source_id)
        return int((await self._session.execute(stmt)).scalar_one())


class IndexRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        workspace_id: uuid.UUID,
        name: str,
        modality: str = "text",
        embedding_provider: str = "openai",
        embedding_model: str = "text-embedding-3-small",
        embedding_dim: int,
        chunk_size: int = 1200,
        overlap: int = 150,
    ) -> Index:
        index = Index(
            workspace_id=workspace_id,
            name=name,
            modality=modality,
            embedding_provider=embedding_provider,
            embedding_model=embedding_model,
            embedding_dim=embedding_dim,
            chunk_size=chunk_size,
            overlap=overlap,
        )
        self._session.add(index)
        await self._session.flush()
        return index

    async def list(self, workspace_id: uuid.UUID) -> list[Index]:
        stmt = (
            select(Index)
            .where(Index.workspace_id == workspace_id)
            .order_by(Index.created_at.desc())
        )
        return list((await self._session.execute(stmt)).scalars())

    async def get(self, index_id: uuid.UUID, workspace_id: uuid.UUID) -> Index | None:
        stmt = select(Index).where(Index.id == index_id, Index.workspace_id == workspace_id)
        return (await self._session.execute(stmt)).scalar_one_or_none()


class DocumentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        workspace_id: uuid.UUID,
        filename: str,
        content_type: str | None,
        source_id: uuid.UUID | None = None,
        index_id: uuid.UUID | None = None,
    ) -> Document:
        document = Document(
            workspace_id=workspace_id,
            filename=filename,
            content_type=content_type,
            source_id=source_id,
            index_id=index_id,
            status="pending",
        )
        self._session.add(document)
        await self._session.flush()
        return document

    async def mark_indexed(self, document: Document) -> None:
        document.status = "indexed"

    async def list(
        self,
        workspace_id: uuid.UUID,
        *,
        q: str | None = None,
        status: str | None = None,
        source_id: uuid.UUID | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Document]:
        stmt = select(Document).where(Document.workspace_id == workspace_id)
        if q:
            stmt = stmt.where(Document.filename.ilike(f"%{q}%"))
        if status:
            stmt = stmt.where(Document.status == status)
        if source_id:
            stmt = stmt.where(Document.source_id == source_id)
        stmt = stmt.order_by(Document.created_at.desc()).limit(limit).offset(offset)
        return list((await self._session.execute(stmt)).scalars())

    async def count(
        self,
        workspace_id: uuid.UUID,
        *,
        q: str | None = None,
        status: str | None = None,
        source_id: uuid.UUID | None = None,
    ) -> int:
        stmt = select(func.count(Document.id)).where(Document.workspace_id == workspace_id)
        if q:
            stmt = stmt.where(Document.filename.ilike(f"%{q}%"))
        if status:
            stmt = stmt.where(Document.status == status)
        if source_id:
            stmt = stmt.where(Document.source_id == source_id)
        return int((await self._session.execute(stmt)).scalar_one())

    async def get(self, document_id: uuid.UUID, workspace_id: uuid.UUID) -> Document | None:
        stmt = select(Document).where(
            Document.id == document_id, Document.workspace_id == workspace_id
        )
        return (await self._session.execute(stmt)).scalar_one_or_none()

    async def chunk_count(self, document_id: uuid.UUID) -> int:
        stmt = select(func.count(Chunk.id)).where(Chunk.document_id == document_id)
        return int((await self._session.execute(stmt)).scalar_one())

    async def list_chunks(
        self,
        document_id: uuid.UUID,
        workspace_id: uuid.UUID,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Chunk]:
        stmt = (
            select(Chunk)
            .where(Chunk.document_id == document_id, Chunk.workspace_id == workspace_id)
            .order_by(Chunk.chunk_index)
            .limit(limit)
            .offset(offset)
        )
        return list((await self._session.execute(stmt)).scalars())


class ChunkRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add_many(
        self,
        *,
        workspace_id: uuid.UUID,
        document_id: uuid.UUID,
        chunks: Iterable[RuntimeChunk],
    ) -> int:
        count = 0
        for c in chunks:
            self._session.add(
                Chunk(
                    workspace_id=workspace_id,
                    document_id=document_id,
                    chunk_index=c.index,
                    text=c.text,
                    embedding=c.embedding,
                    meta=c.metadata,
                )
            )
            count += 1
        return count


class PipelineRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self, *, workspace_id: uuid.UUID, name: str, graph: dict | None = None
    ) -> Pipeline:
        pipeline = Pipeline(
            workspace_id=workspace_id,
            name=name,
            graph=graph or {"nodes": [], "edges": []},
        )
        self._session.add(pipeline)
        await self._session.flush()
        return pipeline

    async def list(self, workspace_id: uuid.UUID) -> list[Pipeline]:
        stmt = (
            select(Pipeline)
            .where(Pipeline.workspace_id == workspace_id)
            .order_by(Pipeline.updated_at.desc())
        )
        return list((await self._session.execute(stmt)).scalars())

    async def get(self, pipeline_id: uuid.UUID, workspace_id: uuid.UUID) -> Pipeline | None:
        stmt = select(Pipeline).where(
            Pipeline.id == pipeline_id, Pipeline.workspace_id == workspace_id
        )
        return (await self._session.execute(stmt)).scalar_one_or_none()

    async def update(
        self,
        pipeline: Pipeline,
        *,
        name: str | None = None,
        graph: dict | None = None,
        status: str | None = None,
    ) -> Pipeline:
        if name is not None:
            pipeline.name = name
        if graph is not None:
            pipeline.graph = graph
        if status is not None:
            pipeline.status = status
        await self._session.flush()
        return pipeline


class AgentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, *, workspace_id: uuid.UUID, name: str, **fields) -> Agent:
        agent = Agent(workspace_id=workspace_id, name=name, **fields)
        self._session.add(agent)
        await self._session.flush()
        return agent

    async def list(self, workspace_id: uuid.UUID) -> list[Agent]:
        stmt = (
            select(Agent)
            .where(Agent.workspace_id == workspace_id)
            .order_by(Agent.updated_at.desc())
        )
        return list((await self._session.execute(stmt)).scalars())

    async def get(self, agent_id: uuid.UUID, workspace_id: uuid.UUID) -> Agent | None:
        stmt = select(Agent).where(Agent.id == agent_id, Agent.workspace_id == workspace_id)
        return (await self._session.execute(stmt)).scalar_one_or_none()

    async def update(self, agent: Agent, **fields) -> Agent:
        for key, value in fields.items():
            if value is not None and hasattr(agent, key):
                setattr(agent, key, value)
        await self._session.flush()
        return agent


class EvalDatasetRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, *, workspace_id: uuid.UUID, name: str, items: list) -> EvalDataset:
        dataset = EvalDataset(workspace_id=workspace_id, name=name, items=items)
        self._session.add(dataset)
        await self._session.flush()
        return dataset

    async def list(self, workspace_id: uuid.UUID) -> list[EvalDataset]:
        stmt = (
            select(EvalDataset)
            .where(EvalDataset.workspace_id == workspace_id)
            .order_by(EvalDataset.created_at.desc())
        )
        return list((await self._session.execute(stmt)).scalars())

    async def get(self, dataset_id: uuid.UUID, workspace_id: uuid.UUID) -> EvalDataset | None:
        stmt = select(EvalDataset).where(
            EvalDataset.id == dataset_id, EvalDataset.workspace_id == workspace_id
        )
        return (await self._session.execute(stmt)).scalar_one_or_none()


class EvalRunRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        workspace_id: uuid.UUID,
        dataset_id: uuid.UUID,
        pipeline_id: uuid.UUID | None,
        status: str,
        summary: dict,
        results: list,
    ) -> EvalRun:
        run = EvalRun(
            workspace_id=workspace_id,
            dataset_id=dataset_id,
            pipeline_id=pipeline_id,
            status=status,
            summary=summary,
            results=results,
            finished_at=datetime.now(UTC),
        )
        self._session.add(run)
        await self._session.flush()
        return run

    async def list_for_dataset(
        self, dataset_id: uuid.UUID, workspace_id: uuid.UUID
    ) -> list[EvalRun]:
        stmt = (
            select(EvalRun)
            .where(EvalRun.dataset_id == dataset_id, EvalRun.workspace_id == workspace_id)
            .order_by(EvalRun.created_at.desc())
        )
        return list((await self._session.execute(stmt)).scalars())

    async def get(self, run_id: uuid.UUID, workspace_id: uuid.UUID) -> EvalRun | None:
        stmt = select(EvalRun).where(
            EvalRun.id == run_id, EvalRun.workspace_id == workspace_id
        )
        return (await self._session.execute(stmt)).scalar_one_or_none()


class WorkspaceRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, workspace_id: uuid.UUID) -> Workspace | None:
        return await self._session.get(Workspace, workspace_id)

    async def update(
        self,
        workspace: Workspace,
        *,
        name: str | None = None,
        key_policy: str | None = None,
        settings: dict | None = None,
    ) -> Workspace:
        if name is not None:
            workspace.name = name
        if key_policy is not None:
            workspace.key_policy = key_policy
        if settings is not None:
            workspace.settings = settings
        await self._session.flush()
        return workspace


class MemberRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list(self, workspace_id: uuid.UUID) -> list[tuple[Membership, User]]:
        stmt = (
            select(Membership, User)
            .join(User, User.id == Membership.user_id)
            .where(Membership.workspace_id == workspace_id)
            .order_by(Membership.created_at)
        )
        return [(m, u) for m, u in (await self._session.execute(stmt)).all()]

    async def add(self, *, workspace_id: uuid.UUID, user_id: uuid.UUID, role: str) -> Membership:
        membership = Membership(workspace_id=workspace_id, user_id=user_id, role=role)
        self._session.add(membership)
        await self._session.flush()
        return membership

    async def get(self, membership_id: uuid.UUID, workspace_id: uuid.UUID) -> Membership | None:
        stmt = select(Membership).where(
            Membership.id == membership_id, Membership.workspace_id == workspace_id
        )
        return (await self._session.execute(stmt)).scalar_one_or_none()

    async def remove(self, membership: Membership) -> None:
        await self._session.delete(membership)


class ProviderCredentialRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list(self, workspace_id: uuid.UUID) -> list[ProviderCredential]:
        stmt = (
            select(ProviderCredential)
            .where(ProviderCredential.workspace_id == workspace_id)
            .order_by(ProviderCredential.created_at.desc())
        )
        return list((await self._session.execute(stmt)).scalars())

    async def create(
        self,
        *,
        workspace_id: uuid.UUID,
        provider: str,
        label: str,
        key_prefix: str,
        key_ciphertext: str,
    ) -> ProviderCredential:
        cred = ProviderCredential(
            workspace_id=workspace_id,
            provider=provider,
            label=label,
            key_prefix=key_prefix,
            key_ciphertext=key_ciphertext,
        )
        self._session.add(cred)
        await self._session.flush()
        return cred

    async def get(self, cred_id: uuid.UUID, workspace_id: uuid.UUID) -> ProviderCredential | None:
        stmt = select(ProviderCredential).where(
            ProviderCredential.id == cred_id, ProviderCredential.workspace_id == workspace_id
        )
        return (await self._session.execute(stmt)).scalar_one_or_none()

    async def delete(self, cred: ProviderCredential) -> None:
        await self._session.delete(cred)


class AuthRepository:
    """Users, workspaces, and memberships for signup/login."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_user_by_email(self, email: str) -> User | None:
        stmt = select(User).where(User.email == email.lower())
        return (await self._session.execute(stmt)).scalar_one_or_none()

    async def get_user(self, user_id: uuid.UUID) -> User | None:
        return await self._session.get(User, user_id)

    async def create_user(
        self,
        *,
        email: str,
        name: str,
        password_hash: str,
        first_name: str | None = None,
        last_name: str | None = None,
        phone: str | None = None,
        company: str | None = None,
    ) -> User:
        user = User(
            email=email.lower(),
            name=name,
            password_hash=password_hash,
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            company=company,
        )
        self._session.add(user)
        await self._session.flush()
        return user

    async def create_workspace(self, *, name: str) -> Workspace:
        workspace = Workspace(name=name, key_policy="platform", allowed_providers=[])
        self._session.add(workspace)
        await self._session.flush()
        return workspace

    async def add_membership(
        self, *, user_id: uuid.UUID, workspace_id: uuid.UUID, role: str = "owner"
    ) -> Membership:
        membership = Membership(user_id=user_id, workspace_id=workspace_id, role=role)
        self._session.add(membership)
        await self._session.flush()
        return membership

    async def primary_membership(self, user_id: uuid.UUID) -> Membership | None:
        stmt = (
            select(Membership)
            .where(Membership.user_id == user_id)
            .order_by(Membership.created_at)
            .limit(1)
        )
        return (await self._session.execute(stmt)).scalar_one_or_none()

    async def is_member(self, user_id: uuid.UUID, workspace_id: uuid.UUID) -> bool:
        stmt = select(Membership.id).where(
            Membership.user_id == user_id, Membership.workspace_id == workspace_id
        )
        return (await self._session.execute(stmt)).scalar_one_or_none() is not None

    # --- password reset ---
    async def set_password(self, user: User, password_hash: str) -> None:
        user.password_hash = password_hash
        await self._session.flush()

    async def create_password_reset(
        self, *, user_id: uuid.UUID, token: str, expires_at
    ) -> PasswordReset:
        pr = PasswordReset(user_id=user_id, token=token, expires_at=expires_at)
        self._session.add(pr)
        await self._session.flush()
        return pr

    async def get_password_reset(self, token: str) -> PasswordReset | None:
        stmt = select(PasswordReset).where(PasswordReset.token == token)
        return (await self._session.execute(stmt)).scalar_one_or_none()

    async def mark_reset_used(self, pr: PasswordReset) -> None:
        pr.used = True
        await self._session.flush()


class DeploymentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        workspace_id: uuid.UUID,
        name: str,
        target_type: str,
        target_id: uuid.UUID,
        key_prefix: str,
        key_hash: str,
    ) -> Deployment:
        deployment = Deployment(
            workspace_id=workspace_id,
            name=name,
            target_type=target_type,
            target_id=target_id,
            key_prefix=key_prefix,
            key_hash=key_hash,
        )
        self._session.add(deployment)
        await self._session.flush()
        return deployment

    async def list(
        self, workspace_id: uuid.UUID, *, limit: int = 20, offset: int = 0
    ) -> list[Deployment]:
        stmt = (
            select(Deployment)
            .where(Deployment.workspace_id == workspace_id)
            .order_by(Deployment.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list((await self._session.execute(stmt)).scalars())

    async def count(self, workspace_id: uuid.UUID) -> int:
        stmt = select(func.count(Deployment.id)).where(Deployment.workspace_id == workspace_id)
        return int((await self._session.execute(stmt)).scalar_one())

    async def get(self, deployment_id: uuid.UUID, workspace_id: uuid.UUID) -> Deployment | None:
        stmt = select(Deployment).where(
            Deployment.id == deployment_id, Deployment.workspace_id == workspace_id
        )
        return (await self._session.execute(stmt)).scalar_one_or_none()

    async def get_for_serving(self, deployment_id: uuid.UUID) -> Deployment | None:
        """Fetch by id only — the serving request authenticates by API key, not session."""
        stmt = select(Deployment).where(Deployment.id == deployment_id)
        return (await self._session.execute(stmt)).scalar_one_or_none()

    async def set_status(self, deployment: Deployment, status: str) -> None:
        deployment.status = status
        await self._session.flush()


class RunRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def start(
        self, *, workspace_id: uuid.UUID, pipeline_id: uuid.UUID | None, kind: str, input: dict
    ) -> Run:
        run = Run(
            workspace_id=workspace_id,
            pipeline_id=pipeline_id,
            kind=kind,
            input=input,
            status="running",
        )
        self._session.add(run)
        await self._session.flush()
        return run

    async def add_span(
        self,
        run: Run,
        *,
        seq: int,
        name: str,
        node_type: str | None,
        status: str,
        latency_ms: int | None,
        detail: dict,
    ) -> Span:
        span = Span(
            run_id=run.id,
            seq=seq,
            name=name,
            node_type=node_type,
            status=status,
            latency_ms=latency_ms,
            detail=detail,
        )
        self._session.add(span)
        await self._session.flush()
        return span

    async def finish(
        self,
        run: Run,
        *,
        status: str,
        output: dict,
        latency_ms: int,
        tokens_in: int = 0,
        tokens_out: int = 0,
    ) -> None:
        run.status = status
        run.output = output
        run.latency_ms = latency_ms
        run.tokens_in = tokens_in
        run.tokens_out = tokens_out
        run.finished_at = datetime.now(UTC)
        await self._session.flush()

    async def list(self, workspace_id: uuid.UUID, *, limit: int = 20, offset: int = 0) -> list[Run]:
        stmt = (
            select(Run)
            .where(Run.workspace_id == workspace_id)
            .order_by(Run.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list((await self._session.execute(stmt)).scalars())

    async def count(self, workspace_id: uuid.UUID) -> int:
        stmt = select(func.count(Run.id)).where(Run.workspace_id == workspace_id)
        return int((await self._session.execute(stmt)).scalar_one())

    async def get(self, run_id: uuid.UUID, workspace_id: uuid.UUID) -> Run | None:
        stmt = (
            select(Run)
            .options(selectinload(Run.spans))
            .where(Run.id == run_id, Run.workspace_id == workspace_id)
        )
        return (await self._session.execute(stmt)).scalar_one_or_none()


class AnalyticsRepository:
    """Aggregations over runs for the analytics dashboards."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def totals(self, workspace_id: uuid.UUID) -> dict:
        stmt = select(
            func.count(Run.id),
            func.coalesce(func.sum(case((Run.status == "succeeded", 1), else_=0)), 0),
            func.coalesce(func.sum(Run.tokens_in), 0),
            func.coalesce(func.sum(Run.tokens_out), 0),
            func.avg(Run.latency_ms),
        ).where(Run.workspace_id == workspace_id)
        cnt, succ, tin, tout, avg = (await self._session.execute(stmt)).one()
        return {
            "runs": int(cnt),
            "succeeded": int(succ),
            "tokens_in": int(tin),
            "tokens_out": int(tout),
            "avg_latency_ms": round(float(avg)) if avg is not None else None,
        }

    async def by_kind(self, workspace_id: uuid.UUID) -> dict:
        stmt = (
            select(Run.kind, func.count())
            .where(Run.workspace_id == workspace_id)
            .group_by(Run.kind)
        )
        return {k: int(c) for k, c in (await self._session.execute(stmt)).all()}

    async def daily_counts(self, workspace_id: uuid.UUID, *, days: int) -> dict[str, int]:
        cutoff = datetime.now(UTC) - timedelta(days=days)
        day = cast(Run.created_at, Date)
        stmt = (
            select(day.label("d"), func.count().label("c"))
            .where(Run.workspace_id == workspace_id, Run.created_at >= cutoff)
            .group_by(day)
        )
        rows = (await self._session.execute(stmt)).all()
        return {d.isoformat(): int(c) for d, c in rows}


class OverviewRepository:
    """Read-only workspace rollups for the dashboard."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def _count(self, model, workspace_id: uuid.UUID) -> int:
        stmt = select(func.count(model.id)).where(model.workspace_id == workspace_id)
        return int((await self._session.execute(stmt)).scalar_one())

    async def stats(self, workspace_id: uuid.UUID) -> dict:
        return {
            "documents": await self._count(Document, workspace_id),
            "chunks": await self._count(Chunk, workspace_id),
            "sources": await self._count(DataSource, workspace_id),
            "indexes": await self._count(Index, workspace_id),
        }


class ConnectionRepository:
    """Bring-your-own service connections. Secret fields are encrypted at rest."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        workspace_id: uuid.UUID,
        name: str,
        capability: str,
        provider: str,
        config: dict,
        secret_ciphertext: str | None,
    ) -> Connection:
        conn = Connection(
            workspace_id=workspace_id,
            name=name,
            capability=capability,
            provider=provider,
            config=config,
            secret_ciphertext=secret_ciphertext,
        )
        self._session.add(conn)
        await self._session.flush()
        return conn

    async def list(
        self, workspace_id: uuid.UUID, *, capability: str | None = None
    ) -> list[Connection]:
        stmt = select(Connection).where(Connection.workspace_id == workspace_id)
        if capability:
            stmt = stmt.where(Connection.capability == capability)
        stmt = stmt.order_by(Connection.created_at.desc())
        return list((await self._session.execute(stmt)).scalars())

    async def get(self, conn_id: uuid.UUID, workspace_id: uuid.UUID) -> Connection | None:
        stmt = select(Connection).where(
            Connection.id == conn_id, Connection.workspace_id == workspace_id
        )
        return (await self._session.execute(stmt)).scalar_one_or_none()

    async def update(
        self,
        conn: Connection,
        *,
        name: str | None = None,
        config: dict | None = None,
        secret_ciphertext: str | None = None,
    ) -> Connection:
        if name is not None:
            conn.name = name
        if config is not None:
            conn.config = config
        if secret_ciphertext is not None:
            conn.secret_ciphertext = secret_ciphertext
        await self._session.flush()
        return conn

    async def set_status(self, conn: Connection, *, status: str, detail: str) -> None:
        conn.status = status
        conn.status_detail = detail
        conn.last_tested_at = datetime.now(UTC)
        await self._session.flush()

    async def delete(self, conn: Connection) -> None:
        await self._session.delete(conn)


class ToolRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        workspace_id: uuid.UUID,
        name: str,
        kind: str = "http",
        description: str = "",
        input_schema: dict | None = None,
        config: dict | None = None,
        enabled: bool = True,
    ) -> Tool:
        tool = Tool(
            workspace_id=workspace_id,
            name=name,
            kind=kind,
            description=description,
            input_schema=input_schema or {},
            config=config or {},
            enabled=enabled,
        )
        self._session.add(tool)
        await self._session.flush()
        return tool

    async def list(self, workspace_id: uuid.UUID) -> list[Tool]:
        stmt = (
            select(Tool)
            .where(Tool.workspace_id == workspace_id)
            .order_by(Tool.updated_at.desc())
        )
        return list((await self._session.execute(stmt)).scalars())

    async def get(self, tool_id: uuid.UUID, workspace_id: uuid.UUID) -> Tool | None:
        stmt = select(Tool).where(Tool.id == tool_id, Tool.workspace_id == workspace_id)
        return (await self._session.execute(stmt)).scalar_one_or_none()

    async def update(self, tool: Tool, **fields) -> Tool:
        for key, value in fields.items():
            if value is not None and hasattr(tool, key):
                setattr(tool, key, value)
        await self._session.flush()
        return tool

    async def delete(self, tool: Tool) -> None:
        await self._session.delete(tool)


class PromptRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self, *, workspace_id: uuid.UUID, name: str, description: str, content: str
    ) -> Prompt:
        prompt = Prompt(
            workspace_id=workspace_id, name=name, description=description, current_version=1
        )
        self._session.add(prompt)
        await self._session.flush()
        self._session.add(
            PromptVersion(prompt_id=prompt.id, version=1, content=content, notes="initial")
        )
        await self._session.flush()
        return prompt

    async def list(self, workspace_id: uuid.UUID) -> list[Prompt]:
        stmt = (
            select(Prompt)
            .where(Prompt.workspace_id == workspace_id)
            .order_by(Prompt.updated_at.desc())
        )
        return list((await self._session.execute(stmt)).scalars())

    async def get(self, prompt_id: uuid.UUID, workspace_id: uuid.UUID) -> Prompt | None:
        stmt = (
            select(Prompt)
            .options(selectinload(Prompt.versions))
            .where(Prompt.id == prompt_id, Prompt.workspace_id == workspace_id)
        )
        return (await self._session.execute(stmt)).scalar_one_or_none()

    async def latest_content(self, prompt: Prompt) -> str:
        stmt = (
            select(PromptVersion.content)
            .where(PromptVersion.prompt_id == prompt.id)
            .order_by(PromptVersion.version.desc())
            .limit(1)
        )
        return (await self._session.execute(stmt)).scalar_one_or_none() or ""

    async def add_version(self, prompt: Prompt, *, content: str, notes: str = "") -> PromptVersion:
        next_version = prompt.current_version + 1
        version = PromptVersion(
            prompt_id=prompt.id, version=next_version, content=content, notes=notes
        )
        self._session.add(version)
        prompt.current_version = next_version
        await self._session.flush()
        return version

    async def update_meta(
        self, prompt: Prompt, *, name: str | None = None, description: str | None = None
    ) -> Prompt:
        if name is not None:
            prompt.name = name
        if description is not None:
            prompt.description = description
        await self._session.flush()
        return prompt

    async def delete(self, prompt: Prompt) -> None:
        await self._session.delete(prompt)


class DataSubjectRequestRepository:
    """GDPR DSAR jobs and the export/erasure that fulfils them."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self, *, workspace_id: uuid.UUID, subject: str, kind: str
    ) -> DataSubjectRequest:
        dsar = DataSubjectRequest(workspace_id=workspace_id, subject=subject, kind=kind)
        self._session.add(dsar)
        await self._session.flush()
        return dsar

    async def list(self, workspace_id: uuid.UUID) -> list[DataSubjectRequest]:
        stmt = (
            select(DataSubjectRequest)
            .where(DataSubjectRequest.workspace_id == workspace_id)
            .order_by(DataSubjectRequest.created_at.desc())
        )
        return list((await self._session.execute(stmt)).scalars())

    async def get(self, dsar_id: uuid.UUID, workspace_id: uuid.UUID) -> DataSubjectRequest | None:
        stmt = select(DataSubjectRequest).where(
            DataSubjectRequest.id == dsar_id, DataSubjectRequest.workspace_id == workspace_id
        )
        return (await self._session.execute(stmt)).scalar_one_or_none()

    async def _matching_documents(
        self, workspace_id: uuid.UUID, subject: str
    ) -> list[Document]:
        """Documents whose filename matches the subject — the unit of data we hold per subject."""
        stmt = select(Document).where(
            Document.workspace_id == workspace_id, Document.filename.ilike(f"%{subject}%")
        )
        return list((await self._session.execute(stmt)).scalars())

    async def export(self, dsar: DataSubjectRequest) -> dict:
        docs = await self._matching_documents(dsar.workspace_id, dsar.subject)
        payload = {
            "subject": dsar.subject,
            "documents": [
                {"id": str(d.id), "filename": d.filename, "status": d.status} for d in docs
            ],
        }
        for d in docs:
            chunks = (
                await self._session.execute(
                    select(Chunk.text).where(Chunk.document_id == d.id).order_by(Chunk.chunk_index)
                )
            ).scalars()
            payload.setdefault("chunks", {})[str(d.id)] = list(chunks)
        dsar.status = "completed"
        dsar.result = {"document_count": len(docs), "export": payload}
        dsar.finished_at = datetime.now(UTC)
        await self._session.flush()
        return payload

    async def erase(self, dsar: DataSubjectRequest) -> int:
        """Crypto-shred: hard-delete matching documents (chunks + embeddings cascade)."""
        docs = await self._matching_documents(dsar.workspace_id, dsar.subject)
        for d in docs:
            await self._session.delete(d)
        dsar.status = "completed"
        dsar.result = {"erased_documents": len(docs)}
        dsar.finished_at = datetime.now(UTC)
        await self._session.flush()
        return len(docs)


class InvitationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        workspace_id: uuid.UUID,
        email: str,
        role: str,
        token: str,
        invited_by: str,
        expires_at,
    ) -> Invitation:
        inv = Invitation(
            workspace_id=workspace_id,
            email=email.lower(),
            role=role,
            token=token,
            invited_by=invited_by,
            expires_at=expires_at,
        )
        self._session.add(inv)
        await self._session.flush()
        return inv

    async def list(self, workspace_id: uuid.UUID) -> list[Invitation]:
        stmt = (
            select(Invitation)
            .where(Invitation.workspace_id == workspace_id)
            .order_by(Invitation.created_at.desc())
        )
        return list((await self._session.execute(stmt)).scalars())

    async def get(self, invite_id: uuid.UUID, workspace_id: uuid.UUID) -> Invitation | None:
        stmt = select(Invitation).where(
            Invitation.id == invite_id, Invitation.workspace_id == workspace_id
        )
        return (await self._session.execute(stmt)).scalar_one_or_none()

    async def get_by_token(self, token: str) -> Invitation | None:
        stmt = select(Invitation).where(Invitation.token == token)
        return (await self._session.execute(stmt)).scalar_one_or_none()

    async def revoke(self, inv: Invitation) -> None:
        inv.status = "revoked"
        await self._session.flush()

    async def mark_accepted(self, inv: Invitation) -> None:
        inv.status = "accepted"
        inv.accepted_at = datetime.now(UTC)
        await self._session.flush()


class NotificationRepository:
    """User-facing inbox — curated, read/unread, dismissible (separate from audit)."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        workspace_id: uuid.UUID,
        category: str,
        title: str,
        body: str = "",
        severity: str = "info",
        link: str | None = None,
    ) -> Notification:
        n = Notification(
            workspace_id=workspace_id,
            category=category,
            title=title,
            body=body,
            severity=severity,
            link=link,
        )
        self._session.add(n)
        await self._session.flush()
        return n

    async def list(
        self, workspace_id: uuid.UUID, *, limit: int = 20
    ) -> list[Notification]:
        stmt = (
            select(Notification)
            .where(Notification.workspace_id == workspace_id)
            .order_by(Notification.created_at.desc())
            .limit(limit)
        )
        return list((await self._session.execute(stmt)).scalars())

    async def unread_count(self, workspace_id: uuid.UUID) -> int:
        stmt = select(func.count(Notification.id)).where(
            Notification.workspace_id == workspace_id, Notification.read.is_(False)
        )
        return int((await self._session.execute(stmt)).scalar_one())

    async def get(self, notif_id: uuid.UUID, workspace_id: uuid.UUID) -> Notification | None:
        stmt = select(Notification).where(
            Notification.id == notif_id, Notification.workspace_id == workspace_id
        )
        return (await self._session.execute(stmt)).scalar_one_or_none()

    async def mark_read(self, notif: Notification) -> None:
        notif.read = True
        notif.read_at = datetime.now(UTC)
        await self._session.flush()

    async def mark_all_read(self, workspace_id: uuid.UUID) -> int:
        from sqlalchemy import update

        stmt = (
            update(Notification)
            .where(Notification.workspace_id == workspace_id, Notification.read.is_(False))
            .values(read=True, read_at=datetime.now(UTC))
        )
        result = await self._session.execute(stmt)
        return result.rowcount or 0

    async def delete(self, notif: Notification) -> None:
        await self._session.delete(notif)

    async def clear(self, workspace_id: uuid.UUID) -> None:
        from sqlalchemy import delete

        await self._session.execute(
            delete(Notification).where(Notification.workspace_id == workspace_id)
        )


class AuditRepository:
    """Append-only, hash-chained audit log."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list(
        self, workspace_id: uuid.UUID, *, limit: int = 20, offset: int = 0
    ) -> list[AuditLog]:
        stmt = (
            select(AuditLog)
            .where(AuditLog.workspace_id == workspace_id)
            .order_by(AuditLog.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list((await self._session.execute(stmt)).scalars())

    async def count(self, workspace_id: uuid.UUID) -> int:
        stmt = select(func.count(AuditLog.id)).where(AuditLog.workspace_id == workspace_id)
        return int((await self._session.execute(stmt)).scalar_one())

    @staticmethod
    def _digest(prev_hash: str | None, payload: dict) -> str:
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(f"{prev_hash or ''}{canonical}".encode()).hexdigest()

    async def record(
        self,
        *,
        actor: str,
        action: str,
        workspace_id: uuid.UUID | None = None,
        resource_type: str | None = None,
        resource_id: str | None = None,
        detail: dict | None = None,
    ) -> AuditLog:
        last = (
            await self._session.execute(
                select(AuditLog.hash).order_by(AuditLog.created_at.desc()).limit(1)
            )
        ).scalar_one_or_none()

        payload = {
            "actor": actor,
            "action": action,
            "workspace_id": str(workspace_id) if workspace_id else None,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "detail": detail or {},
        }
        entry = AuditLog(
            actor=actor,
            action=action,
            workspace_id=workspace_id,
            resource_type=resource_type,
            resource_id=resource_id,
            detail=detail or {},
            prev_hash=last,
            hash=self._digest(last, payload),
        )
        self._session.add(entry)
        return entry
