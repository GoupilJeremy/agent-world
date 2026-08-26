"""Add Epic 6 Collaboration tables (projects, invitations) and project_id to agents.

Revision ID: 20260825_0003
Revises: 20260825_0002
Create Date: 2026-08-25

"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "20260825_0003"
down_revision = "20260825_0002"
branch_labels = None
depends_on = None


def _invitation_status_enum() -> sa.Enum:
    """Create the invitation_status enum for PostgreSQL."""
    return sa.Enum(
        "PENDING",
        "ACCEPTED",
        "EXPIRED",
        "REVOKED",
        name="invitationstatus",
    )


def upgrade() -> None:
    """Upgrade database schema for Epic 6 Collaboration."""
    
    # 1. Create the invitation_status enum
    _invitation_status_enum().create(op.get_bind(), checkfirst=True)
    
    # 2. Create projects table
    if not op.has_table("projects"):
        op.create_table(
            "projects",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("name", sa.String(length=100), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("created_by", sa.Integer(), nullable=False),
            sa.Column("is_public", sa.Boolean(), nullable=False, default=False),
            sa.Column("is_shared", sa.Boolean(), nullable=False, default=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(
            "ix_projects_created_by",
            "projects",
            ["created_by"],
            unique=False,
        )
        op.create_index(
            "ix_projects_name",
            "projects",
            ["name"],
            unique=False,
        )
    
    # 3. Create invitations table
    if not op.has_table("invitations"):
        op.create_table(
            "invitations",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("project_id", sa.Integer(), nullable=False),
            sa.Column("email", sa.String(length=255), nullable=False),
            sa.Column("token", sa.String(length=255), nullable=False),
            sa.Column("role", sa.String(length=50), nullable=False, default="member"),
            sa.Column("status", _invitation_status_enum(), nullable=False, default="PENDING"),
            sa.Column("created_by", sa.Integer(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("expires_at", sa.DateTime(), nullable=False),
            sa.Column("accepted_at", sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("token"),
        )
        op.create_index(
            "ix_invitations_token",
            "invitations",
            ["token"],
            unique=True,
        )
        op.create_index(
            "ix_invitations_project_id",
            "invitations",
            ["project_id"],
            unique=False,
        )
        op.create_index(
            "ix_invitations_email",
            "invitations",
            ["email"],
            unique=False,
        )
        op.create_index(
            "ix_invitations_status",
            "invitations",
            ["status"],
            unique=False,
        )
    
    # 4. Add project_id to agents table (nullable for backward compatibility)
    if op.has_table("agents") and not op.has_column("agents", "project_id"):
        op.add_column(
            "agents",
            sa.Column("project_id", sa.Integer(), nullable=True),
        )
        op.create_foreign_key(
            "fk_agents_project_id",
            "agents",
            "projects",
            ["project_id"],
            ["id"],
            ondelete="SET NULL",
        )
        op.create_index(
            "ix_agents_project_id",
            "agents",
            ["project_id"],
            unique=False,
        )


def downgrade() -> None:
    """Downgrade database schema for Epic 6 Collaboration."""
    
    # 1. Remove project_id from agents table
    if op.has_table("agents") and op.has_column("agents", "project_id"):
        op.drop_constraint("fk_agents_project_id", "agents", type_="foreignkey")
        op.drop_column("agents", "project_id")
    
    # 2. Drop invitations table
    if op.has_table("invitations"):
        op.drop_table("invitations")
    
    # 3. Drop projects table
    if op.has_table("projects"):
        op.drop_table("projects")
    
    # 4. Drop the enum
    _invitation_status_enum().drop(op.get_bind(), checkfirst=True)
