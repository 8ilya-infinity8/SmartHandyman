"""merge chat and username revisions

Revision ID: 20260307_merge_heads
Revises: 59edb9b4cb48, 20260306_username_nonempty
Create Date: 2026-03-07 00:00:00.000000
"""

# revision identifiers, used by Alembic.
revision = "20260307_merge_heads"
down_revision = ("59edb9b4cb48", "20260306_username_nonempty")
branch_labels = None
depends_on = None


def upgrade() -> None:
    # no schema changes; this is a pure merge revision
    pass


def downgrade() -> None:
    # downgrading from a merge usually isn't necessary; just revert to
    # the two parent branches individually.
    pass
