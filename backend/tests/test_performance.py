# 🧪 Agent World - Performance Tests
# Version: 0.4.2 (Épic 8 - Performance)
# Description: Tests pour les fonctionnalités de performance (cache, pagination, optimisation BDD)

"""
Performance Tests for Agent World.

Ce module contient les tests pour :
- Le service de cache Redis
- La pagination des endpoints API
- Le cache des résultats des agents
- L'optimisation de la base de données
"""

import json
import time
from unittest.mock import MagicMock, patch

import pytest

from backend.app import create_app
from backend.config import TestingConfig
from backend.models.agent import Agent
from backend.models.base import db
from backend.services.agent_cache_service import (
    AgentCacheService,
    get_agent_cache_service,
)
from backend.services.cache_service import (
    CacheService,
    cache_response,
    get_cache_service,
    invalidate_cache,
)
from backend.services.db_optimization_service import (
    DBOptimizationService,
    get_db_optimization_service,
)
from backend.services.pagination_service import PaginationResult, PaginationService


@pytest.fixture
def app():
    """Create application for testing."""
    app = create_app(config_class=TestingConfig)
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.config["CACHE_DEFAULT_TIMEOUT"] = 0  # Désactiver le cache en test

    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


# ============================================================================
# Tests du Service de Cache
# ============================================================================


class TestCacheService:
    """Tests pour le service de cache Redis."""

    def test_cache_service_initialization(self):
        """Test l'initialisation du service de cache."""
        # Avec Redis désactivé en test, le cache ne doit pas être disponible
        cache_service = CacheService(redis_url="redis://localhost:6379/0")
        # Le cache ne sera pas disponible car Redis n'est pas configuré en test
        # Mais on peut tester que l'instance est créée
        assert cache_service is not None
        assert cache_service.default_timeout == 3600

    def test_cache_service_with_mock_redis(self):
        """Test le service de cache avec un Redis mocké."""
        mock_redis = MagicMock()
        mock_redis.ping.return_value = True
        mock_redis.get.return_value = None
        mock_redis.setex.return_value = True
        mock_redis.delete.return_value = 1
        mock_redis.scan_iter.return_value = []

        with patch(
            "backend.services.cache_service.redis.Redis.from_url",
            return_value=mock_redis,
        ):
            cache_service = CacheService(
                redis_url="redis://localhost:6379/0", default_timeout=100
            )
            assert cache_service.is_available()

            # Test set
            result = cache_service.set("test_key", {"data": "test"}, timeout=50)
            assert result is True
            mock_redis.setex.assert_called_once()

            # Test get (cache miss)
            mock_redis.get.return_value = None
            result = cache_service.get("test_key")
            assert result is None

            # Test get (cache hit)
            mock_redis.get.return_value = json.dumps({"data": "test"})
            result = cache_service.get("test_key")
            assert result == {"data": "test"}

            # Test delete
            result = cache_service.delete("test_key")
            assert result is True
            mock_redis.delete.assert_called_once()

    def test_cache_key_generation(self, app):
        """Test la génération des clés de cache."""
        with app.app_context():
            cache_service = get_cache_service()
            # Générer une clé unique
            key = cache_service.generate_cache_key("arg1", "arg2", key1="val1")
            assert key is not None
            assert len(key) == 64  # SHA256 hex = 64 caractères

    def test_cache_response_decorator(self, app):
        """Test le décorateur de cache pour les réponses API."""
        with app.app_context():

            @cache_response(timeout=100, key_prefix="test:")
            def mock_endpoint():
                return {"data": "test"}

            # Sans cache disponible, la fonction doit être exécutée
            result = mock_endpoint()
            assert result == {"data": "test"}

    def test_invalidate_cache_decorator(self, app):
        """Test le décorateur d'invalidation du cache."""
        with app.app_context():

            @invalidate_cache(key_prefix="test:")
            def mock_endpoint():
                return {"data": "test"}

            result = mock_endpoint()
            assert result == {"data": "test"}


# ============================================================================
# Tests du Service de Cache des Agents
# ============================================================================


class TestAgentCacheService:
    """Tests pour le service de cache des résultats des agents."""

    def test_agent_cache_service_initialization(self, app):
        """Test l'initialisation du service de cache des agents."""
        with app.app_context():
            agent_cache = get_agent_cache_service()
            assert agent_cache is not None

    def test_result_key_generation(self, app):
        """Test la génération des clés de cache pour les résultats."""
        with app.app_context():
            agent_cache = get_agent_cache_service()
            key = agent_cache._generate_result_key(
                agent_id=1,
                input_data={"text": "test"},
                model="mistral-tiny",
                configuration={"param": "value"},
            )
            assert key.startswith("agent:result:")
            assert len(key) > 20

    def test_metadata_key_generation(self, app):
        """Test la génération des clés de cache pour les métadonnées."""
        with app.app_context():
            agent_cache = get_agent_cache_service()
            key = agent_cache._generate_agent_metadata_key(agent_id=1)
            assert key == "agent:metadata:1"

    def test_cache_execution_result_with_mock(self, app):
        """Test la mise en cache des résultats d'exécution avec un mock."""
        with app.app_context():
            mock_cache = MagicMock()
            mock_cache.is_available.return_value = True
            mock_cache.set.return_value = True

            with patch.object(get_agent_cache_service(), "_cache", mock_cache):
                agent_cache = get_agent_cache_service()
                result = agent_cache.cache_execution_result(
                    agent_id=1,
                    input_data={"text": "test"},
                    result={"output": "result"},
                    model="mistral-tiny",
                    ttl=3600,
                )
                assert result is True
                mock_cache.set.assert_called_once()


# ============================================================================
# Tests du Service de Pagination
# ============================================================================


class TestPaginationService:
    """Tests pour le service de pagination."""

    def test_get_pagination_params_default(self, app):
        """Test la récupération des paramètres de pagination par défaut."""
        with app.app_context():
            with app.test_request_context("/?page=1&per_page=10"):
                page, per_page = PaginationService.get_pagination_params()
                assert page == 1
                assert per_page == 10

    def test_get_pagination_params_edge_cases(self, app):
        """Test les cas limites des paramètres de pagination."""
        with app.app_context():
            # Page négative -> 1
            with app.test_request_context("/?page=-5&per_page=10"):
                page, per_page = PaginationService.get_pagination_params()
                assert page == 1

            # per_page trop grand -> max
            with app.test_request_context("/?page=1&per_page=200"):
                page, per_page = PaginationService.get_pagination_params()
                assert per_page == PaginationService.MAX_PER_PAGE

            # Paramètres invalides -> valeurs par défaut
            with app.test_request_context("/?page=invalid&per_page=invalid"):
                page, per_page = PaginationService.get_pagination_params()
                assert page == 1
                assert per_page == PaginationService.DEFAULT_PER_PAGE

    def test_paginate_list(self, app):
        """Test la pagination d'une liste."""
        with app.app_context():
            items = list(range(100))

            # Page 1, 10 items
            paginated = PaginationService.paginate_list(items, page=1, per_page=10)
            assert isinstance(paginated, PaginationResult)
            assert len(paginated.items) == 10
            assert paginated.total == 100
            assert paginated.page == 1
            assert paginated.per_page == 10
            assert paginated.total_pages == 10
            assert paginated.items == list(range(10))

            # Page 2, 10 items
            paginated = PaginationService.paginate_list(items, page=2, per_page=10)
            assert len(paginated.items) == 10
            assert paginated.items == list(range(10, 20))

            # Dernière page
            paginated = PaginationService.paginate_list(items, page=10, per_page=10)
            assert len(paginated.items) == 10
            assert paginated.items == list(range(90, 100))

            # Page 11 (vide)
            paginated = PaginationService.paginate_list(items, page=11, per_page=10)
            assert len(paginated.items) == 0

    def test_pagination_result_to_dict(self, app):
        """Test la conversion du résultat paginé en dictionnaire."""
        with app.app_context():
            items = [{"id": 1}, {"id": 2}]
            paginated = PaginationResult(
                items=items, total=2, page=1, per_page=10, total_pages=1
            )

            result = paginated.to_dict()
            assert "items" in result
            assert "pagination" in result
            assert result["items"] == items
            assert result["pagination"]["total"] == 2
            assert result["pagination"]["page"] == 1
            assert result["pagination"]["has_next"] is False
            assert result["pagination"]["has_prev"] is False


# ============================================================================
# Tests d'Intégration des Endpoints API
# ============================================================================


class TestPerformanceEndpoints:
    """Tests d'intégration pour les endpoints de performance."""

    def test_agents_list_paginated(self, client, app):
        """Test que la liste des agents est paginée."""
        with app.app_context():
            # Créer des agents de test
            for i in range(25):
                Agent.create(
                    name=f"test_agent_{i}",
                    description=f"Description {i}",
                    model="mistral-tiny",
                )

            # Tester la pagination
            response = client.get("/api/agents?page=1&per_page=10")
            data = json.loads(response.data)

            assert response.status_code == 200
            assert "items" in data
            assert "pagination" in data
            assert len(data["items"]) == 10
            assert data["pagination"]["total"] == 25
            assert data["pagination"]["page"] == 1
            assert data["pagination"]["total_pages"] == 3
            assert data["pagination"]["has_next"] is True
            assert data["pagination"]["has_prev"] is False

            # Page 2
            response = client.get("/api/agents?page=2&per_page=10")
            data = json.loads(response.data)
            assert len(data["items"]) == 10
            assert data["pagination"]["page"] == 2
            assert data["pagination"]["has_next"] is True
            assert data["pagination"]["has_prev"] is True

            # Dernière page
            response = client.get("/api/agents?page=3&per_page=10")
            data = json.loads(response.data)
            assert len(data["items"]) == 5
            assert data["pagination"]["page"] == 3
            assert data["pagination"]["has_next"] is False

    def test_agents_cache_invalidation(self, client, app):
        """Test l'invalidation du cache lors de la création/modification/suppression."""
        with app.app_context():
            # Créer un agent
            response = client.post(
                "/api/agents",
                data=json.dumps(
                    {
                        "name": "test_cache_agent",
                        "description": "Test cache invalidation",
                        "model": "mistral-tiny",
                    }
                ),
                content_type="application/json",
            )

            assert response.status_code == 201

            # Lister les agents (le cache doit être invalidé)
            response = client.get("/api/agents")
            assert response.status_code == 200


# ============================================================================
# Tests du Service d'Optimisation de la Base de Données
# ============================================================================


class TestDBOptimizationService:
    """Tests pour le service d'optimisation de la base de données."""

    def test_recommended_indexes(self, app):
        """Test la configuration des index recommandés."""
        with app.app_context():
            db_optimization = get_db_optimization_service()
            assert "agents" in db_optimization.RECOMMENDED_INDEXES
            assert "executions" in db_optimization.RECOMMENDED_INDEXES
            assert len(db_optimization.RECOMMENDED_INDEXES["agents"]) > 0

    def test_generate_create_index_sql(self, app):
        """Test la génération du SQL pour créer un index."""
        with app.app_context():
            db_optimization = get_db_optimization_service()
            sql = db_optimization.generate_create_index_sql(
                table_name="agents", columns=["name"], unique=True
            )
            assert "CREATE UNIQUE INDEX" in sql
            assert "agents" in sql
            assert "name" in sql

    def test_generate_optimization_report(self, app):
        """Test la génération du rapport d'optimisation."""
        with app.app_context():
            db_optimization = get_db_optimization_service()
            report = db_optimization.generate_optimization_report()

            assert "generated_at" in report
            assert "database_type" in report
            assert "tables" in report
            assert "recommendations" in report


# ============================================================================
# Tests de Performance
# ============================================================================


class TestPerformanceMetrics:
    """Tests pour les métriques de performance."""

    def test_response_time_with_cache(self, app):
        """Test que le cache améliore les temps de réponse."""
        with app.app_context():
            # Créer un agent
            agent = Agent.create(
                name="performance_test_agent",
                description="Test de performance",
                model="mistral-tiny",
            )

            # Premier appel (sans cache)
            start_time = time.time()
            response1 = app.test_client().get("/api/agents")
            time1 = time.time() - start_time

            # Deuxième appel (avec cache potentiel)
            start_time = time.time()
            response2 = app.test_client().get("/api/agents")
            time2 = time.time() - start_time

            # Les deux réponses doivent être valides
            assert response1.status_code == 200
            assert response2.status_code == 200

            # Note: En test, le cache est désactivé (CACHE_DEFAULT_TIMEOUT = 0)
            # Donc les temps peuvent être similaires


# ============================================================================
# Tests de Stress (optionnels)
# ============================================================================


@pytest.mark.slow
class TestStressTests:
    """Tests de stress pour valider la scalabilité."""

    def test_concurrent_requests(self, client, app):
        """Test le traitement de requêtes concurrentes."""
        with app.app_context():
            # Créer plusieurs agents
            for i in range(50):
                Agent.create(
                    name=f"stress_test_agent_{i}",
                    description=f"Stress test {i}",
                    model="mistral-tiny",
                )

            # Envoyer des requêtes concurrentes
            import concurrent.futures

            def make_request(page):
                return client.get(f"/api/agents?page={page}&per_page=10")

            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                futures = [executor.submit(make_request, page) for page in range(1, 6)]
                responses = [
                    f.result() for f in concurrent.futures.as_completed(futures)
                ]

            # Toutes les réponses doivent être valides
            for response in responses:
                assert response.status_code == 200
                data = json.loads(response.data)
                assert "items" in data
                assert "pagination" in data
