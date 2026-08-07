"""Pytest-wide configuration for isolated database tests."""

import os

# backend.app creates a module-level application during import. Configure it to
# use an in-memory database before test modules import the application factory.
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
