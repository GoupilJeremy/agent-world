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
from flask_restful import Api

from .config.settings import Config
from .models.base import init_db
from .routes import agents_bp, register_resources, get_performance_bp, get_compression_bp
from .routes.share_auth import register_share_recipient_auth
from .services.agent_cache_service import AgentCacheService
from .services.agent_service import AgentService
from .services.ai_service import AIService
from .services.audit_service import AuditService
from .services.auth_service import AuthService
from .services.cache_service import CacheService, get_cache_service
from .services.compression_service import CompressionService
from .services.email_service import EmailService
from .services.file_service import FileService
from .services.history_service import HistoryService
from .services.invitation_service import InvitationService
from .services.encryption_service import EncryptionService, init_encryption_service
from .services.log_masking_service import LogMaskingService, setup_log_masking
from .services.permission_service import PermissionService
from .services.prometheus_service import PrometheusService
from .services.two_factor_service import TwoFactorService

# Global API instance will be created in create_app


def create_app(config_class=Config):
    """
    Factory function to create and configure the Flask application.

    Args:
        config_class: Configuration class to use (default: Config)

    Returns:
        Flask app instance
    """
    # Create Flask application
    app = Flask(__name__)

    # Load configuration
    app.config.from_object(config_class)
    app.config["SQLALCHEMY_DATABASE_URI"] = config_class.SQLALCHEMY_DATABASE_URI
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = (
        config_class.SQLALCHEMY_TRACK_MODIFICATIONS
    )

    # Initialize extensions
    CORS(app, resources={r"/api/*": {"origins": app.config["CORS_ORIGINS"]}})
    api = Api(app, prefix="/api")

    # Initialize database
    init_db(app)

    # Register Flask-RESTful resources
    register_resources(api)

    # Register blueprints
    app.register_blueprint(agents_bp)
    
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
    
    # Two-Factor Authentication service (EPIC 10 - US-065)
    two_factor_service = TwoFactorService(
        encryption_key=app.config["TWO_FACTOR_ENCRYPTION_KEY"],
    )
    
    # Permission service (EPIC 10 - US-066)
    permission_service = PermissionService()
    
    # Encryption service (EPIC 10 - US-067)
    encryption_service = EncryptionService(
        master_key=app.config["ENCRYPTION_MASTER_KEY"],
        key_ttl_days=app.config["ENCRYPTION_KEY_TTL_DAYS"],
    )
    
    # Audit service (EPIC 10 - US-068)
    audit_service = AuditService(
        retention_days=app.config.get("AUDIT_LOG_RETENTION_DAYS", 90),
    )
    
    # Log masking service (EPIC 10 - US-067)
    log_masking_service = LogMaskingService()
    
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
    prometheus_service = PrometheusService()
    prometheus_service.init_app(app)
    
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
    app.extensions["two_factor_service"] = two_factor_service
    app.extensions["permission_service"] = permission_service
    app.extensions["encryption_service"] = encryption_service
    app.extensions["log_masking_service"] = log_masking_service
    app.extensions["audit_service"] = audit_service
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
    register_share_recipient_auth(app)
    
    # Initialize default permissions and roles (EPIC 10 - US-066)
    with app.app_context():
        permission_service.initialize_defaults()
    
    # Initialize encryption service (EPIC 10 - US-067)
    with app.app_context():
        from .models.encryption_key import EncryptionKey
        if not EncryptionKey.get_active_key():
            # Create and activate a default key if none exists
            key = encryption_service.create_and_store_key(
                description="Default encryption key"
            )
            encryption_service.activate_key(key.key_id)
    
    # Initialize log masking (EPIC 10 - US-067)
    # Set up log masking for the root logger
    log_masking_service.setup_logging()

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
