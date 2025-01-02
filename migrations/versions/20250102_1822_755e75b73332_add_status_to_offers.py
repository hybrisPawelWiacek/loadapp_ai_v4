"""add_status_to_offers

Revision ID: 755e75b73332
Revises: 19e0a6c12b96
Create Date: 2025-01-02 18:22:48.572955+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '755e75b73332'
down_revision: Union[str, None] = '19e0a6c12b96'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add status column to offers table
    op.add_column('offers',
                  sa.Column('status', sa.String(50), nullable=False, server_default='draft'))


def downgrade() -> None:
    # Remove status column from offers table
    op.drop_column('offers', 'status') 