"""password_resets: single-use reset tokens (delivered by email)

Revision ID: 0015_password_resets
Revises: 0014_invitations
Create Date: 2026-07-03
"""
from __future__ import annotations

from alembic import op

revision = "0015_password_resets"
down_revision = "0014_invitations"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE password_resets (
            id UUID PRIMARY KEY,
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            token VARCHAR(64) NOT NULL UNIQUE,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            expires_at TIMESTAMPTZ,
            used BOOLEAN NOT NULL DEFAULT false
        )
        """
    )
    op.execute("CREATE INDEX ix_password_resets_user_id ON password_resets(user_id)")
    op.execute("CREATE UNIQUE INDEX ix_password_resets_token ON password_resets(token)")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS password_resets CASCADE")
