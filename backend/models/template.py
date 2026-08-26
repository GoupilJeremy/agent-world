# [38;5;214m[0m Template World - Template Model
# Version: 0.3.1 (EPIC 5)
# Description: Modèle de données pour les templates d'agents IA

"""
Template Model for Agent World.

Ce modèle représente un template d'agent IA réutilisable dans la base de données.
Un template peut être utilisé pour créer de nouveaux agents avec une
configuration pré-établie.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from .base import BaseModel, db


class Template(BaseModel):
    """
    Template model representing a reusable AI agent template.

    Attributes:
        id: Unique identifier for the template
        name: Name of the template
        description: Description of what the template does
        model: Default AI model for agents created from this template
        configuration: Default JSON configuration for agents
        parameters: Default parameters for the template (input placeholders, etc.)
        category: Category of the template (e.g., 'translation', 'summary', 'analysis')
        tags: List of tags for easy filtering
        version: Version of the template (e.g., '1.0.0')
        is_official: Whether this is an official template
        is_public: Whether this template is publicly accessible
        created_by: ID of the user who created the template
        created_at: Timestamp when the template was created
        updated_at: Timestamp when the template was last updated
    """

    __tablename__ = "templates"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=True)
    model = db.Column(db.String(50), nullable=False, default="mistral-tiny")
    configuration = db.Column(db.JSON, nullable=False, default={})
    parameters = db.Column(db.JSON, nullable=False, default={})
    category = db.Column(db.String(50), nullable=False, default="general")
    tags = db.Column(db.JSON, nullable=False, default=[])
    version = db.Column(db.String(20), nullable=False, default="1.0.0")
    is_official = db.Column(db.Boolean, nullable=False, default=False)
    is_public = db.Column(db.Boolean, nullable=False, default=False)
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    creator = db.relationship("User", foreign_keys=[created_by])
    # For versioning: a template can have multiple versions
    # This will be handled through TemplateVersion model

    def __init__(
        self,
        name: str,
        model: str = "mistral-tiny",
        description: Optional[str] = None,
        configuration: Optional[Dict[str, Any]] = None,
        parameters: Optional[Dict[str, Any]] = None,
        category: str = "general",
        tags: Optional[List[str]] = None,
        version: str = "1.0.0",
        is_official: bool = False,
        is_public: bool = False,
        created_by: Optional[int] = None,
    ):
        """
        Initialize a new Template instance.

        Args:
            name: Name of the template
            model: Default AI model to use
            description: Optional description
            configuration: Optional JSON configuration
            parameters: Optional parameters definition
            category: Category for classification
            tags: List of tags for filtering
            version: Version string
            is_official: Whether this is an official template
            is_public: Whether this template is publicly accessible
            created_by: ID of the creating user
        """
        self.name = name
        self.model = model
        self.description = description or f"Template for {model} model"
        self.configuration = configuration or {}
        self.parameters = parameters or {}
        self.category = category
        self.tags = tags or []
        self.version = version
        self.is_official = is_official
        self.is_public = is_public
        self.created_by = created_by

    def __repr__(self) -> str:
        return (
            f"<Template(id={self.id}, name={self.name}, "
            f"version={self.version}, category={self.category})>"
        )

    def to_dict(self) -> dict:
        """Convert template to dictionary for API responses."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "model": self.model,
            "configuration": self.configuration,
            "parameters": self.parameters,
            "category": self.category,
            "tags": self.tags,
            "version": self.version,
            "is_official": self.is_official,
            "is_public": self.is_public,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def to_dict_minimal(self) -> dict:
        """Convert template to minimal dictionary (for lists)."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "tags": self.tags,
            "version": self.version,
            "is_official": self.is_official,
            "is_public": self.is_public,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def update(self, **kwargs) -> None:
        """Update template attributes."""
        for key, value in kwargs.items():
            if hasattr(self, key) and key != "id":
                setattr(self, key, value)
        self.updated_at = datetime.utcnow()
        db.session.commit()

    @classmethod
    def create(cls, **kwargs) -> "Template":
        """Create a new template and save to database."""
        template = cls(**kwargs)
        db.session.add(template)
        db.session.commit()
        return template

    @classmethod
    def get_by_id(cls, template_id: int) -> Optional["Template"]:
        """Get template by ID."""
        return cls.query.get(template_id)

    @classmethod
    def get_by_name(cls, name: str) -> Optional["Template"]:
        """Get template by name."""
        return cls.query.filter_by(name=name).first()

    @classmethod
    def get_all(cls) -> List["Template"]:
        """Get all templates."""
        return cls.query.all()

    @classmethod
    def get_public(cls) -> List["Template"]:
        """Get all public templates."""
        return cls.query.filter_by(is_public=True).all()

    @classmethod
    def get_official(cls) -> List["Template"]:
        """Get all official templates."""
        return cls.query.filter_by(is_official=True).all()

    @classmethod
    def get_by_category(cls, category: str) -> List["Template"]:
        """Get templates by category."""
        return cls.query.filter_by(category=category).all()

    @classmethod
    def get_by_tag(cls, tag: str) -> List["Template"]:
        """Get templates by tag."""
        # For JSON arrays, we use like with JSON string matching
        # This works for both PostgreSQL and SQLite
        import json

        # Escape the tag for JSON (in case it contains special characters)
        escaped_tag = json.dumps(tag)[1:-1]  # Remove quotes
        return cls.query.filter(
            Template.tags.like(f'%"{escaped_tag}"%')
        ).all()  # type: ignore[arg-type]

    @classmethod
    def search(
        cls,
        query: Optional[str] = None,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
        is_public: Optional[bool] = None,
        limit: int = 10,
    ) -> List["Template"]:
        """
        Search templates with filters.

        Args:
            query: Search string in name or description
            category: Filter by category
            tags: Filter by tags
            is_public: Filter by public status
            limit: Maximum number of results

        Returns:
            List of matching templates
        """
        from sqlalchemy import or_

        search_query = cls.query

        if query:
            search_query = search_query.filter(
                or_(
                    Template.name.ilike(f"%{query}%"),
                    Template.description.ilike(f"%{query}%"),
                )
            )

        if category:
            search_query = search_query.filter_by(category=category)

        if tags:
            for tag in tags:
                # For JSON arrays in SQLite, we use like with JSON string matching
                import json

                escaped_tag = json.dumps(tag)[1:-1]
                search_query = search_query.filter(
                    Template.tags.like(f'%"{escaped_tag}"%')
                )  # type: ignore[arg-type]

        if is_public is not None:
            search_query = search_query.filter_by(is_public=is_public)

        return search_query.limit(limit).all()

    def delete(self) -> None:
        """Delete the template from database."""
        # Delete all versions first to avoid foreign key constraints
        TemplateVersion.delete_all_for_template(self.id)
        db.session.delete(self)
        db.session.commit()

    def increment_version(self, version_type: str = "patch") -> str:
        """
        Increment the version number.

        Args:
            version_type: Type of version increment ('major', 'minor', 'patch')

        Returns:
            New version string
        """
        try:
            parts = list(map(int, self.version.split(".")))
            while len(parts) < 3:
                parts.append(0)

            if version_type == "major":
                parts[0] += 1
                parts[1] = 0
                parts[2] = 0
            elif version_type == "minor":
                parts[1] += 1
                parts[2] = 0
            else:  # patch
                parts[2] += 1

            new_version = ".".join(map(str, parts))
            self.version = new_version
            self.updated_at = datetime.utcnow()
            db.session.commit()
            return new_version
        except (ValueError, AttributeError):
            # If version is not semver format, just append -1
            new_version = f"{self.version}-1"
            self.version = new_version
            self.updated_at = datetime.utcnow()
            db.session.commit()
            return new_version


class TemplateVersion(BaseModel):
    """
    TemplateVersion model for tracking versions of templates.

    Attributes:
        id: Unique identifier for the version
        template_id: ID of the parent template
        version: Version string (e.g., '1.0.0')
        data: JSON snapshot of the template at this version
        created_at: Timestamp when the version was created
        created_by: ID of the user who created this version
    """

    __tablename__ = "template_versions"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    template_id = db.Column(db.Integer, db.ForeignKey("templates.id"), nullable=False)
    version = db.Column(db.String(20), nullable=False)
    data = db.Column(db.JSON, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)

    # Relationships
    template = db.relationship("Template", backref="versions")
    creator = db.relationship("User", foreign_keys=[created_by])

    def __init__(
        self,
        template_id: int,
        version: str,
        data: Dict[str, Any],
        created_by: Optional[int] = None,
    ):
        """
        Initialize a new TemplateVersion instance.

        Args:
            template_id: ID of the parent template
            version: Version string
            data: Snapshot of template data
            created_by: ID of the creating user
        """
        self.template_id = template_id
        self.version = version
        self.data = data
        self.created_by = created_by

    def __repr__(self) -> str:
        return (
            f"<TemplateVersion(id={self.id}, template_id={self.template_id}, "
            f"version={self.version})>"
        )

    def to_dict(self) -> dict:
        """Convert template version to dictionary."""
        return {
            "id": self.id,
            "template_id": self.template_id,
            "version": self.version,
            "data": self.data,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "created_by": self.created_by,
        }

    @classmethod
    def create(cls, **kwargs) -> "TemplateVersion":
        """Create a new template version and save to database."""
        version = cls(**kwargs)
        db.session.add(version)
        db.session.commit()
        return version

    @classmethod
    def get_by_template(cls, template_id: int) -> List["TemplateVersion"]:
        """Get all versions for a template."""
        return cls.query.filter_by(template_id=template_id).all()

    @classmethod
    def get_by_version(
        cls, template_id: int, version: str
    ) -> Optional["TemplateVersion"]:
        """Get a specific version of a template."""
        return cls.query.filter_by(template_id=template_id, version=version).first()

    @classmethod
    def get_latest(cls, template_id: int) -> Optional["TemplateVersion"]:
        """Get the latest version of a template."""
        from sqlalchemy import desc

        return (
            cls.query.filter_by(template_id=template_id)
            .order_by(desc(cls.created_at))
            .first()
        )

    @classmethod
    def delete_all_for_template(cls, template_id: int) -> None:
        """Delete all versions for a specific template."""
        versions = cls.query.filter_by(template_id=template_id).all()
        for version in versions:
            db.session.delete(version)
        db.session.commit()

    def restore(self) -> Optional["Template"]:
        """Restore this version as a new template."""
        template_data = self.data.copy()
        template_data.pop("id", None)
        template_data.pop("created_at", None)
        template_data.pop("updated_at", None)
        template_data["version"] = self.version

        template = Template.create(**template_data)
        return template
