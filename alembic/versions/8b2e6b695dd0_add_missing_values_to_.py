"""Add missing values to ChangeRequestStatus enum

Revision ID: 8b2e6b695dd0
Revises: abcaf40e49a9
Create Date: 2026-07-08 17:01:49.411684

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8b2e6b695dd0'
down_revision: Union[str, None] = 'abcaf40e49a9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add new values to ChangeRequestStatus enum
    if op.get_context().dialect.name == 'postgresql':
        op.execute("ALTER TYPE changerequeststatus ADD VALUE IF NOT EXISTS 'draft'")
        op.execute("ALTER TYPE changerequeststatus ADD VALUE IF NOT EXISTS 'submitted'")
        op.execute("ALTER TYPE changerequeststatus ADD VALUE IF NOT EXISTS 'completed'")


def downgrade() -> None:
    pass
