"""Update country segments table.

Revision ID: 20240103_1200
Revises: 20241231_1643_19e0a6c12b96
Create Date: 2024-01-03 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20240103_1200'
down_revision = '20241231_1643_19e0a6c12b96'
branch_labels = None
depends_on = None


def upgrade():
    # Drop existing foreign key constraint
    op.drop_constraint('country_segments_route_id_fkey', 'country_segments', type_='foreignkey')
    
    # Re-add foreign key constraint with cascade delete
    op.create_foreign_key(
        'country_segments_route_id_fkey',
        'country_segments', 'routes',
        ['route_id'], ['id'],
        ondelete='CASCADE'
    )


def downgrade():
    # Drop cascade delete foreign key constraint
    op.drop_constraint('country_segments_route_id_fkey', 'country_segments', type_='foreignkey')
    
    # Re-add original foreign key constraint
    op.create_foreign_key(
        'country_segments_route_id_fkey',
        'country_segments', 'routes',
        ['route_id'], ['id']
    ) 