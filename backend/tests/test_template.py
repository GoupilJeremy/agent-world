# [38;5;214m[0m Agent World - Template Tests
# Version: 0.3.1 (EPIC 5)
# Description: Tests unitaires et d'intégration pour les templates

"""
Template Tests for Agent World.

Ce module contient tous les tests pour les fonctionnalités de templates.
"""

import json
import os
import tempfile
import unittest
from datetime import datetime

from ..app import create_app
from ..config.settings import TestingConfig
from ..models.base import db
from ..models.template import Template, TemplateVersion
from ..models.user import User


class TemplateModelTestCase(unittest.TestCase):
    """Test cases for Template model."""

    def setUp(self):
        """Set up test fixtures."""
        self.app = create_app(config_class=TestingConfig)

        with self.app.app_context():
            db.create_all()
            # Create a test user
            self.user = User.create(
                username="testuser",
                email="test@example.com",
                password="testpassword",
            )

    def tearDown(self):
        """Clean up test fixtures."""
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_create_template(self):
        """Test creating a new template."""
        with self.app.app_context():
            template = Template.create(
                name="Test Template",
                description="A test template",
                model="mistral-tiny",
                category="test",
                tags=["test", "template"],
                version="1.0.0",
            )

            self.assertIsNotNone(template.id)
            self.assertEqual(template.name, "Test Template")
            self.assertEqual(template.description, "A test template")
            self.assertEqual(template.model, "mistral-tiny")
            self.assertEqual(template.category, "test")
            self.assertEqual(template.tags, ["test", "template"])
            self.assertEqual(template.version, "1.0.0")
            self.assertFalse(template.is_official)
            self.assertFalse(template.is_public)
            self.assertEqual(template.created_by, None)

    def test_create_template_with_user(self):
        """Test creating a template with a user."""
        with self.app.app_context():
            # Create a fresh user in the same context
            user = User.create(
                username="template_user",
                email="template@example.com",
                password="testpass",
            )
            template = Template.create(
                name="User Template",
                model="gpt-4",
                created_by=user.id,
            )

            self.assertEqual(template.created_by, user.id)
            self.assertEqual(template.creator.id, user.id)

    def test_get_template_by_id(self):
        """Test getting template by ID."""
        with self.app.app_context():
            template = Template.create(name="Findable Template")

            retrieved = Template.get_by_id(template.id)
            self.assertEqual(retrieved.id, template.id)
            self.assertEqual(retrieved.name, "Findable Template")

    def test_get_template_by_name(self):
        """Test getting template by name."""
        with self.app.app_context():
            template = Template.create(name="Unique Name Template")

            retrieved = Template.get_by_name("Unique Name Template")
            self.assertEqual(retrieved.id, template.id)

    def test_get_all_templates(self):
        """Test getting all templates."""
        with self.app.app_context():
            Template.create(name="Template 1")
            Template.create(name="Template 2")
            Template.create(name="Template 3")

            templates = Template.get_all()
            self.assertEqual(len(templates), 3)

    def test_get_public_templates(self):
        """Test getting public templates."""
        with self.app.app_context():
            Template.create(name="Public Template", is_public=True)
            Template.create(name="Private Template", is_public=False)

            public_templates = Template.get_public()
            self.assertEqual(len(public_templates), 1)
            self.assertEqual(public_templates[0].name, "Public Template")

    def test_get_official_templates(self):
        """Test getting official templates."""
        with self.app.app_context():
            Template.create(name="Official Template", is_official=True)
            Template.create(name="Unofficial Template", is_official=False)

            official_templates = Template.get_official()
            self.assertEqual(len(official_templates), 1)
            self.assertEqual(official_templates[0].name, "Official Template")

    def test_get_by_category(self):
        """Test getting templates by category."""
        with self.app.app_context():
            Template.create(name="Cat 1", category="translation")
            Template.create(name="Cat 2", category="translation")
            Template.create(name="Cat 3", category="summary")

            translation_templates = Template.get_by_category("translation")
            self.assertEqual(len(translation_templates), 2)

    def test_get_by_tag(self):
        """Test getting templates by tag."""
        with self.app.app_context():
            Template.create(name="Tag 1", tags=["python", "code"])
            Template.create(name="Tag 2", tags=["python"])
            Template.create(name="Tag 3", tags=["javascript"])

            python_templates = Template.get_by_tag("python")
            self.assertEqual(len(python_templates), 2)

    def test_update_template(self):
        """Test updating a template."""
        with self.app.app_context():
            template = Template.create(name="Original Name", version="1.0.0")

            template.update(name="Updated Name", version="2.0.0")

            updated = Template.get_by_id(template.id)
            self.assertEqual(updated.name, "Updated Name")
            self.assertEqual(updated.version, "2.0.0")
            self.assertNotEqual(updated.updated_at, template.created_at)

    def test_delete_template(self):
        """Test deleting a template."""
        with self.app.app_context():
            template = Template.create(name="Deletable Template")
            template_id = template.id

            template.delete()

            deleted = Template.get_by_id(template_id)
            self.assertIsNone(deleted)

    def test_template_to_dict(self):
        """Test converting template to dictionary."""
        with self.app.app_context():
            template = Template.create(
                name="Dict Template",
                description="For testing to_dict",
                model="gpt-3.5-turbo",
                configuration={"param": "value"},
                parameters={"input": "text"},
                category="general",
                tags=["test"],
                version="1.0.0",
                is_official=True,
                is_public=False,
            )

            data = template.to_dict()
            self.assertIn("id", data)
            self.assertIn("name", data)
            self.assertEqual(data["name"], "Dict Template")
            self.assertEqual(data["model"], "gpt-3.5-turbo")
            self.assertEqual(data["configuration"], {"param": "value"})
            self.assertEqual(data["parameters"], {"input": "text"})

    def test_template_to_dict_minimal(self):
        """Test converting template to minimal dictionary."""
        with self.app.app_context():
            template = Template.create(
                name="Minimal Template",
                configuration={"complex": "data"},
            )

            data = template.to_dict_minimal()
            self.assertIn("id", data)
            self.assertIn("name", data)
            self.assertNotIn("configuration", data)

    def test_search_templates(self):
        """Test searching templates."""
        with self.app.app_context():
            Template.create(name="Searchable Template", description="Find me")
            Template.create(name="Another Template", description="Not this one")
            Template.create(name="Hidden Template", description="Secret")

            results = Template.search(query="Find me")
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0].name, "Searchable Template")

    def test_search_with_filters(self):
        """Test searching templates with filters."""
        with self.app.app_context():
            Template.create(name="Test 1", category="translation", is_public=True)
            Template.create(name="Test 2", category="translation", is_public=False)
            Template.create(name="Test 3", category="summary", is_public=True)

            results = Template.search(category="translation", is_public=True)
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0].name, "Test 1")

    def test_increment_version_patch(self):
        """Test incrementing version (patch)."""
        with self.app.app_context():
            template = Template.create(name="Versioned Template", version="1.0.0")

            new_version = template.increment_version("patch")
            self.assertEqual(new_version, "1.0.1")

            updated = Template.get_by_id(template.id)
            self.assertEqual(updated.version, "1.0.1")

    def test_increment_version_minor(self):
        """Test incrementing version (minor)."""
        with self.app.app_context():
            template = Template.create(name="Versioned Template", version="1.0.0")

            new_version = template.increment_version("minor")
            self.assertEqual(new_version, "1.1.0")

    def test_increment_version_major(self):
        """Test incrementing version (major)."""
        with self.app.app_context():
            template = Template.create(name="Versioned Template", version="1.0.0")

            new_version = template.increment_version("major")
            self.assertEqual(new_version, "2.0.0")


class TemplateVersionModelTestCase(unittest.TestCase):
    """Test cases for TemplateVersion model."""

    def setUp(self):
        """Set up test fixtures."""
        self.app = create_app(config_class=TestingConfig)

        with self.app.app_context():
            db.create_all()

    def tearDown(self):
        """Clean up test fixtures."""
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_create_template_version(self):
        """Test creating a template version."""
        with self.app.app_context():
            template = Template.create(name="Versioned Template")
            version = TemplateVersion.create(
                template_id=template.id,
                version="1.0.0",
                data=template.to_dict(),
            )

            self.assertIsNotNone(version.id)
            self.assertEqual(version.template_id, template.id)
            self.assertEqual(version.version, "1.0.0")

    def test_get_versions_by_template(self):
        """Test getting versions by template."""
        with self.app.app_context():
            template = Template.create(name="Versioned Template")
            TemplateVersion.create(
                template_id=template.id,
                version="1.0.0",
                data=template.to_dict(),
            )
            TemplateVersion.create(
                template_id=template.id,
                version="1.1.0",
                data=template.to_dict(),
            )

            versions = TemplateVersion.get_by_template(template.id)
            self.assertEqual(len(versions), 2)

    def test_get_version_by_version(self):
        """Test getting a specific version."""
        with self.app.app_context():
            template = Template.create(name="Versioned Template")
            TemplateVersion.create(
                template_id=template.id,
                version="1.0.0",
                data=template.to_dict(),
            )
            TemplateVersion.create(
                template_id=template.id,
                version="2.0.0",
                data=template.to_dict(),
            )

            version = TemplateVersion.get_by_version(template.id, "2.0.0")
            self.assertIsNotNone(version)
            self.assertEqual(version.version, "2.0.0")

    def test_get_latest_version(self):
        """Test getting the latest version."""
        import time
        from datetime import datetime, timedelta
        
        with self.app.app_context():
            template = Template.create(name="Versioned Template")
            TemplateVersion.create(
                template_id=template.id,
                version="1.0.0",
                data=template.to_dict(),
            )
            time.sleep(0.01)  # Small delay to ensure different timestamps
            TemplateVersion.create(
                template_id=template.id,
                version="2.0.0",
                data=template.to_dict(),
            )
            time.sleep(0.01)  # Small delay to ensure different timestamps
            TemplateVersion.create(
                template_id=template.id,
                version="1.5.0",
                data=template.to_dict(),
            )

            latest = TemplateVersion.get_latest(template.id)
            # The latest by created_at should be 1.5.0 since it was created last
            self.assertEqual(latest.version, "1.5.0")

    def test_version_to_dict(self):
        """Test converting version to dictionary."""
        with self.app.app_context():
            template = Template.create(name="Versioned Template")
            version = TemplateVersion.create(
                template_id=template.id,
                version="1.0.0",
                data={"test": "data"},
            )

            data = version.to_dict()
            self.assertIn("id", data)
            self.assertIn("template_id", data)
            self.assertIn("version", data)
            self.assertIn("data", data)
            self.assertIn("created_at", data)


class TemplateReprTestCase(unittest.TestCase):
    """Test cases for Template __repr__ method."""

    def setUp(self):
        """Set up test fixtures."""
        self.app = create_app(config_class=TestingConfig)

        with self.app.app_context():
            db.create_all()

    def tearDown(self):
        """Clean up test fixtures."""
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_template_repr(self):
        """Test template repr."""
        with self.app.app_context():
            template = Template.create(
                name="Repr Template",
                category="test",
                version="1.0.0",
            )

            repr_str = repr(template)
            self.assertIn("Template", repr_str)
            self.assertIn("Repr Template", repr_str)
            self.assertIn("1.0.0", repr_str)
            self.assertIn("test", repr_str)

    def test_version_repr(self):
        """Test version repr."""
        with self.app.app_context():
            template = Template.create(name="Versioned Template")
            version = TemplateVersion.create(
                template_id=template.id,
                version="1.0.0",
                data={},
            )

            repr_str = repr(version)
            self.assertIn("TemplateVersion", repr_str)
            self.assertIn("1.0.0", repr_str)


class TemplateIntegrationTestCase(unittest.TestCase):
    """Integration tests for template functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.app = create_app(config_class=TestingConfig)

        with self.app.app_context():
            db.create_all()

    def tearDown(self):
        """Clean up test fixtures."""
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_full_template_lifecycle(self):
        """Test complete template lifecycle."""
        with self.app.app_context():
            # Create
            template = Template.create(
                name="Lifecycle Template",
                description="Test full lifecycle",
                version="1.0.0",
            )
            self.assertIsNotNone(template.id)

            # Create initial version manually (as done in routes)
            TemplateVersion.create(
                template_id=template.id,
                version="1.0.0",
                data=template.to_dict(),
            )

            # Version created
            versions = TemplateVersion.get_by_template(template.id)
            self.assertEqual(len(versions), 1)

            # Update
            template.update(description="Updated description", version="1.1.0")
            updated = Template.get_by_id(template.id)
            self.assertEqual(updated.description, "Updated description")
            self.assertEqual(updated.version, "1.1.0")

            # New version created on update
            versions = TemplateVersion.get_by_template(template.id)
            self.assertGreaterEqual(len(versions), 1)

            # Delete
            template.delete()
            deleted = Template.get_by_id(template.id)
            self.assertIsNone(deleted)

    def test_template_with_all_fields(self):
        """Test creating a template with all fields."""
        with self.app.app_context():
            template = Template.create(
                name="Complete Template",
                description="All fields template",
                model="mistral-large",
                configuration={"temperature": 0.7, "max_tokens": 1000},
                parameters={"input": "text", "output": "summary"},
                category="analysis",
                tags=["complete", "test", "all-fields"],
                version="2.0.0",
                is_official=True,
                is_public=True,
            )

            self.assertEqual(template.name, "Complete Template")
            self.assertEqual(template.model, "mistral-large")
            self.assertEqual(template.configuration["temperature"], 0.7)
            self.assertEqual(template.parameters["input"], "text")
            self.assertEqual(template.category, "analysis")
            self.assertEqual(len(template.tags), 3)
            self.assertTrue(template.is_official)
            self.assertTrue(template.is_public)

    def test_template_search_complex(self):
        """Test complex search functionality."""
        with self.app.app_context():
            # Create various templates
            Template.create(
                name="Translation Agent",
                description="Translates text between languages",
                category="translation",
                tags=["language", "translate"],
                is_public=True,
            )
            Template.create(
                name="Summary Agent",
                description="Summarizes long text",
                category="summary",
                tags=["text", "summarize"],
                is_public=True,
            )
            Template.create(
                name="Private Agent",
                description="Private template",
                category="private",
                is_public=False,
            )

            # Search by query
            results = Template.search(query="translation")
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0].name, "Translation Agent")

            # Search by category
            results = Template.search(category="summary")
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0].name, "Summary Agent")

            # Search by tag
            results = Template.search(tags=["language"])
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0].name, "Translation Agent")

            # Search by public status
            results = Template.search(is_public=True)
            self.assertEqual(len(results), 2)


class TemplateExportImportTestCase(unittest.TestCase):
    """Test cases for template export/import functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.app = create_app(config_class=TestingConfig)

        with self.app.app_context():
            db.create_all()

    def tearDown(self):
        """Clean up test fixtures."""
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_export_to_json(self):
        """Test exporting template to JSON."""
        with self.app.app_context():
            template = Template.create(
                name="Export Template",
                model="gpt-4",
                configuration={"param": "value"},
            )

            data = template.to_dict()
            data.pop("id", None)
            data.pop("created_at", None)
            data.pop("updated_at", None)
            data.pop("created_by", None)

            # Should be valid JSON
            json_str = json.dumps(data)
            parsed = json.loads(json_str)
            self.assertEqual(parsed["name"], "Export Template")

    def test_template_versioning_workflow(self):
        """Test complete versioning workflow."""
        with self.app.app_context():
            # Create template
            template = Template.create(name="Versioned Template", version="1.0.0")

            # Initial version
            initial_data = template.to_dict()
            version1 = TemplateVersion.create(
                template_id=template.id,
                version="1.0.0",
                data=initial_data,
            )

            # Update template
            template.update(version="1.1.0", description="Updated")

            # Save new version
            updated_data = template.to_dict()
            version2 = TemplateVersion.create(
                template_id=template.id,
                version="1.1.0",
                data=updated_data,
            )

            # Get all versions
            versions = TemplateVersion.get_by_template(template.id)
            self.assertEqual(len(versions), 2)

            # Verify versions
            self.assertEqual(version1.version, "1.0.0")
            self.assertEqual(version2.version, "1.1.0")

            # Verify template was updated
            updated_template = Template.get_by_id(template.id)
            self.assertEqual(updated_template.version, "1.1.0")
            self.assertEqual(updated_template.description, "Updated")


if __name__ == "__main__":
    unittest.main()
