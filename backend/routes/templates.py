# [38;5;214m[0m Agent World - Templates Routes
# Version: 0.3.1 (EPIC 5)
# Description: Endpoints REST pour la gestion des templates d'agents

"""
Templates Routes for Agent World API.

Ce module contient tous les endpoints REST pour la gestion des templates d'agents IA.
Il implémente les opérations CRUD et les fonctionnalités de recherche.
"""

import json
from typing import Any, Dict, List, Optional

from flask import current_app, request
from flask_restful import Resource, reqparse

from ..models.base import db
from ..models.template import Template, TemplateVersion
from ..models.user import User

# Initialize parser for request parsing
parser = reqparse.RequestParser()
parser.add_argument("name", type=str, required=True, help="Template name is required")
parser.add_argument("description", type=str, help="Template description")
parser.add_argument(
    "model",
    type=str,
    default="mistral-tiny",
    help="AI model to use (default: mistral-tiny)",
)
parser.add_argument(
    "configuration", type=dict, default={}, help="Template configuration as JSON"
)
parser.add_argument(
    "parameters", type=dict, default={}, help="Template parameters as JSON"
)
parser.add_argument(
    "category",
    type=str,
    default="general",
    help="Template category (default: general)",
)
parser.add_argument(
    "tags",
    type=list,
    location="json",
    default=[],
    help="List of tags for the template",
)
parser.add_argument(
    "version",
    type=str,
    default="1.0.0",
    help="Template version (default: 1.0.0)",
)
parser.add_argument(
    "is_official",
    type=bool,
    default=False,
    help="Whether this is an official template (default: False)",
)
parser.add_argument(
    "is_public",
    type=bool,
    default=False,
    help="Whether this template is public (default: False)",
)


class TemplateListResource(Resource):
    """Resource for listing and creating templates."""

    def get(self):
        """
        List all templates.

        ---
        parameters:
          - in: query
            name: category
            schema:
              type: string
            description: Filter by category
          - in: query
            name: tag
            schema:
              type: string
            description: Filter by tag
          - in: query
            name: search
            schema:
              type: string
            description: Search in name and description
          - in: query
            name: official
            schema:
              type: boolean
            description: Filter by official status
          - in: query
            name: public
            schema:
              type: boolean
            description: Filter by public status
          - in: query
            name: limit
            schema:
              type: integer
              default: 10
            description: Maximum number of results
        responses:
          200:
            description: A list of all templates
            content:
              application/json:
                schema:
                  type: array
                  items:
                    $ref: '#/components/schemas/Template'
        """
        # Parse query parameters
        args = request.args

        category = args.get("category")
        tag = args.get("tag")
        search_query = args.get("search")
        is_official = args.get("official")
        is_public = args.get("public")
        limit = int(args.get("limit", 10))

        # Parse boolean values
        official_filter = None
        if is_official is not None:
            official_filter = is_official.lower() == "true"

        public_filter = None
        if is_public is not None:
            public_filter = is_public.lower() == "true"

        # Get templates based on filters
        if search_query or category or tag or official_filter or public_filter:
            templates = Template.search(
                query=search_query,
                category=category,
                tags=[tag] if tag else None,
                is_public=public_filter,
                limit=limit,
            )

            # Additional filtering for official
            if official_filter is not None:
                templates = [t for t in templates if t.is_official == official_filter]
        else:
            templates = Template.get_all()

        return [template.to_dict_minimal() for template in templates], 200

    def post(self):
        """
        Create a new template.

        ---
        requestBody:
          required: true
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/TemplateInput'
        responses:
          201:
            description: The created template
            content:
              application/json:
                schema:
                  $ref: '#/components/schemas/Template'
          400:
            description: Invalid input data
          409:
            description: Template with this name already exists
        """
        args = parser.parse_args()

        # Handle tags from JSON body
        data = request.get_json(silent=True) or {}
        tags = data.get("tags", args.tags or [])

        # Check if template with same name already exists
        existing_template = Template.get_by_name(args.name)
        if existing_template:
            return (
                {"error": f'Template with name "{args.name}" already exists'},
                409,
            )

        # Create new template
        template_data = {
            "name": args.name,
            "description": args.description,
            "model": args.model,
            "configuration": args.configuration,
            "parameters": args.parameters,
            "category": args.category,
            "tags": tags,
            "version": args.version,
            "is_official": args.is_official,
            "is_public": args.is_public,
        }

        try:
            template = Template.create(**template_data)

            # Create initial version
            TemplateVersion.create(
                template_id=template.id,
                version=template.version,
                data=template.to_dict(),
            )

            return template.to_dict(), 201
        except Exception as e:
            db.session.rollback()
            return {"error": str(e)}, 500


class TemplateResource(Resource):
    """Resource for individual template operations."""

    def get(self, template_id: int):
        """
        Get a specific template by ID.

        ---
        parameters:
          - in: path
            name: template_id
            schema:
              type: integer
            required: true
        responses:
          200:
            description: The requested template
            content:
              application/json:
                schema:
                  $ref: '#/components/schemas/Template'
          404:
            description: Template not found
        """
        template = Template.get_by_id(template_id)
        if not template:
            return {"error": f"Template with ID {template_id} not found"}, 404

        return template.to_dict(), 200

    def put(self, template_id: int):
        """
        Update an existing template.

        ---
        parameters:
          - in: path
            name: template_id
            schema:
              type: integer
            required: true
        requestBody:
          required: true
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/TemplateInput'
        responses:
          200:
            description: The updated template
            content:
              application/json:
                schema:
                  $ref: '#/components/schemas/Template'
          404:
            description: Template not found
        """
        template = Template.get_by_id(template_id)
        if not template:
            return {"error": f"Template with ID {template_id} not found"}, 404

        args = parser.parse_args()
        data = request.get_json(silent=True) or {}
        tags = data.get("tags", args.tags or [])

        # Check if another template with same name exists
        if args.name and args.name != template.name:
            existing_template = Template.get_by_name(args.name)
            if existing_template and existing_template.id != template_id:
                return (
                    {"error": f'Template with name "{args.name}" already exists'},
                    409,
                )

        update_data = {}
        if args.name:
            update_data["name"] = args.name
        if args.description:
            update_data["description"] = args.description
        if args.model:
            update_data["model"] = args.model
        if args.configuration:
            update_data["configuration"] = args.configuration
        if args.parameters:
            update_data["parameters"] = args.parameters
        if args.category:
            update_data["category"] = args.category
        if tags:
            update_data["tags"] = tags
        if args.version:
            update_data["version"] = args.version
        if args.is_official is not None:
            update_data["is_official"] = args.is_official
        if args.is_public is not None:
            update_data["is_public"] = args.is_public

        try:
            # Save current version before update
            TemplateVersion.create(
                template_id=template.id,
                version=template.version,
                data=template.to_dict(),
            )

            template.update(**update_data)

            # Create new version after update
            TemplateVersion.create(
                template_id=template.id,
                version=template.version,
                data=template.to_dict(),
            )

            return template.to_dict(), 200
        except Exception as e:
            db.session.rollback()
            return {"error": str(e)}, 500

    def delete(self, template_id: int):
        """
        Delete a template.

        ---
        parameters:
          - in: path
            name: template_id
            schema:
              type: integer
            required: true
        responses:
          204:
            description: Template deleted successfully
          404:
            description: Template not found
        """
        template = Template.get_by_id(template_id)
        if not template:
            return {"error": f"Template with ID {template_id} not found"}, 404

        try:
            # Also delete all versions
            versions = TemplateVersion.get_by_template(template_id)
            for version in versions:
                db.session.delete(version)

            template.delete()
            return "", 204
        except Exception as e:
            db.session.rollback()
            return {"error": str(e)}, 500


class TemplateExportResource(Resource):
    """Resource for exporting templates."""

    def get(self, template_id: int):
        """
        Export a template in JSON or YAML format.

        ---
        parameters:
          - in: path
            name: template_id
            schema:
              type: integer
            required: true
          - in: query
            name: format
            schema:
              type: string
              enum: [json, yaml]
              default: json
            description: Export format
        responses:
          200:
            description: Template in requested format
            content:
              application/json:
                schema:
                  type: object
          404:
            description: Template not found
        """
        template = Template.get_by_id(template_id)
        if not template:
            return {"error": f"Template with ID {template_id} not found"}, 404

        args = request.args
        fmt = args.get("format", "json")

        template_data = template.to_dict()
        # Remove database-specific fields
        template_data.pop("id", None)
        template_data.pop("created_at", None)
        template_data.pop("updated_at", None)
        template_data.pop("created_by", None)

        if fmt == "yaml":
            import yaml

            yaml_output = yaml.dump(
                template_data, default_flow_style=False, allow_unicode=True
            )
            return yaml_output, 200, {"Content-Type": "application/yaml"}
        else:
            return template_data, 200


class TemplateImportResource(Resource):
    """Resource for importing templates."""

    def post(self):
        """
        Import a template from JSON or YAML.

        ---
        requestBody:
          required: true
          content:
            application/json:
              schema:
                type: object
                required:
                  - name
                properties:
                  name:
                    type: string
                  description:
                    type: string
                  model:
                    type: string
                  configuration:
                    type: object
                  parameters:
                    type: object
                  category:
                    type: string
                  tags:
                    type: array
                    items:
                      type: string
                  version:
                    type: string
          400:
            description: Invalid input data
          409:
            description: Template with this name already exists
        """
        # Try to parse as JSON first
        data = request.get_json(silent=True)

        if not data:
            # Try to parse as YAML
            try:
                import yaml

                yaml_data = request.get_data(as_text=True)
                if yaml_data:
                    data = yaml.safe_load(yaml_data)
            except Exception:
                pass

        if not data or not isinstance(data, dict):
            return {"error": "Invalid template data. Must be JSON or YAML."}, 400

        if "name" not in data:
            return {"error": "Template name is required."}, 400

        # Check if template with same name already exists
        existing_template = Template.get_by_name(data["name"])
        if existing_template:
            return (
                {"error": f'Template with name "{data["name"]}" already exists'},
                409,
            )

        try:
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

            # Create initial version
            TemplateVersion.create(
                template_id=template.id,
                version=template.version,
                data=template.to_dict(),
            )

            return template.to_dict(), 201
        except Exception as e:
            db.session.rollback()
            return {"error": str(e)}, 500


class TemplateCustomizeResource(Resource):
    """Resource for customizing templates."""

    def post(self, template_id: int):
        """
        Customize a template before using it to create an agent.

        ---
        parameters:
          - in: path
            name: template_id
            schema:
              type: integer
            required: true
        requestBody:
          required: true
          content:
            application/json:
              schema:
                type: object
                properties:
                  configuration:
                    type: object
                    description: Override configuration
                  parameters:
                    type: object
                    description: Override parameters
                  model:
                    type: string
                    description: Override model
        responses:
          200:
            description: Customized template preview
            content:
              application/json:
                schema:
                  type: object
                  properties:
                    template:
                      $ref: '#/components/schemas/Template'
                    customized_config:
                      type: object
                    agent_preview:
                      type: object
          404:
            description: Template not found
        """
        template = Template.get_by_id(template_id)
        if not template:
            return {"error": f"Template with ID {template_id} not found"}, 404

        data = request.get_json(silent=True) or {}

        # Get overrides
        config_override = data.get("configuration", {})
        params_override = data.get("parameters", {})
        model_override = data.get("model")

        # Merge with template defaults
        merged_config = {**template.configuration, **config_override}
        merged_params = {**template.parameters, **params_override}
        merged_model = model_override or template.model

        # Create preview
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

        return preview, 200


class TemplateVersionsResource(Resource):
    """Resource for managing template versions."""

    def get(self, template_id: int):
        """
        Get all versions of a template.

        ---
        parameters:
          - in: path
            name: template_id
            schema:
              type: integer
            required: true
        responses:
          200:
            description: List of all versions for the template
            content:
              application/json:
                schema:
                  type: array
                  items:
                    type: object
                    properties:
                      id:
                        type: integer
                      version:
                        type: string
                      created_at:
                        type: string
          404:
            description: Template not found
        """
        template = Template.get_by_id(template_id)
        if not template:
            return {"error": f"Template with ID {template_id} not found"}, 404

        versions = TemplateVersion.get_by_template(template_id)
        return [v.to_dict() for v in versions], 200

    def post(self, template_id: int):
        """
        Create a new version of a template.

        ---
        parameters:
          - in: path
            name: template_id
            schema:
              type: integer
            required: true
        requestBody:
          required: true
          content:
            application/json:
              schema:
                type: object
                required:
                  - version
                properties:
                  version:
                    type: string
                    description: New version number
        responses:
          201:
            description: New version created
            content:
              application/json:
                schema:
                  type: object
          404:
            description: Template not found
        """
        template = Template.get_by_id(template_id)
        if not template:
            return {"error": f"Template with ID {template_id} not found"}, 404

        data = request.get_json(silent=True) or {}
        new_version = data.get("version")

        if not new_version:
            return {"error": "Version is required."}, 400

        try:
            # Save current state as a version
            version_record = TemplateVersion.create(
                template_id=template.id,
                version=new_version,
                data=template.to_dict(),
            )

            # Update template version
            template.version = new_version
            template.updated_at = datetime.utcnow()
            db.session.commit()

            return version_record.to_dict(), 201
        except Exception as e:
            db.session.rollback()
            return {"error": str(e)}, 500


class TemplateRestoreResource(Resource):
    """Resource for restoring template versions."""

    def post(self, template_id: int, version: str):
        """
        Restore a specific version of a template.

        ---
        parameters:
          - in: path
            name: template_id
            schema:
              type: integer
            required: true
          - in: path
            name: version
            schema:
              type: string
            required: true
        responses:
          200:
            description: Template restored from version
            content:
              application/json:
                schema:
                  $ref: '#/components/schemas/Template'
          404:
            description: Template or version not found
        """
        from datetime import datetime

        template = Template.get_by_id(template_id)
        if not template:
            return {"error": f"Template with ID {template_id} not found"}, 404

        version_record = TemplateVersion.get_by_version(template_id, version)
        if not version_record:
            return {
                "error": f"Version {version} of template {template_id} not found"
            }, 404

        try:
            # Save current state before restore
            TemplateVersion.create(
                template_id=template.id,
                version=template.version,
                data=template.to_dict(),
            )

            # Restore from version
            template_data = version_record.data.copy()
            template.name = template_data.get("name", template.name)
            template.description = template_data.get(
                "description", template.description
            )
            template.model = template_data.get("model", template.model)
            template.configuration = template_data.get(
                "configuration", template.configuration
            )
            template.parameters = template_data.get("parameters", template.parameters)
            template.category = template_data.get("category", template.category)
            template.tags = template_data.get("tags", template.tags)
            template.version = version
            template.updated_at = datetime.utcnow()
            db.session.commit()

            # Create version record for the restored version
            TemplateVersion.create(
                template_id=template.id,
                version=version,
                data=template.to_dict(),
            )

            return template.to_dict(), 200
        except Exception as e:
            db.session.rollback()
            return {"error": str(e)}, 500


class TemplateCategoriesResource(Resource):
    """Resource for getting available template categories."""

    def get(self):
        """
        Get all unique template categories.

        ---
        responses:
          200:
            description: List of all categories
            content:
              application/json:
                schema:
                  type: array
                  items:
                    type: string
        """
        templates = Template.get_all()
        categories = set(t.category for t in templates if t.category)
        return sorted(list(categories)), 200


class TemplateTagsResource(Resource):
    """Resource for getting available template tags."""

    def get(self):
        """
        Get all unique template tags.

        ---
        responses:
          200:
            description: List of all tags
            content:
              application/json:
                schema:
                  type: array
                  items:
                    type: string
        """
        templates = Template.get_all()
        all_tags = []
        for t in templates:
            if t.tags:
                all_tags.extend(t.tags)
        unique_tags = sorted(list(set(all_tags)))
        return unique_tags, 200


class TemplateShareResource(Resource):
    """Resource for sharing templates."""

    def get(self, template_id: int):
        """
        Get share information for a template.

        ---
        parameters:
          - in: path
            name: template_id
            schema:
              type: integer
            required: true
        responses:
          200:
            description: Share information for the template
            content:
              application/json:
                schema:
                  type: object
                  properties:
                    is_public:
                      type: boolean
                    share_permissions:
                      type: array
                      items:
                        type: object
                    share_tokens:
                      type: array
                      items:
                        type: object
          404:
            description: Template not found
        """
        template = Template.get_by_id(template_id)
        if not template:
            return {"error": f"Template with ID {template_id} not found"}, 404

        from ..models.template_share import SharePermission, ShareToken

        permissions = SharePermission.get_active_shares(template_id)
        tokens = ShareToken.get_active_tokens(template_id)

        return {
            "template_id": template_id,
            "is_public": template.is_public,
            "share_permissions": [p.to_dict() for p in permissions],
            "share_tokens": [t.to_dict() for t in tokens],
        }, 200

    def post(self, template_id: int):
        """
        Share a template with specific users or make it public.

        ---
        parameters:
          - in: path
            name: template_id
            schema:
              type: integer
            required: true
        requestBody:
          required: true
          content:
            application/json:
              schema:
                type: object
                properties:
                  is_public:
                    type: boolean
                    description: Make template publicly accessible
                  user_ids:
                    type: array
                    items:
                      type: integer
                    description: List of user IDs to share with
                  permission_level:
                    type: string
                    enum: [read, edit, admin]
                    default: read
                    description: Permission level for user shares
                  generate_token:
                    type: boolean
                    description: Generate a shareable token
                  token_permission:
                    type: string
                    enum: [read, edit, admin]
                    default: read
                    description: Permission level for share token
                  token_expires_in:
                    type: integer
                    description: Token expiration in days (optional)
        responses:
          200:
            description: Template shared successfully
            content:
              application/json:
                schema:
                  type: object
          404:
            description: Template not found
        """
        template = Template.get_by_id(template_id)
        if not template:
            return {"error": f"Template with ID {template_id} not found"}, 404

        from ..models.template_share import SharePermission, ShareToken

        data = request.get_json(silent=True) or {}

        try:
            # Handle public sharing
            if "is_public" in data:
                template.is_public = data["is_public"]
                template.updated_at = datetime.utcnow()

            # Handle user-specific sharing
            if "user_ids" in data and data["user_ids"]:
                permission_level = data.get("permission_level", SharePermission.READ)
                for user_id in data["user_ids"]:
                    # Check if share already exists
                    existing_share = SharePermission.get_share_with_user(
                        template_id, user_id
                    )
                    if existing_share:
                        existing_share.update_permission(permission_level)
                    else:
                        SharePermission.create(
                            template_id=template_id,
                            shared_with_id=user_id,
                            permission_level=permission_level,
                            shared_by=template.created_by,
                        )

            # Handle share token generation
            if data.get("generate_token", False):
                token_permission = data.get("token_permission", SharePermission.READ)
                expires_in_days = data.get("token_expires_in")

                expires_at = None
                if expires_in_days:
                    expires_at = datetime.utcnow() + timedelta(days=expires_in_days)

                token = ShareToken.create(
                    template_id=template_id,
                    permission_level=token_permission,
                    created_by=template.created_by,
                    expires_at=expires_at,
                )

            db.session.commit()

            return {
                "message": "Template shared successfully",
                "template": template.to_dict_minimal(),
            }, 200
        except Exception as e:
            db.session.rollback()
            return {"error": str(e)}, 500


# Import datetime for use in resources
from datetime import datetime, timedelta


def register_resources(api):
    """Register template resources with the Flask-RESTful API."""
    api.add_resource(TemplateListResource, "/templates")
    api.add_resource(TemplateResource, "/templates/<int:template_id>")
    api.add_resource(TemplateExportResource, "/templates/<int:template_id>/export")
    api.add_resource(TemplateImportResource, "/templates/import")
    api.add_resource(
        TemplateCustomizeResource, "/templates/<int:template_id>/customize"
    )
    api.add_resource(TemplateVersionsResource, "/templates/<int:template_id>/versions")
    api.add_resource(
        TemplateRestoreResource,
        "/templates/<int:template_id>/versions/<string:version>/restore",
    )
    api.add_resource(TemplateCategoriesResource, "/templates/categories")
    api.add_resource(TemplateTagsResource, "/templates/tags")
    api.add_resource(TemplateShareResource, "/templates/<int:template_id>/share")
