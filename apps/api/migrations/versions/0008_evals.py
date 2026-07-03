"""evals: datasets and eval runs

Revision ID: 0008_evals
Revises: 0007_settings
Create Date: 2026-06-25
"""
from __future__ import annotations

from alembic import op

revision = "0008_evals"
down_revision = "0007_settings"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE eval_datasets (
            id UUID PRIMARY KEY,
            workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
            name VARCHAR(256) NOT NULL,
            items JSONB NOT NULL DEFAULT '[]'::jsonb,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )
    op.execute("CREATE INDEX ix_eval_datasets_workspace_id ON eval_datasets(workspace_id)")

    op.execute(
        """
        CREATE TABLE eval_runs (
            id UUID PRIMARY KEY,
            workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
            dataset_id UUID NOT NULL REFERENCES eval_datasets(id) ON DELETE CASCADE,
            pipeline_id UUID REFERENCES pipelines(id) ON DELETE SET NULL,
            status VARCHAR(32) NOT NULL DEFAULT 'running',
            summary JSONB NOT NULL DEFAULT '{}'::jsonb,
            results JSONB NOT NULL DEFAULT '[]'::jsonb,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            finished_at TIMESTAMPTZ
        )
        """
    )
    op.execute("CREATE INDEX ix_eval_runs_workspace_id ON eval_runs(workspace_id)")
    op.execute("CREATE INDEX ix_eval_runs_dataset_id ON eval_runs(dataset_id)")

    for table in ("eval_datasets", "eval_runs"):
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(
            f"CREATE POLICY {table}_workspace_isolation ON {table} "
            "USING (workspace_id::text = current_setting('app.workspace_id', true))"
        )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS eval_runs CASCADE")
    op.execute("DROP TABLE IF EXISTS eval_datasets CASCADE")
