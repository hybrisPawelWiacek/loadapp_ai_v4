"""add finalized_at to offers

Revision ID: 20250103_1201
Revises: 20250103_1112_d974fa1a23d9
Create Date: 2024-01-03 12:01:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20250103_1201'
down_revision = '20250103_1112_d974fa1a23d9'
branch_labels = None
depends_on = None


def upgrade():
    # Add finalized_at column to offers table
    op.add_column('offers',
        sa.Column('finalized_at', sa.DateTime(timezone=True), nullable=True)
    )


def downgrade():
    # Remove finalized_at column from offers table
    op.drop_column('offers', 'finalized_at') 