# 🎫 Agent World - Invitation Service
# Version: 0.4.0 (Collaboration)
# Description: Service pour la gestion des invitations

"""
Invitation Service for Agent World.

Ce service gère la création, l'envoi, l'acceptation et la révocation
des invitations d'utilisateurs pour rejoindre des projets.
"""

import secrets
from datetime import datetime, timedelta
from typing import Optional

from flask import current_app

from ..models.base import db
from ..models.invitation import Invitation, InvitationStatus
from ..models.project import Project
from ..models.user import User
from .email_service import EmailService


class InvitationError(Exception):
    """Exception levée en cas d'erreur liée aux invitations."""

    pass


class InvitationService:
    """
    Service pour gérer les invitations d'utilisateurs.

    Ce service fournit des méthodes pour :
    - Créer des invitations
    - Envoyer des invitations par email
    - Accepter des invitations
    - Révoquer des invitations
    - Lister les invitations
    """

    def __init__(self, email_service: Optional[EmailService] = None):
        """
        Initialiser le service d'invitation.

        Args:
            email_service: Service d'envoi d'emails (optionnel)
        """
        self.email_service = email_service

    def generate_token(self, length: int = 32) -> str:
        """
        Générer un token d'invitation unique.

        Args:
            length: Longueur du token (default: 32)

        Returns:
            Un token unique
        """
        return secrets.token_urlsafe(length)

    def create_invitation(
        self,
        project_id: int,
        email: str,
        role: str = "member",
        created_by: Optional[int] = None,
        expires_in_days: int = 7,
    ) -> Invitation:
        """
        Créer une nouvelle invitation.

        Args:
            project_id: ID du projet
            email: Email de l'utilisateur invité
            role: Rôle à attribuer (default: "member")
            created_by: ID de l'utilisateur qui crée l'invitation
            expires_in_days: Durée de validité en jours (default: 7)

        Returns:
            L'invitation créée

        Raises:
            InvitationError: Si le projet ou l'utilisateur n'existe pas
        """
        # Vérifier que le projet existe
        project = Project.get_by_id(project_id)
        if not project:
            raise InvitationError(f"Projet {project_id} introuvable")

        # Vérifier que l'utilisateur créateur existe
        if created_by:
            creator = User.get_by_id(created_by)
            if not creator:
                raise InvitationError(f"Utilisateur {created_by} introuvable")

        # Vérifier qu'une invitation similaire n'existe pas déjà
        existing = Invitation.get_by_email_and_project(email, project_id)
        if existing and existing.is_pending:
            raise InvitationError(
                f"Une invitation pendante existe déjà pour {email} "
                f"sur le projet {project_id}"
            )

        # Générer un token unique
        token = self.generate_token()

        # Calculer la date d'expiration
        expires_at = datetime.utcnow() + timedelta(days=expires_in_days)

        # Créer l'invitation
        invitation = Invitation.create(
            project_id=project_id,
            email=email,
            token=token,
            role=role,
            created_by=created_by,
            expires_at=expires_at,
        )

        return invitation

    def send_invitation(self, invitation: Invitation) -> bool:
        """
        Envoyer une invitation par email.

        Args:
            invitation: L'invitation à envoyer

        Returns:
            True si l'email a été envoyé avec succès

        Raises:
            InvitationError: Si l'envoi échoue
        """
        if not self.email_service:
            current_app.logger.warning(
                "Aucun service d'email configuré. L'invitation ne sera "
                "pas envoyée par email."
            )
            return False

        # Récupérer le projet
        project = Project.get_by_id(invitation.project_id)

        # Construire le sujet et le contenu de l'email
        subject = f"Invitation à rejoindre le projet {project.name}"

        accept_url = self._build_accept_url(invitation.token)

        message = f"""
Bonjour,

Vous avez été invité(e) à rejoindre le projet **{project.name}** sur Agent World.

Rôle: {invitation.role}

Pour accepter cette invitation, veuillez cliquer sur le lien suivant :
{accept_url}

Ce lien expirera le {invitation.expires_at.strftime('%Y-%m-%d %H:%M:%S')}.

Cordialement,
L'équipe Agent World
        """

        try:
            self.email_service.send_email(
                recipient=invitation.email,
                subject=subject,
                body=message,
            )
            return True
        except Exception as e:
            current_app.logger.error(f"Erreur lors de l'envoi de l'invitation: {e}")
            raise InvitationError(f"Échec de l'envoi de l'email: {e}")

    def _build_accept_url(self, token: str) -> str:
        """
        Construire l'URL d'acceptation de l'invitation.

        Args:
            token: Token de l'invitation

        Returns:
            L'URL complète pour accepter l'invitation
        """
        base_url = current_app.config.get("FRONTEND_URL", "http://localhost:3000")
        return f"{base_url}/invitations/accept?token={token}"

    def accept_invitation(self, token: str, user_id: int) -> Invitation:
        """
        Accepter une invitation.

        Args:
            token: Token de l'invitation
            user_id: ID de l'utilisateur qui accepte

        Returns:
            L'invitation acceptée

        Raises:
            InvitationError: Si l'invitation est invalide ou a déjà été acceptée
        """
        invitation = Invitation.get_by_token(token)

        if not invitation:
            raise InvitationError("Invitation introuvable")

        if not invitation.is_pending:
            raise InvitationError(
                f"Invitation non valide (statut: {invitation.status})"
            )

        # Marquer l'invitation comme acceptée
        invitation.accept()

        # TODO: Créer la relation user-project-role (à implémenter avec US-041)
        # Cela sera géré par le service de gestion des rôles

        return invitation

    def revoke_invitation(self, invitation_id: int, revoked_by: int) -> Invitation:
        """
        Révoquer une invitation.

        Args:
            invitation_id: ID de l'invitation à révoquer
            revoked_by: ID de l'utilisateur qui révoke

        Returns:
            L'invitation révoquée

        Raises:
            InvitationError: Si l'invitation n'existe pas ou n'appartient
            pas à l'utilisateur
        """
        invitation = Invitation.get_by_id(invitation_id)

        if not invitation:
            raise InvitationError(f"Invitation {invitation_id} introuvable")

        # Vérifier que l'utilisateur a le droit de révoquer (créateur ou admin)
        if revoked_by != invitation.created_by:
            revoker = User.get_by_id(revoked_by)
            if not revoker or not revoker.is_admin:
                raise InvitationError(
                    "Seul le créateur de l'invitation ou un administrateur "
                    "peut la révoquer"
                )

        invitation.revoke()
        return invitation

    def get_invitation_by_token(self, token: str) -> Optional[Invitation]:
        """
        Récupérer une invitation par son token.

        Args:
            token: Token de l'invitation

        Returns:
            L'invitation ou None si introuvable
        """
        return Invitation.get_by_token(token)

    def get_invitations_by_project(self, project_id: int) -> list[Invitation]:
        """
        Récupérer toutes les invitations pour un projet.

        Args:
            project_id: ID du projet

        Returns:
            Liste des invitations pour ce projet
        """
        return Invitation.get_by_project(project_id)

    def get_pending_invitations_by_email(self, email: str) -> list[Invitation]:
        """
        Récupérer toutes les invitations pendantes pour un email.

        Args:
            email: Adresse email

        Returns:
            Liste des invitations pendantes
        """
        return Invitation.get_pending_by_email(email)

    def cleanup_expired_invitations(self) -> int:
        """
        Nettoyer les invitations expirées.

        Returns:
            Nombre d'invitations expirées supprimées
        """
        # Récupérer toutes les invitations expirées
        all_invitations = Invitation.query.all()
        expired_count = 0

        for invitation in all_invitations:
            if invitation.is_expired and invitation.status == InvitationStatus.PENDING:
                invitation.status = InvitationStatus.EXPIRED
                expired_count += 1

        if expired_count > 0:
            db.session.commit()

        return expired_count
