"""merge timestamp branch

Revision ID: 64018941537a
Revises: 20260307_merge_heads, 20260308_fix_message_timestamp
Create Date: 2026-03-06 01:03:29.462415

"""

from typing import Sequence, Union


# revision identifiers, used by Alembic.
revision: str = "64018941537a"
down_revision: Union[str, Sequence[str], None] = (
    "20260307_merge_heads",
    "20260308_fix_message_timestamp",
)
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
