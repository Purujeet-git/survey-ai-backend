"""Create documents table

Revision ID: b2c3d4e5f6a1
Revises: 7f8a9b0c1d2e
Create Date: 2026-08-13 12:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'b2c3d4e5f6a1'
down_revision: Union[str, Sequence[str], None] = '7f8a9b0c1d2e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'documents',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('claim_id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('organization_id', sa.UUID(), nullable=True),
        sa.Column('document_type', sa.String(length=50), server_default='other', nullable=False),
        sa.Column('file_name', sa.String(length=255), nullable=False),
        sa.Column('storage_key', sa.String(length=500), nullable=False),
        sa.Column('content_type', sa.String(length=100), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=False),
        sa.Column('file_hash', sa.String(length=64), nullable=False),
        sa.Column('version', sa.Integer(), server_default='1', nullable=False),
        sa.Column('parent_document_id', sa.UUID(), nullable=True),
        sa.Column('is_latest', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('processing_status', sa.String(length=30), server_default='uploaded', nullable=False),
        sa.Column('extracted_text', sa.Text(), nullable=True),
        sa.Column('classification_confidence', sa.Float(), nullable=True),
        sa.Column('doc_metadata', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['claim_id'], ['claims.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['parent_document_id'], ['documents.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('storage_key')
    )
    op.create_index(op.f('ix_documents_claim_id'), 'documents', ['claim_id'], unique=False)
    op.create_index(op.f('ix_documents_user_id'), 'documents', ['user_id'], unique=False)
    op.create_index(op.f('ix_documents_organization_id'), 'documents', ['organization_id'], unique=False)
    op.create_index(op.f('ix_documents_document_type'), 'documents', ['document_type'], unique=False)
    op.create_index(op.f('ix_documents_file_hash'), 'documents', ['file_hash'], unique=False)
    op.create_index(op.f('ix_documents_parent_document_id'), 'documents', ['parent_document_id'], unique=False)
    op.create_index(op.f('ix_documents_is_latest'), 'documents', ['is_latest'], unique=False)
    op.create_index(op.f('ix_documents_processing_status'), 'documents', ['processing_status'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_documents_processing_status'), table_name='documents')
    op.drop_index(op.f('ix_documents_is_latest'), table_name='documents')
    op.drop_index(op.f('ix_documents_parent_document_id'), table_name='documents')
    op.drop_index(op.f('ix_documents_file_hash'), table_name='documents')
    op.drop_index(op.f('ix_documents_document_type'), table_name='documents')
    op.drop_index(op.f('ix_documents_organization_id'), table_name='documents')
    op.drop_index(op.f('ix_documents_user_id'), table_name='documents')
    op.drop_index(op.f('ix_documents_claim_id'), table_name='documents')
    op.drop_table('documents')
