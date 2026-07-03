"""runs and spans (execution traces)

Revision ID: 0004_runs
Revises: 0003_build
Create Date: 2026-06-25
"""
from __future__ import annotations

from alembic import op

revision = "0004_runs"
down_revision = "0003_build"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE runs (
            id UUID PRIMARY KEY,
            workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
            pipeline_id UUID REFERENCES pipelines(id) ON DELETE SET NULL,
            kind VARCHAR(32) NOT NULL DEFAULT 'pipeline',
            status VARCHAR(32) NOT NULL DEFAULT 'running',
            input JSONB NOT NULL DEFAULT '{}'::jsonb,
            output JSONB NOT NULL DEFAULT '{}'::jsonb,
            latency_ms INTEGER,
            tokens_in INTEGER NOT NULL DEFAULT 0,
            tokens_out INTEGER NOT NULL DEFAULT 0,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            finished_at TIMESTAMPTZ
        )
        """
    )
    op.execute("CREATE INDEX ix_runs_workspace_id ON runs(workspace_id)")
    op.execute("CREATE INDEX ix_runs_pipeline_id ON runs(pipeline_id)")

    op.execute(
        """
        CREATE TABLE spans (
            id UUID PRIMARY KEY,
            run_id UUID NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
            seq INTEGER NOT NULL DEFAULT 0,
            name VARCHAR(128) NOT NULL,
            node_type VARCHAR(64),
            status VARCHAR(32) NOT NULL DEFAULT 'succeeded',
            latency_ms INTEGER,
            detail JSONB NOT NULL DEFAULT '{}'::jsonb,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )
    op.execute("CREATE INDEX ix_spans_run_id ON spans(run_id)")

    op.execute("ALTER TABLE runs ENABLE ROW LEVEL SECURITY")
    op.execute(
        "CREATE POLICY runs_workspace_isolation ON runs "
        "USING (workspace_id::text = current_setting('app.workspace_id', true))"
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS spans CASCADE")
    op.execute("DROP TABLE IF EXISTS runs CASCADE")
