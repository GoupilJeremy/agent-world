"""Alembic environment for the Agent World SQLAlchemy metadata."""

from __future__ import annotations

import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from backend.config.settings import Config
from backend.models import (  # noqa: F401
    agent,
    execution,
    generated_file,
    user,
    workflow,
)
from backend.models.base import db

alembic_config = context.config

if alembic_config.config_file_name is not None:
    fileConfig(alembic_config.config_file_name)

target_metadata = db.metadata


def database_url() -> str:
    """Return an explicit Alembic URL, then the application-configured URL."""

    configured = alembic_config.get_main_option("sqlalchemy.url").strip()
    if configured:
        return configured
    return os.environ.get("DATABASE_URL") or Config.SQLALCHEMY_DATABASE_URI


def run_migrations_offline() -> None:
    """Run migrations without creating an Engine."""

    context.configure(
        url=database_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations through an Engine connection."""

    configuration = alembic_config.get_section(
        alembic_config.config_ini_section, {}
    )
    configuration["sqlalchemy.url"] = database_url()
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
