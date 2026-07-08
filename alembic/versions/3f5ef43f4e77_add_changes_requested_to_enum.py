"""add_changes_requested_to_enum

Revision ID: 3f5ef43f4e77
Revises: 8d4bdf2ee71b
Create Date: 2026-07-06 17:19:21.059221

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3f5ef43f4e77'
down_revision: Union[str, None] = '8d4bdf2ee71b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Use autocommit isolation level because ALTER TYPE cannot run inside a transaction block in Postgres
    op.execute("ALTER TYPE requirementstatus ADD VALUE IF NOT EXISTS 'changes_requested'")


def downgrade() -> None:
    pass
