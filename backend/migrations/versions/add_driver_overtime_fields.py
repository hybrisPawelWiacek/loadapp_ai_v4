"""Add overtime fields to driver specifications.

Revision ID: add_driver_overtime_fields
Revises: 
Create Date: 2025-01-07 13:06:38.492

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_driver_overtime_fields'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Add max_driving_hours and overtime_rate_multiplier columns with default values
    op.add_column('driver_specifications',
                  sa.Column('max_driving_hours', sa.String(50), nullable=False, server_default="9"))
    op.add_column('driver_specifications',
                  sa.Column('overtime_rate_multiplier', sa.String(50), nullable=False, server_default="1.5"))


def downgrade():
    # Remove the columns
    op.drop_column('driver_specifications', 'max_driving_hours')
    op.drop_column('driver_specifications', 'overtime_rate_multiplier') 