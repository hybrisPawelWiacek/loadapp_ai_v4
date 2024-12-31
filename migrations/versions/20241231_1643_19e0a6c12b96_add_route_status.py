"""add route status

Revision ID: 19e0a6c12b96
Revises: 707351151d52
Create Date: 2024-12-31 16:43:19.123456

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '19e0a6c12b96'
down_revision: Union[str, None] = '707351151d52'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add status column with default value
    op.add_column('routes', sa.Column('status', sa.String(50), nullable=False, server_default='draft'))


def downgrade() -> None:
    # Remove status column
    op.drop_column('routes', 'status') 