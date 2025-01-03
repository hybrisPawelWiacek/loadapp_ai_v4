"""merge heads

Revision ID: 20250103_1202
Revises: 20250103_1112_d974fa1a23d9, 20250103_1201
Create Date: 2024-01-03 12:02:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20250103_1202'
down_revision = None
branch_labels = None
depends_on = None

# Multiple revisions being merged
revisions = ['20250103_1112_d974fa1a23d9', '20250103_1201']


def upgrade():
    pass


def downgrade():
    pass 