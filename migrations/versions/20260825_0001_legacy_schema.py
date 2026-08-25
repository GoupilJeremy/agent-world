"""Create or adopt the pre-Alembic Agent World schema.

Revision ID: 20260825_0001
Revises: None
Create Date: 2026-08-25
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "20260825_0001"
down_revision = None
branch_labels = None
depends_on = None


def _table_names() -> set[str]:
    return set(sa.inspect(op.get_bind()).get_table_names())


def _execution_status() -> sa.Enum:
    return sa.Enum(
        "PENDING",
        "RUNNING",
        "COMPLETED",
        "FAILED",
        "CANCELLED",
        name="executionstatus",
    )


def upgrade() -> None:
    """Create missing baseline tables while safely adopting existing ones."""

    tables = _table_names()
    if "users" not in tables:
        op.create_table(
            "users",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("email", sa.String(length=120), nullable=False),
            sa.Column("username", sa.String(length=80), nullable=False),
            sa.Column("password_hash", sa.String(length=255), nullable=False),
            sa.Column("first_name", sa.String(length=50), nullable=True),
            sa.Column("last_name", sa.String(length=50), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=False),
            sa.Column("is_admin", sa.Boolean(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("email"),
            sa.UniqueConstraint("username"),
        )
        tables.add("users")

    if "agents" not in tables:
        op.create_table(
            "agents",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("name", sa.String(length=100), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("model", sa.String(length=50), nullable=False),
            sa.Column("configuration", sa.JSON(), nullable=False),
            sa.Column("is_active", sa.Boolean(), nullable=False),
            sa.Column("created_by", sa.Integer(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("name"),
        )
        tables.add("agents")

    if "workflows" not in tables:
        op.create_table(
            "workflows",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("name", sa.String(length=100), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("agent_id", sa.Integer(), nullable=False),
            sa.Column("steps", sa.JSON(), nullable=False),
            sa.Column("configuration", sa.JSON(), nullable=False),
            sa.Column("is_active", sa.Boolean(), nullable=False),
            sa.Column("created_by", sa.Integer(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(["agent_id"], ["agents.id"]),
            sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
        tables.add("workflows")

    if "executions" not in tables:
        op.create_table(
            "executions",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("agent_id", sa.Integer(), nullable=False),
            sa.Column("workflow_id", sa.Integer(), nullable=True),
            sa.Column("input_data", sa.JSON(), nullable=False),
            sa.Column("output_data", sa.JSON(), nullable=True),
            sa.Column("status", _execution_status(), nullable=False),
            sa.Column("error_message", sa.Text(), nullable=True),
            sa.Column("duration_ms", sa.Integer(), nullable=True),
            sa.Column("started_at", sa.DateTime(), nullable=True),
            sa.Column("completed_at", sa.DateTime(), nullable=True),
            sa.Column("executed_by", sa.Integer(), nullable=True),
            sa.Column("model_used", sa.String(length=50), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(["agent_id"], ["agents.id"]),
            sa.ForeignKeyConstraint(["executed_by"], ["users.id"]),
            sa.ForeignKeyConstraint(["workflow_id"], ["workflows.id"]),
            sa.PrimaryKeyConstraint("id"),
        )


def downgrade() -> None:
    """Remove the complete baseline schema in dependency order."""

    tables = _table_names()
    for table_name in ("executions", "workflows", "agents", "users"):
        if table_name in tables:
            op.drop_table(table_name)
    if op.get_bind().dialect.name == "postgresql":
        _execution_status().drop(op.get_bind(), checkfirst=True)
