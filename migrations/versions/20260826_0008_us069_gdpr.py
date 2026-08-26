"""Add GDPR consent and deletion fields to users (US-069)

Revision ID: 20260826_0008
Revises: 20260826_0007
Create Date: 2026-08-26 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20260826_0008'
down_revision = '20260826_0007'
branch_labels = None
depends_on = None


def upgrade():
    """Add GDPR consent and deletion fields to users (US-069)."""
    with op.batch_alter_table('users') as batch:
        batch.add_column(sa.Column('consent_given_at', sa.DateTime(), nullable=True))
        batch.add_column(sa.Column('data_deleted_at', sa.DateTime(), nullable=True))


def downgrade():
    """Remove GDPR consent and deletion fields from users (US-069)."""
    with op.batch_alter_table('users') as batch:
        batch.drop_column('data_deleted_at')
        batch.drop_column('consent_given_at')
