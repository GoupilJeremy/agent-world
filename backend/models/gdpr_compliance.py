# 🛡️ Agent World - GDPR Compliance Model
# Version: 1.0.0 (EPIC 10 - US-069)
# Description: Modèles pour la conformité RGPD

"""
GDPR Compliance Models for Agent World.

Ces modèles permettent de gérer:
- Les consentements des utilisateurs
- Les demandes d'accès et de suppression des données (droit à l'oubli)
- Les versions de la politique de confidentialité
- Le suivi des données personnelles
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from .base import BaseModel, db


class ConsentType(str, Enum):
    """Types de consentement RGPD."""
    
    MARKETING = "marketing"
    ANALYTICS = "analytics"
    PROFILING = "profiling"
    DATA_SHARE = "data_share"
    THIRD_PARTY = "third_party"
    NEWSLETTER = "newsletter"
    COOKIES = "cookies"


class ConsentStatus(str, Enum):
    """Statut du consentement."""
    
    GRANTED = "granted"
    REVOKED = "revoked"
    PENDING = "pending"
    EXPIRED = "expired"


class RequestType(str, Enum):
    """Types de demandes RGPD."""
    
    ACCESS = "access"           # Droit d'accès
    RECTIFICATION = "rectification"  # Droit de rectification
    ERASURE = "erasure"        # Droit à l'oubli
    RESTRICTION = "restriction" # Droit à la limitation
    PORTABILITY = "portability" # Droit à la portabilité
    OBJECTION = "objection"    # Droit d'opposition


class RequestStatus(str, Enum):
    """Statut des demandes RGPD."""
    
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    REJECTED = "rejected"
    VERIFIED = "verified"


class GDPRConsent(BaseModel):
    """
    Modèle pour stocker les consentements des utilisateurs.
    
    Chaque consentement enregistres:
    - L'utilisateur qui a consenti
    - Le type de consentement
    - Le statut (accordé/révoqué)
    - La date de consentement
    - La version de la politique acceptée
    - La source (IP, user agent)
    """
    
    __tablename__ = "gdpr_consents"
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    consent_type = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(20), nullable=False, default="granted")
    consent_version = db.Column(db.String(50), nullable=True)  # Version de la politique
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.Text, nullable=True)
    consent_text = db.Column(db.Text, nullable=True)  # Texte du consentement
    is_required = db.Column(db.Boolean, nullable=False, default=False)
    expires_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    user = db.relationship("User", backref="gdpr_consents")
    
    def __init__(
        self,
        user_id: int,
        consent_type: str,
        status: str = "granted",
        consent_version: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        consent_text: Optional[str] = None,
        is_required: bool = False,
        expires_at: Optional[datetime] = None,
    ):
        self.user_id = user_id
        self.consent_type = consent_type
        self.status = status
        self.consent_version = consent_version
        self.ip_address = ip_address
        self.user_agent = user_agent
        self.consent_text = consent_text
        self.is_required = is_required
        self.expires_at = expires_at
    
    def __repr__(self) -> str:
        return f"<GDPRConsent(id={self.id}, user_id={self.user_id}, type={self.consent_type}, status={self.status})>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert consent to dictionary."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "user": self.user.to_dict() if self.user else None,
            "consent_type": self.consent_type,
            "status": self.status,
            "consent_version": self.consent_version,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "consent_text": self.consent_text,
            "is_required": self.is_required,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
    
    @classmethod
    def get_by_user(cls, user_id: int) -> List["GDPRConsent"]:
        """Get all consents for a user."""
        return cls.query.filter_by(user_id=user_id).order_by(cls.created_at.desc()).all()
    
    @classmethod
    def get_by_type(cls, user_id: int, consent_type: str) -> Optional["GDPRConsent"]:
        """Get a specific consent type for a user."""
        return cls.query.filter_by(user_id=user_id, consent_type=consent_type).order_by(cls.created_at.desc()).first()
    
    @classmethod
    def has_consent(cls, user_id: int, consent_type: str) -> bool:
        """Check if user has granted consent for a type."""
        consent = cls.query.filter_by(
            user_id=user_id,
            consent_type=consent_type,
            status="granted"
        ).order_by(cls.created_at.desc()).first()
        return consent is not None
    
    @classmethod
    def revoke_all(cls, user_id: int) -> int:
        """Revoke all consents for a user."""
        count = cls.query.filter_by(user_id=user_id, status="granted").update({"status": "revoked"})
        db.session.commit()
        return count


class DataSubjectRequest(BaseModel):
    """
    Modèle pour les demandes des personnes concernées (Data Subject Requests).
    
    Ces demandes permettent aux utilisateurs d'exercer leurs droits RGPD:
    - Accès à leurs données
    - Rectification des données
    - Suppression (droit à l'oubli)
    - Restriction du traitement
    - Portabilité des données
    - Opposition au traitement
    """
    
    __tablename__ = "gdpr_requests"
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    request_id = db.Column(db.String(50), unique=True, nullable=False)  # UUID pour référence
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    request_type = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(20), nullable=False, default="pending")
    description = db.Column(db.Text, nullable=True)
    data_scope = db.Column(db.Text, nullable=True)  # Quelles données concernent
    response_data = db.Column(db.Text, nullable=True)  # JSON avec la réponse
    processed_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)  # Admin qui a traité
    processing_notes = db.Column(db.Text, nullable=True)
    deadline = db.Column(db.DateTime, nullable=True)  # Date limite de traitement (30 jours)
    completed_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship("User", foreign_keys=[user_id], backref="gdpr_requests")
    processor = db.relationship("User", foreign_keys=[processed_by])
    
    def __init__(
        self,
        user_id: int,
        request_type: str,
        request_id: Optional[str] = None,
        description: Optional[str] = None,
        data_scope: Optional[str] = None,
    ):
        import uuid
        self.user_id = user_id
        self.request_type = request_type
        self.request_id = request_id or str(uuid.uuid4())[:12].upper()
        self.description = description
        self.data_scope = data_scope
        self.status = "pending"
        self.deadline = datetime.utcnow() + timedelta(days=30)  # 30 jours pour traiter
    
    def __repr__(self) -> str:
        return f"<DataSubjectRequest(id={self.id}, request_id={self.request_id}, type={self.request_type}, status={self.status})>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert request to dictionary."""
        from ..services.gdpr_service import calculate_days_remaining
        
        return {
            "id": self.id,
            "request_id": self.request_id,
            "user_id": self.user_id,
            "user": self.user.to_dict() if self.user else None,
            "request_type": self.request_type,
            "status": self.status,
            "description": self.description,
            "data_scope": self.data_scope,
            "response_data": self.response_data,
            "processed_by": self.processed_by,
            "processor": self.processor.to_dict() if self.processor else None,
            "processing_notes": self.processing_notes,
            "deadline": self.deadline.isoformat() if self.deadline else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "days_remaining": calculate_days_remaining(self.deadline) if self.deadline else 0,
        }
    
    @classmethod
    def get_by_id(cls, request_id: int) -> Optional["DataSubjectRequest"]:
        """Get request by database ID."""
        return cls.query.get(request_id)
    
    @classmethod
    def get_by_request_id(cls, request_id: str) -> Optional["DataSubjectRequest"]:
        """Get request by request_id (UUID)."""
        return cls.query.filter_by(request_id=request_id).first()
    
    @classmethod
    def get_by_user(cls, user_id: int) -> List["DataSubjectRequest"]:
        """Get all requests for a user."""
        return cls.query.filter_by(user_id=user_id).order_by(cls.created_at.desc()).all()
    
    @classmethod
    def get_pending(cls, limit: int = 100) -> List["DataSubjectRequest"]:
        """Get all pending requests."""
        return cls.query.filter_by(status="pending").order_by(cls.created_at.asc()).limit(limit).all()
    
    @classmethod
    def get_overdue(cls) -> List["DataSubjectRequest"]:
        """Get overdue requests (past deadline)."""
        return cls.query.filter(
            cls.status != "completed",
            cls.deadline < datetime.utcnow()
        ).order_by(cls.deadline.asc()).all()
    
    @classmethod
    def count_by_status(cls) -> Dict[str, int]:
        """Count requests by status."""
        from sqlalchemy import func
        results = db.session.query(cls.status, func.count(cls.id)).group_by(cls.status).all()
        return {status: count for status, count in results}
    
    @classmethod
    def count_by_type(cls) -> Dict[str, int]:
        """Count requests by type."""
        from sqlalchemy import func
        results = db.session.query(cls.request_type, func.count(cls.id)).group_by(cls.request_type).all()
        return {request_type: count for request_type, count in results}


class PrivacyPolicyVersion(BaseModel):
    """
    Modèle pour versionner la politique de confidentialité.
    
    Chaque version contient:
    - Le texte de la politique
    - La date de publication
    - Si c'est la version active
    - Les changements par rapport à la version précédente
    """
    
    __tablename__ = "privacy_policy_versions"
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    version = db.Column(db.String(20), unique=True, nullable=False)  # ex: "v1.0", "v2.0"
    title = db.Column(db.String(200), nullable=True)
    content = db.Column(db.Text, nullable=False)  # Markdown/HTML
    content_summary = db.Column(db.Text, nullable=True)  # Résumé des changements
    is_active = db.Column(db.Boolean, nullable=False, default=False)
    published_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)
    published_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    requires_consent = db.Column(db.Boolean, nullable=False, default=True)
    consent_deadline = db.Column(db.DateTime, nullable=True)  # Date limite pour accepter
    
    # Relationship
    publisher = db.relationship("User")
    
    def __init__(
        self,
        version: str,
        content: str,
        title: Optional[str] = None,
        content_summary: Optional[str] = None,
        is_active: bool = False,
        published_by: Optional[int] = None,
        requires_consent: bool = True,
        consent_deadline: Optional[datetime] = None,
    ):
        self.version = version
        self.title = title or f"Politique de Confidentialité {version}"
        self.content = content
        self.content_summary = content_summary
        self.is_active = is_active
        self.published_by = published_by
        self.requires_consent = requires_consent
        self.consent_deadline = consent_deadline
    
    def __repr__(self) -> str:
        return f"<PrivacyPolicyVersion(id={self.id}, version={self.version}, active={self.is_active})>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert policy version to dictionary."""
        return {
            "id": self.id,
            "version": self.version,
            "title": self.title,
            "content": self.content,
            "content_summary": self.content_summary,
            "is_active": self.is_active,
            "published_at": self.published_at.isoformat() if self.published_at else None,
            "published_by": self.published_by,
            "publisher": self.publisher.to_dict() if self.publisher else None,
            "requires_consent": self.requires_consent,
            "consent_deadline": self.consent_deadline.isoformat() if self.consent_deadline else None,
        }
    
    @classmethod
    def get_active(cls) -> Optional["PrivacyPolicyVersion"]:
        """Get the currently active privacy policy."""
        return cls.query.filter_by(is_active=True).order_by(cls.published_at.desc()).first()
    
    @classmethod
    def get_latest(cls) -> Optional["PrivacyPolicyVersion"]:
        """Get the latest version (by published_at)."""
        return cls.query.order_by(cls.published_at.desc()).first()
    
    @classmethod
    def get_all(cls, limit: int = 100) -> List["PrivacyPolicyVersion"]:
        """Get all versions."""
        return cls.query.order_by(cls.published_at.desc()).limit(limit).all()
    
    @classmethod
    def set_active(cls, version_id: int) -> Optional["PrivacyPolicyVersion"]:
        """Set a specific version as active."""
        # Deactivate all others
        cls.query.update({"is_active": False})
        db.session.commit()
        
        # Activate the selected one
        policy = cls.query.get(version_id)
        if policy:
            policy.is_active = True
            db.session.commit()
        return policy


class PersonalDataLog(BaseModel):
    """
    Modèle pour logger les accès aux données personnelles.
    
    Requirement RGPD : tenir un registre des traitements de données personnelles.
    """
    
    __tablename__ = "personal_data_logs"
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    action = db.Column(db.String(50), nullable=False)  # access, update, delete, export
    data_type = db.Column(db.String(100), nullable=True)  # Quel type de donnée
    data_description = db.Column(db.Text, nullable=True)  # Description des données
    requested_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)  # Qui a demandé
    request_purpose = db.Column(db.Text, nullable=True)
    legal_basis = db.Column(db.String(100), nullable=True)  # consent, contract, legal_obligation, etc.
    retention_period = db.Column(db.String(100), nullable=True)
    third_party_involved = db.Column(db.Boolean, nullable=False, default=False)
    third_party_details = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)
    
    def __init__(
        self,
        user_id: Optional[int] = None,
        action: str = "",
        data_type: Optional[str] = None,
        data_description: Optional[str] = None,
        requested_by: Optional[int] = None,
        request_purpose: Optional[str] = None,
        legal_basis: Optional[str] = None,
        retention_period: Optional[str] = None,
        third_party_involved: bool = False,
        third_party_details: Optional[str] = None,
    ):
        self.user_id = user_id
        self.action = action
        self.data_type = data_type
        self.data_description = data_description
        self.requested_by = requested_by
        self.request_purpose = request_purpose
        self.legal_basis = legal_basis
        self.retention_period = retention_period
        self.third_party_involved = third_party_involved
        self.third_party_details = third_party_details
    
    @classmethod
    def log_access(
        cls,
        user_id: int,
        data_type: str,
        data_description: str,
        requested_by: Optional[int] = None,
        request_purpose: Optional[str] = None,
    ) -> "PersonalDataLog":
        """Log personal data access."""
        log_entry = cls(
            user_id=user_id,
            action="access",
            data_type=data_type,
            data_description=data_description,
            requested_by=requested_by,
            request_purpose=request_purpose,
            legal_basis="legitimate_interest",
        )
        db.session.add(log_entry)
        db.session.commit()
        return log_entry
    
    @classmethod
    def log_export(cls, user_id: int, data_types: List[str]) -> "PersonalDataLog":
        """Log personal data export."""
        log_entry = cls(
            user_id=user_id,
            action="export",
            data_type=", ".join(data_types),
            data_description=f"Export des données: {', '.join(data_types)}",
            legal_basis="consent",
            request_purpose="User requested data export (GDPR Art. 20)",
        )
        db.session.add(log_entry)
        db.session.commit()
        return log_entry


# Import timedelta at the bottom to avoid circular imports
from datetime import timedelta
