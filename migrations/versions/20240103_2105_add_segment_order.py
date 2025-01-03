"""add segment order to country segments

Revision ID: 20240103_2105
Revises: 20241231_1618_707351151d52
Create Date: 2024-01-03 21:05:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20240103_2105'
down_revision = '20241231_1618_707351151d52'
branch_labels = None
depends_on = None


def upgrade():
    # Add segment_order column with default value 0
    op.add_column('country_segments', sa.Column('segment_order', sa.Integer(), nullable=False, server_default='0'))


def downgrade():
    # Remove segment_order column
    op.drop_column('country_segments', 'segment_order') 