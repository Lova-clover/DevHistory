"""production schema v2

- users: add github_username, is_admin
- user_profiles: add public_slug, portfolio_public, portfolio_show_email, share_token, share_token_expires_at, public_updated_at
- generated_contents: rename type→content_type, content_metadata→metadata, add status/error_message/updated_at/started_at/completed_at/generation_seconds
- new table: llm_credentials
- new table: analytics_events

Revision ID: 003
Revises: 002
Create Date: 2026-02-27

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── users ──────────────────────────────────────────────
    op.add_column('users', sa.Column('github_username', sa.String(), nullable=True))
    op.add_column('users', sa.Column('is_admin', sa.Boolean(), nullable=False, server_default='false'))
    op.create_index(op.f('ix_users_github_username'), 'users', ['github_username'], unique=True)

    # ── user_profiles (share fields) ──────────────────────
    op.add_column('user_profiles', sa.Column('public_slug', sa.String(), nullable=True))
    op.add_column('user_profiles', sa.Column('portfolio_public', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('user_profiles', sa.Column('portfolio_show_email', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('user_profiles', sa.Column('share_token', sa.String(), nullable=True))
    op.add_column('user_profiles', sa.Column('share_token_expires_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('user_profiles', sa.Column('public_updated_at', sa.DateTime(timezone=True), nullable=True))
    op.create_index(op.f('ix_user_profiles_public_slug'), 'user_profiles', ['public_slug'], unique=True)
    op.create_index(op.f('ix_user_profiles_share_token'), 'user_profiles', ['share_token'], unique=True)

    # ── generated_contents (unify schema) ─────────────────
    # Rename 'type' → 'content_type'
    op.alter_column('generated_contents', 'type', new_column_name='content_type')
    # Rename 'content_metadata' → 'metadata' (original migration used 'metadata', model had 'content_metadata')
    # Check if content_metadata exists; in migration 001, the column was named 'metadata'.
    # The ORM model had Column named 'content_metadata' but DB column is 'metadata'.
    # Since DB column is already 'metadata' from migration 001, we only need to add new columns.
    op.add_column('generated_contents', sa.Column('status', sa.String(), nullable=False, server_default='completed'))
    op.add_column('generated_contents', sa.Column('error_message', sa.Text(), nullable=True))
    op.add_column('generated_contents', sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('generated_contents', sa.Column('started_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('generated_contents', sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('generated_contents', sa.Column('generation_seconds', sa.Float(), nullable=True))
    # Backfill updated_at = created_at for existing rows
    op.execute("UPDATE generated_contents SET updated_at = created_at WHERE updated_at IS NULL")

    # ── llm_credentials ───────────────────────────────────
    op.create_table(
        'llm_credentials',
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('provider', sa.String(), nullable=False, server_default='openai'),
        sa.Column('encrypted_api_key', sa.Text(), nullable=False),
        sa.Column('key_last4', sa.String(4), nullable=False),
        sa.Column('model', sa.String(), nullable=False, server_default='gpt-4o-mini'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('last_verified_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('user_id'),
    )

    # ── analytics_events ──────────────────────────────────
    op.create_table(
        'analytics_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('event_name', sa.String(), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('session_id', sa.String(), nullable=True),
        sa.Column('path', sa.String(), nullable=True),
        sa.Column('referrer', sa.String(), nullable=True),
        sa.Column('user_agent', sa.String(), nullable=True),
        sa.Column('ip_hash', sa.String(), nullable=True),
        sa.Column('meta', postgresql.JSONB(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_analytics_events_created_at', 'analytics_events', ['created_at'])
    op.create_index('ix_analytics_events_event_name', 'analytics_events', ['event_name'])
    op.create_index('ix_analytics_events_user_id', 'analytics_events', ['user_id'])


def downgrade() -> None:
    op.drop_table('analytics_events')
    op.drop_table('llm_credentials')

    op.drop_column('generated_contents', 'generation_seconds')
    op.drop_column('generated_contents', 'completed_at')
    op.drop_column('generated_contents', 'started_at')
    op.drop_column('generated_contents', 'updated_at')
    op.drop_column('generated_contents', 'error_message')
    op.drop_column('generated_contents', 'status')
    op.alter_column('generated_contents', 'content_type', new_column_name='type')

    op.drop_index(op.f('ix_user_profiles_share_token'), table_name='user_profiles')
    op.drop_index(op.f('ix_user_profiles_public_slug'), table_name='user_profiles')
    op.drop_column('user_profiles', 'public_updated_at')
    op.drop_column('user_profiles', 'share_token_expires_at')
    op.drop_column('user_profiles', 'share_token')
    op.drop_column('user_profiles', 'portfolio_show_email')
    op.drop_column('user_profiles', 'portfolio_public')
    op.drop_column('user_profiles', 'public_slug')

    op.drop_index(op.f('ix_users_github_username'), table_name='users')
    op.drop_column('users', 'is_admin')
    op.drop_column('users', 'github_username')
