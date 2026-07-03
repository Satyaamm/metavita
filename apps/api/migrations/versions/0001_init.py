"""initial schema: workspaces, documents, chunks (pgvector), audit_logs

Revision ID: 0001_init
Revises:
Create Date: 2026-06-25
"""
from __future__ import annotations

from alembic import op

revision = "0001_init"
down_revision = None
branch_labels = None
depends_on = None

# Historical schema created a fixed-dim vector column; migration 0013 later makes it
# dimensionless (the user's own embedding model decides the dimension).
DIM = 1536


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")

    op.execute(
        """
        CREATE TABLE workspaces (
            id UUID PRIMARY KEY,
            name VARCHAR(256) NOT NULL,
            key_policy VARCHAR(32) NOT NULL DEFAULT 'platform',
            allowed_providers JSONB NOT NULL DEFAULT '[]'::jsonb,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )

    op.execute(
        """
        CREATE TABLE documents (
            id UUID PRIMARY KEY,
            workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
            filename VARCHAR(1024) NOT NULL,
            content_type VARCHAR(256),
            status VARCHAR(32) NOT NULL DEFAULT 'pending',
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )
    op.execute("CREATE INDEX ix_documents_workspace_id ON documents(workspace_id)")

    op.execute(
        f"""
        CREATE TABLE chunks (
            id UUID PRIMARY KEY,
            workspace_id UUID NOT NULL,
            document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
            chunk_index INTEGER NOT NULL,
            text TEXT NOT NULL,
            embedding vector({DIM}) NOT NULL,
            meta JSONB NOT NULL DEFAULT '{{}}'::jsonb
        )
        """
    )
    op.execute("CREATE INDEX ix_chunks_workspace_id ON chunks(workspace_id)")
    op.execute("CREATE INDEX ix_chunks_document_id ON chunks(document_id)")
    op.execute(
        "CREATE INDEX ix_chunks_embedding_hnsw ON chunks "
        "USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64)"
    )

    op.execute(
        """
        CREATE TABLE audit_logs (
            id UUID PRIMARY KEY,
            workspace_id UUID,
            actor VARCHAR(256) NOT NULL,
            action VARCHAR(128) NOT NULL,
            resource_type VARCHAR(128),
            resource_id VARCHAR(256),
            detail JSONB NOT NULL DEFAULT '{}'::jsonb,
            prev_hash VARCHAR(64),
            hash VARCHAR(64) NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )
    op.execute("CREATE INDEX ix_audit_logs_workspace_id ON audit_logs(workspace_id)")

    # --- Tenant-isolation RLS skeleton (defense-in-depth) -------------------
    # Enabled here; policies use a per-request GUC `app.workspace_id` set by the
    # API. In M0 the app also scopes every query by workspace_id; M1 wires the
    # GUC + a non-superuser app role so RLS is actively enforced.
    op.execute("ALTER TABLE documents ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE chunks ENABLE ROW LEVEL SECURITY")
    op.execute(
        """
        CREATE POLICY documents_workspace_isolation ON documents
        USING (workspace_id::text = current_setting('app.workspace_id', true))
        """
    )
    op.execute(
        """
        CREATE POLICY chunks_workspace_isolation ON chunks
        USING (workspace_id::text = current_setting('app.workspace_id', true))
        """
    )
    # Audit log is append-only: forbid UPDATE/DELETE even for the app role.
    op.execute("ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY")
    op.execute(
        "CREATE POLICY audit_logs_insert_only ON audit_logs FOR INSERT WITH CHECK (true)"
    )
    op.execute("CREATE POLICY audit_logs_select ON audit_logs FOR SELECT USING (true)")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS audit_logs CASCADE")
    op.execute("DROP TABLE IF EXISTS chunks CASCADE")
    op.execute("DROP TABLE IF EXISTS documents CASCADE")
    op.execute("DROP TABLE IF EXISTS workspaces CASCADE")
