# 📩 Agent World - Invitations Routes
# Version: 0.4.0 (Collaboration)
# Description: Endpoints REST pour la gestion des invitations

"""
Invitations Routes for Agent World API.

Ce module contient tous les endpoints REST pour la gestion des invitations
d'utilisateurs pour rejoindre des projets.
"""

from flask import current_app, request
from flask_restful import Resource, reqparse

from ..models.invitation import Invitation
from ..models.project import Project
from ..services.invitation_service import InvitationError, InvitationService

# Initialize parser
parser = reqparse.RequestParser()
parser.add_argument(
    "project_id", type=int, required=True, help="Project ID is required"
)
parser.add_argument("email", type=str, required=True, help="Email is required")
parser.add_argument(
    "role", type=str, default="member", help="Role to assign (default: member)"
)
parser.add_argument(
    "expires_in_days", type=int, default=7, help="Expiration in days (default: 7)"
)


class InvitationListResource(Resource):
    """Resource for managing invitations (list and create)."""

    def __init__(self):
        self.invitation_service = InvitationService()

    def get(self):
        """
        Lister toutes les invitations.

        ---
        tags:
          - invitations
        responses:
          200:
            description: Liste des invitations
            content:
              application/json:
                schema:
                  type: array
                  items:
                    $ref: '#/components/schemas/Invitation'
          401:
            description: Non autorisé
        """
        # Pour l'instant, retourner toutes les invitations
        # TODO: Ajouter la pagination et le filtrage
        invitations = Invitation.query.all()
        return [invitation.to_dict() for invitation in invitations], 200

    def post(self):
        """
        Créer une nouvelle invitation.

        ---
        tags:
          - invitations
        requestBody:
          required: true
          content:
            application/json:
              schema:
                type: object
                required:
                  - project_id
                  - email
                properties:
                  project_id:
                    type: integer
                    description: ID du projet
                  email:
                    type: string
                    format: email
                    description: Email de l'utilisateur invité
                  role:
                    type: string
                    description: Rôle à attribuer
                    default: member
                    enum: [admin, member, viewer]
                  expires_in_days:
                    type: integer
                    description: Durée de validité en jours
                    default: 7
        responses:
          201:
            description: Invitation créée avec succès
            content:
              application/json:
                schema:
                  $ref: '#/components/schemas/Invitation'
          400:
            description: Données invalides
          401:
            description: Non autorisé
          404:
            description: Projet ou utilisateur introuvable
        """
        args = parser.parse_args()

        # Récupérer l'utilisateur actuel depuis le token JWT
        # Pour l'instant, on utilise un utilisateur par défaut pour les tests
        # TODO: Implémenter l'authentification JWT
        created_by = 1  # User ID 1 (admin) pour les tests

        try:
            invitation = self.invitation_service.create_invitation(
                project_id=args["project_id"],
                email=args["email"],
                role=args["role"],
                created_by=created_by,
                expires_in_days=args["expires_in_days"],
            )

            # Envoyer l'email d'invitation (optionnel)
            try:
                self.invitation_service.send_invitation(invitation)
            except InvitationError as e:
                current_app.logger.warning(f"Échec de l'envoi de l'email: {e}")

            return invitation.to_dict(), 201

        except InvitationError as e:
            return {"error": str(e)}, 400


class InvitationResource(Resource):
    """Resource for managing a single invitation."""

    def __init__(self):
        self.invitation_service = InvitationService()

    def get(self, token: str):
        """
        Récupérer une invitation par son token.

        ---
        tags:
          - invitations
        parameters:
          - in: path
            name: token
            required: true
            description: Token de l'invitation
            schema:
              type: string
        responses:
          200:
            description: Invitation trouvée
            content:
              application/json:
                schema:
                  $ref: '#/components/schemas/Invitation'
          404:
            description: Invitation introuvable
        """
        invitation = self.invitation_service.get_invitation_by_token(token)

        if not invitation:
            return {"error": "Invitation introuvable"}, 404

        return invitation.to_dict(), 200


class InvitationAcceptResource(Resource):
    """Resource for accepting invitations."""

    def __init__(self):
        self.invitation_service = InvitationService()

    def post(self, token: str):
        """
        Accepter une invitation.

        ---
        tags:
          - invitations
        parameters:
          - in: path
            name: token
            required: true
            description: Token de l'invitation
            schema:
              type: string
        requestBody:
          required: true
          content:
            application/json:
              schema:
                type: object
                required:
                  - user_id
                properties:
                  user_id:
                    type: integer
                    description: ID de l'utilisateur qui accepte
        responses:
          200:
            description: Invitation acceptée avec succès
            content:
              application/json:
                schema:
                  $ref: '#/components/schemas/Invitation'
          400:
            description: Invitation invalide ou déjà acceptée
          404:
            description: Invitation introuvable
        """
        # Parse request body
        data = request.get_json()
        if not data or "user_id" not in data:
            return {"error": "user_id is required"}, 400

        user_id = data["user_id"]

        try:
            invitation = self.invitation_service.accept_invitation(token, user_id)
            return invitation.to_dict(), 200

        except InvitationError as e:
            return {"error": str(e)}, 400


class InvitationRevokeResource(Resource):
    """Resource for revoking invitations."""

    def __init__(self):
        self.invitation_service = InvitationService()

    def delete(self, invitation_id: int):
        """
        Révoquer une invitation.

        ---
        tags:
          - invitations
        parameters:
          - in: path
            name: invitation_id
            required: true
            description: ID de l'invitation à révoquer
            schema:
              type: integer
        responses:
          200:
            description: Invitation révoquée avec succès
            content:
              application/json:
                schema:
                  $ref: '#/components/schemas/Invitation'
          400:
            description: Invitation introuvable ou non autorisé
          401:
            description: Non autorisé
        """
        # TODO: Implémenter l'authentification pour récupérer l'utilisateur actuel
        revoked_by = 1  # User ID 1 (admin) pour les tests

        try:
            invitation = self.invitation_service.revoke_invitation(
                invitation_id, revoked_by
            )
            return invitation.to_dict(), 200

        except InvitationError as e:
            return {"error": str(e)}, 400


class ProjectInvitationsResource(Resource):
    """Resource for managing invitations of a specific project."""

    def __init__(self):
        self.invitation_service = InvitationService()

    def get(self, project_id: int):
        """
        Lister les invitations d'un projet.

        ---
        tags:
          - invitations
        parameters:
          - in: path
            name: project_id
            required: true
            description: ID du projet
            schema:
              type: integer
        responses:
          200:
            description: Liste des invitations du projet
            content:
              application/json:
                schema:
                  type: array
                  items:
                    $ref: '#/components/schemas/Invitation'
          404:
            description: Projet introuvable
        """
        project = Project.get_by_id(project_id)
        if not project:
            return {"error": f"Projet {project_id} introuvable"}, 404

        invitations = self.invitation_service.get_invitations_by_project(project_id)
        return [invitation.to_dict() for invitation in invitations], 200


def register_resources(api):
    """Register invitation resources on the API."""
    api.add_resource(
        InvitationListResource,
        "/invitations",
        "/api/invitations",
    )
    api.add_resource(
        InvitationResource,
        "/invitations/<string:token>",
        "/api/invitations/<string:token>",
    )
    api.add_resource(
        InvitationAcceptResource,
        "/invitations/<string:token>/accept",
        "/api/invitations/<string:token>/accept",
    )
    api.add_resource(
        InvitationRevokeResource,
        "/invitations/<int:invitation_id>",
        "/api/invitations/<int:invitation_id>",
    )
    api.add_resource(
        ProjectInvitationsResource,
        "/projects/<int:project_id>/invitations",
        "/api/projects/<int:project_id>/invitations",
    )
