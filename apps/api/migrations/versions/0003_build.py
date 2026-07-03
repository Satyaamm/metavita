"""build: pipelines and agents

Revision ID: 0003_build
Revises: 0002_knowledge
Create Date: 2026-06-25
"""
from __future__ import annotations

from alembic import op

revision = "0003_build"
down_revision = "0002_knowledge"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE pipelines (
            id UUID PRIMARY KEY,
            workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
            name VARCHAR(256) NOT NULL,
            graph JSONB NOT NULL DEFAULT '{"nodes": [], "edges": []}'::jsonb,
            status VARCHAR(32) NOT NULL DEFAULT 'draft',
            version INTEGER NOT NULL DEFAULT 1,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )
    op.execute("CREATE INDEX ix_pipelines_workspace_id ON pipelines(workspace_id)")

    op.execute(
        """
        CREATE TABLE agents (
            id UUID PRIMARY KEY,
            workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
            name VARCHAR(256) NOT NULL,
            system_prompt TEXT,
            provider VARCHAR(64) NOT NULL DEFAULT 'anthropic',
            model VARCHAR(128) NOT NULL DEFAULT 'claude-opus-4-8',
            tools JSONB NOT NULL DEFAULT '[]'::jsonb,
            index_id UUID REFERENCES indexes(id) ON DELETE SET NULL,
            memory BOOLEAN NOT NULL DEFAULT false,
            status VARCHAR(32) NOT NULL DEFAULT 'draft',
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )
    op.execute("CREATE INDEX ix_agents_workspace_id ON agents(workspace_id)")

    for table in ("pipelines", "agents"):
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(
            f"CREATE POLICY {table}_workspace_isolation ON {table} "
            "USING (workspace_id::text = current_setting('app.workspace_id', true))"
        )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS agents CASCADE")
    op.execute("DROP TABLE IF EXISTS pipelines CASCADE")
