"""add_route_status_history

Revision ID: 5a17d0dfa5e0
Revises: 1448c6a801cc
Create Date: 2025-01-04 09:36:42.123456

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5a17d0dfa5e0'
down_revision: Union[str, None] = '1448c6a801cc'
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