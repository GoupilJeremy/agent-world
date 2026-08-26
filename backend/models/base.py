# 🏗️ Agent World - Base Model
# Version: 0.1.0 (MVP)
# Description: Classe de base pour tous les modèles

"""
Base Model for Agent World.

Ce fichier contient la classe de base pour tous les modèles de données.
Il initialise SQLAlchemy et fournit des fonctionnalités communes.
"""

from typing import Any

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import String
from sqlalchemy.types import TypeDecorator

# Initialize SQLAlchemy without binding to any app
# The app will be bound in the factory function
db = SQLAlchemy()  # type: ignore[name-defined]


class EncryptedString(TypeDecorator):
    """Transparently encrypt/decrypt string values using the EncryptionService."""

    impl = String
    cache_ok = True

    def process_bind_param(self, value, dialect):  # type: ignore[override]
        if value is None:
            return None
        from ..services.encryption_service import get_encryption_service

        return get_encryption_service().encrypt(value)

    def process_result_value(self, value, dialect):  # type: ignore[override]
        if value is None:
            return None
        from ..services.encryption_service import get_encryption_service

        return get_encryption_service().decrypt(value)


class BaseModel(db.Model):  # type: ignore[name-defined]
    """
    Base model class that all models should inherit from.

    This class provides common functionality and ensures that all models
    have access to the database session.
    """

    __abstract__ = True

    def save(self) -> None:
        """Save the current instance to the database."""
        db.session.add(self)
        db.session.commit()

    def save_and_flush(self) -> None:
        """Save and flush the current instance."""
        db.session.add(self)
        db.session.flush()

    @classmethod
    def delete_all(cls) -> None:
        """Delete all instances of this model."""
        cls.query.delete()
        db.session.commit()

    @classmethod
    def count(cls) -> int:
        """Count all instances of this model."""
        return cls.query.count()  # type: ignore[no-any-return]

    @classmethod
    def exists(cls, **filters: Any) -> bool:
        """Check if any instance exists with the given filters."""
        return cls.query.filter_by(**filters).first() is not None


def init_db(app):
    """
    Initialize the database with the given Flask app.

    Args:
        app: Flask application instance
    """
    db.init_app(app)

    # Import all models to register them with SQLAlchemy
    from . import (  # noqa: F401
        agent,
        agent_history,
        audit_log,
        execution,
        generated_file,
        history_notification,
        invitation,
        project,
        role,
        template,
        template_share,
        user,
        workflow,
    )

    # Development and tests may bootstrap ephemeral schemas. Production uses
    # the versioned Alembic migrations shipped with the application.
    if app.config.get("AUTO_CREATE_DB", False):
        with app.app_context():
            db.create_all()
