"""add_route_status_history

Revision ID: 2535a8ec0e25
Revises: 9fbf8cacaea5
Create Date: 2025-01-04 09:55:00.866722+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2535a8ec0e25'
down_revision: Union[str, None] = '9fbf8cacaea5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'route_status_history',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('route_id', sa.String(36), sa.ForeignKey('routes.id'), nullable=False),
        sa.Column('status', sa.String(50), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('comment', sa.String(500), nullable=True),
    )
    op.create_index(
        'ix_route_status_history_route_id',
        'route_status_history',
        ['route_id']
    )
    op.create_index(
        'ix_route_status_history_timestamp',
        'route_status_history',
        ['timestamp']
    )


def downgrade() -> None:
    op.drop_index('ix_route_status_history_timestamp')
    op.drop_index('ix_route_status_history_route_id')
    op.drop_table('route_status_history') 