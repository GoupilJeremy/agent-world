#!/usr/bin/env python3
# 📦 Agent World - Setup Script
# Version: 0.1.0 (MVP)
# Description: Script d'installation pour le package Python

"""
Setup script for Agent World.

Ce script permet d'installer le package Agent World en mode développement
ou production.

Usage:
    pip install -e .          # Installation en mode éditable (développement)
    pip install .             # Installation normale
    python setup.py develop    # Mode développement
"""

import re
from pathlib import Path

from setuptools import find_packages, setup

# Lire la description depuis le README
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding="utf-8")

# Lire la version depuis pyproject.toml
version_match = re.search(
    r"^version = ['\"]([^'\"]+)['\"]",
    (this_directory / "pyproject.toml").read_text(),
    re.M,
)
version = version_match.group(1) if version_match else "0.1.0"


setup(
    name="agent-world",
    version=version,
    description="Plateforme open-source pour créer, gérer et déployer des agents IA",
    long_description=long_description,
    long_description_content_type="text/markdown",
    
    author="Jeremy Goupil",
    author_email="goupiljeremy@gmail.com",
    
    url="https://github.com/GoupilJeremy/agent-world",
    project_urls={
        "Bug Tracker": "https://github.com/GoupilJeremy/agent-world/issues",
        "Documentation": "https://github.com/GoupilJeremy/agent-world#readme",
        "Source Code": "https://github.com/GoupilJeremy/agent-world",
    },
    
    packages=find_packages(),
    python_requires=">=3.10",
    
    install_requires=[
        # Framework & Core
        "Flask>=3.0.0",
        "Flask-RESTful>=0.3.10",
        "Flask-CORS>=4.0.0",
        "Flask-SQLAlchemy>=3.1.1",
        "python-dotenv>=1.0.0",
        
        # Database
        "SQLAlchemy>=2.0.25",
        "psycopg2-binary>=2.9.9",
        "alembic>=1.13.1",
        
        # AI Models
        "requests>=2.31.0",
        "httpx>=0.26.0",
        
        # Security
        "pyjwt>=2.8.0",
        "passlib>=1.7.4",
        "werkzeug>=3.0.0",
        
        # Performance
        "redis>=5.0.1",
    ],
    
    extras_require={
        "dev": [
            # Testing
            "pytest>=8.0.0",
            "pytest-cov>=4.1.0",
            "pytest-flask>=1.3.0",
            "pytest-mock>=3.12.0",
            "factory-boy>=3.3.0",
            "coverage>=7.4.0",
            
            # Linting & Formatting
            "black>=24.1.1",
            "flake8>=6.1.0",
            "isort>=5.13.2",
            "mypy>=1.8.0",
            "pylint>=3.0.3",
            
            # Documentation
            "mkdocs>=1.5.3",
            "mkdocs-material>=9.5.6",
            
            # Build & Package
            "setuptools>=69.0.2",
            "wheel>=0.42.0",
            "twine>=5.0.0",
            
            # Development
            "pre-commit>=3.6.0",
            "tox>=4.12.1",
        ],
        "docs": [
            "mkdocs>=1.5.3",
            "mkdocs-material>=9.5.6",
            "pymdown-extensions>=10.7.1",
        ],
        "test": [
            "pytest>=8.0.0",
            "pytest-cov>=4.1.0",
            "pytest-flask>=1.3.0",
            "factory-boy>=3.3.0",
            "coverage>=7.4.0",
        ],
    },
    
    entry_points={
        "console_scripts": [
            "agent=backend.cli.main:main",
            "agent-world=run:main",
        ],
    },
    
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Framework :: Flask",
        "Typing :: Typed",
    ],
    
    keywords=[
        "ai",
        "agents",
        "llm",
        "mistral",
        "openai",
        "api",
        "cli",
        "flask",
        "artificial-intelligence",
        "machine-learning",
    ],
    
    package_data={
        "backend": ["**/*.py"],
        "tests": ["**/*.py"],
    },
    
    include_package_data=True,
    
    zip_safe=False,
)
