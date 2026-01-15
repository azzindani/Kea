"""Initial schema - users, sessions, conversations

Revision ID: 001_initial
Revises: 
Create Date: 2026-01-16

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Users table
    op.create_table(
        'users',
        sa.Column('user_id', sa.String(36), primary_key=True),
        sa.Column('email', sa.String(255), unique=True, nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('role', sa.String(50), default='user'),
        sa.Column('tenant_id', sa.String(36), nullable=True),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index('ix_users_email', 'users', ['email'])
    op.create_index('ix_users_tenant', 'users', ['tenant_id'])
    
    # API Keys table
    op.create_table(
        'api_keys',
        sa.Column('key_id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('key_prefix', sa.String(10), nullable=False),
        sa.Column('key_hash', sa.String(255), nullable=False),
        sa.Column('scopes', sa.Text, default='[]'),
        sa.Column('last_used_at', sa.DateTime, nullable=True),
        sa.Column('expires_at', sa.DateTime, nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index('ix_api_keys_user', 'api_keys', ['user_id'])
    op.create_index('ix_api_keys_prefix', 'api_keys', ['key_prefix'])
    
    # Sessions table
    op.create_table(
        'sessions',
        sa.Column('session_id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False),
        sa.Column('ip_address', sa.String(50), nullable=True),
        sa.Column('user_agent', sa.String(500), nullable=True),
        sa.Column('expires_at', sa.DateTime, nullable=False),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index('ix_sessions_user', 'sessions', ['user_id'])
    op.create_index('ix_sessions_expires', 'sessions', ['expires_at'])
    
    # Conversations table
    op.create_table(
        'conversations',
        sa.Column('conversation_id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False),
        sa.Column('tenant_id', sa.String(36), nullable=True),
        sa.Column('title', sa.String(500), default='New Chat'),
        sa.Column('message_count', sa.Integer, default=0),
        sa.Column('is_archived', sa.Boolean, default=False),
        sa.Column('is_pinned', sa.Boolean, default=False),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index('ix_conversations_user', 'conversations', ['user_id'])
    op.create_index('ix_conversations_tenant', 'conversations', ['tenant_id'])
    op.create_index('ix_conversations_updated', 'conversations', ['updated_at'])
    
    # Messages table
    op.create_table(
        'messages',
        sa.Column('message_id', sa.String(36), primary_key=True),
        sa.Column('conversation_id', sa.String(36), sa.ForeignKey('conversations.conversation_id', ondelete='CASCADE'), nullable=False),
        sa.Column('role', sa.String(20), nullable=False),  # user, assistant, system
        sa.Column('content', sa.Text, nullable=False),
        sa.Column('intent', sa.String(50), nullable=True),
        sa.Column('attachments', sa.Text, default='[]'),
        sa.Column('sources', sa.Text, default='[]'),
        sa.Column('tool_calls', sa.Text, default='[]'),
        sa.Column('confidence', sa.Float, nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index('ix_messages_conversation', 'messages', ['conversation_id'])
    op.create_index('ix_messages_created', 'messages', ['created_at'])
    
    # Research jobs table
    op.create_table(
        'research_jobs',
        sa.Column('job_id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.user_id', ondelete='SET NULL'), nullable=True),
        sa.Column('conversation_id', sa.String(36), sa.ForeignKey('conversations.conversation_id', ondelete='SET NULL'), nullable=True),
        sa.Column('query', sa.Text, nullable=False),
        sa.Column('status', sa.String(20), default='pending'),  # pending, running, completed, failed
        sa.Column('result', sa.Text, nullable=True),
        sa.Column('confidence', sa.Float, nullable=True),
        sa.Column('sources_count', sa.Integer, default=0),
        sa.Column('duration_ms', sa.Integer, nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('completed_at', sa.DateTime, nullable=True),
    )
    op.create_index('ix_jobs_user', 'research_jobs', ['user_id'])
    op.create_index('ix_jobs_status', 'research_jobs', ['status'])


def downgrade() -> None:
    op.drop_table('research_jobs')
    op.drop_table('messages')
    op.drop_table('conversations')
    op.drop_table('sessions')
    op.drop_table('api_keys')
    op.drop_table('users')
