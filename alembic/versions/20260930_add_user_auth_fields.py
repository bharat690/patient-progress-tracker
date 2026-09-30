"""Add authentication fields to users.

Revision ID: 20260930_add_auth
Revises:
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "20260930_add_auth"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    columns = {
        column["name"]
        for column in inspect(bind).get_columns("users")
    }

    if "password_hash" not in columns:
        op.add_column(
            "users",
            sa.Column("password_hash", sa.String(length=255), nullable=True),
        )
    if "is_active" not in columns:
        op.add_column(
            "users",
            sa.Column(
                "is_active",
                sa.Boolean(),
                nullable=False,
                server_default=sa.true(),
            ),
        )
    if "created_at" not in columns:
        op.add_column(
            "users",
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.func.now(),
            ),
        )


def downgrade() -> None:
    bind = op.get_bind()
    columns = {
        column["name"]
        for column in inspect(bind).get_columns("users")
    }

    for column_name in ("created_at", "is_active", "password_hash"):
        if column_name in columns:
            op.drop_column("users", column_name)
