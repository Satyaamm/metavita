"""tools registry, versioned prompts, and GDPR DSAR jobs

Revision ID: 0009_tools_prompts_dsar
Revises: 0008_evals
Create Date: 2026-06-26
"""
from __future__ import annotations

from alembic import op

revision = "0009_tools_prompts_dsar"
down_revision = "0008_evals"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE tools (
            id UUID PRIMARY KEY,
            workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
            name VARCHAR(128) NOT NULL,
            kind VARCHAR(32) NOT NULL DEFAULT 'http',
            description TEXT NOT NULL DEFAULT '',
            input_schema JSONB NOT NULL DEFAULT '{}'::jsonb,
            config JSONB NOT NULL DEFAULT '{}'::jsonb,
            enabled BOOLEAN NOT NULL DEFAULT true,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )
    op.execute("CREATE INDEX ix_tools_workspace_id ON tools(workspace_id)")

    op.execute(
        """
        CREATE TABLE prompts (
            id UUID PRIMARY KEY,
            workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
            name VARCHAR(256) NOT NULL,
            description TEXT NOT NULL DEFAULT '',
            current_version INTEGER NOT NULL DEFAULT 1,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )
    op.execute("CREATE INDEX ix_prompts_workspace_id ON prompts(workspace_id)")

    op.execute(
        """
        CREATE TABLE prompt_versions (
            id UUID PRIMARY KEY,
            prompt_id UUID NOT NULL REFERENCES prompts(id) ON DELETE CASCADE,
            version INTEGER NOT NULL,
            content TEXT NOT NULL,
            notes TEXT NOT NULL DEFAULT '',
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            UNIQUE (prompt_id, version)
        )
        """
    )
    op.execute("CREATE INDEX ix_prompt_versions_prompt_id ON prompt_versions(prompt_id)")

    op.execute(
        """
        CREATE TABLE data_subject_requests (
            id UUID PRIMARY KEY,
            workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
            subject VARCHAR(320) NOT NULL,
            kind VARCHAR(16) NOT NULL,
            status VARCHAR(32) NOT NULL DEFAULT 'pending',
            result JSONB NOT NULL DEFAULT '{}'::jsonb,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            finished_at TIMESTAMPTZ
        )
        """
    )
    op.execute(
        "CREATE INDEX ix_data_subject_requests_workspace_id "
        "ON data_subject_requests(workspace_id)"
    )

    # Row-Level Security: tenant isolation on every workspace-scoped table.
    for table in ("tools", "prompts", "data_subject_requests"):
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(
            f"CREATE POLICY {table}_workspace_isolation ON {table} "
            "USING (workspace_id::text = current_setting('app.workspace_id', true))"
        )
    # prompt_versions is isolated transitively through its parent prompt.
    op.execute("ALTER TABLE prompt_versions ENABLE ROW LEVEL SECURITY")
    op.execute(
        "CREATE POLICY prompt_versions_workspace_isolation ON prompt_versions USING ("
        "  EXISTS (SELECT 1 FROM prompts p WHERE p.id = prompt_versions.prompt_id"
        "    AND p.workspace_id::text = current_setting('app.workspace_id', true)))"
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS data_subject_requests CASCADE")
    op.execute("DROP TABLE IF EXISTS prompt_versions CASCADE")
    op.execute("DROP TABLE IF EXISTS prompts CASCADE")
    op.execute("DROP TABLE IF EXISTS tools CASCADE")
