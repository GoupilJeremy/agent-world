"""
Prometheus Service for Agent World

Ce service configure et expose les métriques Prometheus pour le monitoring
des performances de l'application.

US-059: Monitoring des performances
Épic 8: Performance et Scalabilité
"""

from functools import wraps
from time import time

from flask import current_app, request
from prometheus_client import (
    Counter,
    Gauge,
    Histogram,
    generate_latest,
    REGISTRY,
    CollectorRegistry,
    multiprocess,
)


# Créer un registre personnalisé pour isoler les métriques
PROMETHEUS_REGISTRY = CollectorRegistry()

# Configuration du multiprocess mode pour Gunicorn/UWSGI
# Cela permet de partager les métriques entre les workers
if multiprocess.MultiprocessMode.needs_prometheus:
    multiprocess.MultiprocessMode.use_prometheus(PROMETHEUS_REGISTRY)


class PrometheusService:
    """
    Service Prometheus pour l'exposition des métriques.
    
    Ce service expose plusieurs types de métriques :
    - Counter: Compteurs d'événements (requêtes, erreurs)
    - Gauge: Valeurs variables (nombre de requêtes en cours)
    - Histogram: Distribution de valeurs (latence, taille des réponses)
    """
    
    def __init__(self, app=None):
        """
        Initialise le service Prometheus.
        
        Args:
            app: Application Flask (optionnel)
        """
        self.app = app
        self._enabled = True
        self._init_metrics()
        
        if app is not None:
            self.init_app(app)
    
    def _init_metrics(self):
        """Initialise toutes les métriques Prometheus."""
        
        # ========================================================================
        # Métriques HTTP (Flask)
        # ========================================================================
        
        # Compteur de requêtes HTTP
        self.http_requests_total = Counter(
            "flask_http_request_total",
            "Total number of HTTP requests",
            ["method", "endpoint", "status", "http_version"],
            registry=PROMETHEUS_REGISTRY,
        )
        
        # Compteur d'erreurs HTTP
        self.http_errors_total = Counter(
            "flask_http_errors_total",
            "Total number of HTTP errors",
            ["method", "endpoint", "status"],
            registry=PROMETHEUS_REGISTRY,
        )
        
        # Histogram de la durée des requêtes
        self.http_request_duration_seconds = Histogram(
            "flask_http_request_duration_seconds",
            "HTTP request duration in seconds",
            ["method", "endpoint", "status"],
            buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1, 2.5, 5, 7.5, 10],
            registry=PROMETHEUS_REGISTRY,
        )
        
        # Histogram de la taille des requêtes
        self.http_request_size_bytes = Histogram(
            "flask_http_request_size_bytes",
            "HTTP request size in bytes",
            ["method", "endpoint"],
            buckets=[100, 1000, 10000, 100000, 1000000, 10000000],
            registry=PROMETHEUS_REGISTRY,
        )
        
        # Histogram de la taille des réponses
        self.http_response_size_bytes = Histogram(
            "flask_http_response_size_bytes",
            "HTTP response size in bytes",
            ["method", "endpoint", "status"],
            buckets=[100, 1000, 10000, 100000, 1000000, 10000000],
            registry=PROMETHEUS_REGISTRY,
        )
        
        # Gauge du nombre de requêtes en cours
        self.http_requests_in_progress = Gauge(
            "flask_http_requests_in_progress",
            "Number of HTTP requests currently in progress",
            ["method", "endpoint"],
            registry=PROMETHEUS_REGISTRY,
        )
        
        # ========================================================================
        # Métriques Business (Agent World)
        # ========================================================================
        
        # Compteur de création d'agents
        self.agents_created_total = Counter(
            "agent_world_agents_created_total",
            "Total number of agents created",
            ["agent_type", "model"],
            registry=PROMETHEUS_REGISTRY,
        )
        
        # Compteur de suppression d'agents
        self.agents_deleted_total = Counter(
            "agent_world_agents_deleted_total",
            "Total number of agents deleted",
            registry=PROMETHEUS_REGISTRY,
        )
        
        # Compteur d'exécutions d'agents
        self.agents_executed_total = Counter(
            "agent_world_agents_executed_total",
            "Total number of agent executions",
            ["agent_id", "status"],
            registry=PROMETHEUS_REGISTRY,
        )
        
        # Histogram de la durée d'exécution des agents
        self.agents_execution_duration_seconds = Histogram(
            "agent_world_agents_execution_duration_seconds",
            "Agent execution duration in seconds",
            ["agent_id"],
            buckets=[0.1, 0.5, 1, 5, 10, 30, 60, 120, 300, 600],
            registry=PROMETHEUS_REGISTRY,
        )
        
        # Compteur de fichiers générés
        self.files_generated_total = Counter(
            "agent_world_files_generated_total",
            "Total number of files generated",
            ["file_type", "agent_id"],
            registry=PROMETHEUS_REGISTRY,
        )
        
        # Gauge de la taille totale des fichiers générés
        self.files_total_size_bytes = Gauge(
            "agent_world_files_total_size_bytes",
            "Total size of generated files in bytes",
            registry=PROMETHEUS_REGISTRY,
        )
        
        # ========================================================================
        # Métriques Système
        # ========================================================================
        
        # Gauge de l'utilisation CPU
        self.system_cpu_usage = Gauge(
            "agent_world_system_cpu_usage",
            "System CPU usage percentage",
            registry=PROMETHEUS_REGISTRY,
        )
        
        # Gauge de l'utilisation mémoire
        self.system_memory_usage = Gauge(
            "agent_world_system_memory_usage",
            "System memory usage in bytes",
            registry=PROMETHEUS_REGISTRY,
        )
        
        # Gauge du nombre de connexions à la base de données
        self.db_connections = Gauge(
            "agent_world_db_connections",
            "Number of active database connections",
            registry=PROMETHEUS_REGISTRY,
        )
        
        # Compteur d'erreurs de base de données
        self.db_errors_total = Counter(
            "agent_world_db_errors_total",
            "Total number of database errors",
            ["operation", "error_type"],
            registry=PROMETHEUS_REGISTRY,
        )
        
        # ========================================================================
        # Métriques Cache
        # ========================================================================
        
        # Compteur de hits/misses du cache
        self.cache_hits_total = Counter(
            "agent_world_cache_hits_total",
            "Total number of cache hits",
            ["cache_type", "key"],
            registry=PROMETHEUS_REGISTRY,
        )
        
        self.cache_misses_total = Counter(
            "agent_world_cache_misses_total",
            "Total number of cache misses",
            ["cache_type", "key"],
            registry=PROMETHEUS_REGISTRY,
        )
        
        # Gauge de la taille du cache
        self.cache_size_bytes = Gauge(
            "agent_world_cache_size_bytes",
            "Total size of cache in bytes",
            ["cache_type"],
            registry=PROMETHEUS_REGISTRY,
        )
    
    def init_app(self, app):
        """
        Initialise le service avec une application Flask.
        
        Args:
            app: Application Flask
        """
        self.app = app
        
        # Enregistrer le middleware pour tracker les requêtes
        self._register_middleware(app)
        
        # Ajouter l'endpoint /metrics
        self._register_metrics_endpoint(app)
        
        # Stocker le service dans les extensions
        app.extensions["prometheus_service"] = self
    
    def _register_middleware(self, app):
        """Enregistre le middleware pour tracker les requêtes HTTP."""
        
        @app.before_request
        def before_request():
            """Track request start."""
            if not self._enabled:
                return
            
            method = request.method
            endpoint = request.path
            
            # Incrémenter le gauge des requêtes en cours
            self.http_requests_in_progress.labels(method=method, endpoint=endpoint).inc()
            
            # Enregistrer le temps de départ
            request.start_time = time()
            
            # Track la taille de la requête
            if request.content_length:
                self.http_request_size_bytes.labels(
                    method=method,
                    endpoint=endpoint
                ).observe(request.content_length)
        
        @app.after_request
        def after_request(response):
            """Track request completion."""
            if not self._enabled:
                return response
            
            method = request.method
            endpoint = request.path
            status = str(response.status_code)
            http_version = request.environ.get("SERVER_PROTOCOL", "HTTP/1.1")
            
            # Calculer la durée
            duration = time() - request.start_time
            
            # Décrémenter le gauge des requêtes en cours
            self.http_requests_in_progress.labels(method=method, endpoint=endpoint).dec()
            
            # Incrémenter les compteurs
            self.http_requests_total.labels(
                method=method,
                endpoint=endpoint,
                status=status,
                http_version=http_version
            ).inc()
            
            # Track les erreurs
            if response.status_code >= 400:
                self.http_errors_total.labels(
                    method=method,
                    endpoint=endpoint,
                    status=status
                ).inc()
            
            # Track la durée
            self.http_request_duration_seconds.labels(
                method=method,
                endpoint=endpoint,
                status=status
            ).observe(duration)
            
            # Track la taille de la réponse
            response_size = len(response.get_data())
            self.http_response_size_bytes.labels(
                method=method,
                endpoint=endpoint,
                status=status
            ).observe(response_size)
            
            return response
        
        # Gérer les exceptions
        @app.errorhandler(Exception)
        def handle_exception(e):
            """Track exceptions."""
            if not self._enabled:
                return e
            
            method = request.method
            endpoint = request.path
            status = "500"
            
            # Décrémenter le gauge
            self.http_requests_in_progress.labels(method=method, endpoint=endpoint).dec()
            
            # Incrémenter les compteurs d'erreurs
            self.http_requests_total.labels(
                method=method,
                endpoint=endpoint,
                status=status,
                http_version=request.environ.get("SERVER_PROTOCOL", "HTTP/1.1")
            ).inc()
            
            self.http_errors_total.labels(
                method=method,
                endpoint=endpoint,
                status=status
            ).inc()
            
            raise e
    
    def _register_metrics_endpoint(self, app):
        """Ajoute l'endpoint /metrics pour exposer les métriques."""
        
        @app.route("/metrics")
        def metrics():
            """
            Endpoint pour exposer les métriques Prometheus.
            
            Cette route retourne toutes les métriques enregistrées
            dans le registre Prometheus au format texte.
            """
            if not self._enabled:
                return "Prometheus metrics disabled", 404
            
            return generate_latest(PROMETHEUS_REGISTRY), 200, {"Content-Type": "text/plain; charset=utf-8"}
    
    @property
    def enabled(self):
        """Retourne si le service Prometheus est activé."""
        return self._enabled
    
    @enabled.setter
    def enabled(self, value):
        """Active ou désactive le service Prometheus."""
        self._enabled = bool(value)
    
    def track_agent_creation(self, agent_type: str = "unknown", model: str = "unknown"):
        """Track la création d'un agent."""
        self.agents_created_total.labels(agent_type=agent_type, model=model).inc()
    
    def track_agent_deletion(self):
        """Track la suppression d'un agent."""
        self.agents_deleted_total.inc()
    
    def track_agent_execution(self, agent_id: str, status: str = "success", duration: float = None):
        """Track l'exécution d'un agent."""
        self.agents_executed_total.labels(agent_id=agent_id, status=status).inc()
        
        if duration is not None:
            self.agents_execution_duration_seconds.labels(agent_id=agent_id).observe(duration)
    
    def track_file_generation(self, file_type: str, agent_id: str = "unknown", size_bytes: int = 0):
        """Track la génération d'un fichier."""
        self.files_generated_total.labels(file_type=file_type, agent_id=agent_id).inc()
        
        if size_bytes > 0:
            self.files_total_size_bytes.inc(size_bytes)
    
    def track_db_error(self, operation: str, error_type: str):
        """Track une erreur de base de données."""
        self.db_errors_total.labels(operation=operation, error_type=error_type).inc()
    
    def track_cache_hit(self, cache_type: str, key: str):
        """Track un hit de cache."""
        self.cache_hits_total.labels(cache_type=cache_type, key=key).inc()
    
    def track_cache_miss(self, cache_type: str, key: str):
        """Track un miss de cache."""
        self.cache_misses_total.labels(cache_type=cache_type, key=key).inc()
    
    def set_cache_size(self, cache_type: str, size_bytes: int):
        """Met à jour la taille du cache."""
        self.cache_size_bytes.labels(cache_type=cache_type).set(size_bytes)
    
    def get_metrics(self):
        """Retourne toutes les métriques au format texte."""
        return generate_latest(PROMETHEUS_REGISTRY)


def get_prometheus_service():
    """
    Retourne l'instance du service Prometheus.
    
    Returns:
        PrometheusService: Instance du service Prometheus
    """
    return current_app.extensions.get("prometheus_service")
