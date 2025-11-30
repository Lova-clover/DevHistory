"""add portfolio settings

Revision ID: 002
Revises: 001
Create Date: 2025-11-30

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade():
    # Add portfolio settings to user_profiles table
    op.add_column('user_profiles', sa.Column('portfolio_email', sa.String(), nullable=True))
    op.add_column('user_profiles', sa.Column('portfolio_name', sa.String(), nullable=True))
    op.add_column('user_profiles', sa.Column('portfolio_bio', sa.Text(), nullable=True))
    op.add_column('user_profiles', sa.Column('max_portfolio_repos', sa.Integer(), nullable=False, server_default='6'))


def downgrade():
    op.drop_column('user_profiles', 'max_portfolio_repos')
    op.drop_column('user_profiles', 'portfolio_bio')
    op.drop_column('user_profiles', 'portfolio_name')
    op.drop_column('user_profiles', 'portfolio_email')
