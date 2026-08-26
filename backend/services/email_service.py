# 📧 Agent World - Email Service
# Version: 0.4.0 (Collaboration)
# Description: Service pour l'envoi d'emails

"""
Email Service for Agent World.

Ce service permet d'envoyer des emails (invitations, notifications, etc.).
Il peut être configuré pour utiliser différents fournisseurs (SMTP, SendGrid, Mailgun).
"""

from typing import Optional

from flask import current_app


class EmailService:
    """
    Service d'envoi d'emails.

    Ce service fournit une interface unifiée pour envoyer des emails
    via différents fournisseurs.
    """

    def __init__(
        self,
        provider: str = "smtp",
        api_key: Optional[str] = None,
        default_sender: Optional[str] = None,
        app=None,
    ):
        """
        Initialiser le service d'email.

        Args:
            provider: Fournisseur d'email (smtp, sendgrid, mailgun)
            api_key: Clé API pour les fournisseurs SaaS
            default_sender: Adresse email de l'expéditeur par défaut
            app: Flask app pour accéder à la configuration
        """
        self.provider = provider
        self.api_key = api_key
        if app:
            self.default_sender = default_sender or app.config.get(
                "EMAIL_DEFAULT_SENDER", "noreply@agentworld.ai"
            )
        else:
            self.default_sender = default_sender or "noreply@agentworld.ai"

    def send_email(
        self,
        recipient: str,
        subject: str,
        body: str,
        sender: Optional[str] = None,
        is_html: bool = False,
    ) -> bool:
        """
        Envoyer un email.

        Args:
            recipient: Adresse email du destinataire
            subject: Sujet de l'email
            body: Contenu de l'email
            sender: Adresse email de l'expéditeur (optionnel)
            is_html: Si True, le corps est au format HTML

        Returns:
            True si l'email a été envoyé avec succès

        Raises:
            Exception: Si l'envoi échoue
        """
        sender = sender or self.default_sender

        current_app.logger.info(
            f"Envoi d'email à {recipient} | Sujet: {subject} | Expéditeur: {sender}"
        )

        # Implémentation par défaut : logger uniquement
        # En production, remplacer par une implémentation réelle
        current_app.logger.debug(f"Email body: {body[:100]}...")

        # TODO: Implémenter l'envoi réel via SMTP/SendGrid/Mailgun
        # Pour l'instant, on simule le succès
        return True

    def send_invitation_email(
        self,
        recipient: str,
        project_name: str,
        role: str,
        accept_url: str,
        expires_at: str,
        sender: Optional[str] = None,
    ) -> bool:
        """
        Envoyer un email d'invitation.

        Args:
            recipient: Adresse email du destinataire
            project_name: Nom du projet
            role: Rôle attribué
            accept_url: URL pour accepter l'invitation
            expires_at: Date d'expiration
            sender: Adresse email de l'expéditeur

        Returns:
            True si l'email a été envoyé avec succès
        """
        subject = f"Invitation à rejoindre le projet {project_name}"
        body = f"""
Bonjour,

Vous avez été invité(e) à rejoindre le projet **{project_name}** sur Agent World.

Rôle: {role}

Pour accepter cette invitation, veuillez cliquer sur le lien suivant :
{accept_url}

Ce lien expirera le {expires_at}.

Cordialement,
L'équipe Agent World
        """

        return self.send_email(
            recipient=recipient,
            subject=subject,
            body=body,
            sender=sender,
            is_html=False,
        )
