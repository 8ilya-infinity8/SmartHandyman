"""ensure messages.created_at has server default

Revision ID: 20260308_fix_message_timestamp
Revises: 20260307_chat_ts_default
Create Date: 2026-03-08 00:00:00.000000
"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "20260308_fix_message_timestamp"
down_revision = "20260307_chat_ts_default"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    # fix any existing null timestamp
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
        "messages",
        "created_at",
        existing_type=sa.DateTime(timezone=True),
        server_default=sa.func.now(),
        nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        "messages",
        "created_at",
        existing_type=sa.DateTime(timezone=True),
        server_default=None,
        nullable=False,
    )
