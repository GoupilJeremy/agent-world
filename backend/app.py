# 🚀 Agent World - Main Application
# Version: 0.1.0 (MVP)
# Description: Point d'entrée principal du backend Flask

"""
Agent World Flask Application

Ce fichier est le point d'entrée principal de l'application backend.
Il initialise Flask, configure les extensions, et enregistre les routes.
"""

from flask import Flask
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_restful import Api

from .config.settings import Config
from .models.base import init_db
from .routes import agents_bp, get_compression_bp, get_performance_bp, get_security_bp, register_resources
from .routes.share_auth import register_share_recipient_auth
from .services.agent_cache_service import AgentCacheService
from .services.agent_service import AgentService
from .services.ai_service import AIService
from .services.auth_service import AuthService
from .services.cache_service import CacheService, get_cache_service
from .services.compression_service import CompressionService
from .services.email_service import EmailService
from .services.file_service import FileService
from .services.history_service import HistoryService
from .services.invitation_service import InvitationService
from .services.prometheus_service import PrometheusService

# Global API instance will be created in create_app


def create_app(config_class=Config):
    """
    Factory function to create and configure the Flask application.

    Args:
        config_class: Configuration class or dict to use (default: Config)

    Returns:
        Flask app instance
    """
    # Create Flask application
    app = Flask(__name__)

    if isinstance(config_class, dict):
        app.config.from_mapping(config_class)
    else:
        app.config.from_object(config_class)
        if hasattr(config_class, "SQLALCHEMY_DATABASE_URI"):
            app.config["SQLALCHEMY_DATABASE_URI"] = config_class.SQLALCHEMY_DATABASE_URI
        if hasattr(config_class, "SQLALCHEMY_TRACK_MODIFICATIONS"):
            app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = (
                config_class.SQLALCHEMY_TRACK_MODIFICATIONS
            )

    # Ensure default config values exist when a bare dict is passed in tests
    app.config.setdefault("CORS_ORIGINS", ["*"])
    app.config.setdefault("RATE_LIMIT_DEFAULT", "100 per minute")
    app.config.setdefault("RATE_LIMIT_AUTH", "10 per minute")
    app.config.setdefault("REDIS_URL", "redis://localhost:6379/0")
    app.config.setdefault("SESSION_COOKIE_SECURE", False)
    app.config.setdefault("SESSION_COOKIE_HTTPONLY", True)
    app.config.setdefault("SESSION_COOKIE_SAMESITE", "Lax")
    app.config.setdefault("AUTH_ACCESS_TOKEN_TTL_SECONDS", 3600)
    app.config.setdefault("AUTH_TOKEN_ISSUER", "agent-world")
    if not app.config.get("SECRET_KEY"):
        app.config["SECRET_KEY"] = "dev-secret-key-change-in-production"
    app.config.setdefault("FILE_PREVIEW_MAX_BYTES", 1024 * 1024)
    app.config.setdefault("FILE_WRITE_MAX_BYTES", 1024 * 1024)
    app.config.setdefault("FILE_SHARE_DEFAULT_TTL_SECONDS", 7 * 24 * 60 * 60)
    app.config.setdefault("FILE_SHARE_MAX_TTL_SECONDS", 30 * 24 * 60 * 60)
    app.config.setdefault("FILE_CLEANUP_ENABLED", False)
    app.config.setdefault("FILE_CLEANUP_INTERVAL_SECONDS", 24 * 60 * 60)
    app.config.setdefault("FILE_TEMPORARY_TTL_HOURS", 24)
    app.config.setdefault("FILE_OBSOLETE_TTL_DAYS", 30)
    app.config.setdefault("FILE_KEEP_LATEST_VERSIONS", 3)
    app.config.setdefault("CACHE_DEFAULT_TIMEOUT", 3600)
    app.config.setdefault("COMPRESSION_ENABLED", True)
    app.config.setdefault("COMPRESSION_DEFAULT_FORMAT", "gzip")
    app.config.setdefault("COMPRESSION_LEVEL", 6)
    app.config.setdefault("COMPRESSION_KEEP_ORIGINAL", True)
    app.config.setdefault("LOG_LEVEL", "INFO")
    app.config.setdefault("MAX_CONTENT_LENGTH", 1024 * 1024)
    app.config.setdefault("AUTO_CREATE_DB", False)

    # Initialize rate limiter
    limiter = Limiter(
        get_remote_address,
        app=app,
        default_limits=[app.config.get("RATE_LIMIT_DEFAULT", "100 per minute")],
        storage_uri=app.config.get("REDIS_URL", "redis://localhost:6379/0"),
    )
    app.extensions["limiter"] = limiter

    # Initialize extensions
    CORS(app, resources={r"/api/*": {"origins": app.config["CORS_ORIGINS"]}})
    api = Api(app, prefix="/api")

    # Initialize database
    init_db(app)

    # Security headers
    @app.after_request
    def set_security_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'"
        if app.config.get("SESSION_COOKIE_SECURE"):
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response

    # Register Flask-RESTful resources
    register_resources(api)

    # Register blueprints
    app.register_blueprint(agents_bp)
    app.register_blueprint(get_security_bp())
    
    # Register performance blueprint (Épic 8)
    app.register_blueprint(get_performance_bp())
    
    # Register compression blueprint (Épic 8 - US-058)
    app.register_blueprint(get_compression_bp())
    
    # Register integrations blueprint
    from .routes import get_integrations_bp
    app.register_blueprint(get_integrations_bp())

    # Initialize services
    history_service = HistoryService()
    agent_service = AgentService(history_service=history_service)
    ai_service = AIService()
    auth_service = AuthService(
        secret_key=app.config["SECRET_KEY"],
        access_token_ttl_seconds=app.config["AUTH_ACCESS_TOKEN_TTL_SECONDS"],
        issuer=app.config["AUTH_TOKEN_ISSUER"],
    )
    file_service = FileService(
        output_dir=app.config.get("OUTPUT_DIR", "outputs"),
        preview_max_bytes=app.config.get("FILE_PREVIEW_MAX_BYTES", 1024 * 1024),
        write_max_bytes=app.config.get("FILE_WRITE_MAX_BYTES", 1024 * 1024),
        share_default_ttl_seconds=app.config.get("FILE_SHARE_DEFAULT_TTL_SECONDS", 7 * 24 * 60 * 60),
        share_max_ttl_seconds=app.config.get("FILE_SHARE_MAX_TTL_SECONDS", 30 * 24 * 60 * 60),
        cleanup_enabled=app.config.get("FILE_CLEANUP_ENABLED", False),
        cleanup_interval_seconds=app.config.get("FILE_CLEANUP_INTERVAL_SECONDS", 24 * 60 * 60),
        temporary_ttl_hours=app.config.get("FILE_TEMPORARY_TTL_HOURS", 24),
        obsolete_ttl_days=app.config.get("FILE_OBSOLETE_TTL_DAYS", 30),
        keep_latest_versions=app.config.get("FILE_KEEP_LATEST_VERSIONS", 3),
    )
    
    # Cache service (Épic 8 - Performance)
    cache_service = CacheService(
        redis_url=app.config.get("REDIS_URL", "redis://localhost:6379/0"),
        default_timeout=app.config.get("CACHE_DEFAULT_TIMEOUT", 3600)
    )
    
    # Agent cache service (Épic 8 - Performance)
    agent_cache_service = AgentCacheService()
    
    # Compression service (Épic 8 - US-058)
    compression_service = CompressionService(
        enabled=app.config.get("COMPRESSION_ENABLED", True),
        default_format=app.config.get("COMPRESSION_DEFAULT_FORMAT", "gzip"),
        compression_level=app.config.get("COMPRESSION_LEVEL", 6),
        keep_original=app.config.get("COMPRESSION_KEEP_ORIGINAL", True),
    )
    
    # Prometheus service (Épic 8 - US-059)
    from .services.prometheus_service import PrometheusService
    prometheus_service = PrometheusService(app=app)
    
    # Collaboration services (Épic 6)
    email_service = EmailService(
        provider=app.config.get("EMAIL_PROVIDER", "smtp"),
        api_key=app.config.get("EMAIL_API_KEY"),
        default_sender=app.config.get("EMAIL_DEFAULT_SENDER"),
        app=app,
    )
    invitation_service = InvitationService(email_service=email_service)

    # Integration services (Épic 7)
    # Importer ici pour éviter les dépendances circulaires
    from .integrations.integration_manager import IntegrationManager
    from .integrations.oauth.oauth_service import OAuthService
    from .integrations.webhooks.webhook_service import WebhookService
    
    oauth_service = OAuthService()
    webhook_service = WebhookService()
    integration_manager = IntegrationManager(
        oauth_service=oauth_service,
        webhook_service=webhook_service,
    )

    # Register services with app context
    app.extensions["agent_service"] = agent_service
    app.extensions["ai_service"] = ai_service
    app.extensions["auth_service"] = auth_service
    app.extensions["file_service"] = file_service
    app.extensions["history_service"] = history_service
    app.extensions["email_service"] = email_service
    app.extensions["invitation_service"] = invitation_service
    app.extensions["cache_service"] = cache_service
    app.extensions["agent_cache_service"] = agent_cache_service
    app.extensions["compression_service"] = compression_service
    app.extensions["prometheus_service"] = prometheus_service
    app.extensions["integration_manager"] = integration_manager
    app.extensions["oauth_service"] = oauth_service
    app.extensions["webhook_service"] = webhook_service
    app.extensions["limiter"] = limiter
    register_share_recipient_auth(app)

    # Health check endpoint
    @app.route("/health")
    def health_check():
        """Health check endpoint for monitoring."""
        return {
            "status": "healthy",
            "version": "0.1.0",
            "service": "agent-world-backend",
        }, 200

    # Root endpoint
    @app.route("/")
    def index():
        """Root endpoint with API information."""
        return {
            "name": "Agent World API",
            "version": "0.1.0",
            "description": (
                "Open-source platform for creating, managing, "
                "and deploying AI agents"
            ),
            "docs": "/api/docs",
            "health": "/health",
        }, 200

    return app


# Create application instance
app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
