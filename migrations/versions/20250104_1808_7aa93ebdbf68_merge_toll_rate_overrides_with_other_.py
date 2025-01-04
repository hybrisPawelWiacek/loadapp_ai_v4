"""merge toll_rate_overrides with other heads

Revision ID: 7aa93ebdbf68
Revises: c965c01129c4, add_enhanced_driver_cost_fields, add_rate_validation_rules
Create Date: 2025-01-04 18:08:29.442913+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7aa93ebdbf68'
down_revision: Union[str, None] = ('c965c01129c4', 'add_enhanced_driver_cost_fields', 'add_rate_validation_rules')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass 