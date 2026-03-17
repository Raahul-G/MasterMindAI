"""empty message

Revision ID: 2ebdc4031009
Revises: 20622dac37c3
Create Date: 2026-03-16 13:16:42.800209

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2ebdc4031009'
down_revision: Union[str, Sequence[str], None] = '20622dac37c3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
