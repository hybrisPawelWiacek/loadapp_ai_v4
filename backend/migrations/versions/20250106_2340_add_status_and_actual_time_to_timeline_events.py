"""add status and actual_time to timeline events

Revision ID: 20250106_2340
Revises: 20250106_2203_23f1a3b2f42e
Create Date: 2025-01-06 23:40:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20250106_2340'
down_revision = '20250106_2203_23f1a3b2f42e'
branch_labels = None
depends_on = None


def upgrade():
    # Add status and actual_time columns to timeline_events table
    op.add_column('timeline_events',
        sa.Column('status', sa.String(50), nullable=False, server_default='pending')
    )
    op.add_column('timeline_events',
        sa.Column('actual_time', sa.DateTime(timezone=True), nullable=True)
    )


def downgrade():
    # Remove the columns
    op.drop_column('timeline_events', 'actual_time')
    op.drop_column('timeline_events', 'status') 