"""add learned style prompt to style_profiles

Revision ID: 004
Revises: 003
Create Date: 2026-02-28

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('style_profiles', sa.Column('learned_style_prompt', sa.Text(), nullable=True))
    op.add_column('style_profiles', sa.Column('learned_at', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column('style_profiles', 'learned_at')
    op.drop_column('style_profiles', 'learned_style_prompt')
