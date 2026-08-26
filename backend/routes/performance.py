# ⚡ Agent World - Performance Routes
# Version: 0.4.2 (Épic 8 - Performance)
# Description: Endpoints pour le monitoring et l'optimisation des performances

"""
Performance Routes for Agent World API.

Ce module contient les endpoints pour :
- Monitorer les performances de l'API
- Gérer le cache
- Optimiser la base de données
- Obtenir des rapports d'optimisation
"""

from flask import Blueprint, current_app, jsonify, request
from flask_restful import Resource

from ..services.agent_cache_service import get_agent_cache_service
from ..services.cache_service import get_cache_service
from ..services.db_optimization_service import get_db_optimization_service

# Créer un blueprint pour les routes de performance
performance_bp = Blueprint("performance", __name__, url_prefix="/api/performance")


class CacheStatsResource(Resource):
    """Resource for cache statistics."""

    def get(self):
        """
        Get cache statistics.

        ---
        responses:
          200:
            description: Cache statistics
            content:
              application/json:
                schema:
                  type: object
                  properties:
                    available:
                      type: boolean
                    redis_info:
                      type: object
                    agent_cache_stats:
                      type: object
        """
        cache_service = get_cache_service()
        agent_cache = get_agent_cache_service()

        stats = {
            "available": cache_service.is_available(),
            "agent_cache": agent_cache.get_cache_stats(),
        }

        if cache_service.is_available():
            try:
                client = cache_service.client
                info = client.info()
                stats["redis_info"] = {
                    "used_memory": info.get("used_memory_human", "N/A"),
                    "connected_clients": info.get("connected_clients", 0),
                    "uptime_seconds": info.get("uptime_in_seconds", 0),
                    "commands_processed": info.get("total_commands_processed", 0),
                    "keys": {
                        "total": (
                            info.get("db0", {}).get("keys", {}).get("total", 0)
                            if isinstance(info.get("db0"), dict)
                            else 0
                        ),
                        "expires": (
                            info.get("db0", {}).get("keys", {}).get("expires", 0)
                            if isinstance(info.get("db0"), dict)
                            else 0
                        ),
                    },
                }
            except Exception as e:
                stats["redis_info"] = {"error": str(e)}

        return stats, 200


class CacheClearResource(Resource):
    """Resource for clearing cache."""

    def post(self):
        """
        Clear all cache entries.

        ---
        responses:
          200:
            description: Cache cleared successfully
            content:
              application/json:
                schema:
                  type: object
                  properties:
                    status:
                      type: string
                    cleared_keys:
                      type: integer
        """
        cache_service = get_cache_service()
        agent_cache = get_agent_cache_service()

        if not cache_service.is_available():
            return {"status": "error", "message": "Cache not available"}, 503

        # Clear all cache
        redis_cleared = cache_service.clear()
        agent_cleared = agent_cache.clear_all_agent_cache()

        return {
            "status": "success",
            "cleared_keys": redis_cleared + agent_cleared,
            "redis_keys": redis_cleared,
            "agent_keys": agent_cleared,
        }, 200


class DBOptimizationResource(Resource):
    """Resource for database optimization."""

    def get(self):
        """
        Get database optimization report.

        ---
        responses:
          200:
            description: Database optimization report
            content:
              application/json:
                schema:
                  type: object
        """
        db_optimization = get_db_optimization_service()
        report = db_optimization.generate_optimization_report()
        return report, 200


class DBOptimizationIndexResource(Resource):
    """Resource for creating missing database indexes."""

    def post(self):
        """
        Create all missing database indexes.

        ---
        parameters:
          - in: query
            name: table
            schema:
              type: string
            description: Table name to optimize (optional, defaults to all tables)
        responses:
          200:
            description: Indexes created successfully
            content:
              application/json:
                schema:
                  type: object
                  properties:
                    status:
                      type: string
                    created_indexes:
                      type: object
        """
        db_optimization = get_db_optimization_service()
        table_name = request.args.get("table", None)

        created_indexes = db_optimization.create_missing_indexes(table_name)

        return {
            "status": "success",
            "created_indexes": created_indexes,
        }, 200


class DBStatsResource(Resource):
    """Resource for database statistics."""

    def get(self, table_name: str = None):
        """
        Get statistics for a specific table.

        ---
        parameters:
          - in: path
            name: table_name
            schema:
              type: string
            required: true
            description: Table name
        responses:
          200:
            description: Table statistics
            content:
              application/json:
                schema:
                  type: object
        """
        db_optimization = get_db_optimization_service()

        if table_name:
            stats = db_optimization.get_table_statistics(table_name)
        else:
            # Retourner les stats pour toutes les tables
            stats = {}
            for table in db_optimization.RECOMMENDED_INDEXES.keys():
                try:
                    stats[table] = db_optimization.get_table_statistics(table)
                except Exception as e:
                    stats[table] = {"error": str(e)}

        return stats, 200


class DBVacuumResource(Resource):
    """Resource for running VACUUM ANALYZE."""

    def post(self):
        """
        Run VACUUM ANALYZE on the database.

        ---
        parameters:
          - in: query
            name: table
            schema:
              type: string
            description: Table name to vacuum (optional, defaults to all tables)
        responses:
          200:
            description: VACUUM ANALYZE completed
            content:
              application/json:
                schema:
                  type: object
                  properties:
                    status:
                      type: string
                    table:
                      type: string
        """
        db_optimization = get_db_optimization_service()
        table_name = request.args.get("table", None)

        success = db_optimization.run_vacuum_analyze(table_name)

        if success:
            return {
                "status": "success",
                "table": table_name or "all tables",
            }, 200
        else:
            return {
                "status": "error",
                "message": "VACUUM ANALYZE not supported or failed",
            }, 500


# Endpoints pour Flask (non-RESTful)
@performance_bp.route("/cache/stats")
def cache_stats():
    """Get cache statistics (legacy endpoint)."""
    return CacheStatsResource().get()


@performance_bp.route("/cache/clear", methods=["POST"])
def cache_clear():
    """Clear cache (legacy endpoint)."""
    return CacheClearResource().post()


@performance_bp.route("/db/optimize")
def db_optimize():
    """Get database optimization report (legacy endpoint)."""
    return DBOptimizationResource().get()


@performance_bp.route("/db/indexes", methods=["POST"])
def db_create_indexes():
    """Create missing database indexes (legacy endpoint)."""
    return DBOptimizationIndexResource().post()


@performance_bp.route("/db/stats")
@performance_bp.route("/db/stats/<table_name>")
def db_stats(table_name: str = None):
    """Get database statistics (legacy endpoint)."""
    return DBStatsResource().get(table_name)


@performance_bp.route("/db/vacuum", methods=["POST"])
def db_vacuum():
    """Run VACUUM ANALYZE (legacy endpoint)."""
    return DBVacuumResource().post()


# Fonction d'enregistrement des ressources
def register_performance_resources(api):
    """Register performance resources with the Flask-RESTful API."""
    api.add_resource(CacheStatsResource, "/performance/cache/stats")
    api.add_resource(CacheClearResource, "/performance/cache/clear")
    api.add_resource(DBOptimizationResource, "/performance/db/optimize")
    api.add_resource(DBOptimizationIndexResource, "/performance/db/indexes")
    api.add_resource(
        DBStatsResource,
        "/performance/db/stats",
        "/performance/db/stats/<string:table_name>",
    )
    api.add_resource(DBVacuumResource, "/performance/db/vacuum")


# Exporter le blueprint et la fonction d'enregistrement
__all__ = ["performance_bp", "register_performance_resources"]
