"""Synchronize the users ID sequence with existing accounts.

Revision ID: 20260930_sync_users_seq
Revises: 20260930_add_auth
"""

from alembic import op

revision = "20260930_sync_users_seq"
down_revision = "20260930_add_auth"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        SELECT setval(
            pg_get_serial_sequence('users', 'id'),
            COALESCE(MAX(id), 1),
            MAX(id) IS NOT NULL
        )
        FROM users
        """
    )


def downgrade() -> None:
    pass
