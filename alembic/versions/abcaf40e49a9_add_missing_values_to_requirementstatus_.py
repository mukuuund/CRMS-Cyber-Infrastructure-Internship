"""Add missing values to RequirementStatus enum

Revision ID: abcaf40e49a9
Revises: 63fad1fc3229
Create Date: 2026-07-08 16:48:03.137435

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'abcaf40e49a9'
down_revision: Union[str, None] = '63fad1fc3229'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add new values to RequirementStatus enum
    if op.get_context().dialect.name == 'postgresql':
        op.execute("ALTER TYPE requirementstatus ADD VALUE IF NOT EXISTS 'submitted'")
        op.execute("ALTER TYPE requirementstatus ADD VALUE IF NOT EXISTS 'rejected'")
        op.execute("ALTER TYPE requirementstatus ADD VALUE IF NOT EXISTS 'in_progress'")


def downgrade() -> None:
    # PostgreSQL does not support dropping enum values easily
    pass
