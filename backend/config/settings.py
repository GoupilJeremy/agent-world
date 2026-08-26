# ⚙️ Agent World - Configuration Settings
# Version: 0.1.0 (MVP)
# Description: Configuration de l'application Flask

"""
Configuration settings for Agent World application.

Ce fichier contient toutes les configurations pour les différents environnements
(développement, test, production).
"""

import os

from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()


class Config:
    """Base configuration class."""

    # Flask settings
    SECRET_KEY = os.environ.get("SECRET_KEY") or "dev-secret-key-change-in-production"
    AUTH_ACCESS_TOKEN_TTL_SECONDS = int(
        os.environ.get("AUTH_ACCESS_TOKEN_TTL_SECONDS", "3600")
    )
    AUTH_TOKEN_ISSUER = os.environ.get("AUTH_TOKEN_ISSUER", "agent-world")
    DEBUG = False
    TESTING = False
    MAX_CONTENT_LENGTH = 1024 * 1024  # 1 MiB maximum request body

    # Database settings (PostgreSQL by default)
    SQLALCHEMY_DATABASE_URI = (
        os.environ.get("DATABASE_URL")
        or "postgresql://user:password@localhost:5432/agent_world"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # Schema creation is convenient for local development and isolated tests.
    # Deployed environments must apply the versioned Alembic migrations instead.
    AUTO_CREATE_DB = False

    # API settings
    API_TITLE = "Agent World API"
    API_VERSION = "0.1.0"
    API_DESCRIPTION = (
        "Open-source platform for creating, managing, and deploying AI agents"
    )
    OPENAPI_VERSION = "3.0.2"
    OPENAPI_URL_PREFIX = "/api"
    OPENAPI_SWAGGER_UI_PATH = "/api/docs"
    OPENAPI_SWAGGER_UI_URL = "/api/docs/"

    # CORS settings
    CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "*").split(",")

    # AI Model settings
    MISTRAL_API_KEY = os.environ.get("MISTRAL_API_KEY")
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
    DEFAULT_AI_MODEL = os.environ.get("DEFAULT_AI_MODEL", "mistral-tiny")

    # Cache settings (Redis)
    REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
    CACHE_DEFAULT_TIMEOUT = 3600  # 1 hour

    # File output settings
    OUTPUT_DIR = os.environ.get("OUTPUT_DIR", "outputs")
    FILE_PREVIEW_MAX_BYTES = int(
        os.environ.get("FILE_PREVIEW_MAX_BYTES", str(1024 * 1024))
    )
    FILE_WRITE_MAX_BYTES = int(os.environ.get("FILE_WRITE_MAX_BYTES", str(1024 * 1024)))
    FILE_SHARE_DEFAULT_TTL_SECONDS = int(
        os.environ.get("FILE_SHARE_DEFAULT_TTL_SECONDS", str(7 * 24 * 60 * 60))
    )
    FILE_SHARE_MAX_TTL_SECONDS = int(
        os.environ.get("FILE_SHARE_MAX_TTL_SECONDS", str(30 * 24 * 60 * 60))
    )
    FILE_CLEANUP_ENABLED = os.environ.get("FILE_CLEANUP_ENABLED", "false").lower() in {
        "1",
        "true",
        "yes",
        "on",
    }
    FILE_CLEANUP_INTERVAL_SECONDS = int(
        os.environ.get("FILE_CLEANUP_INTERVAL_SECONDS", str(24 * 60 * 60))
    )
    FILE_TEMPORARY_TTL_HOURS = int(os.environ.get("FILE_TEMPORARY_TTL_HOURS", "24"))
    FILE_OBSOLETE_TTL_DAYS = int(os.environ.get("FILE_OBSOLETE_TTL_DAYS", "30"))
    FILE_KEEP_LATEST_VERSIONS = int(os.environ.get("FILE_KEEP_LATEST_VERSIONS", "3"))
    # When unset, destructive cleanup remains available through FileService but
    # its HTTP administration endpoints are disabled.
    FILE_CLEANUP_TOKEN = os.environ.get("FILE_CLEANUP_TOKEN")

    # Compression settings (Épic 8 - US-058)
    COMPRESSION_ENABLED = os.environ.get("COMPRESSION_ENABLED", "true").lower() in {
        "1",
        "true",
        "yes",
        "on",
    }
    COMPRESSION_DEFAULT_FORMAT = os.environ.get("COMPRESSION_DEFAULT_FORMAT", "gzip").lower()
    COMPRESSION_LEVEL = int(os.environ.get("COMPRESSION_LEVEL", "6"))
    COMPRESSION_KEEP_ORIGINAL = os.environ.get("COMPRESSION_KEEP_ORIGINAL", "true").lower() in {
        "1",
        "true",
        "yes",
        "on",
    }

    # Logging
    LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


class DevelopmentConfig(Config):
    """Development configuration."""

    DEBUG = True
    AUTO_CREATE_DB = True
    SQLALCHEMY_ECHO = True  # Log SQL queries
    LOG_LEVEL = "DEBUG"


class TestingConfig(Config):
    """Testing configuration."""

    TESTING = True
    AUTO_CREATE_DB = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"  # In-memory database for tests
    SQLALCHEMY_ECHO = False
    CACHE_DEFAULT_TIMEOUT = 0  # Disable cache in tests
    LOG_LEVEL = "WARNING"


class ProductionConfig(Config):
    """Production configuration."""

    DEBUG = False
    SQLALCHEMY_ECHO = False
    LOG_LEVEL = "INFO"

    # Security settings for production
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"

    # Database connection pooling
    SQLALCHEMY_POOL_SIZE = 20
    SQLALCHEMY_MAX_OVERFLOW = 10
    SQLALCHEMY_POOL_TIMEOUT = 30
    SQLALCHEMY_POOL_RECYCLE = 3600


# Configuration mapping
config = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
