"""add_overhead_rate_types

Revision ID: bcb9286cf0e4
Revises: 6708fd66e995
Create Date: 2025-01-07 16:02:32.016037+00:00

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from decimal import Decimal
import uuid


# revision identifiers, used by Alembic.
revision: str = 'bcb9286cf0e4'
down_revision: Union[str, None] = '6708fd66e995'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add overhead rate types to rate_validation_rules table
    overhead_rates = [
        {
            'id': str(uuid.uuid4()),
            'rate_type': 'overhead_admin_rate',
            'min_value': Decimal('0.01'),
            'max_value': Decimal('1000.0'),
            'country_specific': False,
            'requires_certification': False,
            'description': 'Administrative overhead costs per route'
        },
        {
            'id': str(uuid.uuid4()),
            'rate_type': 'overhead_insurance_rate',
            'min_value': Decimal('0.01'),
            'max_value': Decimal('1000.0'),
            'country_specific': False,
            'requires_certification': False,
            'description': 'Insurance overhead costs per route'
        },
        {
            'id': str(uuid.uuid4()),
            'rate_type': 'overhead_facilities_rate',
            'min_value': Decimal('0.01'),
            'max_value': Decimal('1000.0'),
            'country_specific': False,
            'requires_certification': False,
            'description': 'Facilities overhead costs per route'
        },
        {
            'id': str(uuid.uuid4()),
            'rate_type': 'overhead_other_rate',
            'min_value': Decimal('0.0'),
            'max_value': Decimal('1000.0'),
            'country_specific': False,
            'requires_certification': False,
            'description': 'Other overhead costs per route'
        }
    ]
    
    op.bulk_insert(sa.table('rate_validation_rules',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('rate_type', sa.String(50), nullable=False),
        sa.Column('min_value', sa.Numeric(10, 2), nullable=False),
        sa.Column('max_value', sa.Numeric(10, 2), nullable=False),
        sa.Column('country_specific', sa.Boolean, nullable=False),
        sa.Column('requires_certification', sa.Boolean, nullable=False),
        sa.Column('description', sa.String(200))
    ), overhead_rates)


def downgrade() -> None:
    # Remove overhead rate types from rate_validation_rules table
    op.execute("""
        DELETE FROM rate_validation_rules 
        WHERE rate_type IN (
            'overhead_admin_rate',
            'overhead_insurance_rate',
            'overhead_facilities_rate',
            'overhead_other_rate'
        )
    """)
