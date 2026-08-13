"""Create survey_reports table

Revision ID: c3d4e5f6a1b2
Revises: b2c3d4e5f6a1
Create Date: 2026-08-13 13:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'c3d4e5f6a1b2'
down_revision: Union[str, Sequence[str], None] = 'b2c3d4e5f6a1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'survey_reports',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('claim_id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('version', sa.Integer(), server_default='1', nullable=False),
        sa.Column('status', sa.String(length=30), server_default='DRAFT', nullable=False),
        sa.Column('excel_storage_key', sa.String(length=500), nullable=True),
        sa.Column('docx_storage_key', sa.String(length=500), nullable=True),
        sa.Column('summary_data', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['claim_id'], ['claims.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_survey_reports_claim_id'), 'survey_reports', ['claim_id'], unique=False)
    op.create_index(op.f('ix_survey_reports_user_id'), 'survey_reports', ['user_id'], unique=False)
    op.create_index(op.f('ix_survey_reports_status'), 'survey_reports', ['status'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_survey_reports_status'), table_name='survey_reports')
    op.drop_index(op.f('ix_survey_reports_user_id'), table_name='survey_reports')
    op.drop_index(op.f('ix_survey_reports_claim_id'), table_name='survey_reports')
    op.drop_table('survey_reports')
