"""Add two-factor authentication fields to users (US-065)

Revision ID: 20260826_0005
Revises: 20260826_0004
Create Date: 2026-08-26 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20260826_0005'
down_revision = '20260826_0004'
branch_labels = None
depends_on = None


def upgrade():
    """Add two-factor authentication fields to users (US-065)."""
    with op.batch_alter_table('users') as batch:
        batch.add_column(sa.Column('totp_secret', sa.String(255), nullable=True))
        batch.add_column(sa.Column('totp_enabled', sa.Boolean(), nullable=False, server_default=sa.false()))
        batch.add_column(sa.Column('totp_verified_at', sa.DateTime(), nullable=True))
        batch.add_column(sa.Column('backup_codes', sa.JSON(), nullable=True))


def downgrade():
    """Remove two-factor authentication fields from users (US-065)."""
    with op.batch_alter_table('users') as batch:
        batch.drop_column('backup_codes')
        batch.drop_column('totp_verified_at')
        batch.drop_column('totp_enabled')
        batch.drop_column('totp_secret')
