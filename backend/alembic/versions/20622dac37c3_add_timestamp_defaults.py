"""add_timestamp_defaults

Revision ID: 20622dac37c3
Revises: a0c633b599ae
Create Date: 2026-03-09 23:26:30.726963

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20622dac37c3'
down_revision: Union[str, Sequence[str], None] = 'a0c633b599ae'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TABLE users ALTER COLUMN created_at SET DEFAULT now()")
    op.execute("ALTER TABLE users ALTER COLUMN updated_at SET DEFAULT now()")


def downgrade() -> None:
    op.execute("ALTER TABLE users ALTER COLUMN created_at DROP DEFAULT")
    op.execute("ALTER TABLE users ALTER COLUMN updated_at DROP DEFAULT")
