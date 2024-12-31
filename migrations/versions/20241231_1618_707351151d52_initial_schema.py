"""initial_schema

Revision ID: 707351151d52
Revises: 
Create Date: 2024-12-31 16:18:48.572955+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision: str = '707351151d52'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create truck specifications table
    op.create_table(
        'truck_specifications',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('fuel_consumption_empty', sa.Float(), nullable=False),
        sa.Column('fuel_consumption_loaded', sa.Float(), nullable=False),
        sa.Column('toll_class', sa.String(50), nullable=False),
        sa.Column('euro_class', sa.String(50), nullable=False),
        sa.Column('co2_class', sa.String(50), nullable=False),
        sa.Column('maintenance_rate_per_km', sa.String(50), nullable=False)
    )

    # Create driver specifications table
    op.create_table(
        'driver_specifications',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('daily_rate', sa.String(50), nullable=False),
        sa.Column('required_license_type', sa.String(50), nullable=False),
        sa.Column('required_certifications', sqlite.JSON(), nullable=False)
    )

    # Create transport types table
    op.create_table(
        'transport_types',
        sa.Column('id', sa.String(50), primary_key=True),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('truck_specifications_id', sa.String(36),
                 sa.ForeignKey('truck_specifications.id'), nullable=False),
        sa.Column('driver_specifications_id', sa.String(36),
                 sa.ForeignKey('driver_specifications.id'), nullable=False)
    )

    # Create business entities table with all required fields
    op.create_table(
        'business_entities',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('address', sa.String(200), nullable=False),
        sa.Column('contact_info', sqlite.JSON(), nullable=False),
        sa.Column('business_type', sa.String(50), nullable=False),
        sa.Column('certifications', sqlite.JSON(), nullable=False),
        sa.Column('operating_countries', sqlite.JSON(), nullable=False),
        sa.Column('cost_overheads', sqlite.JSON(), nullable=False)
    )

    # Create transports table
    op.create_table(
        'transports',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('transport_type_id', sa.String(50),
                 sa.ForeignKey('transport_types.id'), nullable=False),
        sa.Column('business_entity_id', sa.String(36),
                 sa.ForeignKey('business_entities.id'), nullable=False),
        sa.Column('truck_specifications_id', sa.String(36),
                 sa.ForeignKey('truck_specifications.id'), nullable=False),
        sa.Column('driver_specifications_id', sa.String(36),
                 sa.ForeignKey('driver_specifications.id'), nullable=False),
        sa.Column('is_active', sa.Boolean(), default=True)
    )

    # Create cargos table
    op.create_table(
        'cargos',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('business_entity_id', sa.String(36),
                 sa.ForeignKey('business_entities.id'), nullable=False),
        sa.Column('weight', sa.Float(), nullable=False),
        sa.Column('volume', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('cargo_type', sa.String(50), nullable=False, server_default='general'),
        sa.Column('value', sa.String(50), nullable=False),
        sa.Column('special_requirements', sqlite.JSON(), nullable=False),
        sa.Column('status', sa.String(50), nullable=False, server_default='pending')
    )

    # Create locations table
    op.create_table(
        'locations',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('latitude', sa.Float(), nullable=False),
        sa.Column('longitude', sa.Float(), nullable=False),
        sa.Column('address', sa.String(500), nullable=False)
    )

    # Create empty drivings table
    op.create_table(
        'empty_drivings',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('distance_km', sa.Float(), nullable=False),
        sa.Column('duration_hours', sa.Float(), nullable=False)
    )

    # Create routes table
    op.create_table(
        'routes',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('transport_id', sa.String(36), sa.ForeignKey('transports.id'), nullable=False),
        sa.Column('business_entity_id', sa.String(36), sa.ForeignKey('business_entities.id'), nullable=False),
        sa.Column('cargo_id', sa.String(36), sa.ForeignKey('cargos.id'), nullable=False),
        sa.Column('origin_id', sa.String(36), sa.ForeignKey('locations.id'), nullable=False),
        sa.Column('destination_id', sa.String(36), sa.ForeignKey('locations.id'), nullable=False),
        sa.Column('pickup_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('delivery_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('empty_driving_id', sa.String(36), sa.ForeignKey('empty_drivings.id'), nullable=False),
        sa.Column('total_distance_km', sa.Float(), nullable=False),
        sa.Column('total_duration_hours', sa.Float(), nullable=False),
        sa.Column('is_feasible', sa.Boolean(), nullable=False, default=True)
    )

    # Create timeline events table
    op.create_table(
        'timeline_events',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('route_id', sa.String(36), sa.ForeignKey('routes.id'), nullable=False),
        sa.Column('type', sa.String(50), nullable=False),
        sa.Column('location_id', sa.String(36), sa.ForeignKey('locations.id'), nullable=False),
        sa.Column('planned_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('duration_hours', sa.Float(), nullable=False),
        sa.Column('event_order', sa.Integer(), nullable=False)
    )

    # Create country segments table
    op.create_table(
        'country_segments',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('route_id', sa.String(36), sa.ForeignKey('routes.id'), nullable=False),
        sa.Column('country_code', sa.String(2), nullable=False),
        sa.Column('distance_km', sa.Float(), nullable=False),
        sa.Column('duration_hours', sa.Float(), nullable=False),
        sa.Column('start_location_id', sa.String(36), sa.ForeignKey('locations.id'), nullable=False),
        sa.Column('end_location_id', sa.String(36), sa.ForeignKey('locations.id'), nullable=False)
    )

    # Create cost settings table
    op.create_table(
        'cost_settings',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('route_id', sa.String(36), sa.ForeignKey('routes.id'), nullable=False),
        sa.Column('business_entity_id', sa.String(36), sa.ForeignKey('business_entities.id'), nullable=False),
        sa.Column('enabled_components', sqlite.JSON(), nullable=False),
        sa.Column('rates', sqlite.JSON(), nullable=False)
    )

    # Create cost breakdowns table
    op.create_table(
        'cost_breakdowns',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('route_id', sa.String(36), sa.ForeignKey('routes.id'), nullable=False),
        sa.Column('fuel_costs', sqlite.JSON(), nullable=False),
        sa.Column('toll_costs', sqlite.JSON(), nullable=False),
        sa.Column('driver_costs', sa.String(50), nullable=False),
        sa.Column('overhead_costs', sa.String(50), nullable=False),
        sa.Column('timeline_event_costs', sqlite.JSON(), nullable=False),
        sa.Column('total_cost', sa.String(50), nullable=False)
    )

    # Create offers table
    op.create_table(
        'offers',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('route_id', sa.String(36), sa.ForeignKey('routes.id'), nullable=False),
        sa.Column('cost_breakdown_id', sa.String(36), sa.ForeignKey('cost_breakdowns.id'), nullable=False),
        sa.Column('margin_percentage', sa.String(50), nullable=False),
        sa.Column('final_price', sa.String(50), nullable=False),
        sa.Column('ai_content', sa.String(1000), nullable=True),
        sa.Column('fun_fact', sa.String(500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False)
    )


def downgrade() -> None:
    op.drop_table('offers')
    op.drop_table('cost_breakdowns')
    op.drop_table('cost_settings')
    op.drop_table('country_segments')
    op.drop_table('timeline_events')
    op.drop_table('routes')
    op.drop_table('empty_drivings')
    op.drop_table('locations')
    op.drop_table('cargos')
    op.drop_table('transports')
    op.drop_table('business_entities')
    op.drop_table('transport_types')
    op.drop_table('driver_specifications')
    op.drop_table('truck_specifications') 