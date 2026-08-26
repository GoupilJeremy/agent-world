# 🧪 Agent World - GDPR Service Tests
# Version: 1.0.0 (EPIC 10 - US-069)
# Description: Tests unitaires pour le service GDPRService

"""
Unit tests for GDPRService.

Ces tests couvrent:
- Gestion des consentements
- Traitement des demandes d'accès et de suppression
- Export des données personnelles
- Gestion des politiques de confidentialité
- Vérification de la conformité
"""

import json
from datetime import datetime, timedelta

import unittest
from unittest.mock import MagicMock, patch

from backend.app import create_app
from backend.models.base import db
from backend.models.gdpr_compliance import (
    ConsentStatus,
    ConsentType,
    DataSubjectRequest,
    GDPRConsent,
    PersonalDataLog,
    PrivacyPolicyVersion,
    RequestStatus,
    RequestType,
)
from backend.models.user import User
from backend.services.gdpr_service import (
    GDPRAccessDeniedError,
    GDPRConsentError,
    GDPRError,
    GDPRNotFoundError,
    GDPRRequestError,
    GDPRService,
)


class TestGDPRServiceConsent(unittest.TestCase):
    """Test cases for consent management."""

    def setUp(self):
        """Set up test fixtures."""
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
        self.app.config["AUTO_CREATE_DB"] = True

        self.client = self.app.test_client()

        with self.app.app_context():
            db.create_all()
            self.gdpr_service = GDPRService()

            # Create a test user with date of birth
            self.user = User(
                email="test@example.com",
                username="testuser",
                password="testpassword123",
                date_of_birth=datetime(2000, 1, 1),  # 26 years old in 2026
            )
            db.session.add(self.user)
            db.session.commit()

    def tearDown(self):
        """Clean up test fixtures."""
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_grant_consent(self):
        """Test granting consent."""
        with self.app.app_context():
            consent = self.gdpr_service.grant_consent(
                user_id=self.user.id,
                consent_type=ConsentType.MARKETING,
                version="v1.0",
                ip_address="192.168.1.1",
                user_agent="Test Agent",
            )

            self.assertIsNotNone(consent)
            self.assertEqual(consent.user_id, self.user.id)
            self.assertEqual(consent.consent_type, "marketing")
            self.assertEqual(consent.status, "granted")
            self.assertEqual(consent.consent_version, "v1.0")

    def test_grant_consent_with_string_type(self):
        """Test granting consent with string type."""
        with self.app.app_context():
            consent = self.gdpr_service.grant_consent(
                user_id=self.user.id,
                consent_type="analytics",
            )

            self.assertIsNotNone(consent)
            self.assertEqual(consent.consent_type, "analytics")

    def test_grant_consent_invalid_user(self):
        """Test granting consent for non-existent user raises error."""
        with self.app.app_context():
            with self.assertRaises(GDPRNotFoundError):
                self.gdpr_service.grant_consent(
                    user_id=99999,
                    consent_type=ConsentType.MARKETING,
                )

    def test_grant_consent_underage_user(self):
        """Test granting consent for underage user raises error."""
        with self.app.app_context():
            # Create underage user (15 years old)
            underage_user = User(
                email="underage@example.com",
                username="underageuser",
                password="testpassword123",
                date_of_birth=datetime(2011, 1, 1),  # 15 years old in 2026
            )
            db.session.add(underage_user)
            db.session.commit()

            with self.assertRaises(GDPRConsentError):
                self.gdpr_service.grant_consent(
                    user_id=underage_user.id,
                    consent_type=ConsentType.MARKETING,
                )

    def test_revoke_consent(self):
        """Test revoking consent."""
        with self.app.app_context():
            # First grant consent
            consent = self.gdpr_service.grant_consent(
                user_id=self.user.id,
                consent_type=ConsentType.MARKETING,
            )

            # Then revoke it
            revoked = self.gdpr_service.revoke_consent(
                user_id=self.user.id,
                consent_type=ConsentType.MARKETING,
            )

            self.assertEqual(revoked.status, "revoked")
            self.assertEqual(revoked.id, consent.id)

    def test_revoke_consent_not_found(self):
        """Test revoking non-existent consent raises error."""
        with self.app.app_context():
            with self.assertRaises(GDPRNotFoundError):
                self.gdpr_service.revoke_consent(
                    user_id=self.user.id,
                    consent_type=ConsentType.MARKETING,
                )

    def test_revoke_consent_already_revoked(self):
        """Test revoking already revoked consent raises error."""
        with self.app.app_context():
            # Grant and revoke consent
            self.gdpr_service.grant_consent(
                user_id=self.user.id,
                consent_type=ConsentType.MARKETING,
            )
            self.gdpr_service.revoke_consent(
                user_id=self.user.id,
                consent_type=ConsentType.MARKETING,
            )

            # Try to revoke again
            with self.assertRaises(GDPRConsentError):
                self.gdpr_service.revoke_consent(
                    user_id=self.user.id,
                    consent_type=ConsentType.MARKETING,
                )

    def test_get_consent(self):
        """Test getting consent."""
        with self.app.app_context():
            self.gdpr_service.grant_consent(
                user_id=self.user.id,
                consent_type=ConsentType.MARKETING,
            )

            consent = self.gdpr_service.get_consent(self.user.id, ConsentType.MARKETING)

            self.assertIsNotNone(consent)
            self.assertEqual(consent.consent_type, "marketing")

    def test_get_consent_not_found(self):
        """Test getting non-existent consent returns None."""
        with self.app.app_context():
            consent = self.gdpr_service.get_consent(self.user.id, ConsentType.MARKETING)
            self.assertIsNone(consent)

    def test_has_consent(self):
        """Test checking if user has consent."""
        with self.app.app_context():
            # Initially no consent
            self.assertFalse(self.gdpr_service.has_consent(self.user.id, ConsentType.MARKETING))

            # Grant consent
            self.gdpr_service.grant_consent(
                user_id=self.user.id,
                consent_type=ConsentType.MARKETING,
            )

            # Now should have consent
            self.assertTrue(self.gdpr_service.has_consent(self.user.id, ConsentType.MARKETING))

    def test_get_all_consents(self):
        """Test getting all consents for a user."""
        with self.app.app_context():
            self.gdpr_service.grant_consent(
                user_id=self.user.id,
                consent_type=ConsentType.MARKETING,
            )
            self.gdpr_service.grant_consent(
                user_id=self.user.id,
                consent_type=ConsentType.ANALYTICS,
            )

            consents = self.gdpr_service.get_all_consents(self.user.id)

            self.assertEqual(len(consents), 2)

    def test_check_required_consents(self):
        """Test checking required consents."""
        with self.app.app_context():
            self.gdpr_service.grant_consent(
                user_id=self.user.id,
                consent_type=ConsentType.MARKETING,
                is_required=True,
            )

            consents = self.gdpr_service.check_required_consents(self.user.id)

            self.assertIn("marketing", consents)
            self.assertTrue(consents["marketing"]["has_consent"])
            self.assertTrue(consents["marketing"]["is_required"])


class TestGDPRServiceRequests(unittest.TestCase):
    """Test cases for data subject requests."""

    def setUp(self):
        """Set up test fixtures."""
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
        self.app.config["AUTO_CREATE_DB"] = True

        self.client = self.app.test_client()

        with self.app.app_context():
            db.create_all()
            self.gdpr_service = GDPRService()

            # Create a test user
            self.user = User(
                email="test@example.com",
                username="testuser",
                password="testpassword123",
            )
            db.session.add(self.user)
            db.session.commit()

    def tearDown(self):
        """Clean up test fixtures."""
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_create_request(self):
        """Test creating a data subject request."""
        with self.app.app_context():
            dsr = self.gdpr_service.create_request(
                user_id=self.user.id,
                request_type=RequestType.ACCESS,
                description="Request to access my data",
            )

            self.assertIsNotNone(dsr)
            self.assertEqual(dsr.user_id, self.user.id)
            self.assertEqual(dsr.request_type, "access")
            self.assertEqual(dsr.status, "pending")
            self.assertIsNotNone(dsr.request_id)
            self.assertIsNotNone(dsr.deadline)

    def test_create_request_invalid_type(self):
        """Test creating request with invalid type raises error."""
        with self.app.app_context():
            with self.assertRaises(GDPRRequestError):
                self.gdpr_service.create_request(
                    user_id=self.user.id,
                    request_type="invalid_type",
                )

    def test_create_request_invalid_user(self):
        """Test creating request for non-existent user raises error."""
        with self.app.app_context():
            with self.assertRaises(GDPRNotFoundError):
                self.gdpr_service.create_request(
                    user_id=99999,
                    request_type=RequestType.ACCESS,
                )

    def test_get_request_by_id(self):
        """Test getting request by database ID."""
        with self.app.app_context():
            dsr = self.gdpr_service.create_request(
                user_id=self.user.id,
                request_type=RequestType.ACCESS,
            )

            fetched = self.gdpr_service.get_request(dsr.id)
            self.assertEqual(fetched.id, dsr.id)

    def test_get_request_by_request_id(self):
        """Test getting request by request_id."""
        with self.app.app_context():
            dsr = self.gdpr_service.create_request(
                user_id=self.user.id,
                request_type=RequestType.ACCESS,
            )

            fetched = self.gdpr_service.get_request(dsr.request_id)
            self.assertEqual(fetched.id, dsr.id)

    def test_get_request_not_found(self):
        """Test getting non-existent request raises error."""
        with self.app.app_context():
            with self.assertRaises(GDPRNotFoundError):
                self.gdpr_service.get_request("INVALID")

    def test_get_user_requests(self):
        """Test getting all requests for a user."""
        with self.app.app_context():
            self.gdpr_service.create_request(
                user_id=self.user.id,
                request_type=RequestType.ACCESS,
            )
            self.gdpr_service.create_request(
                user_id=self.user.id,
                request_type=RequestType.ERASURE,
            )

            requests = self.gdpr_service.get_user_requests(self.user.id)

            self.assertEqual(len(requests), 2)

    def test_get_pending_requests(self):
        """Test getting pending requests."""
        with self.app.app_context():
            self.gdpr_service.create_request(
                user_id=self.user.id,
                request_type=RequestType.ACCESS,
            )

            pending = self.gdpr_service.get_pending_requests()

            self.assertEqual(len(pending), 1)
            self.assertEqual(pending[0].status, "pending")

    def test_update_request_status(self):
        """Test updating request status."""
        with self.app.app_context():
            dsr = self.gdpr_service.create_request(
                user_id=self.user.id,
                request_type=RequestType.ACCESS,
            )

            updated = self.gdpr_service.update_request_status(
                request_id=dsr.id,
                status="processing",
                processed_by=self.user.id,
            )

            self.assertEqual(updated.status, "processing")
            self.assertEqual(updated.processed_by, self.user.id)

    def test_process_access_request(self):
        """Test processing an access request."""
        with self.app.app_context():
            dsr = self.gdpr_service.create_request(
                user_id=self.user.id,
                request_type=RequestType.ACCESS,
            )

            # Create an admin user
            admin = User(
                email="admin@example.com",
                username="admin",
                password="adminpassword123",
            )
            db.session.add(admin)
            db.session.commit()

            processed = self.gdpr_service.process_access_request(
                request_id=dsr.id,
                processed_by=admin.id,
            )

            self.assertEqual(processed.status, "completed")
            self.assertIsNotNone(processed.response_data)

    def test_process_erasure_request(self):
        """Test processing an erasure request."""
        with self.app.app_context():
            dsr = self.gdpr_service.create_request(
                user_id=self.user.id,
                request_type=RequestType.ERASURE,
            )

            # Create an admin user
            admin = User(
                email="admin@example.com",
                username="admin",
                password="adminpassword123",
            )
            db.session.add(admin)
            db.session.commit()

            processed = self.gdpr_service.process_erasure_request(
                request_id=dsr.id,
                processed_by=admin.id,
                hard_delete=False,
            )

            self.assertEqual(processed.status, "completed")


class TestGDPRServiceDataCollection(unittest.TestCase):
    """Test cases for data collection."""

    def setUp(self):
        """Set up test fixtures."""
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
        self.app.config["AUTO_CREATE_DB"] = True

        self.client = self.app.test_client()

        with self.app.app_context():
            db.create_all()
            self.gdpr_service = GDPRService()

            # Create a test user
            self.user = User(
                email="test@example.com",
                username="testuser",
                password="testpassword123",
            )
            db.session.add(self.user)
            db.session.commit()

    def tearDown(self):
        """Clean up test fixtures."""
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_collect_user_data(self):
        """Test collecting user data."""
        with self.app.app_context():
            data = self.gdpr_service.collect_user_data(self.user.id)

            self.assertIn("export_date", data)
            self.assertIn("user_id", data)
            self.assertEqual(data["user_id"], self.user.id)
            self.assertIn("data", data)
            self.assertIn("user", data["data"])

    def test_delete_user_data(self):
        """Test deleting user data."""
        with self.app.app_context():
            # Create some consents to delete
            self.gdpr_service.grant_consent(
                user_id=self.user.id,
                consent_type=ConsentType.MARKETING,
            )

            deleted_count = self.gdpr_service.delete_user_data(
                user_id=self.user.id,
                data_scope="consents",
            )

            self.assertGreater(deleted_count, 0)


class TestGDPRServicePolicy(unittest.TestCase):
    """Test cases for privacy policy management."""

    def setUp(self):
        """Set up test fixtures."""
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
        self.app.config["AUTO_CREATE_DB"] = True

        self.client = self.app.test_client()

        with self.app.app_context():
            db.create_all()
            self.gdpr_service = GDPRService()

            # Create a test user
            self.user = User(
                email="test@example.com",
                username="testuser",
                password="testpassword123",
            )
            db.session.add(self.user)
            db.session.commit()

    def tearDown(self):
        """Clean up test fixtures."""
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_create_policy_version(self):
        """Test creating a privacy policy version."""
        with self.app.app_context():
            policy = self.gdpr_service.create_policy_version(
                version="v1.0",
                content="# Privacy Policy\n\nThis is our privacy policy.",
                title="Privacy Policy v1.0",
                published_by=self.user.id,
            )

            self.assertIsNotNone(policy)
            self.assertEqual(policy.version, "v1.0")
            self.assertEqual(policy.title, "Privacy Policy v1.0")
            self.assertIn("Privacy Policy", policy.content)

    def test_create_policy_version_duplicate(self):
        """Test creating duplicate policy version raises error."""
        with self.app.app_context():
            self.gdpr_service.create_policy_version(
                version="v1.0",
                content="# Privacy Policy",
            )

            with self.assertRaises(GDPRError):
                self.gdpr_service.create_policy_version(
                    version="v1.0",
                    content="# Another Policy",
                )

    def test_get_active_policy(self):
        """Test getting active policy."""
        with self.app.app_context():
            # Initially no active policy
            self.assertIsNone(self.gdpr_service.get_active_policy())

            # Create and activate a policy
            policy = self.gdpr_service.create_policy_version(
                version="v1.0",
                content="# Privacy Policy",
            )
            self.gdpr_service.set_active_policy(policy.id)

            active = self.gdpr_service.get_active_policy()
            self.assertEqual(active.id, policy.id)

    def test_get_policy_version(self):
        """Test getting a specific policy version."""
        with self.app.app_context():
            self.gdpr_service.create_policy_version(
                version="v1.0",
                content="# Privacy Policy",
            )

            policy = self.gdpr_service.get_policy_version("v1.0")
            self.assertEqual(policy.version, "v1.0")

    def test_get_policy_version_not_found(self):
        """Test getting non-existent policy version raises error."""
        with self.app.app_context():
            with self.assertRaises(GDPRNotFoundError):
                self.gdpr_service.get_policy_version("v99.0")

    def test_set_active_policy(self):
        """Test setting active policy."""
        with self.app.app_context():
            policy1 = self.gdpr_service.create_policy_version(
                version="v1.0",
                content="# Policy 1",
            )
            policy2 = self.gdpr_service.create_policy_version(
                version="v2.0",
                content="# Policy 2",
            )

            # Set policy2 as active
            active = self.gdpr_service.set_active_policy(policy2.id)
            self.assertEqual(active.id, policy2.id)

            # policy1 should no longer be active
            policy1_updated = PrivacyPolicyVersion.query.get(policy1.id)
            self.assertFalse(policy1_updated.is_active)

    def test_get_all_policies(self):
        """Test getting all policies."""
        with self.app.app_context():
            self.gdpr_service.create_policy_version(
                version="v1.0",
                content="# Policy 1",
            )
            self.gdpr_service.create_policy_version(
                version="v2.0",
                content="# Policy 2",
            )

            policies = self.gdpr_service.get_all_policies()
            self.assertEqual(len(policies), 2)


class TestGDPRServiceCompliance(unittest.TestCase):
    """Test cases for compliance checking."""

    def setUp(self):
        """Set up test fixtures."""
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
        self.app.config["AUTO_CREATE_DB"] = True

        self.client = self.app.test_client()

        with self.app.app_context():
            db.create_all()
            self.gdpr_service = GDPRService()

            # Create a test user
            self.user = User(
                email="test@example.com",
                username="testuser",
                password="testpassword123",
                date_of_birth=datetime(2000, 1, 1),  # 26 years old
            )
            db.session.add(self.user)
            db.session.commit()

    def tearDown(self):
        """Clean up test fixtures."""
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_check_user_compliance(self):
        """Test checking user compliance."""
        with self.app.app_context():
            compliance = self.gdpr_service.check_user_compliance(self.user.id)

            self.assertIn("user_id", compliance)
            self.assertIn("age", compliance)
            self.assertIn("is_adult", compliance)
            self.assertIn("required_consents_granted", compliance)
            self.assertIn("policy_consent_ok", compliance)
            self.assertIn("compliant", compliance)

    def test_get_compliance_stats(self):
        """Test getting compliance statistics."""
        with self.app.app_context():
            # Create some consents and requests
            self.gdpr_service.grant_consent(
                user_id=self.user.id,
                consent_type=ConsentType.MARKETING,
            )
            self.gdpr_service.create_request(
                user_id=self.user.id,
                request_type=RequestType.ACCESS,
            )

            stats = self.gdpr_service.get_compliance_stats()

            self.assertIn("total_users", stats)
            self.assertIn("consent_counts", stats)
            self.assertIn("request_stats", stats)
            self.assertIn("pending_requests", stats)


class TestGDPRServiceHelpers(unittest.TestCase):
    """Test cases for helper methods."""

    def setUp(self):
        """Set up test fixtures."""
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
        self.app.config["AUTO_CREATE_DB"] = True

        with self.app.app_context():
            db.create_all()
            self.gdpr_service = GDPRService()

    def tearDown(self):
        """Clean up test fixtures."""
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_calculate_age(self):
        """Test age calculation."""
        # Test with known date
        birth_date = datetime(2000, 1, 1)
        age = self.gdpr_service.calculate_age(birth_date)
        
        # In 2026, should be 26 (if birthday has passed) or 25 (if not)
        self.assertIn(age, [25, 26])

    def test_calculate_days_remaining(self):
        """Test days remaining calculation."""
        deadline = datetime.utcnow() + timedelta(days=10)
        days = self.gdpr_service.calculate_days_remaining(deadline)
        
        # Should be approximately 10 (could vary by a day)
        self.assertAlmostEqual(days, 10, delta=1)

    def test_calculate_days_remaining_overdue(self):
        """Test days remaining for overdue deadline."""
        deadline = datetime.utcnow() - timedelta(days=5)
        days = self.gdpr_service.calculate_days_remaining(deadline)
        
        self.assertAlmostEqual(days, -5, delta=1)


class TestGDPRModels(unittest.TestCase):
    """Test cases for GDPR models."""

    def setUp(self):
        """Set up test fixtures."""
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
        self.app.config["AUTO_CREATE_DB"] = True

        with self.app.app_context():
            db.create_all()

            # Create a test user
            self.user = User(
                email="test@example.com",
                username="testuser",
                password="testpassword123",
            )
            db.session.add(self.user)
            db.session.commit()

    def tearDown(self):
        """Clean up test fixtures."""
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_consent_type_enum(self):
        """Test ConsentType enum."""
        self.assertEqual(ConsentType.MARKETING.value, "marketing")
        self.assertEqual(ConsentType.ANALYTICS.value, "analytics")
        self.assertEqual(ConsentType.COOKIES.value, "cookies")

    def test_request_type_enum(self):
        """Test RequestType enum."""
        self.assertEqual(RequestType.ACCESS.value, "access")
        self.assertEqual(RequestType.ERASURE.value, "erasure")
        self.assertEqual(RequestType.PORTABILITY.value, "portability")

    def test_gdpr_consent_to_dict(self):
        """Test GDPRConsent to_dict method."""
        with self.app.app_context():
            consent = GDPRConsent(
                user_id=self.user.id,
                consent_type="marketing",
                status="granted",
            )
            db.session.add(consent)
            db.session.commit()

            consent_dict = consent.to_dict()
            self.assertIn("id", consent_dict)
            self.assertEqual(consent_dict["consent_type"], "marketing")

    def test_data_subject_request_to_dict(self):
        """Test DataSubjectRequest to_dict method."""
        with self.app.app_context():
            dsr = DataSubjectRequest(
                user_id=self.user.id,
                request_type="access",
            )
            db.session.add(dsr)
            db.session.commit()

            dsr_dict = dsr.to_dict()
            self.assertIn("id", dsr_dict)
            self.assertEqual(dsr_dict["request_type"], "access")

    def test_privacy_policy_to_dict(self):
        """Test PrivacyPolicyVersion to_dict method."""
        with self.app.app_context():
            policy = PrivacyPolicyVersion(
                version="v1.0",
                content="# Privacy Policy",
            )
            db.session.add(policy)
            db.session.commit()

            policy_dict = policy.to_dict()
            self.assertIn("id", policy_dict)
            self.assertEqual(policy_dict["version"], "v1.0")


class TestGDPRErrors(unittest.TestCase):
    """Test cases for GDPR error classes."""

    def test_gdpr_error_base(self):
        """Test GDPRError base exception."""
        error = GDPRError("Test error")
        self.assertEqual(error.status_code, 400)
        self.assertEqual(error.error_code, "gdpr_error")

    def test_consent_error(self):
        """Test GDPRConsentError exception."""
        error = GDPRConsentError("Consent error")
        self.assertEqual(error.status_code, 400)
        self.assertEqual(error.error_code, "gdpr_consent_error")

    def test_request_error(self):
        """Test GDPRRequestError exception."""
        error = GDPRRequestError("Request error")
        self.assertEqual(error.status_code, 400)
        self.assertEqual(error.error_code, "gdpr_request_error")

    def test_not_found_error(self):
        """Test GDPRNotFoundError exception."""
        error = GDPRNotFoundError("Not found")
        self.assertEqual(error.status_code, 404)
        self.assertEqual(error.error_code, "gdpr_not_found")

    def test_access_denied_error(self):
        """Test GDPRAccessDeniedError exception."""
        error = GDPRAccessDeniedError("Access denied")
        self.assertEqual(error.status_code, 403)
        self.assertEqual(error.error_code, "gdpr_access_denied")


if __name__ == "__main__":
    unittest.main()
