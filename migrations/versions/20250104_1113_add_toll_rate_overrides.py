"""Add toll rate overrides

Revision ID: c965c01129c4
Create Date: 2025-01-04 11:13:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite


# revision identifiers, used by Alembic
revision = 'c965c01129c4'
down_revision = 'c965c01129c3'
branch_labels = None
depends_on = None


def upgrade():
    # Create toll_rate_overrides table
    op.create_table(
        'toll_rate_overrides',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('vehicle_class', sa.String(50), nullable=False),
        sa.Column('rate_multiplier', sa.Numeric(3, 2), nullable=False),
        sa.Column('country_code', sa.String(2), nullable=False),
        sa.Column('route_type', sa.String(50)),
        sa.Column('business_entity_id', sa.String(36), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['business_entity_id'], ['business_entities.id'], ),
        sa.CheckConstraint('rate_multiplier > 0', name='toll_rate_multiplier_positive')
    )
    
    # Create index for faster lookups
    op.create_index(
        'ix_toll_rate_overrides_lookup',
        'toll_rate_overrides',
        ['country_code', 'vehicle_class', 'business_entity_id']
    )


def downgrade():
    op.drop_index('ix_toll_rate_overrides_lookup')
    op.drop_table('toll_rate_overrides') 