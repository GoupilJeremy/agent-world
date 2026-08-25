"""Integration tests for the Alembic deployment path."""

from datetime import datetime
from pathlib import Path

from alembic import command
from alembic.config import Config as AlembicConfig
from sqlalchemy import create_engine, inspect, text

from backend import models as _models  # noqa: F401
from backend.models.base import db

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
HEAD_REVISION = "20260825_0002"
LEGACY_TABLES = {"users", "agents", "workflows", "executions"}
FILE_TABLES = {"generated_files", "file_versions", "file_shares"}


def _database_url(path: Path) -> str:
    return f"sqlite:///{path.as_posix()}"


def _migration_config(database_url: str) -> AlembicConfig:
    config = AlembicConfig(str(REPOSITORY_ROOT / "alembic.ini"))
    config.set_main_option("sqlalchemy.url", database_url.replace("%", "%%"))
    return config


def test_fresh_database_upgrades_and_downgrades_epic3_schema(tmp_path: Path) -> None:
    database_url = _database_url(tmp_path / "fresh.sqlite")
    config = _migration_config(database_url)

    command.upgrade(config, "head")
    engine = create_engine(database_url)
    try:
        inspector = inspect(engine)
        assert LEGACY_TABLES | FILE_TABLES | {"alembic_version"} <= set(
            inspector.get_table_names()
        )
        assert "recipient_user_id" in {
            column["name"] for column in inspector.get_columns("file_shares")
        }
        assert {
            "ix_generated_files_storage_key",
            "ix_generated_files_management_token_hash",
        } <= {index["name"] for index in inspector.get_indexes("generated_files")}
        with engine.connect() as connection:
            assert (
                connection.execute(
                    text("SELECT version_num FROM alembic_version")
                ).scalar_one()
                == HEAD_REVISION
            )

        command.downgrade(config, "20260825_0001")
        assert FILE_TABLES.isdisjoint(inspect(engine).get_table_names())
        assert LEGACY_TABLES <= set(inspect(engine).get_table_names())

        command.upgrade(config, "head")
        assert FILE_TABLES <= set(inspect(engine).get_table_names())
    finally:
        engine.dispose()


def test_migration_adopts_existing_create_all_schema(tmp_path: Path) -> None:
    """A pre-Alembic database keeps its data when it receives the baseline."""

    database_url = _database_url(tmp_path / "adopted.sqlite")
    engine = create_engine(database_url)
    try:
        for table_name in ("users", "agents", "workflows", "executions"):
            db.metadata.tables[table_name].create(engine, checkfirst=True)
        with engine.begin() as connection:
            connection.execute(
                db.metadata.tables["users"]
                .insert()
                .values(
                    email="existing@example.test",
                    username="existing",
                    password_hash="already-hashed",
                    is_active=True,
                    is_admin=False,
                    created_at=datetime(2026, 8, 25),
                    updated_at=datetime(2026, 8, 25),
                )
            )

        command.upgrade(_migration_config(database_url), "head")

        assert FILE_TABLES <= set(inspect(engine).get_table_names())
        with engine.connect() as connection:
            assert (
                connection.execute(text("SELECT username FROM users")).scalar_one()
                == "existing"
            )
            assert (
                connection.execute(
                    text("SELECT version_num FROM alembic_version")
                ).scalar_one()
                == HEAD_REVISION
            )
    finally:
        engine.dispose()
