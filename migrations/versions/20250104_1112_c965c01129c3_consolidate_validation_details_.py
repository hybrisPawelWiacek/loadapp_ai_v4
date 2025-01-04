"""consolidate_validation_details_migrations

Revision ID: c965c01129c3
Revises: 2535a8ec0e25
Create Date: 2025-01-04 11:12:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision: str = 'c965c01129c3'
down_revision: Union[str, None] = '2535a8ec0e25'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Consolidate all validation details changes
    with op.batch_alter_table('routes') as batch_op:
        # Make validation_details not nullable with default empty dict
        batch_op.alter_column('validation_details',
                            existing_type=sqlite.JSON(),
                            nullable=False,
                            server_default=sa.text("'{}'"))
        
        # Add validation flags
        batch_op.alter_column('certifications_validated',
                            existing_type=sa.Boolean(),
                            nullable=False,
                            server_default=sa.text('0'))
        batch_op.alter_column('operating_countries_validated',
                            existing_type=sa.Boolean(),
                            nullable=False,
                            server_default=sa.text('0'))


def downgrade() -> None:
    # Revert validation details changes
    with op.batch_alter_table('routes') as batch_op:
        # Make validation_details nullable again
        batch_op.alter_column('validation_details',
                            existing_type=sqlite.JSON(),
                            nullable=True,
                            server_default=None)
        
        # Make validation flags nullable
        batch_op.alter_column('certifications_validated',
                            existing_type=sa.Boolean(),
                            nullable=True,
                            server_default=None)
        batch_op.alter_column('operating_countries_validated',
                            existing_type=sa.Boolean(),
                            nullable=True,
                            server_default=None) 