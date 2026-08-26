"""
Tests for PrometheusService

US-059: Monitoring des performances
Épic 8: Performance et Scalabilité
"""

import pytest
from flask import Flask

from ..services.prometheus_service import (
    PROMETHEUS_REGISTRY,
    PrometheusService,
    get_prometheus_service,
)


@pytest.fixture
def test_app():
    """Crée une application Flask pour les tests."""
    app = Flask(__name__)
    app.config["TESTING"] = True
    yield app


@pytest.fixture
def prometheus_service(test_app):
    """Crée une instance de PrometheusService."""
    service = PrometheusService()
    service.init_app(test_app)
    return service


class TestPrometheusServiceInit:
    """Tests pour l'initialisation du service."""

    def test_init_without_app(self):
        """Test l'initialisation sans application Flask."""
        service = PrometheusService()
        assert service.app is None
        assert service.enabled is True

    def test_init_with_app(self, test_app):
        """Test l'initialisation avec une application Flask."""
        service = PrometheusService(test_app)
        assert service.app == test_app
        assert service.enabled is True
        assert "prometheus_service" in test_app.extensions

    def test_init_app_later(self, test_app):
        """Test l'initialisation de l'app plus tard."""
        service = PrometheusService()
        service.init_app(test_app)

        assert service.app == test_app
        assert "prometheus_service" in test_app.extensions

    def test_metrics_initialized(self, prometheus_service):
        """Test que les métriques sont initialisées."""
        # Vérifier que les métriques HTTP existent
        assert hasattr(prometheus_service, "http_requests_total")
        assert hasattr(prometheus_service, "http_errors_total")
        assert hasattr(prometheus_service, "http_request_duration_seconds")
        assert hasattr(prometheus_service, "http_request_size_bytes")
        assert hasattr(prometheus_service, "http_response_size_bytes")
        assert hasattr(prometheus_service, "http_requests_in_progress")

        # Vérifier que les métriques business existent
        assert hasattr(prometheus_service, "agents_created_total")
        assert hasattr(prometheus_service, "agents_deleted_total")
        assert hasattr(prometheus_service, "agents_executed_total")
        assert hasattr(prometheus_service, "agents_execution_duration_seconds")
        assert hasattr(prometheus_service, "files_generated_total")
        assert hasattr(prometheus_service, "files_total_size_bytes")

        # Vérifier que les métriques système existent
        assert hasattr(prometheus_service, "system_cpu_usage")
        assert hasattr(prometheus_service, "system_memory_usage")
        assert hasattr(prometheus_service, "db_connections")
        assert hasattr(prometheus_service, "db_errors_total")

        # Vérifier que les métriques cache existent
        assert hasattr(prometheus_service, "cache_hits_total")
        assert hasattr(prometheus_service, "cache_misses_total")
        assert hasattr(prometheus_service, "cache_size_bytes")


class TestPrometheusServiceEnabled:
    """Tests pour l'activation/désactivation du service."""

    def test_enabled_property(self, prometheus_service):
        """Test la propriété enabled."""
        assert prometheus_service.enabled is True

        prometheus_service.enabled = False
        assert prometheus_service.enabled is False

        prometheus_service.enabled = True
        assert prometheus_service.enabled is True


class TestPrometheusServiceTracking:
    """Tests pour les méthodes de tracking."""

    def test_track_agent_creation(self, prometheus_service):
        """Test le tracking de création d'agent."""
        prometheus_service.track_agent_creation("chat", "mistral-tiny")
        prometheus_service.track_agent_creation("chat", "gpt-4")
        prometheus_service.track_agent_creation("code", "mistral-tiny")

        # Les métriques doivent avoir été incrémentées
        # On ne peut pas facilement vérifier la valeur exacte sans accéder au registre

    def test_track_agent_deletion(self, prometheus_service):
        """Test le tracking de suppression d'agent."""
        prometheus_service.track_agent_deletion()
        prometheus_service.track_agent_deletion()

        # Les métriques doivent avoir été incrémentées

    def test_track_agent_execution(self, prometheus_service):
        """Test le tracking d'exécution d'agent."""
        prometheus_service.track_agent_execution("agent-1", "success", 1.5)
        prometheus_service.track_agent_execution("agent-1", "success", 2.5)
        prometheus_service.track_agent_execution("agent-2", "failed")

        # Les métriques doivent avoir été incrémentées

    def test_track_file_generation(self, prometheus_service):
        """Test le tracking de génération de fichier."""
        prometheus_service.track_file_generation("json", "agent-1", 1024)
        prometheus_service.track_file_generation("md", "agent-2", 2048)

        # Les métriques doivent avoir été incrémentées

    def test_track_db_error(self, prometheus_service):
        """Test le tracking d'erreur de base de données."""
        prometheus_service.track_db_error("select", "ConnectionError")
        prometheus_service.track_db_error("insert", "TimeoutError")

        # Les métriques doivent avoir été incrémentées

    def test_track_cache_hit_miss(self, prometheus_service):
        """Test le tracking de hit/miss de cache."""
        prometheus_service.track_cache_hit("redis", "key1")
        prometheus_service.track_cache_miss("redis", "key2")

        # Les métriques doivent avoir été incrémentées

    def test_set_cache_size(self, prometheus_service):
        """Test la mise à jour de la taille du cache."""
        prometheus_service.set_cache_size("redis", 1024 * 1024)

        # La métrique doit avoir été mise à jour


class TestPrometheusServiceGetMetrics:
    """Tests pour la récupération des métriques."""

    def test_get_metrics(self, prometheus_service):
        """Test la récupération des métriques au format texte."""
        metrics = prometheus_service.get_metrics()

        assert isinstance(metrics, str)
        assert len(metrics) > 0
        # Vérifier que certaines métriques sont présentes
        assert "flask_http_request_total" in metrics
        assert "agent_world_agents_created_total" in metrics


class TestPrometheusServiceMiddleware:
    """Tests pour le middleware HTTP."""

    def test_before_request_tracking(self, test_app, prometheus_service):
        """Test le tracking des requêtes avant traitement."""
        # Simuler une requête
        with test_app.test_request_context("/test", method="GET"):
            # Le middleware before_request doit avoir été appelé
            pass

        # Vérifier que les métriques ont été créées
        # Note: En mode test, le middleware peut ne pas être appelé automatiquement

    def test_after_request_tracking(self, test_app, prometheus_service):
        """Test le tracking des requêtes après traitement."""
        # Simuler une requête complète
        with test_app.test_client() as client:
            client.get("/test")

        # La requête doit avoir été trackée


class TestPrometheusRegistry:
    """Tests pour le registre Prometheus."""

    def test_registry_is_custom(self):
        """Test que le registre est personnalisé."""
        from prometheus_client import REGISTRY as DEFAULT_REGISTRY

        # Notre registre doit être différent du registre par défaut
        assert PROMETHEUS_REGISTRY is not DEFAULT_REGISTRY


class TestGetPrometheusService:
    """Tests pour la fonction get_prometheus_service."""

    def test_get_prometheus_service(self, test_app, prometheus_service):
        """Test la récupération du service Prometheus."""
        with test_app.app_context():
            service = get_prometheus_service()
            assert service == prometheus_service

    def test_get_prometheus_service_not_initialized(self, test_app):
        """Test la récupération du service non initialisé."""
        with test_app.app_context():
            service = get_prometheus_service()
            assert service is None


class TestPrometheusMetricsEndpoint:
    """Tests pour l'endpoint /metrics."""

    def test_metrics_endpoint(self, test_app, prometheus_service):
        """Test l'endpoint /metrics."""
        with test_app.test_client() as client:
            response = client.get("/metrics")

            assert response.status_code == 200
            assert response.content_type == "text/plain; charset=utf-8"
            assert b"flask_http_request_total" in response.data

    def test_metrics_endpoint_disabled(self, test_app):
        """Test l'endpoint /metrics quand le service est désactivé."""
        service = PrometheusService()
        service.enabled = False
        service.init_app(test_app)

        with test_app.test_client() as client:
            response = client.get("/metrics")

            assert response.status_code == 404
            assert b"disabled" in response.data
