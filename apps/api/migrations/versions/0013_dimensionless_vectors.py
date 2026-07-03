"""dimensionless embeddings: the user's own model decides the vector dimension

Revision ID: 0013_dimensionless_vectors
Revises: 0012_notifications
Create Date: 2026-07-03

Makes chunks.embedding a dimensionless pgvector column so a workspace's own
embedding model (brought via a Connection) determines the dimension. The fixed
HNSW index required a fixed dimension, so it is dropped — cosine search runs
exact; an operator can add an ANN index once their embedder's dim is known.
"""
from __future__ import annotations

from alembic import op

revision = "0013_dimensionless_vectors"
down_revision = "0012_notifications"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_chunks_embedding_hnsw")
    op.execute("ALTER TABLE chunks ALTER COLUMN embedding TYPE vector USING embedding::vector")


def downgrade() -> None:
    # Best-effort: restore a fixed dimension (defaults to 1536) + the HNSW index.
    op.execute(
        "ALTER TABLE chunks ALTER COLUMN embedding "
        "TYPE vector(1536) USING embedding::vector(1536)"
    )
    op.execute(
        "CREATE INDEX ix_chunks_embedding_hnsw ON chunks "
        "USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64)"
    )
