"""Add rate validation rules

Revision ID: add_rate_validation_rules
Revises: c965c01129c3
Create Date: 2025-01-05 12:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite


# revision identifiers, used by Alembic
revision = 'add_rate_validation_rules'
down_revision = 'c965c01129c3'
branch_labels = None
depends_on = None


def upgrade():
    # Create rate_validation_rules table
    op.create_table(
        'rate_validation_rules',
        sa.Column('id', sa.String(36), nullable=False),  # UUID as string for SQLite
        sa.Column('rate_type', sa.String(50), nullable=False),
        sa.Column('min_value', sa.Numeric(10, 2), nullable=False),
        sa.Column('max_value', sa.Numeric(10, 2), nullable=False),
        sa.Column('country_specific', sa.Boolean(), nullable=False),
        sa.Column('requires_certification', sa.Boolean(), nullable=False),
        sa.Column('description', sa.String(200)),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Add index on rate_type for faster lookups
    op.create_index(
        'ix_rate_validation_rules_rate_type',
        'rate_validation_rules',
        ['rate_type']
    )


def downgrade():
    # Remove index first
    op.drop_index('ix_rate_validation_rules_rate_type')
    
    # Drop the table
    op.drop_table('rate_validation_rules') 