"""add server defaults for chat timestamps

Revision ID: 20260307_add_chat_timestamps_default
Revises: 59edb9b4cb48
Create Date: 2026-03-06 12:00:00.000000
"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "20260307_add_chat_timestamps_default"
down_revision = "59edb9b4cb48"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # fill any existing nulls just in case and then set server defaults
    conn = op.get_bind()
    conn.execute(
        sa.text(
            """
        UPDATE chats
        SET
            created_at = COALESCE(created_at, now()),
            updated_at = COALESCE(updated_at, now())
        WHERE created_at IS NULL OR updated_at IS NULL;
        """
        )
    )
    # also fix messages table
    conn.execute(
        sa.text(
            """
        UPDATE messages
        SET created_at = COALESCE(created_at, now())
        WHERE created_at IS NULL;
        """
        )
    )
    op.alter_column(
        "chats",
        "created_at",
        existing_type=sa.DateTime(timezone=True),
        server_default=sa.func.now(),
        nullable=False,
    )
    op.alter_column(
        "chats",
        "updated_at",
        existing_type=sa.DateTime(timezone=True),
        server_default=sa.func.now(),
        nullable=False,
    )
    op.alter_column(
        "messages",
        "created_at",
        existing_type=sa.DateTime(timezone=True),
        server_default=sa.func.now(),
        nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        "chats",
        "updated_at",
        existing_type=sa.DateTime(timezone=True),
        server_default=None,
        nullable=False,
    )
    op.alter_column(
        "chats",
        "created_at",
        existing_type=sa.DateTime(timezone=True),
        server_default=None,
        nullable=False,
    )
    op.alter_column(
        "messages",
        "created_at",
        existing_type=sa.DateTime(timezone=True),
        server_default=None,
        nullable=False,
    )
