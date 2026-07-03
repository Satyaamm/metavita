"""auth: users and memberships

Revision ID: 0006_auth
Revises: 0005_deployments
Create Date: 2026-06-25
"""
from __future__ import annotations

from alembic import op

revision = "0006_auth"
down_revision = "0005_deployments"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE users (
            id UUID PRIMARY KEY,
            email VARCHAR(320) NOT NULL UNIQUE,
            name VARCHAR(256) NOT NULL,
            password_hash VARCHAR(128) NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )
    op.execute("CREATE INDEX ix_users_email ON users(email)")

    op.execute(
        """
        CREATE TABLE memberships (
            id UUID PRIMARY KEY,
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
            role VARCHAR(32) NOT NULL DEFAULT 'owner',
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            UNIQUE (user_id, workspace_id)
        )
        """
    )
    op.execute("CREATE INDEX ix_memberships_user_id ON memberships(user_id)")
    op.execute("CREATE INDEX ix_memberships_workspace_id ON memberships(workspace_id)")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS memberships CASCADE")
    op.execute("DROP TABLE IF EXISTS users CASCADE")
