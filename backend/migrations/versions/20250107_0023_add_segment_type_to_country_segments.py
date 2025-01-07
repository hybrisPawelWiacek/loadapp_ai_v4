"""add segment_type to country_segments

Revision ID: 20250107_0023
Revises: 20250106_2340
Create Date: 2025-01-07 00:23:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20250107_0023'
down_revision = '20250106_2340'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add segment_type column with default value 'route'
    op.add_column('country_segments', 
        sa.Column('segment_type', sa.String(20), nullable=False, server_default='route')
    )


def downgrade() -> None:
    # Remove the column
    op.drop_column('country_segments', 'segment_type') 