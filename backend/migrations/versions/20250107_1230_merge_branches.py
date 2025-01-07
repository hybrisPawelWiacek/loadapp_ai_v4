"""Merge country segments and driver overtime branches.

Revision ID: 20250107_1230
Revises: 20250107_0023, add_driver_overtime_fields
Create Date: 2025-01-07 12:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20250107_1230'
down_revision = None
branch_labels = None
depends_on = ('20250107_0023', 'add_driver_overtime_fields')


def upgrade():
    pass


def downgrade():
    pass 