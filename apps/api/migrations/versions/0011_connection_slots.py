"""connection slots: agents pick which Connection fills each capability slot

Adds nullable FK columns to `agents` so a builder can pin the LLM / embeddings /
vector-store Connection used at run time. Null = fall back to the workspace's
default connection for that capability (behavior unchanged).

Pipelines carry per-node `connection_id` in their JSONB graph, so they need no
schema change here.

Revision ID: 0011_connection_slots
Revises: 0010_connections
Create Date: 2026-06-29
"""
from __future__ import annotations

from alembic import op

revision = "0011_connection_slots"
down_revision = "0010_connections"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE agents ADD COLUMN llm_connection_id UUID "
        "REFERENCES connections(id) ON DELETE SET NULL"
    )
    op.execute(
        "ALTER TABLE agents ADD COLUMN embedding_connection_id UUID "
        "REFERENCES connections(id) ON DELETE SET NULL"
    )
    op.execute(
        "ALTER TABLE agents ADD COLUMN vector_store_connection_id UUID "
        "REFERENCES connections(id) ON DELETE SET NULL"
    )


def downgrade() -> None:
    op.execute("ALTER TABLE agents DROP COLUMN IF EXISTS vector_store_connection_id")
    op.execute("ALTER TABLE agents DROP COLUMN IF EXISTS embedding_connection_id")
    op.execute("ALTER TABLE agents DROP COLUMN IF EXISTS llm_connection_id")
