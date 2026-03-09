"""populate missing usernames and enforce nonempty constraint

Revision ID: 20260306_username_nonempty
Revises: b347a0a3b88e
Create Date: 2026-03-06 00:00:00.000000
"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "20260306_username_nonempty"
down_revision = "b347a0a3b88e"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Upgrade schema: fill blank usernames and add a check constraint."""
    conn = op.get_bind()
    # generate a random username for any existing records that would violate
    # the nonempty rule; using PostgreSQL functions for randomness.
    conn.execute(
        sa.text(
            """
        UPDATE users
        SET username = 'user_' || substring(md5(random()::text),1,8)
        WHERE username IS NULL OR username = '';
        """
        )
    )
    # add a check constraint so that empty strings can never be inserted again
    op.create_check_constraint(
        "username_nonempty",
        "users",
        "char_length(username) > 0",
    )


def downgrade() -> None:
    """Drop the nonempty constraint; data remains altered."""
    op.drop_constraint("username_nonempty", "users", type_="check")
