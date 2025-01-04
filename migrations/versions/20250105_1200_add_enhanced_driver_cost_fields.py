"""Add enhanced driver cost fields

Revision ID: add_enhanced_driver_cost_fields
Revises: c965c01129c3
Create Date: 2025-01-05 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from decimal import Decimal


# revision identifiers, used by Alembic.
revision = 'add_enhanced_driver_cost_fields'
down_revision = 'c965c01129c3'
branch_labels = None
depends_on = None


def upgrade():
    # Add new columns to driver_specifications table
    op.add_column('driver_specifications',
        sa.Column('driving_time_rate', sa.Numeric(10, 2), nullable=False, server_default='25.00')
    )
    op.add_column('driver_specifications',
        sa.Column('overtime_rate_multiplier', sa.Numeric(3, 2), nullable=False, server_default='1.50')
    )
    op.add_column('driver_specifications',
        sa.Column('max_driving_hours', sa.Integer, nullable=False, server_default='9')
    )


def downgrade():
    # Remove the new columns
    op.drop_column('driver_specifications', 'driving_time_rate')
    op.drop_column('driver_specifications', 'overtime_rate_multiplier')
    op.drop_column('driver_specifications', 'max_driving_hours') 