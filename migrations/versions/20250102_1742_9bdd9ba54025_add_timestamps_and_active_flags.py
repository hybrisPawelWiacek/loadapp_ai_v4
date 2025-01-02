"""add_timestamps_and_active_flags

Revision ID: 9bdd9ba54025
Revises: 7b315ad0519b
Create Date: 2025-01-02 17:42:42.487115+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector


# revision identifiers, used by Alembic.
revision: str = '9bdd9ba54025'
down_revision: Union[str, None] = '7b315ad0519b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def has_column(table_name: str, column_name: str) -> bool:
    """Check if a column exists in a table."""
    inspector = Inspector.from_engine(op.get_bind())
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    return column_name in columns


def upgrade() -> None:
    # Create cargos table if it doesn't exist
    if not op.get_bind().dialect.has_table(op.get_bind(), 'cargos'):
        op.create_table(
            'cargos',
            sa.Column('id', sa.String(36), primary_key=True),
            sa.Column('business_entity_id', sa.String(36), sa.ForeignKey('business_entities.id')),
            sa.Column('weight', sa.Float, nullable=False),
            sa.Column('volume', sa.Float, nullable=False, default=0.0),
            sa.Column('cargo_type', sa.String(50), nullable=False, default='general'),
            sa.Column('value', sa.String(50), nullable=False),
            sa.Column('special_requirements', sa.JSON, nullable=False),
            sa.Column('status', sa.String(50), nullable=False, default='pending'),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('is_active', sa.Boolean, nullable=False, default=True)
        )

    # Add columns to business_entities if they don't exist
    if not has_column('business_entities', 'is_active'):
        op.add_column('business_entities', sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'))

    # Add columns to routes if they don't exist
    if not has_column('routes', 'created_at'):
        op.add_column('routes', sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')))
    if not has_column('routes', 'updated_at'):
        op.add_column('routes', sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True))
    if not has_column('routes', 'is_active'):
        op.add_column('routes', sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'))

    # Add columns to transports if they don't exist
    if not has_column('transports', 'created_at'):
        op.add_column('transports', sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')))
    if not has_column('transports', 'updated_at'):
        op.add_column('transports', sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True))

    # Add columns to offers if they don't exist
    if not has_column('offers', 'updated_at'):
        op.add_column('offers', sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True))
    if not has_column('offers', 'is_active'):
        op.add_column('offers', sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'))


def downgrade() -> None:
    # Remove columns from business_entities
    if has_column('business_entities', 'is_active'):
        op.drop_column('business_entities', 'is_active')

    # Remove columns from routes
    if has_column('routes', 'created_at'):
        op.drop_column('routes', 'created_at')
    if has_column('routes', 'updated_at'):
        op.drop_column('routes', 'updated_at')
    if has_column('routes', 'is_active'):
        op.drop_column('routes', 'is_active')

    # Remove columns from transports
    if has_column('transports', 'created_at'):
        op.drop_column('transports', 'created_at')
    if has_column('transports', 'updated_at'):
        op.drop_column('transports', 'updated_at')

    # Remove columns from offers
    if has_column('offers', 'updated_at'):
        op.drop_column('offers', 'updated_at')
    if has_column('offers', 'is_active'):
        op.drop_column('offers', 'is_active') 