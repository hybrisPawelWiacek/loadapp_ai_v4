"""merge_heads

Revision ID: a0e79ffbf702
Revises: 59c0a7115643, 755e75b73332
Create Date: 2025-01-03 11:12:05.765829+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a0e79ffbf702'
down_revision: Union[str, None] = ('59c0a7115643', '755e75b73332')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass 