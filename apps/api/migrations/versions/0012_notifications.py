"""notifications: user-facing inbox (separate from the audit log)

Revision ID: 0012_notifications
Revises: 0011_connection_slots
Create Date: 2026-06-29
"""
from __future__ import annotations

from alembic import op

revision = "0012_notifications"
down_revision = "0011_connection_slots"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE notifications (
            id UUID PRIMARY KEY,
            workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
            category VARCHAR(64) NOT NULL,
            title VARCHAR(256) NOT NULL,
            body TEXT NOT NULL DEFAULT '',
            severity VARCHAR(16) NOT NULL DEFAULT 'info',
            link VARCHAR(512),
            read BOOLEAN NOT NULL DEFAULT false,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            read_at TIMESTAMPTZ
        )
        """
    )
    op.execute(
        "CREATE INDEX ix_notifications_workspace_id ON notifications(workspace_id, created_at DESC)"
    )
    op.execute("ALTER TABLE notifications ENABLE ROW LEVEL SECURITY")
    op.execute(
        "CREATE POLICY notifications_workspace_isolation ON notifications "
        "USING (workspace_id::text = current_setting('app.workspace_id', true))"
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS notifications CASCADE")
