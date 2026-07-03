"""settings: workspace settings + provider credentials

Revision ID: 0007_settings
Revises: 0006_auth
Create Date: 2026-06-25
"""
from __future__ import annotations

from alembic import op

revision = "0007_settings"
down_revision = "0006_auth"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE workspaces ADD COLUMN settings JSONB NOT NULL DEFAULT '{}'::jsonb")

    op.execute(
        """
        CREATE TABLE provider_credentials (
            id UUID PRIMARY KEY,
            workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
            provider VARCHAR(64) NOT NULL,
            label VARCHAR(256) NOT NULL,
            key_prefix VARCHAR(16) NOT NULL,
            key_ciphertext TEXT NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )
    op.execute(
        "CREATE INDEX ix_provider_credentials_workspace_id ON provider_credentials(workspace_id)"
    )

    op.execute("ALTER TABLE provider_credentials ENABLE ROW LEVEL SECURITY")
    op.execute(
        "CREATE POLICY provider_credentials_workspace_isolation ON provider_credentials "
        "USING (workspace_id::text = current_setting('app.workspace_id', true))"
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS provider_credentials CASCADE")
    op.execute("ALTER TABLE workspaces DROP COLUMN IF EXISTS settings")
