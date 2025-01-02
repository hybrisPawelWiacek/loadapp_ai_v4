"""add_timestamps_and_active_flags

Revision ID: 7b315ad0519b
Revises: 19e0a6c12b96
Create Date: 2025-01-02 17:41:31.487115+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision: str = '7b315ad0519b'
down_revision: Union[str, None] = '19e0a6c12b96'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('truck_specifications')
    op.drop_table('routes')
    op.drop_table('transport_types')
    op.drop_table('locations')
    op.drop_table('cargos')
    op.drop_table('cost_breakdowns')
    op.drop_table('driver_specifications')
    op.drop_table('offers')
    op.drop_table('empty_drivings')
    op.drop_table('business_entities')
    op.drop_table('country_segments')
    op.drop_table('transports')
    op.drop_table('cost_settings')
    op.drop_table('timeline_events')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('timeline_events',
    sa.Column('id', sa.VARCHAR(length=36), nullable=False),
    sa.Column('route_id', sa.VARCHAR(length=36), nullable=False),
    sa.Column('type', sa.VARCHAR(length=50), nullable=False),
    sa.Column('location_id', sa.VARCHAR(length=36), nullable=False),
    sa.Column('planned_time', sa.DATETIME(), nullable=False),
    sa.Column('duration_hours', sa.FLOAT(), nullable=False),
    sa.Column('event_order', sa.INTEGER(), nullable=False),
    sa.ForeignKeyConstraint(['location_id'], ['locations.id'], ),
    sa.ForeignKeyConstraint(['route_id'], ['routes.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('cost_settings',
    sa.Column('id', sa.VARCHAR(length=36), nullable=False),
    sa.Column('route_id', sa.VARCHAR(length=36), nullable=False),
    sa.Column('business_entity_id', sa.VARCHAR(length=36), nullable=False),
    sa.Column('enabled_components', sqlite.JSON(), nullable=False),
    sa.Column('rates', sqlite.JSON(), nullable=False),
    sa.ForeignKeyConstraint(['business_entity_id'], ['business_entities.id'], ),
    sa.ForeignKeyConstraint(['route_id'], ['routes.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('transports',
    sa.Column('id', sa.VARCHAR(length=36), nullable=False),
    sa.Column('transport_type_id', sa.VARCHAR(length=50), nullable=False),
    sa.Column('business_entity_id', sa.VARCHAR(length=36), nullable=False),
    sa.Column('truck_specifications_id', sa.VARCHAR(length=36), nullable=False),
    sa.Column('driver_specifications_id', sa.VARCHAR(length=36), nullable=False),
    sa.Column('is_active', sa.BOOLEAN(), nullable=True),
    sa.ForeignKeyConstraint(['business_entity_id'], ['business_entities.id'], ),
    sa.ForeignKeyConstraint(['driver_specifications_id'], ['driver_specifications.id'], ),
    sa.ForeignKeyConstraint(['transport_type_id'], ['transport_types.id'], ),
    sa.ForeignKeyConstraint(['truck_specifications_id'], ['truck_specifications.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('country_segments',
    sa.Column('id', sa.VARCHAR(length=36), nullable=False),
    sa.Column('route_id', sa.VARCHAR(length=36), nullable=False),
    sa.Column('country_code', sa.VARCHAR(length=2), nullable=False),
    sa.Column('distance_km', sa.FLOAT(), nullable=False),
    sa.Column('duration_hours', sa.FLOAT(), nullable=False),
    sa.Column('start_location_id', sa.VARCHAR(length=36), nullable=False),
    sa.Column('end_location_id', sa.VARCHAR(length=36), nullable=False),
    sa.ForeignKeyConstraint(['end_location_id'], ['locations.id'], ),
    sa.ForeignKeyConstraint(['route_id'], ['routes.id'], ),
    sa.ForeignKeyConstraint(['start_location_id'], ['locations.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('business_entities',
    sa.Column('id', sa.VARCHAR(length=36), nullable=False),
    sa.Column('name', sa.VARCHAR(length=200), nullable=False),
    sa.Column('address', sa.VARCHAR(length=200), nullable=False),
    sa.Column('contact_info', sqlite.JSON(), nullable=False),
    sa.Column('business_type', sa.VARCHAR(length=50), nullable=False),
    sa.Column('certifications', sqlite.JSON(), nullable=False),
    sa.Column('operating_countries', sqlite.JSON(), nullable=False),
    sa.Column('cost_overheads', sqlite.JSON(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('empty_drivings',
    sa.Column('id', sa.VARCHAR(length=36), nullable=False),
    sa.Column('distance_km', sa.FLOAT(), nullable=False),
    sa.Column('duration_hours', sa.FLOAT(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('offers',
    sa.Column('id', sa.VARCHAR(length=36), nullable=False),
    sa.Column('route_id', sa.VARCHAR(length=36), nullable=False),
    sa.Column('cost_breakdown_id', sa.VARCHAR(length=36), nullable=False),
    sa.Column('margin_percentage', sa.VARCHAR(length=50), nullable=False),
    sa.Column('final_price', sa.VARCHAR(length=50), nullable=False),
    sa.Column('ai_content', sa.VARCHAR(length=1000), nullable=True),
    sa.Column('fun_fact', sa.VARCHAR(length=500), nullable=True),
    sa.Column('created_at', sa.DATETIME(), nullable=False),
    sa.ForeignKeyConstraint(['cost_breakdown_id'], ['cost_breakdowns.id'], ),
    sa.ForeignKeyConstraint(['route_id'], ['routes.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('driver_specifications',
    sa.Column('id', sa.VARCHAR(length=36), nullable=False),
    sa.Column('daily_rate', sa.VARCHAR(length=50), nullable=False),
    sa.Column('required_license_type', sa.VARCHAR(length=50), nullable=False),
    sa.Column('required_certifications', sqlite.JSON(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('cost_breakdowns',
    sa.Column('id', sa.VARCHAR(length=36), nullable=False),
    sa.Column('route_id', sa.VARCHAR(length=36), nullable=False),
    sa.Column('fuel_costs', sqlite.JSON(), nullable=False),
    sa.Column('toll_costs', sqlite.JSON(), nullable=False),
    sa.Column('driver_costs', sa.VARCHAR(length=50), nullable=False),
    sa.Column('overhead_costs', sa.VARCHAR(length=50), nullable=False),
    sa.Column('timeline_event_costs', sqlite.JSON(), nullable=False),
    sa.Column('total_cost', sa.VARCHAR(length=50), nullable=False),
    sa.ForeignKeyConstraint(['route_id'], ['routes.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('cargos',
    sa.Column('id', sa.VARCHAR(length=36), nullable=False),
    sa.Column('business_entity_id', sa.VARCHAR(length=36), nullable=False),
    sa.Column('weight', sa.FLOAT(), nullable=False),
    sa.Column('volume', sa.FLOAT(), server_default=sa.text("'0.0'"), nullable=False),
    sa.Column('cargo_type', sa.VARCHAR(length=50), server_default=sa.text("'general'"), nullable=False),
    sa.Column('value', sa.VARCHAR(length=50), nullable=False),
    sa.Column('special_requirements', sqlite.JSON(), nullable=False),
    sa.Column('status', sa.VARCHAR(length=50), server_default=sa.text("'pending'"), nullable=False),
    sa.ForeignKeyConstraint(['business_entity_id'], ['business_entities.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('locations',
    sa.Column('id', sa.VARCHAR(length=36), nullable=False),
    sa.Column('latitude', sa.FLOAT(), nullable=False),
    sa.Column('longitude', sa.FLOAT(), nullable=False),
    sa.Column('address', sa.VARCHAR(length=500), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('transport_types',
    sa.Column('id', sa.VARCHAR(length=50), nullable=False),
    sa.Column('name', sa.VARCHAR(length=100), nullable=False),
    sa.Column('truck_specifications_id', sa.VARCHAR(length=36), nullable=False),
    sa.Column('driver_specifications_id', sa.VARCHAR(length=36), nullable=False),
    sa.ForeignKeyConstraint(['driver_specifications_id'], ['driver_specifications.id'], ),
    sa.ForeignKeyConstraint(['truck_specifications_id'], ['truck_specifications.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('routes',
    sa.Column('id', sa.VARCHAR(length=36), nullable=False),
    sa.Column('transport_id', sa.VARCHAR(length=36), nullable=False),
    sa.Column('business_entity_id', sa.VARCHAR(length=36), nullable=False),
    sa.Column('cargo_id', sa.VARCHAR(length=36), nullable=False),
    sa.Column('origin_id', sa.VARCHAR(length=36), nullable=False),
    sa.Column('destination_id', sa.VARCHAR(length=36), nullable=False),
    sa.Column('pickup_time', sa.DATETIME(), nullable=False),
    sa.Column('delivery_time', sa.DATETIME(), nullable=False),
    sa.Column('empty_driving_id', sa.VARCHAR(length=36), nullable=False),
    sa.Column('total_distance_km', sa.FLOAT(), nullable=False),
    sa.Column('total_duration_hours', sa.FLOAT(), nullable=False),
    sa.Column('is_feasible', sa.BOOLEAN(), nullable=False),
    sa.Column('status', sa.VARCHAR(length=50), server_default=sa.text("'draft'"), nullable=False),
    sa.ForeignKeyConstraint(['business_entity_id'], ['business_entities.id'], ),
    sa.ForeignKeyConstraint(['cargo_id'], ['cargos.id'], ),
    sa.ForeignKeyConstraint(['destination_id'], ['locations.id'], ),
    sa.ForeignKeyConstraint(['empty_driving_id'], ['empty_drivings.id'], ),
    sa.ForeignKeyConstraint(['origin_id'], ['locations.id'], ),
    sa.ForeignKeyConstraint(['transport_id'], ['transports.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('truck_specifications',
    sa.Column('id', sa.VARCHAR(length=36), nullable=False),
    sa.Column('fuel_consumption_empty', sa.FLOAT(), nullable=False),
    sa.Column('fuel_consumption_loaded', sa.FLOAT(), nullable=False),
    sa.Column('toll_class', sa.VARCHAR(length=50), nullable=False),
    sa.Column('euro_class', sa.VARCHAR(length=50), nullable=False),
    sa.Column('co2_class', sa.VARCHAR(length=50), nullable=False),
    sa.Column('maintenance_rate_per_km', sa.VARCHAR(length=50), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ### 