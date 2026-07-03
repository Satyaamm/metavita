"""user profile fields: first/last name, phone, company

Revision ID: 0016_user_profile
Revises: 0015_password_resets
Create Date: 2026-07-03
"""
from __future__ import annotations

from alembic import op

revision = "0016_user_profile"
down_revision = "0015_password_resets"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE users ADD COLUMN first_name VARCHAR(128)")
    op.execute("ALTER TABLE users ADD COLUMN last_name VARCHAR(128)")
    op.execute("ALTER TABLE users ADD COLUMN phone VARCHAR(32)")
    op.execute("ALTER TABLE users ADD COLUMN company VARCHAR(256)")


def downgrade() -> None:
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS first_name")
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS last_name")
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS phone")
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS company")
