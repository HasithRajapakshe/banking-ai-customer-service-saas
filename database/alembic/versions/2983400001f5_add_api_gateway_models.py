"""Add API Gateway models

Revision ID: 2983400001f5
Revises: 
Create Date: 2026-10-06 12:52:58.261900

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '2983400001f5'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- RBAC Models ---
    op.create_table('role',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=50), nullable=False),
        sa.Column('description', sa.String(length=255), nullable=True),
        sa.Column('is_system', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('tenant_id', 'name', name='uq_role_tenant_name')
    )

    op.create_table('permission',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('code', sa.String(length=100), nullable=False),
        sa.Column('description', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code')
    )

    op.create_table('role_permission',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('role_id', sa.UUID(), nullable=False),
        sa.Column('permission_id', sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(['permission_id'], ['permission.id'], ),
        sa.ForeignKeyConstraint(['role_id'], ['role.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('role_id', 'permission_id', name='uq_role_permission')
    )

    op.create_table('app_user',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('customer_id', sa.UUID(), nullable=True),
        sa.Column('username', sa.String(length=100), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=200), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('tenant_id', 'email', name='uq_user_tenant_email'),
        sa.UniqueConstraint('tenant_id', 'username', name='uq_user_tenant_username')
    )

    op.create_table('user_role',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('role_id', sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(['role_id'], ['role.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['app_user.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'role_id', name='uq_user_role')
    )

    # --- Conversation Models ---
    op.create_table('conversation',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('customer_id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=True),
        sa.Column('title', sa.String(length=255), nullable=True),
        sa.Column('channel', sa.String(length=20), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['app_user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table('message',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('conversation_id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('role', sa.String(length=20), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('intent', sa.String(length=50), nullable=True),
        sa.Column('tool_name', sa.String(length=100), nullable=True),
        sa.Column('tool_arguments', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('tool_result_summary', sa.Text(), nullable=True),
        sa.Column('correlation_id', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversation.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # --- Audit Models ---
    op.create_table('audit_log',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=True),
        sa.Column('customer_id', sa.UUID(), nullable=True),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('resource', sa.String(length=100), nullable=True),
        sa.Column('resource_id', sa.String(length=100), nullable=True),
        sa.Column('result', sa.String(length=20), nullable=False),
        sa.Column('risk_level', sa.String(length=20), nullable=True),
        sa.Column('details', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('correlation_id', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table('tool_execution',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('customer_id', sa.UUID(), nullable=True),
        sa.Column('user_id', sa.UUID(), nullable=True),
        sa.Column('conversation_id', sa.UUID(), nullable=True),
        sa.Column('tool_name', sa.String(length=100), nullable=False),
        sa.Column('risk_level', sa.String(length=20), nullable=False),
        sa.Column('arguments', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('executed', sa.Boolean(), nullable=False),
        sa.Column('success', sa.Boolean(), nullable=False),
        sa.Column('error_code', sa.String(length=50), nullable=True),
        sa.Column('elapsed_seconds', sa.Numeric(precision=10, scale=4), nullable=True),
        sa.Column('correlation_id', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    # --- Document / RAG Models ---
    op.create_table('document',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('filename', sa.String(length=255), nullable=False),
        sa.Column('content_type', sa.String(length=50), nullable=False),
        sa.Column('category', sa.String(length=100), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('chunk_count', sa.Integer(), nullable=False),
        sa.Column('uploaded_by', sa.UUID(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table('document_chunk',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('document_id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('chunk_index', sa.Integer(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('metadata_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['document_id'], ['document.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Add pgvector extension if not exists
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')
    
    # Add vector column
    op.execute('ALTER TABLE document_chunk ADD COLUMN embedding vector(1536)')


def downgrade() -> None:
    op.drop_table('document_chunk')
    op.drop_table('document')
    op.drop_table('tool_execution')
    op.drop_table('audit_log')
    op.drop_table('message')
    op.drop_table('conversation')
    op.drop_table('user_role')
    op.drop_table('app_user')
    op.drop_table('role_permission')
    op.drop_table('permission')
    op.drop_table('role')
