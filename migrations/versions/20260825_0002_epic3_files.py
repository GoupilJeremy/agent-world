"""Add the Epic 3 generated-file catalogue.

Revision ID: 20260825_0002
Revises: 20260825_0001
Create Date: 2026-08-25
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "20260825_0002"
down_revision = "20260825_0001"
branch_labels = None
depends_on = None


def _table_names() -> set[str]:
    return set(sa.inspect(op.get_bind()).get_table_names())


def upgrade() -> None:
    """Create or adopt the persistent file, version, and share tables."""

    tables = _table_names()
    if "generated_files" not in tables:
        op.create_table(
            "generated_files",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("agent_id", sa.Integer(), nullable=False),
            sa.Column("execution_id", sa.Integer(), nullable=True),
            sa.Column("created_by", sa.Integer(), nullable=True),
            sa.Column("logical_name", sa.String(length=255), nullable=False),
            sa.Column("file_format", sa.String(length=16), nullable=False),
            sa.Column("mime_type", sa.String(length=100), nullable=False),
            sa.Column("storage_key", sa.String(length=36), nullable=False),
            sa.Column("storage_root", sa.Text(), nullable=False),
            sa.Column("current_version", sa.Integer(), nullable=False),
            sa.Column("size_bytes", sa.Integer(), nullable=False),
            sa.Column("sha256", sa.String(length=64), nullable=False),
            sa.Column("management_token_hash", sa.String(length=64), nullable=False),
            sa.Column("is_temporary", sa.Boolean(), nullable=False),
            sa.Column("pinned", sa.Boolean(), nullable=False),
            sa.Column("expires_at", sa.DateTime(), nullable=True),
            sa.Column("last_accessed_at", sa.DateTime(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(
                ["agent_id"], ["agents.id"], ondelete="CASCADE"
            ),
            sa.ForeignKeyConstraint(
                ["created_by"], ["users.id"], ondelete="SET NULL"
            ),
            sa.ForeignKeyConstraint(
                ["execution_id"], ["executions.id"], ondelete="SET NULL"
            ),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint(
                "agent_id", "logical_name", name="uq_generated_file_agent_name"
            ),
        )
        op.create_index(
            "ix_generated_files_management_token_hash",
            "generated_files",
            ["management_token_hash"],
            unique=True,
        )
        op.create_index(
            "ix_generated_files_storage_key",
            "generated_files",
            ["storage_key"],
            unique=True,
        )
        tables.add("generated_files")

    if "file_versions" not in tables:
        op.create_table(
            "file_versions",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("generated_file_id", sa.Integer(), nullable=False),
            sa.Column("version", sa.Integer(), nullable=False),
            sa.Column("relative_path", sa.String(length=1024), nullable=False),
            sa.Column("size_bytes", sa.Integer(), nullable=False),
            sa.Column("sha256", sa.String(length=64), nullable=False),
            sa.Column("created_by", sa.Integer(), nullable=True),
            sa.Column("execution_id", sa.Integer(), nullable=True),
            sa.Column("restored_from_version_id", sa.Integer(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(
                ["created_by"], ["users.id"], ondelete="SET NULL"
            ),
            sa.ForeignKeyConstraint(
                ["execution_id"], ["executions.id"], ondelete="SET NULL"
            ),
            sa.ForeignKeyConstraint(
                ["generated_file_id"], ["generated_files.id"], ondelete="CASCADE"
            ),
            sa.ForeignKeyConstraint(
                ["restored_from_version_id"],
                ["file_versions.id"],
                ondelete="SET NULL",
            ),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint(
                "generated_file_id", "relative_path", name="uq_file_version_path"
            ),
            sa.UniqueConstraint(
                "generated_file_id", "version", name="uq_file_version_number"
            ),
        )
        op.create_index(
            "ix_file_versions_generated_file_id",
            "file_versions",
            ["generated_file_id"],
            unique=False,
        )
        tables.add("file_versions")

    if "file_shares" not in tables:
        op.create_table(
            "file_shares",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("generated_file_id", sa.Integer(), nullable=False),
            sa.Column("created_by", sa.Integer(), nullable=True),
            sa.Column("recipient_user_id", sa.Integer(), nullable=True),
            sa.Column("permission", sa.String(length=8), nullable=False),
            sa.Column("token_hash", sa.String(length=64), nullable=False),
            sa.Column("expires_at", sa.DateTime(), nullable=False),
            sa.Column("revoked_at", sa.DateTime(), nullable=True),
            sa.Column("last_accessed_at", sa.DateTime(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(
                ["created_by"], ["users.id"], ondelete="SET NULL"
            ),
            sa.ForeignKeyConstraint(
                ["generated_file_id"], ["generated_files.id"], ondelete="CASCADE"
            ),
            sa.ForeignKeyConstraint(
                ["recipient_user_id"], ["users.id"], ondelete="CASCADE"
            ),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(
            "ix_file_shares_generated_file_id",
            "file_shares",
            ["generated_file_id"],
            unique=False,
        )
        op.create_index(
            "ix_file_shares_token_hash",
            "file_shares",
            ["token_hash"],
            unique=True,
        )


def downgrade() -> None:
    """Remove the Epic 3 catalogue in dependency order."""

    tables = _table_names()
    for table_name in ("file_shares", "file_versions", "generated_files"):
        if table_name in tables:
            op.drop_table(table_name)
