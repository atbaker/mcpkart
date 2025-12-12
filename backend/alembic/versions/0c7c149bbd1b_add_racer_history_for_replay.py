"""Add racer_history column for replay support

Revision ID: 0c7c149bbd1b
Revises: b3f84e836b3d
Create Date: 2025-12-11 22:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON


# revision identifiers, used by Alembic.
revision: str = '0c7c149bbd1b'
down_revision: Union[str, Sequence[str], None] = 'b3f84e836b3d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add racer_history JSON column to race_results table."""
    op.add_column('race_results', sa.Column('racer_history', JSON, nullable=True))


def downgrade() -> None:
    """Remove racer_history column."""
    op.drop_column('race_results', 'racer_history')
