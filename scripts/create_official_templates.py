#!/usr/bin/env python
# Agent World - Script to create official templates
# Version: 0.3.1 (EPIC 5)
# Description: Crée les templates officiels pour l'EPIC 5

"""
Script to create official templates for Agent World.

This script creates the 10+ official templates as specified in US-039.
Run with: python scripts/create_official_templates.py
"""

import sys
from backend.app import create_app
from backend.config.settings import TestingConfig
from backend.models.base import db
from backend.models.template import Template, TemplateVersion

# Official templates definition
OFFICIAL_TEMPLATES = [
    {
        "name": "translation_agent",
        "description": "Translates text between multiple languages using AI",
        "model": "mistral-tiny",
        "category": "translation",
        "tags": ["translation", "language", "multilingual"],
        "version": "1.0.0",
        "configuration": {
            "temperature": 0.3,
            "max_tokens": 500,
        },
        "parameters": {
            "source_language": "auto",
            "target_language": "en",
            "preserve_format": True,
        },
        "is_official": True,
        "is_public": True,
    },
    {
        "name": "summary_agent",
        "description": "Creates concise summaries of long text documents",
        "model": "mistral-small",
        "category": "text_processing",
        "tags": ["summary", "text", "document"],
        "version": "1.0.0",
        "configuration": {
            "temperature": 0.2,
            "max_tokens": 1000,
        },
        "parameters": {
            "summary_length": "medium",
            "include_key_points": True,
        },
        "is_official": True,
        "is_public": True,
    },
    {
        "name": "code_analyzer",
        "description": "Analyzes and explains code snippets",
        "model": "mistral-small",
        "category": "development",
        "tags": ["code", "analysis", "development"],
        "version": "1.0.0",
        "configuration": {
            "temperature": 0.1,
            "max_tokens": 1500,
        },
        "parameters": {
            "language": "python",
            "explain_line_by_line": False,
            "suggest_improvements": True,
        },
        "is_official": True,
        "is_public": True,
    },
    {
        "name": "question_answerer",
        "description": "Answers questions based on provided context",
        "model": "mistral-small",
        "category": "qa",
        "tags": ["question", "answer", "context"],
        "version": "1.0.0",
        "configuration": {
            "temperature": 0.2,
            "max_tokens": 800,
        },
        "parameters": {
            "context_required": True,
            "multi_turn": False,
        },
        "is_official": True,
        "is_public": True,
    },
    {
        "name": "content_generator",
        "description": "Generates creative content (articles, stories, etc.)",
        "model": "mistral-tiny",
        "category": "creative",
        "tags": ["content", "generation", "creative"],
        "version": "1.0.0",
        "configuration": {
            "temperature": 0.7,
            "max_tokens": 2000,
        },
        "parameters": {
            "content_type": "article",
            "word_count": 500,
            "tone": "neutral",
        },
        "is_official": True,
        "is_public": True,
    },
    {
        "name": "email_assistant",
        "description": "Helps draft and improve email messages",
        "model": "mistral-tiny",
        "category": "productivity",
        "tags": ["email", "productivity", "writing"],
        "version": "1.0.0",
        "configuration": {
            "temperature": 0.3,
            "max_tokens": 1000,
        },
        "parameters": {
            "formality": "professional",
            "include_signature": True,
        },
        "is_official": True,
        "is_public": True,
    },
    {
        "name": "data_analyzer",
        "description": "Analyzes structured data and provides insights",
        "model": "mistral-small",
        "category": "data",
        "tags": ["data", "analysis", "statistics"],
        "version": "1.0.0",
        "configuration": {
            "temperature": 0.1,
            "max_tokens": 1500,
        },
        "parameters": {
            "data_format": "json",
            "generate_visualizations": False,
        },
        "is_official": True,
        "is_public": True,
    },
    {
        "name": "resume_reviewer",
        "description": "Reviews and provides feedback on resumes/CVs",
        "model": "mistral-small",
        "category": "hr",
        "tags": ["resume", "cv", "review", "hr"],
        "version": "1.0.0",
        "configuration": {
            "temperature": 0.2,
            "max_tokens": 1200,
        },
        "parameters": {
            "industry": "general",
            "focus_areas": ["experience", "skills", "formatting"],
        },
        "is_official": True,
        "is_public": True,
    },
    {
        "name": "meeting_notes",
        "description": "Generates meeting notes and action items",
        "model": "mistral-tiny",
        "category": "productivity",
        "tags": ["meeting", "notes", "productivity"],
        "version": "1.0.0",
        "configuration": {
            "temperature": 0.2,
            "max_tokens": 1000,
        },
        "parameters": {
            "include_action_items": True,
            "include_decision_points": True,
            "format": "bullet_points",
        },
        "is_official": True,
        "is_public": True,
    },
    {
        "name": "technical_writer",
        "description": "Creates technical documentation and tutorials",
        "model": "mistral-small",
        "category": "documentation",
        "tags": ["technical", "writing", "documentation"],
        "version": "1.0.0",
        "configuration": {
            "temperature": 0.2,
            "max_tokens": 1500,
        },
        "parameters": {
            "audience": "intermediate",
            "include_code_samples": True,
        },
        "is_official": True,
        "is_public": True,
    },
    {
        "name": "chatbot_designer",
        "description": "Designs conversational flows for chatbots",
        "model": "mistral-tiny",
        "category": "development",
        "tags": ["chatbot", "conversation", "dialogue"],
        "version": "1.0.0",
        "configuration": {
            "temperature": 0.5,
            "max_tokens": 1000,
        },
        "parameters": {
            "platform": "web",
            "personality": "friendly",
        },
        "is_official": True,
        "is_public": True,
    },
    {
        "name": "social_media_assistant",
        "description": "Creates social media posts and content",
        "model": "mistral-tiny",
        "category": "marketing",
        "tags": ["social", "media", "marketing", "content"],
        "version": "1.0.0",
        "configuration": {
            "temperature": 0.8,
            "max_tokens": 500,
        },
        "parameters": {
            "platform": "twitter",
            "include_hashtags": True,
            "max_length": 280,
        },
        "is_official": True,
        "is_public": True,
    },
]


def create_official_templates():
    """Create official templates in the database."""
    app = create_app(config_class=TestingConfig)

    with app.app_context():
        db.create_all()

        created_count = 0
        for template_data in OFFICIAL_TEMPLATES:
            # Check if template already exists
            existing = Template.get_by_name(template_data["name"])
            if existing:
                print(f"Template '{template_data['name']}' already exists, skipping...")
                continue

            # Create the template
            template = Template.create(**template_data)
            print(f"Created official template: {template.name}")

            # Create initial version
            TemplateVersion.create(
                template_id=template.id,
                version=template.version,
                data=template.to_dict(),
            )
            created_count += 1

        print(f"\nTotal official templates created: {created_count}")
        print(f"Total official templates in database: {len(Template.get_official())}")

        # Verify all templates were created
        official_templates = Template.get_official()
        if len(official_templates) >= 10:
            print("SUCCESS: At least 10 official templates created!")
            return 0
        else:
            print(f"WARNING: Only {len(official_templates)} official templates found")
            return 1


if __name__ == "__main__":
    sys.exit(create_official_templates())
