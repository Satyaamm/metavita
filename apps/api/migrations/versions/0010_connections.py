"""connections: bring-your-own integrations (LLM, embeddings, vector DB, video, …)

Revision ID: 0010_connections
Revises: 0009_tools_prompts_dsar
Create Date: 2026-06-29
"""
from __future__ import annotations

from alembic import op

revision = "0010_connections"
down_revision = "0009_tools_prompts_dsar"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE connections (
            id UUID PRIMARY KEY,
            workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
            name VARCHAR(256) NOT NULL,
            capability VARCHAR(32) NOT NULL,
            provider VARCHAR(64) NOT NULL,
            config JSONB NOT NULL DEFAULT '{}'::jsonb,
            secret_ciphertext TEXT,
            status VARCHAR(32) NOT NULL DEFAULT 'untested',
            status_detail TEXT NOT NULL DEFAULT '',
            last_tested_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )
    op.execute("CREATE INDEX ix_connections_workspace_id ON connections(workspace_id)")
    op.execute("CREATE INDEX ix_connections_capability ON connections(workspace_id, capability)")

    op.execute("ALTER TABLE connections ENABLE ROW LEVEL SECURITY")
    op.execute(
        "CREATE POLICY connections_workspace_isolation ON connections "
        "USING (workspace_id::text = current_setting('app.workspace_id', true))"
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS connections CASCADE")
