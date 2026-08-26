"""Add roles and user_roles association table (US-066)

Revision ID: 20260826_0006
Revises: 20260826_0005
Create Date: 2026-08-26 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20260826_0006'
down_revision = '20260826_0005'
branch_labels = None
depends_on = None


def upgrade():
    """Create roles table and user_roles association (US-066)."""
    op.create_table(
        'roles',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('name', sa.String(80), nullable=False, unique=True),
        sa.Column('permissions', sa.JSON(), nullable=False, server_default='[]'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_table(
        'user_roles',
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), primary_key=True),
        sa.Column('role_id', sa.Integer(), sa.ForeignKey('roles.id'), primary_key=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('idx_roles_name', 'roles', ['name'], unique=True)


def downgrade():
    """Drop roles table and user_roles association (US-066)."""
    op.drop_index('idx_roles_name', table_name='roles')
    op.drop_table('user_roles')
    op.drop_table('roles')
