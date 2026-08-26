# 🛡️ Agent World - GDPR Service
# Version: 1.0.0 (EPIC 10 - US-069)
# Description: Service pour gérer la conformité RGPD

"""
GDPR Service for Agent World.

Ce service gère:
- La gestion des consentements utilisateurs
- Le traitement des demandes d'accès et de suppression
- L'export des données personnelles
- La vérification de la conformité RGPD
- Le droit à l'oubli
"""

import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union

from flask import current_app, request

from ..models.base import db
from ..models.gdpr_compliance import (
    ConsentStatus,
    ConsentType,
    DataSubjectRequest,
    GDPRConsent,
    PersonalDataLog,
    PrivacyPolicyVersion,
    RequestStatus,
    RequestType,
)
from ..models.user import User


class GDPRError(Exception):
    """Base exception for GDPR-related errors."""
    
    status_code = 400
    error_code = "gdpr_error"


class GDPRConsentError(GDPRError):
    """Error related to consent management."""
    
    status_code = 400
    error_code = "gdpr_consent_error"


class GDPRRequestError(GDPRError):
    """Error related to data subject requests."""
    
    status_code = 400
    error_code = "gdpr_request_error"


class GDPRNotFoundError(GDPRError):
    """Resource not found."""
    
    status_code = 404
    error_code = "gdpr_not_found"


class GDPRAccessDeniedError(GDPRError):
    """Access denied to GDPR resource."""
    
    status_code = 403
    error_code = "gdpr_access_denied"


class GDPRService:
    """
    Service for managing GDPR compliance.
    
    This service provides functionality for:
    - Managing user consents
    - Processing data subject requests (DSRs)
    - Exporting personal data
    - Managing privacy policy versions
    - Logging personal data access
    """
    
    # Deadline for processing DSRs (30 days per GDPR)
    DSR_PROCESSING_DEADLINE_DAYS = 30
    
    # Age of consent (16 years in most EU countries, 13 in some)
    CONSENT_AGE = 16
    
    def __init__(self):
        """Initialize the GDPRService."""
        pass

    # ==================== Consent Management ====================

    def grant_consent(
        self,
        user_id: int,
        consent_type: Union[str, ConsentType],
        version: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        consent_text: Optional[str] = None,
        is_required: bool = False,
        expires_in_days: Optional[int] = None,
    ) -> GDPRConsent:
        """
        Grant consent for a specific type.
        
        Args:
            user_id: ID of the user granting consent
            consent_type: Type of consent (ConsentType enum or string)
            version: Version of the privacy policy
            ip_address: IP address of the request
            user_agent: User agent of the request
            consent_text: Text of the consent
            is_required: Whether this consent is required
            expires_in_days: Number of days until consent expires
            
        Returns:
            The created GDPRConsent record
        """
        consent_type_str = consent_type.value if isinstance(consent_type, ConsentType) else consent_type
        
        # Check if user exists
        user = User.get_by_id(user_id)
        if not user:
            raise GDPRNotFoundError(f"User with ID {user_id} not found")
        
        # Check user age (if birth date is available)
        if user.date_of_birth:
            age = self.calculate_age(user.date_of_birth)
            if age < self.CONSENT_AGE:
                raise GDPRConsentError(f"User must be at least {self.CONSENT_AGE} years old to grant consent")
        
        # Get request info if not provided
        if not ip_address or not user_agent:
            req_info = self.get_request_info()
            ip_address = ip_address or req_info.get("ip_address")
            user_agent = user_agent or req_info.get("user_agent")
        
        # Calculate expiration
        expires_at = None
        if expires_in_days:
            expires_at = datetime.utcnow() + timedelta(days=expires_in_days)
        
        # Create consent record
        consent = GDPRConsent(
            user_id=user_id,
            consent_type=consent_type_str,
            status="granted",
            consent_version=version,
            ip_address=ip_address,
            user_agent=user_agent,
            consent_text=consent_text,
            is_required=is_required,
            expires_at=expires_at,
        )
        
        db.session.add(consent)
        db.session.commit()
        
        # Log the consent
        PersonalDataLog.log_access(
            user_id=user_id,
            data_type="consent",
            data_description=f"Consent granted for {consent_type_str}",
            request_purpose="User consent for data processing",
            legal_basis="consent",
        )
        
        return consent

    def revoke_consent(
        self,
        user_id: int,
        consent_type: Union[str, ConsentType],
    ) -> GDPRConsent:
        """
        Revoke consent for a specific type.
        
        Args:
            user_id: ID of the user revoking consent
            consent_type: Type of consent to revoke
            
        Returns:
            The updated GDPRConsent record
        """
        consent_type_str = consent_type.value if isinstance(consent_type, ConsentType) else consent_type
        
        # Find the most recent consent for this type
        consent = GDPRConsent.get_by_type(user_id, consent_type_str)
        if not consent:
            raise GDPRNotFoundError(f"No consent found for type {consent_type_str} for user {user_id}")
        
        # Check if consent is already revoked
        if consent.status == "revoked":
            raise GDPRConsentError(f"Consent for {consent_type_str} is already revoked")
        
        # Update consent status
        consent.status = "revoked"
        consent.updated_at = datetime.utcnow()
        db.session.commit()
        
        # Log the revocation
        PersonalDataLog.log_access(
            user_id=user_id,
            data_type="consent",
            data_description=f"Consent revoked for {consent_type_str}",
            request_purpose="User revoked consent for data processing",
            legal_basis="consent",
        )
        
        return consent

    def get_consent(
        self,
        user_id: int,
        consent_type: Union[str, ConsentType],
    ) -> Optional[GDPRConsent]:
        """
        Get consent for a specific type.
        
        Args:
            user_id: ID of the user
            consent_type: Type of consent
            
        Returns:
            GDPRConsent record or None
        """
        consent_type_str = consent_type.value if isinstance(consent_type, ConsentType) else consent_type
        return GDPRConsent.get_by_type(user_id, consent_type_str)

    def has_consent(
        self,
        user_id: int,
        consent_type: Union[str, ConsentType],
    ) -> bool:
        """
        Check if user has granted consent for a type.
        
        Args:
            user_id: ID of the user
            consent_type: Type of consent
            
        Returns:
            True if consent is granted, False otherwise
        """
        consent_type_str = consent_type.value if isinstance(consent_type, ConsentType) else consent_type
        return GDPRConsent.has_consent(user_id, consent_type_str)

    def get_all_consents(self, user_id: int) -> List[GDPRConsent]:
        """
        Get all consents for a user.
        
        Args:
            user_id: ID of the user
            
        Returns:
            List of GDPRConsent records
        """
        return GDPRConsent.get_by_user(user_id)

    def check_required_consents(self, user_id: int) -> Dict[str, bool]:
        """
        Check all required consents for a user.
        
        Args:
            user_id: ID of the user
            
        Returns:
            Dictionary with consent types and their status
        """
        consents = self.get_all_consents(user_id)
        result = {}
        
        for consent_type in ConsentType:
            consent = next((c for c in consents if c.consent_type == consent_type.value), None)
            result[consent_type.value] = {
                "has_consent": consent and consent.status == "granted",
                "status": consent.status if consent else "not_given",
                "is_required": consent.is_required if consent else False,
            }
        
        return result

    # ==================== Data Subject Requests (DSR) ====================

    def create_request(
        self,
        user_id: int,
        request_type: Union[str, RequestType],
        description: Optional[str] = None,
        data_scope: Optional[str] = None,
    ) -> DataSubjectRequest:
        """
        Create a new data subject request.
        
        Args:
            user_id: ID of the user making the request
            request_type: Type of request (RequestType enum or string)
            description: Description of the request
            data_scope: Scope of data to be processed
            
        Returns:
            The created DataSubjectRequest
        """
        request_type_str = request_type.value if isinstance(request_type, RequestType) else request_type
        
        # Validate request type
        if request_type_str not in [rt.value for rt in RequestType]:
            raise GDPRRequestError(f"Invalid request type: {request_type_str}")
        
        # Check if user exists
        user = User.get_by_id(user_id)
        if not user:
            raise GDPRNotFoundError(f"User with ID {user_id} not found")
        
        # Create request
        dsr = DataSubjectRequest(
            user_id=user_id,
            request_type=request_type_str,
            description=description,
            data_scope=data_scope,
        )
        
        db.session.add(dsr)
        db.session.commit()
        
        # Log the request
        PersonalDataLog.log_access(
            user_id=user_id,
            data_type="dsr",
            data_description=f"Data Subject Request: {request_type_str}",
            request_purpose=f"User submitted {request_type_str} request",
            legal_basis="legal_obligation",
        )
        
        return dsr

    def get_request(self, request_id: Union[int, str]) -> DataSubjectRequest:
        """
        Get a data subject request by ID or request_id.
        
        Args:
            request_id: Database ID or request_id (UUID)
            
        Returns:
            DataSubjectRequest
        """
        if isinstance(request_id, int):
            request = DataSubjectRequest.get_by_id(request_id)
        else:
            request = DataSubjectRequest.get_by_request_id(request_id)
        
        if not request:
            raise GDPRNotFoundError(f"Data subject request not found: {request_id}")
        
        return request

    def get_user_requests(self, user_id: int) -> List[DataSubjectRequest]:
        """
        Get all requests for a user.
        
        Args:
            user_id: ID of the user
            
        Returns:
            List of DataSubjectRequest
        """
        return DataSubjectRequest.get_by_user(user_id)

    def get_pending_requests(self, limit: int = 100) -> List[DataSubjectRequest]:
        """
        Get all pending requests.
        
        Args:
            limit: Maximum number of requests to return
            
        Returns:
            List of pending DataSubjectRequest
        """
        return DataSubjectRequest.get_pending(limit)

    def get_overdue_requests(self) -> List[DataSubjectRequest]:
        """
        Get all overdue requests (past deadline).
        
        Returns:
            List of overdue DataSubjectRequest
        """
        return DataSubjectRequest.get_overdue()

    def update_request_status(
        self,
        request_id: Union[int, str],
        status: Union[str, RequestStatus],
        processed_by: Optional[int] = None,
        response_data: Optional[Dict[str, Any]] = None,
        processing_notes: Optional[str] = None,
    ) -> DataSubjectRequest:
        """
        Update the status of a data subject request.
        
        Args:
            request_id: ID or request_id of the request
            status: New status
            processed_by: ID of the user who processed the request
            response_data: Response data (for completed requests)
            processing_notes: Notes about the processing
            
        Returns:
            Updated DataSubjectRequest
        """
        request = self.get_request(request_id)
        status_str = status.value if isinstance(status, RequestStatus) else status
        
        # Validate status
        if status_str not in [rs.value for rs in RequestStatus]:
            raise GDPRRequestError(f"Invalid status: {status_str}")
        
        # Update request
        request.status = status_str
        request.processed_by = processed_by
        request.processing_notes = processing_notes
        
        if status_str == "completed":
            request.completed_at = datetime.utcnow()
        
        if response_data:
            request.response_data = json.dumps(response_data, default=str, ensure_ascii=False)
        
        request.updated_at = datetime.utcnow()
        db.session.commit()
        
        return request

    def process_access_request(
        self,
        request_id: Union[int, str],
        processed_by: int,
    ) -> DataSubjectRequest:
        """
        Process an access request (droit d'accès).
        
        Args:
            request_id: ID or request_id of the request
            processed_by: ID of the admin processing the request
            
        Returns:
            Updated DataSubjectRequest with response data
        """
        request = self.get_request(request_id)
        
        if request.request_type != "access":
            raise GDPRRequestError("This is not an access request")
        
        # Collect user data
        user = request.user
        if not user:
            raise GDPRNotFoundError("User not found")
        
        response_data = self.collect_user_data(user.id, request.data_scope)
        
        # Update request
        return self.update_request_status(
            request_id=request.id,
            status="completed",
            processed_by=processed_by,
            response_data=response_data,
            processing_notes="Access request processed. User data exported.",
        )

    def process_erasure_request(
        self,
        request_id: Union[int, str],
        processed_by: int,
        hard_delete: bool = False,
    ) -> DataSubjectRequest:
        """
        Process an erasure request (droit à l'oubli).
        
        Args:
            request_id: ID or request_id of the request
            processed_by: ID of the admin processing the request
            hard_delete: Whether to permanently delete (vs anonymize)
            
        Returns:
            Updated DataSubjectRequest
        """
        request = self.get_request(request_id)
        
        if request.request_type != "erasure":
            raise GDPRRequestError("This is not an erasure request")
        
        user = request.user
        if not user:
            raise GDPRNotFoundError("User not found")
        
        # Delete user data based on scope
        deleted_count = self.delete_user_data(user.id, request.data_scope, hard_delete)
        
        # Mark user as deleted (soft delete) or actually delete
        if hard_delete:
            db.session.delete(user)
        else:
            user.email = f"deleted_user_{user.id}@{datetime.utcnow().strftime('%Y%m%d')}.invalid"
            user.username = f"deleted_{user.id}"
            user.is_active = False
        
        db.session.commit()
        
        # Update request
        return self.update_request_status(
            request_id=request.id,
            status="completed",
            processed_by=processed_by,
            response_data={"deleted_count": deleted_count, "hard_delete": hard_delete},
            processing_notes=f"Erasure request processed. {deleted_count} records affected.",
        )

    def collect_user_data(
        self,
        user_id: int,
        data_scope: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Collect all personal data for a user.
        
        Args:
            user_id: ID of the user
            data_scope: Optional scope filter
            
        Returns:
            Dictionary with all user data
        """
        user = User.get_by_id(user_id)
        if not user:
            raise GDPRNotFoundError(f"User with ID {user_id} not found")
        
        # Log the access
        PersonalDataLog.log_export(
            user_id=user_id,
            data_types=["profile", "agents", "projects", "files", "consents", "audit_logs"],
        )
        
        # Build comprehensive data export
        data = {
            "user": user.to_dict(include_sensitive=True),
            "consents": [c.to_dict() for c in GDPRConsent.get_by_user(user_id)],
            "requests": [r.to_dict() for r in DataSubjectRequest.get_by_user(user_id)],
        }
        
        # Add data based on scope or if no scope specified
        if not data_scope or "agents" in (data_scope or ""):
            data["agents"] = self._collect_agent_data(user_id)
        
        if not data_scope or "projects" in (data_scope or ""):
            data["projects"] = self._collect_project_data(user_id)
        
        if not data_scope or "files" in (data_scope or ""):
            data["files"] = self._collect_file_data(user_id)
        
        if not data_scope or "templates" in (data_scope or ""):
            data["templates"] = self._collect_template_data(user_id)
        
        if not data_scope or "workflows" in (data_scope or ""):
            data["workflows"] = self._collect_workflow_data(user_id)
        
        if not data_scope or "audit" in (data_scope or ""):
            data["audit_logs"] = self._collect_audit_data(user_id)
        
        return {
            "export_date": datetime.utcnow().isoformat(),
            "user_id": user_id,
            "data": data,
        }

    def _collect_agent_data(self, user_id: int) -> List[Dict[str, Any]]:
        """Collect agent data for a user."""
        try:
            from ..models.agent import Agent
            agents = Agent.query.filter_by(user_id=user_id).all()
            return [agent.to_dict() for agent in agents]
        except ImportError:
            return []

    def _collect_project_data(self, user_id: int) -> List[Dict[str, Any]]:
        """Collect project data for a user."""
        try:
            from ..models.project import Project
            projects = Project.query.filter_by(owner_id=user_id).all()
            return [project.to_dict() for project in projects]
        except ImportError:
            return []

    def _collect_file_data(self, user_id: int) -> List[Dict[str, Any]]:
        """Collect file data for a user."""
        try:
            from ..models.generated_file import GeneratedFile
            files = GeneratedFile.query.filter_by(user_id=user_id).all()
            return [file.to_dict() for file in files]
        except ImportError:
            return []

    def _collect_template_data(self, user_id: int) -> List[Dict[str, Any]]:
        """Collect template data for a user."""
        try:
            from ..models.template import Template
            templates = Template.query.filter_by(creator_id=user_id).all()
            return [template.to_dict() for template in templates]
        except ImportError:
            return []

    def _collect_workflow_data(self, user_id: int) -> List[Dict[str, Any]]:
        """Collect workflow data for a user."""
        try:
            from ..models.workflow import Workflow
            workflows = Workflow.query.filter_by(user_id=user_id).all()
            return [workflow.to_dict() for workflow in workflows]
        except ImportError:
            return []

    def _collect_audit_data(self, user_id: int) -> List[Dict[str, Any]]:
        """Collect audit log data for a user."""
        try:
            from ..models.audit_log import AuditLog
            logs = AuditLog.get_by_user(user_id, limit=1000)
            return [log.to_dict() for log in logs]
        except ImportError:
            return []

    def delete_user_data(
        self,
        user_id: int,
        data_scope: Optional[str] = None,
        hard_delete: bool = False,
    ) -> int:
        """
        Delete user data based on scope.
        
        Args:
            user_id: ID of the user
            data_scope: Optional scope filter
            hard_delete: Whether to permanently delete
            
        Returns:
            Number of records deleted
        """
        deleted_count = 0
        
        # Log the erasure
        PersonalDataLog.log_access(
            user_id=user_id,
            data_type="erasure",
            data_description=f"Data erasure request for user {user_id}",
            request_purpose="GDPR Art. 17 - Right to erasure",
            legal_basis="legal_obligation",
        )
        
        # Delete based on scope
        if not data_scope or "consents" in (data_scope or ""):
            count = GDPRConsent.query.filter_by(user_id=user_id).delete()
            deleted_count += count
        
        if not data_scope or "requests" in (data_scope or ""):
            count = DataSubjectRequest.query.filter_by(user_id=user_id).delete()
            deleted_count += count
        
        if not data_scope or "agents" in (data_scope or ""):
            try:
                from ..models.agent import Agent
                count = Agent.query.filter_by(user_id=user_id).delete()
                deleted_count += count
            except ImportError:
                pass
        
        if not data_scope or "projects" in (data_scope or ""):
            try:
                from ..models.project import Project
                count = Project.query.filter_by(owner_id=user_id).delete()
                deleted_count += count
            except ImportError:
                pass
        
        if not data_scope or "files" in (data_scope or ""):
            try:
                from ..models.generated_file import GeneratedFile
                count = GeneratedFile.query.filter_by(user_id=user_id).delete()
                deleted_count += count
            except ImportError:
                pass
        
        if not data_scope or "templates" in (data_scope or ""):
            try:
                from ..models.template import Template
                count = Template.query.filter_by(creator_id=user_id).delete()
                deleted_count += count
            except ImportError:
                pass
        
        if not data_scope or "workflows" in (data_scope or ""):
            try:
                from ..models.workflow import Workflow
                count = Workflow.query.filter_by(user_id=user_id).delete()
                deleted_count += count
            except ImportError:
                pass
        
        if not data_scope or "audit" in (data_scope or ""):
            # For audit logs, we typically anonymize rather than delete
            try:
                from ..models.audit_log import AuditLog
                count = AuditLog.query.filter_by(user_id=user_id).update({"user_id": None})
                deleted_count += count
            except ImportError:
                pass
        
        db.session.commit()
        return deleted_count

    # ==================== Privacy Policy Management ====================

    def create_policy_version(
        self,
        version: str,
        content: str,
        title: Optional[str] = None,
        content_summary: Optional[str] = None,
        published_by: Optional[int] = None,
        requires_consent: bool = True,
        consent_deadline_days: Optional[int] = None,
    ) -> PrivacyPolicyVersion:
        """
        Create a new privacy policy version.
        
        Args:
            version: Version identifier (e.g., "v1.0")
            content: Policy content (Markdown/HTML)
            title: Policy title
            content_summary: Summary of changes
            published_by: ID of the user publishing the policy
            requires_consent: Whether users need to consent to this version
            consent_deadline_days: Days until consent is required
            
        Returns:
            The created PrivacyPolicyVersion
        """
        # Check if version already exists
        existing = PrivacyPolicyVersion.query.filter_by(version=version).first()
        if existing:
            raise GDPRError(f"Privacy policy version {version} already exists")
        
        # Calculate deadline if provided
        consent_deadline = None
        if consent_deadline_days:
            consent_deadline = datetime.utcnow() + timedelta(days=consent_deadline_days)
        
        policy = PrivacyPolicyVersion(
            version=version,
            content=content,
            title=title,
            content_summary=content_summary,
            is_active=False,
            published_by=published_by,
            requires_consent=requires_consent,
            consent_deadline=consent_deadline,
        )
        
        db.session.add(policy)
        db.session.commit()
        
        return policy

    def get_active_policy(self) -> Optional[PrivacyPolicyVersion]:
        """
        Get the currently active privacy policy.
        
        Returns:
            Active PrivacyPolicyVersion or None
        """
        return PrivacyPolicyVersion.get_active()

    def get_policy_version(self, version: str) -> PrivacyPolicyVersion:
        """
        Get a specific privacy policy version.
        
        Args:
            version: Version identifier
            
        Returns:
            PrivacyPolicyVersion
        """
        policy = PrivacyPolicyVersion.query.filter_by(version=version).first()
        if not policy:
            raise GDPRNotFoundError(f"Privacy policy version {version} not found")
        return policy

    def set_active_policy(self, version_id: int) -> PrivacyPolicyVersion:
        """
        Set a specific version as active.
        
        Args:
            version_id: Database ID of the version
            
        Returns:
            Activated PrivacyPolicyVersion
        """
        policy = PrivacyPolicyVersion.query.get(version_id)
        if not policy:
            raise GDPRNotFoundError(f"Privacy policy version with ID {version_id} not found")
        
        # Deactivate all others and activate this one
        return PrivacyPolicyVersion.set_active(version_id)

    def get_all_policies(self, limit: int = 100) -> List[PrivacyPolicyVersion]:
        """
        Get all privacy policy versions.
        
        Args:
            limit: Maximum number of versions to return
            
        Returns:
            List of PrivacyPolicyVersion
        """
        return PrivacyPolicyVersion.get_all(limit)

    # ==================== Compliance Utilities ====================

    def check_user_compliance(self, user_id: int) -> Dict[str, Any]:
        """
        Check overall compliance status for a user.
        
        Args:
            user_id: ID of the user
            
        Returns:
            Compliance status dictionary
        """
        user = User.get_by_id(user_id)
        if not user:
            raise GDPRNotFoundError(f"User with ID {user_id} not found")
        
        # Check age
        age = None
        if user.date_of_birth:
            age = self.calculate_age(user.date_of_birth)
        
        # Check required consents
        required_consents = self.check_required_consents(user_id)
        all_consents_granted = all(
            c["has_consent"] for c in required_consents.values() if c["is_required"]
        )
        
        # Check active policy consent
        active_policy = self.get_active_policy()
        policy_consent_ok = True
        if active_policy and active_policy.requires_consent:
            policy_consent = GDPRConsent.get_by_type(user_id, "privacy_policy")
            policy_consent_ok = policy_consent and policy_consent.status == "granted"
        
        # Check pending requests
        pending_requests = DataSubjectRequest.get_by_user(user_id)
        pending_requests = [r for r in pending_requests if r.status == "pending"]
        
        return {
            "user_id": user_id,
            "age": age,
            "is_adult": age is None or age >= self.CONSENT_AGE,
            "required_consents_granted": all_consents_granted,
            "policy_consent_ok": policy_consent_ok,
            "active_policy_version": active_policy.version if active_policy else None,
            "pending_requests_count": len(pending_requests),
            "compliant": (
                (age is None or age >= self.CONSENT_AGE) and
                all_consents_granted and
                policy_consent_ok and
                len(pending_requests) == 0
            ),
        }

    def get_compliance_stats(self) -> Dict[str, Any]:
        """
        Get compliance statistics across all users.
        
        Returns:
            Compliance statistics dictionary
        """
        from ..models.user import User
        
        total_users = User.query.count()
        
        # Count users with required consents
        required_consent_counts = {}
        for consent_type in ConsentType:
            count = GDPRConsent.query.filter_by(
                consent_type=consent_type.value,
                status="granted"
            ).count()
            required_consent_counts[consent_type.value] = count
        
        # Count requests by status
        request_stats = DataSubjectRequest.count_by_status()
        
        # Count requests by type
        request_type_stats = DataSubjectRequest.count_by_type()
        
        # Check active policy
        active_policy = self.get_active_policy()
        
        return {
            "total_users": total_users,
            "consent_counts": required_consent_counts,
            "request_stats": request_stats,
            "request_type_stats": request_type_stats,
            "active_policy": active_policy.version if active_policy else None,
            "pending_requests": len(DataSubjectRequest.get_pending(1000)),
            "overdue_requests": len(DataSubjectRequest.get_overdue()),
        }

    # ==================== Helper Methods ====================

    def get_request_info(self) -> Dict[str, Optional[str]]:
        """
        Get IP address and user agent from the current request.
        
        Returns:
            Dictionary with ip_address and user_agent
        """
        ip_address = None
        user_agent = None
        
        if request:
            # Get IP address (handle proxy headers)
            ip_address = request.remote_addr
            if request.headers.get("X-Forwarded-For"):
                ip_address = request.headers.get("X-Forwarded-For").split(",")[0].strip()
            elif request.headers.get("X-Real-IP"):
                ip_address = request.headers.get("X-Real-IP")
            
            # Get user agent
            user_agent = request.headers.get("User-Agent")
        
        return {
            "ip_address": ip_address,
            "user_agent": user_agent,
        }

    @staticmethod
    def calculate_age(birth_date: datetime) -> int:
        """
        Calculate age from birth date.
        
        Args:
            birth_date: Date of birth
            
        Returns:
            Age in years
        """
        today = datetime.utcnow()
        age = today.year - birth_date.year
        if today.month < birth_date.month or (today.month == birth_date.month and today.day < birth_date.day):
            age -= 1
        return age

    @staticmethod
    def calculate_days_remaining(deadline: datetime) -> int:
        """
        Calculate days remaining until deadline.
        
        Args:
            deadline: Deadline datetime
            
        Returns:
            Days remaining (negative if overdue)
        """
        if not deadline:
            return 0
        delta = deadline - datetime.utcnow()
        return delta.days
