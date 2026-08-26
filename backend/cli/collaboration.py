# 🤝 Agent World - Collaboration CLI Commands
# Version: 0.4.0 (Collaboration)
# Description: Commandes CLI pour la gestion de la collaboration

"""
Collaboration CLI Commands for Agent World.

Ce module contient les commandes CLI pour :
- Gérer les invitations (US-040)
- Gérer les rôles (US-041)
- Partager des projets (US-042)
- Gérer les commentaires (US-043)
"""

import argparse
import json
from typing import Any, Dict, List, Optional

from ..models.invitation import Invitation, InvitationStatus
from ..models.project import Project
from ..models.user import User
from ..services.invitation_service import InvitationService, InvitationError


class CollaborationCLIHandler:
    """Handler for collaboration-related CLI commands."""

    def __init__(self):
        """Initialize the collaboration CLI handler."""
        self.verbose = False
        self.format = "table"
        self.invitation_service = InvitationService()

    def add_commands(self, subparsers: argparse._SubParsersAction) -> None:
        """Add collaboration commands to the CLI parser."""
        
        # Invite command
        invite_parser = subparsers.add_parser(
            "invite",
            help="Invite a user to a project",
            description="Send an invitation to a user to join a project",
        )
        invite_parser.add_argument(
            "--project", "-p", type=int, required=True, help="ID of the project"
        )
        invite_parser.add_argument(
            "--email", "-e", type=str, required=True, help="Email of the user to invite"
        )
        invite_parser.add_argument(
            "--role",
            "-r",
            type=str,
            default="member",
            choices=["admin", "member", "viewer"],
            help="Role to assign (default: member)",
        )
        invite_parser.add_argument(
            "--expires-in",
            type=int,
            default=7,
            help="Number of days until the invitation expires (default: 7)",
        )
        invite_parser.add_argument(
            "--send-email",
            action="store_true",
            help="Send invitation email (default: False)",
        )
        invite_parser.set_defaults(handler=self.handle_invite)

        # Invite list command
        invite_list_parser = subparsers.add_parser(
            "invitations",
            help="List invitations",
            description="List all invitations or invitations for a specific project",
        )
        invite_list_parser.add_argument(
            "--project", "-p", type=int, help="Filter by project ID"
        )
        invite_list_parser.add_argument(
            "--email", "-e", type=str, help="Filter by email"
        )
        invite_list_parser.add_argument(
            "--status",
            "-s",
            type=str,
            choices=["pending", "accepted", "expired", "revoked"],
            help="Filter by status",
        )
        invite_list_parser.set_defaults(handler=self.handle_invitations_list)

        # Invite accept command
        invite_accept_parser = subparsers.add_parser(
            "accept-invite",
            help="Accept an invitation",
            description="Accept a project invitation using the token",
        )
        invite_accept_parser.add_argument(
            "token", type=str, help="Invitation token"
        )
        invite_accept_parser.set_defaults(handler=self.handle_accept_invite)

        # Invite revoke command
        invite_revoke_parser = subparsers.add_parser(
            "revoke-invite",
            help="Revoke an invitation",
            description="Revoke a previously sent invitation",
        )
        invite_revoke_parser.add_argument(
            "invitation_id", type=int, help="ID of the invitation to revoke"
        )
        invite_revoke_parser.set_defaults(handler=self.handle_revoke_invite)

        # Project create command
        project_create_parser = subparsers.add_parser(
            "create-project",
            help="Create a new project",
            description="Create a new project workspace",
        )
        project_create_parser.add_argument(
            "--name", "-n", type=str, required=True, help="Name of the project"
        )
        project_create_parser.add_argument(
            "--description", "-d", type=str, help="Description of the project"
        )
        project_create_parser.add_argument(
            "--public",
            action="store_true",
            help="Make the project publicly visible",
        )
        project_create_parser.set_defaults(handler=self.handle_create_project)

        # Project list command
        project_list_parser = subparsers.add_parser(
            "list-projects",
            help="List projects",
            description="List all projects",
        )
        project_list_parser.add_argument(
            "--user", "-u", type=int, help="Filter by creator user ID"
        )
        project_list_parser.set_defaults(handler=self.handle_list_projects)

    def handle_invite(self, args: argparse.Namespace) -> int:
        """Handle the invite command."""
        try:
            # Pour les tests, on utilise l'utilisateur ID 1
            # TODO: Récupérer l'utilisateur actuel depuis la session
            created_by = 1

            invitation = self.invitation_service.create_invitation(
                project_id=args.project,
                email=args.email,
                role=args.role,
                created_by=created_by,
                expires_in_days=args.expires_in,
            )

            if args.send_email:
                try:
                    self.invitation_service.send_invitation(invitation)
                    if self.verbose:
                        print("✉️  Invitation email sent")
                except InvitationError as e:
                    if self.verbose:
                        print(f"⚠️  Failed to send email: {e}")

            if self.verbose:
                print(f"🎫 Invitation created for {args.email}")
                print(f"   Token: {invitation.token}")
                print(f"   Expires: {invitation.expires_at}")

            self.print_invitation(invitation)
            return 0

        except InvitationError as e:
            print(f"❌ Error: {e}")
            return 1
        except Exception as e:
            if self.verbose:
                import traceback
                traceback.print_exc()
            print(f"❌ Unexpected error: {e}")
            return 1

    def handle_invitations_list(self, args: argparse.Namespace) -> int:
        """Handle the invitations list command."""
        try:
            if args.project:
                invitations = self.invitation_service.get_invitations_by_project(args.project)
            elif args.email:
                if args.status == "pending":
                    invitations = self.invitation_service.get_pending_invitations_by_email(args.email)
                else:
                    # TODO: Filter by other statuses
                    invitations = Invitation.get_by_email_and_project(args.email, args.project or 0) or []
                    invitations = [invitations] if invitations else []
            else:
                invitations = Invitation.query.all()

            if not invitations:
                print("🔍 No invitations found")
                return 0

            self.print_invitations(invitations)
            return 0

        except Exception as e:
            if self.verbose:
                import traceback
                traceback.print_exc()
            print(f"❌ Error listing invitations: {e}")
            return 1

    def handle_accept_invite(self, args: argparse.Namespace) -> int:
        """Handle the accept-invite command."""
        try:
            # TODO: Récupérer l'utilisateur actuel depuis la session
            user_id = 1

            invitation = self.invitation_service.accept_invitation(
                token=args.token,
                user_id=user_id,
            )

            print(f"✅ Invitation accepted!")
            print(f"   Project ID: {invitation.project_id}")
            print(f"   Role: {invitation.role}")

            self.print_invitation(invitation)
            return 0

        except InvitationError as e:
            print(f"❌ Error: {e}")
            return 1
        except Exception as e:
            if self.verbose:
                import traceback
                traceback.print_exc()
            print(f"❌ Unexpected error: {e}")
            return 1

    def handle_revoke_invite(self, args: argparse.Namespace) -> int:
        """Handle the revoke-invite command."""
        try:
            # TODO: Récupérer l'utilisateur actuel depuis la session
            revoked_by = 1

            invitation = self.invitation_service.revoke_invitation(
                invitation_id=args.invitation_id,
                revoked_by=revoked_by,
            )

            print(f"✅ Invitation revoked")
            self.print_invitation(invitation)
            return 0

        except InvitationError as e:
            print(f"❌ Error: {e}")
            return 1
        except Exception as e:
            if self.verbose:
                import traceback
                traceback.print_exc()
            print(f"❌ Unexpected error: {e}")
            return 1

    def handle_create_project(self, args: argparse.Namespace) -> int:
        """Handle the create-project command."""
        try:
            # TODO: Récupérer l'utilisateur actuel depuis la session
            created_by = 1

            project = Project.create(
                name=args.name,
                description=args.description or f"Project: {args.name}",
                created_by=created_by,
                is_public=args.public,
            )

            print(f"✅ Project created: {project.name}")
            print(f"   ID: {project.id}")

            self.print_project(project)
            return 0

        except Exception as e:
            if self.verbose:
                import traceback
                traceback.print_exc()
            print(f"❌ Error creating project: {e}")
            return 1

    def handle_list_projects(self, args: argparse.Namespace) -> int:
        """Handle the list-projects command."""
        try:
            if args.user:
                projects = Project.get_by_user(args.user)
            else:
                projects = Project.get_all()

            if not projects:
                print("🔍 No projects found")
                return 0

            self.print_projects(projects)
            return 0

        except Exception as e:
            if self.verbose:
                import traceback
                traceback.print_exc()
            print(f"❌ Error listing projects: {e}")
            return 1

    def print_invitation(self, invitation: Invitation) -> None:
        """Print invitation information."""
        if self.format == "json":
            print(json.dumps(invitation.to_dict(), indent=2))
        else:
            print(f"🎫 Invitation ID: {invitation.id}")
            print(f"   Project: {invitation.project_id}")
            print(f"   Email: {invitation.email}")
            print(f"   Role: {invitation.role}")
            print(f"   Status: {invitation.status.value}")
            print(f"   Token: {invitation.token}")
            print(f"   Created: {invitation.created_at}")
            print(f"   Expires: {invitation.expires_at}")
            if invitation.accepted_at:
                print(f"   Accepted: {invitation.accepted_at}")

    def print_invitations(self, invitations: List[Invitation]) -> None:
        """Print a list of invitations."""
        if self.format == "json":
            print(json.dumps([inv.to_dict() for inv in invitations], indent=2))
        else:
            print(f"\n🎫 Invitations ({len(invitations)})")
            print("=" * 80)
            print(f"{'ID':<5} {'Project':<8} {'Email':<25} {'Role':<10} {'Status':<12} {'Token':<20}")
            print("-" * 80)
            for inv in invitations:
                token_display = inv.token[:8] + "..." if len(inv.token) > 8 else inv.token
                print(f"{inv.id:<5} {inv.project_id:<8} {inv.email:<25} {inv.role:<10} {inv.status.value:<12} {token_display:<20}")

    def print_project(self, project: Project) -> None:
        """Print project information."""
        if self.format == "json":
            print(json.dumps(project.to_dict(), indent=2))
        else:
            print(f"📁 Project: {project.name}")
            print(f"   ID: {project.id}")
            if project.description:
                print(f"   Description: {project.description}")
            print(f"   Created by: {project.created_by}")
            print(f"   Public: {project.is_public}")
            print(f"   Shared: {project.is_shared}")
            print(f"   Created: {project.created_at}")
            print(f"   Updated: {project.updated_at}")

    def print_projects(self, projects: List[Project]) -> None:
        """Print a list of projects."""
        if self.format == "json":
            print(json.dumps([p.to_dict() for p in projects], indent=2))
        else:
            print(f"\n📁 Projects ({len(projects)})")
            print("=" * 80)
            print(f"{'ID':<5} {'Name':<25} {'Creator':<10} {'Public':<8} {'Shared':<8}")
            print("-" * 80)
            for p in projects:
                print(f"{p.id:<5} {p.name:<25} {p.created_by:<10} {str(p.is_public):<8} {str(p.is_shared):<8}")
