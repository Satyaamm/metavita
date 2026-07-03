"""knowledge: data_sources, indexes, and document links

Revision ID: 0002_knowledge
Revises: 0001_init
Create Date: 2026-06-25
"""
from __future__ import annotations

from alembic import op

revision = "0002_knowledge"
down_revision = "0001_init"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE data_sources (
            id UUID PRIMARY KEY,
            workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
            name VARCHAR(256) NOT NULL,
            type VARCHAR(32) NOT NULL DEFAULT 'upload',
            connector VARCHAR(64),
            modality VARCHAR(16) NOT NULL DEFAULT 'text',
            status VARCHAR(32) NOT NULL DEFAULT 'active',
            config JSONB NOT NULL DEFAULT '{}'::jsonb,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )
    op.execute("CREATE INDEX ix_data_sources_workspace_id ON data_sources(workspace_id)")

    op.execute(
        """
        CREATE TABLE indexes (
            id UUID PRIMARY KEY,
            workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
            name VARCHAR(256) NOT NULL,
            modality VARCHAR(16) NOT NULL DEFAULT 'text',
            embedding_provider VARCHAR(64) NOT NULL DEFAULT 'openai',
            embedding_model VARCHAR(128) NOT NULL DEFAULT 'text-embedding-3-small',
            embedding_dim INTEGER NOT NULL,
            chunk_size INTEGER NOT NULL DEFAULT 1200,
            overlap INTEGER NOT NULL DEFAULT 150,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )
    op.execute("CREATE INDEX ix_indexes_workspace_id ON indexes(workspace_id)")

    op.execute(
        "ALTER TABLE documents "
        "ADD COLUMN source_id UUID REFERENCES data_sources(id) ON DELETE SET NULL, "
        "ADD COLUMN index_id UUID REFERENCES indexes(id) ON DELETE SET NULL"
    )
    op.execute("CREATE INDEX ix_documents_source_id ON documents(source_id)")
    op.execute("CREATE INDEX ix_documents_index_id ON documents(index_id)")

    # RLS on the new tenant tables (defense-in-depth, matching 0001).
    op.execute("ALTER TABLE data_sources ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE indexes ENABLE ROW LEVEL SECURITY")
    op.execute(
        "CREATE POLICY data_sources_workspace_isolation ON data_sources "
        "USING (workspace_id::text = current_setting('app.workspace_id', true))"
    )
    op.execute(
        "CREATE POLICY indexes_workspace_isolation ON indexes "
        "USING (workspace_id::text = current_setting('app.workspace_id', true))"
    )


def downgrade() -> None:
    op.execute("ALTER TABLE documents DROP COLUMN IF EXISTS index_id")
    op.execute("ALTER TABLE documents DROP COLUMN IF EXISTS source_id")
    op.execute("DROP TABLE IF EXISTS indexes CASCADE")
    op.execute("DROP TABLE IF EXISTS data_sources CASCADE")
