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
from flask_sqlalchemy import SQLAlchemy
from .config.settings import Config
from .routes import agents_bp, register_resources
from .models.base import db, init_db
from .services.agent_service import AgentService
from .services.ai_service import AIService

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
    app.config['SQLALCHEMY_DATABASE_URI'] = config_class.SQLALCHEMY_DATABASE_URI
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = config_class.SQLALCHEMY_TRACK_MODIFICATIONS
    
    # Initialize extensions
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    api = Api(app, prefix="/api")
    
    # Initialize database
    init_db(app)
    
    # Register Flask-RESTful resources
    register_resources(api)
    
    # Register blueprints
    app.register_blueprint(agents_bp)
    
    # Initialize services
    agent_service = AgentService()
    ai_service = AIService()
    
    # Register services with app context
    app.extensions['agent_service'] = agent_service
    app.extensions['ai_service'] = ai_service
    
    # Health check endpoint
    @app.route('/health')
    def health_check():
        """Health check endpoint for monitoring."""
        return {
            "status": "healthy",
            "version": "0.1.0",
            "service": "agent-world-backend"
        }, 200
    
    # Root endpoint
    @app.route('/')
    def index():
        """Root endpoint with API information."""
        return {
            "name": "Agent World API",
            "version": "0.1.0",
            "description": "Open-source platform for creating, managing, and deploying AI agents",
            "docs": "/api/docs",
            "health": "/health"
        }, 200
    
    return app


# Create application instance
app = create_app()


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
