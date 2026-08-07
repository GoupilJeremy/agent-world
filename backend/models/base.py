# 🏗️ Agent World - Base Model
# Version: 0.1.0 (MVP)
# Description: Classe de base pour tous les modèles

"""
Base Model for Agent World.

Ce fichier contient la classe de base pour tous les modèles de données.
Il initialise SQLAlchemy et fournit des fonctionnalités communes.
"""

from flask_sqlalchemy import SQLAlchemy

# Initialize SQLAlchemy without binding to any app
# The app will be bound in the factory function
db = SQLAlchemy()


class BaseModel(db.Model):
    """
    Base model class that all models should inherit from.
    
    This class provides common functionality and ensures that all models
    have access to the database session.
    """
    
    __abstract__ = True
    
    def save(self):
        """Save the current instance to the database."""
        db.session.add(self)
        db.session.commit()
    
    def save_and_flush(self):
        """Save and flush the current instance."""
        db.session.add(self)
        db.session.flush()
    
    @classmethod
    def delete_all(cls):
        """Delete all instances of this model."""
        cls.query.delete()
        db.session.commit()
    
    @classmethod
    def count(cls) -> int:
        """Count all instances of this model."""
        return cls.query.count()
    
    @classmethod
    def exists(cls, **filters) -> bool:
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
    from . import agent, user, workflow, execution
    
    # Create tables (only in development, use migrations in production)
    if app.config.get('ENV', 'development') == 'development':
        with app.app_context():
            db.create_all()
