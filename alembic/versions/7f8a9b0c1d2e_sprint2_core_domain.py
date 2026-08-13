"""Create Sprint 2 Core Domain tables and columns

Revision ID: 7f8a9b0c1d2e
Revises: 422d6b455f03
Create Date: 2026-08-13 12:05:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '7f8a9b0c1d2e'
down_revision: Union[str, Sequence[str], None] = '422d6b455f03'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create organizations table
    op.create_table(
        'organizations',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('code', sa.String(length=50), nullable=False),
        sa.Column('contact_email', sa.String(length=255), nullable=True),
        sa.Column('address', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=20), server_default='active', nullable=False),
        sa.Column('settings', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code')
    )
    op.create_index(op.f('ix_organizations_code'), 'organizations', ['code'], unique=True)
    op.create_index(op.f('ix_organizations_status'), 'organizations', ['status'], unique=False)

    # 2. Add columns to users table
    op.add_column('users', sa.Column('organization_id', sa.UUID(), nullable=True))
    op.add_column('users', sa.Column('role', sa.String(length=50), server_default='surveyor', nullable=False))
    op.create_foreign_key('fk_users_organization_id', 'users', 'organizations', ['organization_id'], ['id'], ondelete='SET NULL')
    op.create_index(op.f('ix_users_organization_id'), 'users', ['organization_id'], unique=False)
    op.create_index(op.f('ix_users_role'), 'users', ['role'], unique=False)

    # 3. Add columns to claims table
    op.add_column('claims', sa.Column('organization_id', sa.UUID(), nullable=True))
    op.add_column('claims', sa.Column('assigned_to_id', sa.UUID(), nullable=True))
    op.create_foreign_key('fk_claims_organization_id', 'claims', 'organizations', ['organization_id'], ['id'], ondelete='SET NULL')
    op.create_foreign_key('fk_claims_assigned_to_id', 'claims', 'users', ['assigned_to_id'], ['id'], ondelete='SET NULL')
    op.create_index(op.f('ix_claims_organization_id'), 'claims', ['organization_id'], unique=False)
    op.create_index(op.f('ix_claims_assigned_to_id'), 'claims', ['assigned_to_id'], unique=False)

    # 4. Create timeline_events table
    op.create_table(
        'timeline_events',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('claim_id', sa.UUID(), nullable=False),
        sa.Column('actor_id', sa.UUID(), nullable=True),
        sa.Column('event_type', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('payload', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['actor_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['claim_id'], ['claims.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_timeline_events_actor_id'), 'timeline_events', ['actor_id'], unique=False)
    op.create_index(op.f('ix_timeline_events_claim_id'), 'timeline_events', ['claim_id'], unique=False)
    op.create_index(op.f('ix_timeline_events_created_at'), 'timeline_events', ['created_at'], unique=False)
    op.create_index(op.f('ix_timeline_events_event_type'), 'timeline_events', ['event_type'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_timeline_events_event_type'), table_name='timeline_events')
    op.drop_index(op.f('ix_timeline_events_created_at'), table_name='timeline_events')
    op.drop_index(op.f('ix_timeline_events_claim_id'), table_name='timeline_events')
    op.drop_index(op.f('ix_timeline_events_actor_id'), table_name='timeline_events')
    op.drop_table('timeline_events')

    op.drop_index(op.f('ix_claims_assigned_to_id'), table_name='claims')
    op.drop_index(op.f('ix_claims_organization_id'), table_name='claims')
    op.drop_constraint('fk_claims_assigned_to_id', 'claims', type_='foreignkey')
    op.drop_constraint('fk_claims_organization_id', 'claims', type_='foreignkey')
    op.drop_column('claims', 'assigned_to_id')
    op.drop_column('claims', 'organization_id')

    op.drop_index(op.f('ix_users_role'), table_name='users')
    op.drop_index(op.f('ix_users_organization_id'), table_name='users')
    op.drop_constraint('fk_users_organization_id', 'users', type_='foreignkey')
    op.drop_column('users', 'role')
    op.drop_column('users', 'organization_id')

    op.drop_index(op.f('ix_organizations_status'), table_name='organizations')
    op.drop_index(op.f('ix_organizations_code'), table_name='organizations')
    op.drop_table('organizations')
