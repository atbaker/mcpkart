"""Use timezone-aware timestamps

Revision ID: b1c63f6819c9
Revises: 0c7c149bbd1b
Create Date: 2025-12-11 16:40:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b1c63f6819c9'
down_revision: Union[str, Sequence[str], None] = '0c7c149bbd1b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Convert datetime columns to timezone-aware (TIMESTAMP WITH TIME ZONE)."""
    # race_results table
    op.alter_column('race_results', 'started_at',
        type_=sa.DateTime(timezone=True),
        existing_type=sa.DateTime(),
        existing_nullable=False)
    op.alter_column('race_results', 'finished_at',
        type_=sa.DateTime(timezone=True),
        existing_type=sa.DateTime(),
        existing_nullable=False)

    # users table
    op.alter_column('users', 'created_at',
        type_=sa.DateTime(timezone=True),
        existing_type=sa.DateTime(),
        existing_nullable=False)
    op.alter_column('users', 'updated_at',
        type_=sa.DateTime(timezone=True),
        existing_type=sa.DateTime(),
        existing_nullable=False)


def downgrade() -> None:
    """Revert to timezone-naive timestamps."""
    # race_results table
    op.alter_column('race_results', 'started_at',
        type_=sa.DateTime(),
        existing_type=sa.DateTime(timezone=True),
        existing_nullable=False)
    op.alter_column('race_results', 'finished_at',
        type_=sa.DateTime(),
        existing_type=sa.DateTime(timezone=True),
        existing_nullable=False)

    # users table
    op.alter_column('users', 'created_at',
        type_=sa.DateTime(),
        existing_type=sa.DateTime(timezone=True),
        existing_nullable=False)
    op.alter_column('users', 'updated_at',
        type_=sa.DateTime(),
        existing_type=sa.DateTime(timezone=True),
        existing_nullable=False)
