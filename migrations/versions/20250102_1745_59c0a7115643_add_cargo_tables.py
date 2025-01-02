"""add_cargo_tables

Revision ID: 59c0a7115643
Revises: 9bdd9ba54025
Create Date: 2025-01-02 17:45:05.927393+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '59c0a7115643'
down_revision: Union[str, None] = '9bdd9ba54025'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create cost_settings table if it doesn't exist
    if not op.get_bind().dialect.has_table(op.get_bind(), 'cost_settings'):
        op.create_table(
            'cost_settings',
            sa.Column('id', sa.String(36), primary_key=True),
            sa.Column('route_id', sa.String(36), sa.ForeignKey('routes.id')),
            sa.Column('business_entity_id', sa.String(36), sa.ForeignKey('business_entities.id')),
            sa.Column('enabled_components', sa.JSON, nullable=False),
            sa.Column('rates', sa.JSON, nullable=False)
        )

    # Create cost_breakdowns table if it doesn't exist
    if not op.get_bind().dialect.has_table(op.get_bind(), 'cost_breakdowns'):
        op.create_table(
            'cost_breakdowns',
            sa.Column('id', sa.String(36), primary_key=True),
            sa.Column('route_id', sa.String(36), sa.ForeignKey('routes.id')),
            sa.Column('fuel_costs', sa.JSON, nullable=False),
            sa.Column('toll_costs', sa.JSON, nullable=False),
            sa.Column('driver_costs', sa.String(50), nullable=False),
            sa.Column('overhead_costs', sa.String(50), nullable=False),
            sa.Column('timeline_event_costs', sa.JSON, nullable=False),
            sa.Column('total_cost', sa.String(50), nullable=False)
        )

    # Create offers table if it doesn't exist
    if not op.get_bind().dialect.has_table(op.get_bind(), 'offers'):
        op.create_table(
            'offers',
            sa.Column('id', sa.String(36), primary_key=True),
            sa.Column('route_id', sa.String(36), sa.ForeignKey('routes.id')),
            sa.Column('cost_breakdown_id', sa.String(36), sa.ForeignKey('cost_breakdowns.id')),
            sa.Column('margin_percentage', sa.String(50), nullable=False),
            sa.Column('final_price', sa.String(50), nullable=False),
            sa.Column('ai_content', sa.String(1000), nullable=True),
            sa.Column('fun_fact', sa.String(500), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False)
        )


def downgrade() -> None:
    # Drop tables in reverse order
    if op.get_bind().dialect.has_table(op.get_bind(), 'offers'):
        op.drop_table('offers')
    if op.get_bind().dialect.has_table(op.get_bind(), 'cost_breakdowns'):
        op.drop_table('cost_breakdowns')
    if op.get_bind().dialect.has_table(op.get_bind(), 'cost_settings'):
        op.drop_table('cost_settings') 