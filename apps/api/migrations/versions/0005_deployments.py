"""deployments (serving)

Revision ID: 0005_deployments
Revises: 0004_runs
Create Date: 2026-06-25
"""
from __future__ import annotations

from alembic import op

revision = "0005_deployments"
down_revision = "0004_runs"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE deployments (
            id UUID PRIMARY KEY,
            workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
            name VARCHAR(256) NOT NULL,
            target_type VARCHAR(16) NOT NULL,
            target_id UUID NOT NULL,
            status VARCHAR(32) NOT NULL DEFAULT 'active',
            key_prefix VARCHAR(16) NOT NULL,
            key_hash VARCHAR(64) NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )
    op.execute("CREATE INDEX ix_deployments_workspace_id ON deployments(workspace_id)")
    # key_hash is the serving credential lookup; index it.
    op.execute("CREATE INDEX ix_deployments_key_hash ON deployments(key_hash)")

    op.execute("ALTER TABLE deployments ENABLE ROW LEVEL SECURITY")
    op.execute(
        "CREATE POLICY deployments_workspace_isolation ON deployments "
        "USING (workspace_id::text = current_setting('app.workspace_id', true))"
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS deployments CASCADE")
