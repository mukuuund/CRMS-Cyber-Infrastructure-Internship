"""Add missing ML columns to requirements

Revision ID: 63fad1fc3229
Revises: f6ad57c37b94
Create Date: 2026-07-08 16:24:46.050966

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '63fad1fc3229'
down_revision: Union[str, None] = 'f6ad57c37b94'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('requirements', sa.Column('ai_low_probability', sa.Float(), nullable=True))
    op.add_column('requirements', sa.Column('ai_medium_probability', sa.Float(), nullable=True))
    op.add_column('requirements', sa.Column('ai_high_probability', sa.Float(), nullable=True))
    op.add_column('requirements', sa.Column('effort_overridden', sa.Boolean(), server_default=sa.text('false'), nullable=False))


def downgrade() -> None:
    op.drop_column('requirements', 'effort_overridden')
    op.drop_column('requirements', 'ai_high_probability')
    op.drop_column('requirements', 'ai_medium_probability')
    op.drop_column('requirements', 'ai_low_probability')
