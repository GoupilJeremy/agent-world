# Agent World - CLI Templates Commands
# Version: 0.3.1 (EPIC 5)
# Description: Commandes CLI pour la gestion des templates d'agents

"""
CLI Templates Commands for Agent World.

Ce module contient les commandes CLI spécifiques aux templates.
Il est intégré au parser principal dans main.py.
"""

import argparse
import json
from typing import List

from ..models.template import Template, TemplateVersion


def add_template_commands(subparsers: argparse._SubParsersAction) -> None:
    """Add template-related commands to the CLI parser."""

    # Template subcommand group
    template_parser = subparsers.add_parser(
        "template",
        help="Manage agent templates",
        description="Create, list, update, and delete agent templates",
    )

    template_subparsers = template_parser.add_subparsers(
        title="template commands",
        dest="template_command",
        required=True,
    )

    # Create template command
    template_create_parser = template_subparsers.add_parser(
        "create",
        help="Create a new template",
        description="Create a new reusable agent template",
    )
    template_create_parser.add_argument(
        "--name", "-n", required=True, help="Name of the template (required)"
    )
    template_create_parser.add_argument(
        "--description", "-d", help="Description of the template"
    )
    template_create_parser.add_argument(
        "--model",
        "-m",
        default="mistral-tiny",
        help="AI model to use (default: mistral-tiny)",
    )
    template_create_parser.add_argument(
        "--config",
        "-c",
        type=json.loads,
        default={},
        help="JSON configuration for the template",
    )
    template_create_parser.add_argument(
        "--parameters",
        "-p",
        type=json.loads,
        default={},
        help="JSON parameters for the template",
    )
    template_create_parser.add_argument(
        "--category",
        "-g",
        default="general",
        help="Category for the template (default: general)",
    )
    template_create_parser.add_argument(
        "--tags",
        "-t",
        nargs="*",
        default=[],
        help="Tags for the template (space-separated)",
    )
    template_create_parser.add_argument(
        "--version",
        default="1.0.0",
        help="Version of the template (default: 1.0.0)",
    )
    template_create_parser.add_argument(
        "--official",
        action="store_true",
        help="Mark as official template",
    )
    template_create_parser.add_argument(
        "--public",
        action="store_true",
        help="Make template publicly accessible",
    )

    # List templates command
    template_list_parser = template_subparsers.add_parser(
        "list",
        help="List all templates",
        description="List all available agent templates with filters",
    )
    template_list_parser.add_argument("--category", "-g", help="Filter by category")
    template_list_parser.add_argument("--tag", "-t", help="Filter by tag")
    template_list_parser.add_argument(
        "--search", "-s", help="Search in name and description"
    )
    template_list_parser.add_argument(
        "--official",
        action="store_true",
        help="Show only official templates",
    )
    template_list_parser.add_argument(
        "--public",
        action="store_true",
        help="Show only public templates",
    )
    template_list_parser.add_argument(
        "--all", "-a", action="store_true", help="Show all templates"
    )
    template_list_parser.add_argument(
        "--limit", "-l", type=int, default=10, help="Maximum number of results"
    )

    # Show template command
    template_show_parser = template_subparsers.add_parser(
        "show",
        help="Show template details",
        description="Show detailed information about a specific template",
    )
    template_show_parser.add_argument("id", type=int, help="ID of the template to show")
    template_show_parser.add_argument(
        "--versions",
        "-v",
        action="store_true",
        help="Show template versions",
    )

    # Update template command
    template_update_parser = template_subparsers.add_parser(
        "update",
        help="Update a template",
        description="Update an existing template",
    )
    template_update_parser.add_argument(
        "id", type=int, help="ID of the template to update"
    )
    template_update_parser.add_argument(
        "--name", "-n", help="New name for the template"
    )
    template_update_parser.add_argument(
        "--description", "-d", help="New description for the template"
    )
    template_update_parser.add_argument(
        "--model", "-m", help="New AI model for the template"
    )
    template_update_parser.add_argument(
        "--config",
        "-c",
        type=json.loads,
        help="New JSON configuration for the template",
    )
    template_update_parser.add_argument(
        "--parameters",
        "-p",
        type=json.loads,
        help="New JSON parameters for the template",
    )
    template_update_parser.add_argument(
        "--category", "-g", help="New category for the template"
    )
    template_update_parser.add_argument(
        "--tags",
        "-t",
        nargs="*",
        default=[],
        help="New tags for the template (space-separated)",
    )
    template_update_parser.add_argument(
        "--version", help="New version for the template"
    )
    template_update_parser.add_argument(
        "--official",
        action="store_true",
        help="Mark as official template",
    )
    template_update_parser.add_argument(
        "--public",
        action="store_true",
        help="Make template publicly accessible",
    )

    # Delete template command
    template_delete_parser = template_subparsers.add_parser(
        "delete",
        help="Delete a template",
        description="Delete an existing template from the database",
    )
    template_delete_parser.add_argument(
        "id", type=int, help="ID of the template to delete"
    )
    template_delete_parser.add_argument(
        "--force", "-f", action="store_true", help="Force deletion without confirmation"
    )

    # Export template command
    template_export_parser = template_subparsers.add_parser(
        "export",
        help="Export a template",
        description="Export a template to JSON or YAML format",
    )
    template_export_parser.add_argument(
        "id", type=int, help="ID of the template to export"
    )
    template_export_parser.add_argument(
        "--format",
        "-f",
        choices=["json", "yaml"],
        default="json",
        help="Export format (default: json)",
    )
    template_export_parser.add_argument(
        "--output", "-o", help="Output file path (default: stdout)"
    )

    # Import template command
    template_import_parser = template_subparsers.add_parser(
        "import",
        help="Import a template",
        description="Import a template from JSON or YAML file",
    )
    template_import_parser.add_argument(
        "file", help="Path to JSON or YAML file to import"
    )

    # Customize template command
    template_customize_parser = template_subparsers.add_parser(
        "customize",
        help="Customize a template",
        description="Customize a template before using it to create an agent",
    )
    template_customize_parser.add_argument(
        "id", type=int, help="ID of the template to customize"
    )
    template_customize_parser.add_argument(
        "--model", "-m", help="Override the AI model"
    )
    template_customize_parser.add_argument(
        "--config",
        "-c",
        type=json.loads,
        default={},
        help="Override configuration (JSON)",
    )
    template_customize_parser.add_argument(
        "--parameters",
        "-p",
        type=json.loads,
        default={},
        help="Override parameters (JSON)",
    )

    # Template versions commands
    template_versions_parser = template_subparsers.add_parser(
        "versions",
        help="Manage template versions",
        description="List, restore, or manage template versions",
    )
    template_versions_subparsers = template_versions_parser.add_subparsers(
        title="versions commands",
        dest="versions_command",
        required=True,
    )

    # List versions
    versions_list_parser = template_versions_subparsers.add_parser(
        "list", help="List all versions of a template"
    )
    versions_list_parser.add_argument("id", type=int, help="ID of the template")

    # Restore version
    versions_restore_parser = template_versions_subparsers.add_parser(
        "restore", help="Restore a specific version of a template"
    )
    versions_restore_parser.add_argument("id", type=int, help="ID of the template")
    versions_restore_parser.add_argument(
        "version", help="Version to restore (e.g., '1.0.0')"
    )


class TemplateCLIHandler:
    """Handler for template CLI commands."""

    def __init__(self, verbose: bool = False, output_format: str = "table"):
        """Initialize the template CLI handler."""
        self.verbose = verbose
        self.format = output_format

    def handle_template_create(self, args: argparse.Namespace) -> int:
        """Handle the template create command."""
        try:
            from flask import has_app_context

            from ..app import app

            if not has_app_context():
                with app.app_context():
                    return self._create_template(args)
            else:
                return self._create_template(args)
        except Exception as e:
            if self.verbose:
                import traceback

                traceback.print_exc()
            print(f"Error creating template: {str(e)}")
            return 1

    def _create_template(self, args: argparse.Namespace) -> int:
        """Create a new template."""
        template_data = {
            "name": args.name,
            "description": args.description,
            "model": args.model,
            "configuration": args.config,
            "parameters": args.parameters,
            "category": args.category,
            "tags": args.tags,
            "version": args.version,
            "is_official": args.official,
            "is_public": args.public,
        }

        if self.verbose:
            print(f"Creating template: {args.name}")

        existing_template = Template.get_by_name(args.name)
        if existing_template:
            print(f"Template with name '{args.name}' already exists")
            return 1

        template = Template.create(**template_data)
        TemplateVersion.create(
            template_id=template.id,
            version=template.version,
            data=template.to_dict(),
        )

        if self.verbose:
            print(f"Template created with ID: {template.id}")

        self.print_template(template)
        return 0

    def handle_template_list(self, args: argparse.Namespace) -> int:
        """Handle the template list command."""
        try:
            from flask import has_app_context

            from ..app import app

            if not has_app_context():
                with app.app_context():
                    return self._list_templates(args)
            else:
                return self._list_templates(args)
        except Exception as e:
            if self.verbose:
                import traceback

                traceback.print_exc()
            print(f"Error listing templates: {str(e)}")
            return 1

    def _list_templates(self, args: argparse.Namespace) -> int:
        """List all templates with filters."""
        if args.search or args.category or args.tag or args.official or args.public:
            templates = Template.search(
                query=args.search,
                category=args.category,
                tags=[args.tag] if args.tag else None,
                is_public=args.public if args.public is not None else None,
                limit=args.limit,
            )
            if args.official:
                templates = [t for t in templates if t.is_official]
        else:
            templates = Template.get_all()

        if not templates:
            print("No templates found")
            return 0

        if self.format == "json":
            output = [t.to_dict_minimal() for t in templates]
            print(json.dumps(output, indent=2, ensure_ascii=False))
        else:
            self.print_template_table(templates)
        return 0

    def handle_template_show(self, args: argparse.Namespace) -> int:
        """Handle the template show command."""
        try:
            from flask import has_app_context

            from ..app import app

            if not has_app_context():
                with app.app_context():
                    return self._show_template(args)
            else:
                return self._show_template(args)
        except Exception as e:
            if self.verbose:
                import traceback

                traceback.print_exc()
            print(f"Error showing template: {str(e)}")
            return 1

    def _show_template(self, args: argparse.Namespace) -> int:
        """Show template details."""
        template = Template.get_by_id(args.id)
        if not template:
            print(f"Template with ID {args.id} not found")
            return 1

        if args.versions:
            versions = TemplateVersion.get_by_template(args.id)
            if self.format == "json":
                print(json.dumps([v.to_dict() for v in versions], indent=2))
            else:
                if not versions:
                    print(f"No versions found for template {args.id}")
                else:
                    print(f"\nVersions for Template: {template.name}")
                    print("=" * 60)
                    for v in versions:
                        print(f"  v{v.version}: {v.created_at}")
        else:
            self.print_template(template, detailed=True)
        return 0

    def handle_template_update(self, args: argparse.Namespace) -> int:
        """Handle the template update command."""
        try:
            from flask import has_app_context

            from ..app import app

            if not has_app_context():
                with app.app_context():
                    return self._update_template(args)
            else:
                return self._update_template(args)
        except Exception as e:
            if self.verbose:
                import traceback

                traceback.print_exc()
            print(f"Error updating template: {str(e)}")
            return 1

    def _update_template(self, args: argparse.Namespace) -> int:
        """Update a template."""
        template = Template.get_by_id(args.id)
        if not template:
            print(f"Template with ID {args.id} not found")
            return 1

        update_data = {}
        if args.name:
            update_data["name"] = args.name
        if args.description:
            update_data["description"] = args.description
        if args.model:
            update_data["model"] = args.model
        if args.config:
            update_data["configuration"] = args.config
        if args.parameters:
            update_data["parameters"] = args.parameters
        if args.category:
            update_data["category"] = args.category
        if args.tags:
            update_data["tags"] = args.tags
        if args.version:
            update_data["version"] = args.version
        if args.official:
            update_data["is_official"] = args.official
        if args.public:
            update_data["is_public"] = args.public

        if not update_data:
            print("No fields to update")
            return 0

        if self.verbose:
            print(f"Updating template {args.id}")

        if "name" in update_data and update_data["name"] != template.name:
            existing = Template.get_by_name(update_data["name"])
            if existing and existing.id != args.id:
                print(f"Template with name '{update_data['name']}' already exists")
                return 1

        TemplateVersion.create(
            template_id=template.id,
            version=template.version,
            data=template.to_dict(),
        )
        template.update(**update_data)
        TemplateVersion.create(
            template_id=template.id,
            version=template.version,
            data=template.to_dict(),
        )

        if self.verbose:
            print(f"Template updated: {template.name}")
        self.print_template(template)
        return 0

    def handle_template_delete(self, args: argparse.Namespace) -> int:
        """Handle the template delete command."""
        try:
            from flask import has_app_context

            from ..app import app

            if not has_app_context():
                with app.app_context():
                    return self._delete_template(args)
            else:
                return self._delete_template(args)
        except Exception as e:
            if self.verbose:
                import traceback

                traceback.print_exc()
            print(f"Error deleting template: {str(e)}")
            return 1

    def _delete_template(self, args: argparse.Namespace) -> int:
        """Delete a template."""
        template = Template.get_by_id(args.id)
        if not template:
            print(f"Template with ID {args.id} not found")
            return 1

        if not args.force:
            response = input(
                f"Are you sure you want to delete template '{template.name}'? (y/N): "
            )
            if response.lower() not in ["y", "yes"]:
                print("Deletion cancelled")
                return 0

        versions = TemplateVersion.get_by_template(args.id)
        for v in versions:
            v.delete()
        template.delete()
        print(f"Template {template.name} (ID: {args.id}) deleted")
        return 0

    def handle_template_export(self, args: argparse.Namespace) -> int:
        """Handle the template export command."""
        try:
            from flask import has_app_context

            from ..app import app

            if not has_app_context():
                with app.app_context():
                    return self._export_template(args)
            else:
                return self._export_template(args)
        except Exception as e:
            if self.verbose:
                import traceback

                traceback.print_exc()
            print(f"Error exporting template: {str(e)}")
            return 1

    def _export_template(self, args: argparse.Namespace) -> int:
        """Export a template to JSON or YAML."""
        template = Template.get_by_id(args.id)
        if not template:
            print(f"Template with ID {args.id} not found")
            return 1

        template_data = template.to_dict()
        template_data.pop("id", None)
        template_data.pop("created_at", None)
        template_data.pop("updated_at", None)
        template_data.pop("created_by", None)

        if args.format == "yaml":
            try:
                import yaml

                output = yaml.dump(
                    template_data, default_flow_style=False, allow_unicode=True
                )
            except ImportError:
                print("PyYAML not installed. Install with: pip install pyyaml")
                return 1
        else:
            output = json.dumps(template_data, indent=2, ensure_ascii=False)

        if args.output:
            try:
                with open(args.output, "w", encoding="utf-8") as f:
                    f.write(output)
                print(f"Template exported to: {args.output}")
            except IOError as e:
                print(f"Error writing to file: {str(e)}")
                return 1
        else:
            print(output)
        return 0

    def handle_template_import(self, args: argparse.Namespace) -> int:
        """Handle the template import command."""
        try:
            from flask import has_app_context

            from ..app import app

            if not has_app_context():
                with app.app_context():
                    return self._import_template(args)
            else:
                return self._import_template(args)
        except Exception as e:
            if self.verbose:
                import traceback

                traceback.print_exc()
            print(f"Error importing template: {str(e)}")
            return 1

    def _import_template(self, args: argparse.Namespace) -> int:
        """Import a template from JSON or YAML file."""
        import os

        if not os.path.exists(args.file):
            print(f"File not found: {args.file}")
            return 1

        try:
            with open(args.file, "r", encoding="utf-8") as f:
                content = f.read()
        except IOError as e:
            print(f"Error reading file: {str(e)}")
            return 1

        try:
            data = json.loads(content)
        except json.JSONDecodeError:
            try:
                import yaml

                data = yaml.safe_load(content)
            except Exception as e:
                print(f"Invalid file format: {str(e)}")
                return 1

        if not isinstance(data, dict):
            print("Invalid template data. Must be a JSON object or YAML mapping.")
            return 1
        if "name" not in data:
            print("Template name is required.")
            return 1

        existing_template = Template.get_by_name(data["name"])
        if existing_template:
            print(f"Template with name '{data['name']}' already exists")
            return 1

        template = Template.create(
            name=data["name"],
            description=data.get("description"),
            model=data.get("model", "mistral-tiny"),
            configuration=data.get("configuration", {}),
            parameters=data.get("parameters", {}),
            category=data.get("category", "general"),
            tags=data.get("tags", []),
            version=data.get("version", "1.0.0"),
            is_official=data.get("is_official", False),
            is_public=data.get("is_public", False),
        )
        TemplateVersion.create(
            template_id=template.id,
            version=template.version,
            data=template.to_dict(),
        )
        if self.verbose:
            print(f"Template imported with ID: {template.id}")
        self.print_template(template)
        return 0

    def handle_template_customize(self, args: argparse.Namespace) -> int:
        """Handle the template customize command."""
        try:
            from flask import has_app_context

            from ..app import app

            if not has_app_context():
                with app.app_context():
                    return self._customize_template(args)
            else:
                return self._customize_template(args)
        except Exception as e:
            if self.verbose:
                import traceback

                traceback.print_exc()
            print(f"Error customizing template: {str(e)}")
            return 1

    def _customize_template(self, args: argparse.Namespace) -> int:
        """Customize a template and show preview."""
        template = Template.get_by_id(args.id)
        if not template:
            print(f"Template with ID {args.id} not found")
            return 1

        merged_config = {**template.configuration, **args.config}
        merged_params = {**template.parameters, **args.parameters}
        merged_model = args.model or template.model

        if self.format == "json":
            preview = {
                "template": template.to_dict_minimal(),
                "customized_config": {
                    "model": merged_model,
                    "configuration": merged_config,
                    "parameters": merged_params,
                },
                "agent_preview": {
                    "name": f"{template.name}-customized",
                    "model": merged_model,
                    "configuration": merged_config,
                    "description": f"Customized from template: {template.name}",
                },
            }
            print(json.dumps(preview, indent=2, ensure_ascii=False))
        else:
            print(f"\nCustomizing Template: {template.name}")
            print("=" * 60)
            print(f"  Model: {merged_model}")
            print(f"  Configuration: {json.dumps(merged_config, indent=2)}")
            print(f"  Parameters: {json.dumps(merged_params, indent=2)}")
            print("\nAgent Preview:")
            print(f"  Name: {template.name}-customized")
            print(f"  Model: {merged_model}")
            print(f"  Description: Customized from template: {template.name}")
        return 0

    def handle_template_versions_list(self, args: argparse.Namespace) -> int:
        """Handle the template versions list command."""
        try:
            from flask import has_app_context

            from ..app import app

            if not has_app_context():
                with app.app_context():
                    return self._list_versions(args)
            else:
                return self._list_versions(args)
        except Exception as e:
            if self.verbose:
                import traceback

                traceback.print_exc()
            print(f"Error listing versions: {str(e)}")
            return 1

    def _list_versions(self, args: argparse.Namespace) -> int:
        """List all versions of a template."""
        template = Template.get_by_id(args.id)
        if not template:
            print(f"Template with ID {args.id} not found")
            return 1
        versions = TemplateVersion.get_by_template(args.id)
        if self.format == "json":
            print(json.dumps([v.to_dict() for v in versions], indent=2))
        else:
            if not versions:
                print(f"No versions found for template {args.id}")
            else:
                print(f"\nVersions for Template: {template.name}")
                print("=" * 60)
                for v in versions:
                    print(f"  v{v.version}: {v.created_at}")
        return 0

    def handle_template_versions_restore(self, args: argparse.Namespace) -> int:
        """Handle the template versions restore command."""
        try:
            from flask import has_app_context

            from ..app import app

            if not has_app_context():
                with app.app_context():
                    return self._restore_version(args)
            else:
                return self._restore_version(args)
        except Exception as e:
            if self.verbose:
                import traceback

                traceback.print_exc()
            print(f"Error restoring version: {str(e)}")
            return 1

    def _restore_version(self, args: argparse.Namespace) -> int:
        """Restore a specific version of a template."""
        from datetime import datetime

        from ..models.base import db

        template = Template.get_by_id(args.id)
        if not template:
            print(f"Template with ID {args.id} not found")
            return 1

        version_record = TemplateVersion.get_by_version(args.id, args.version)
        if not version_record:
            print(f"Version {args.version} not found for template {args.id}")
            return 1

        TemplateVersion.create(
            template_id=template.id,
            version=template.version,
            data=template.to_dict(),
        )
        template_data = version_record.data.copy()
        template.name = template_data.get("name", template.name)
        template.description = template_data.get("description", template.description)
        template.model = template_data.get("model", template.model)
        template.configuration = template_data.get(
            "configuration", template.configuration
        )
        template.parameters = template_data.get("parameters", template.parameters)
        template.category = template_data.get("category", template.category)
        template.tags = template_data.get("tags", template.tags)
        template.version = args.version
        template.updated_at = datetime.utcnow()
        db.session.commit()
        TemplateVersion.create(
            template_id=template.id,
            version=args.version,
            data=template.to_dict(),
        )
        print(f"Template restored to version {args.version}")
        self.print_template(template)
        return 0

    def print_template(self, template: Template, detailed: bool = False) -> None:
        """Print template information."""
        if self.format == "json":
            if detailed:
                print(json.dumps(template.to_dict(), indent=2, ensure_ascii=False))
            else:
                print(
                    json.dumps(template.to_dict_minimal(), indent=2, ensure_ascii=False)
                )
        else:
            print(f"Template: {template.name}")
            print(f"   ID: {template.id}")
            print(f"   Version: {template.version}")
            print(f"   Category: {template.category}")
            print(f"   Model: {template.model}")
            if template.description:
                print(f"   Description: {template.description}")
            print(f"   Tags: {', '.join(template.tags) if template.tags else 'None'}")
            print(f"   Official: {template.is_official}")
            print(f"   Public: {template.is_public}")
            print(f"   Created: {template.created_at}")
            if detailed:
                print(
                    f"   Configuration: {json.dumps(template.configuration, indent=2)}"
                )
                print(f"   Parameters: {json.dumps(template.parameters, indent=2)}")

    def print_template_table(self, templates: List[Template]) -> None:
        """Print templates as a formatted table."""
        if not templates:
            print("No templates to display")
            return
        print(
            f"\n{'ID':<5} {'Name':<25} {'Version':<10} "
            f"{'Category':<15} {'Official':<10} {'Public':<10}"
        )
        print("-" * 80)
        for template in templates:
            official = "Yes" if template.is_official else "No"
            public = "Yes" if template.is_public else "No"
            print(
                f"{template.id:<5} {template.name[:25]:<25} "
                f"{template.version:<10} {template.category[:15]:<15} "
                f"{official:<10} {public:<10}"
            )
