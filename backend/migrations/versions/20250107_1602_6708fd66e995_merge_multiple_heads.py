"""merge_multiple_heads

Revision ID: 6708fd66e995
Revises: 20250107_0023, 20250107_1230, add_driver_overtime_fields
Create Date: 2025-01-07 16:02:25.259948+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6708fd66e995'
down_revision: Union[str, None] = ('20250107_0023', '20250107_1230', 'add_driver_overtime_fields')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
