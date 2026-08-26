"""Épic 11 - Multi-Modèles: benchmark_results, model_quotas, model_usage_logs

Revision ID: 20260826_0005
Revises: 20260826_0004_epic8_performance
Create Date: 2026-08-26

Tables created:
  - benchmark_results: stores benchmark comparison results
  - model_quotas: per-user, per-model usage quotas
  - model_usage_logs: detailed log of each model API call
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = "20260826_0005"
down_revision = "20260826_0004_epic8_performance"
branch_labels = None
depends_on = None


def upgrade():
    # --- benchmark_results ---
    op.create_table(
        "benchmark_results",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("benchmark_run_id", sa.String(36), nullable=False, index=True),
        sa.Column("model_id", sa.String(100), nullable=False),
        sa.Column("prompt", sa.Text(), nullable=False),
        sa.Column("response_text", sa.Text(), nullable=True),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.Column("tokens_input", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("tokens_output", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("cost_usd", sa.Float(), nullable=False, server_default="0"),
        sa.Column("quality_score", sa.Float(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column(
            "status", sa.String(20), nullable=False, server_default="completed"
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
        ),
        sa.Column("created_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    # --- model_quotas ---
    op.create_table(
        "model_quotas",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column(
            "user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False
        ),
        sa.Column("model_id", sa.String(100), nullable=False),
        sa.Column("max_tokens_per_month", sa.Integer(), nullable=True),
        sa.Column("max_cost_per_month", sa.Float(), nullable=True),
        sa.Column("tokens_used", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("cost_used", sa.Float(), nullable=False, server_default="0"),
        sa.Column(
            "period_start",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
        ),
        sa.Column("period_end", sa.DateTime(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "model_id", name="uq_user_model_quota"),
    )

    # --- model_usage_logs ---
    op.create_table(
        "model_usage_logs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column(
            "user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True
        ),
        sa.Column("model_id", sa.String(100), nullable=False),
        sa.Column(
            "execution_id",
            sa.Integer(),
            sa.ForeignKey("executions.id"),
            nullable=True,
        ),
        sa.Column("tokens_input", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("tokens_output", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("cost_usd", sa.Float(), nullable=False, server_default="0"),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Indexes for common queries
    op.create_index(
        "ix_model_usage_logs_user_id", "model_usage_logs", ["user_id"]
    )
    op.create_index(
        "ix_model_usage_logs_model_id", "model_usage_logs", ["model_id"]
    )
    op.create_index(
        "ix_model_usage_logs_created_at", "model_usage_logs", ["created_at"]
    )


def downgrade():
    op.drop_index("ix_model_usage_logs_created_at", table_name="model_usage_logs")
    op.drop_index("ix_model_usage_logs_model_id", table_name="model_usage_logs")
    op.drop_index("ix_model_usage_logs_user_id", table_name="model_usage_logs")
    op.drop_table("model_usage_logs")
    op.drop_table("model_quotas")
    op.drop_table("benchmark_results")
