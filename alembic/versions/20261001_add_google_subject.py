"""Add Google identity to users.

Revision ID: 20261001_google_auth
Revises: 20260930_sync_users_seq
"""

from alembic import op
import sqlalchemy as sa

revision = "20261001_google_auth"
down_revision = "20260930_sync_users_seq"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("google_subject", sa.String(length=255), nullable=True),
    )
    op.create_index(
        "ix_users_google_subject",
        "users",
        ["google_subject"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ix_users_google_subject", table_name="users")
    op.drop_column("users", "google_subject")
