"""invitations: invite users to a workspace by email (token URL)

Revision ID: 0014_invitations
Revises: 0013_dimensionless_vectors
Create Date: 2026-07-03
"""
from __future__ import annotations

from alembic import op

revision = "0014_invitations"
down_revision = "0013_dimensionless_vectors"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE invitations (
            id UUID PRIMARY KEY,
            workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
            email VARCHAR(320) NOT NULL,
            role VARCHAR(32) NOT NULL DEFAULT 'editor',
            token VARCHAR(64) NOT NULL UNIQUE,
            status VARCHAR(32) NOT NULL DEFAULT 'pending',
            invited_by VARCHAR(320) NOT NULL DEFAULT '',
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            expires_at TIMESTAMPTZ,
            accepted_at TIMESTAMPTZ
        )
        """
    )
    op.execute("CREATE INDEX ix_invitations_workspace_id ON invitations(workspace_id)")
    op.execute("CREATE INDEX ix_invitations_email ON invitations(email)")
    op.execute("CREATE UNIQUE INDEX ix_invitations_token ON invitations(token)")
    # Token lookup is public (accept flow), so RLS is scoped to the workspace for
    # the management endpoints; the accept path fetches by unique token directly.
    op.execute("ALTER TABLE invitations ENABLE ROW LEVEL SECURITY")
    op.execute(
        "CREATE POLICY invitations_workspace_isolation ON invitations "
        "USING (workspace_id::text = current_setting('app.workspace_id', true))"
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS invitations CASCADE")
