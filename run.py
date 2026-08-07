#!/usr/bin/env python3
# 🏃 Agent World - Run Script
# Version: 0.1.0 (MVP)
# Description: Script principal pour exécuter l'application

"""
Run script for Agent World.

Ce script est le point d'entrée principal pour exécuter l'application
en mode développement ou production.

Usage:
    python run.py                    # Development mode (debug=True)
    python run.py --production       # Production mode
    python run.py --host 0.0.0.0 --port 8080  # Custom host and port
"""

import argparse
from backend.app import create_app
from backend.config.settings import DevelopmentConfig, ProductionConfig


def main():
    """Main function to run the Agent World application."""
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description='Run Agent World application',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run.py                         Run in development mode
  python run.py --production            Run in production mode
  python run.py --host 0.0.0.0 --port 80  Run on all interfaces, port 80
        """
    )
    
    parser.add_argument(
        '--production',
        action='store_true',
        help='Run in production mode (debug=False)'
    )
    
    parser.add_argument(
        '--host',
        type=str,
        default='127.0.0.1',
        help='Host to bind to (default: 127.0.0.1)'
    )
    
    parser.add_argument(
        '--port',
        type=int,
        default=5000,
        help='Port to listen on (default: 5000)'
    )
    
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug mode (overrides production)'
    )
    
    args = parser.parse_args()
    
    # Select configuration
    if args.production and not args.debug:
        config = ProductionConfig
        debug = False
    else:
        config = DevelopmentConfig
        debug = True
    
    # Create application
    app = create_app(config)
    
    # Print startup information
    print("=" * 60)
    print("🚀 Agent World - Starting Application")
    print("=" * 60)
    print(f"📦 Version: {app.config.get('API_VERSION', '0.1.0')}")
    print(f"🌐 Environment: {'Production' if args.production else 'Development'}")
    print(f"🔌 Host: {args.host}")
    print(f"🔢 Port: {args.port}")
    print(f"🐛 Debug: {debug}")
    print(f"🗃️ Database: {app.config.get('SQLALCHEMY_DATABASE_URI', 'Not configured')}")
    print("=" * 60)
    
    # Run application
    try:
        app.run(host=args.host, port=args.port, debug=debug)
    except KeyboardInterrupt:
        print("\n👋 Agent World - Shutting down gracefully...")
    except Exception as e:
        print(f"\n❌ Agent World - Error: {str(e)}")
        raise


if __name__ == '__main__':
    main()
