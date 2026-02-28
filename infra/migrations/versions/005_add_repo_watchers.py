"""add watchers column to repos

Revision ID: 005
Revises: 004
Create Date: 2026-02-28

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "005"
down_revision = "004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("repos", sa.Column("watchers", sa.Integer(), nullable=False, server_default="0"))
    op.execute("UPDATE repos SET watchers = stars WHERE watchers = 0")


def downgrade() -> None:
    op.drop_column("repos", "watchers")
