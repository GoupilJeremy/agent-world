# 🚀 Agent World - Cache Service
# Version: 0.4.2 (Épic 8 - Performance)
# Description: Service de cache Redis pour l'optimisation des performances

"""
Cache Service for Agent World API.

Ce module fournit une couche d'abstraction pour le cache Redis,
permetant de mettre en cache les réponses API et les résultats des agents.
"""

import hashlib
import json
import logging
from functools import wraps
from typing import Any, Callable, Optional, Union

import redis
from flask import current_app, request

logger = logging.getLogger(__name__)


class CacheService:
    """Service de gestion du cache Redis."""

    def __init__(self, redis_url: Optional[str] = None, default_timeout: int = 3600):
        """
        Initialise le service de cache.

        Args:
            redis_url: URL de connexion Redis (ex: redis://localhost:6379/0)
            default_timeout: Durée de vie par défaut en secondes
        """
        self.redis_url = redis_url or "redis://localhost:6379/0"
        self.default_timeout = default_timeout or 3600
        self._client: Optional[redis.Redis] = None

    @property
    def client(self) -> redis.Redis:
        """Retourne le client Redis (lazy initialization)."""
        if self._client is None:
            try:
                # Essayer d'obtenir la configuration depuis Flask si disponible
                try:
                    from flask import current_app
                    redis_url = current_app.config.get("REDIS_URL", self.redis_url)
                    default_timeout = current_app.config.get("CACHE_DEFAULT_TIMEOUT", self.default_timeout)
                    self.redis_url = redis_url
                    self.default_timeout = default_timeout
                except RuntimeError:
                    # En dehors du contexte Flask, utiliser les valeurs par défaut
                    pass
                
                self._client = redis.Redis.from_url(self.redis_url, decode_responses=True)
                # Test de connexion
                self._client.ping()
                logger.info(f"Redis cache connected to {self.redis_url}")
            except redis.ConnectionError as e:
                logger.warning(f"Redis connection failed: {e}. Cache will be disabled.")
                self._client = None
        return self._client

    def is_available(self) -> bool:
        """Vérifie si le cache Redis est disponible."""
        return self._client is not None

    def get(self, key: str) -> Optional[Any]:
        """
        Récupère une valeur du cache.

        Args:
            key: Clé du cache

        Returns:
            Valeur stockée ou None si non trouvée
        """
        if not self.is_available():
            return None

        try:
            value = self.client.get(key)
            if value is None:
                return None
            return json.loads(value)
        except (redis.RedisError, json.JSONDecodeError) as e:
            logger.error(f"❌ Cache get error for key {key}: {e}")
            return None

    def set(self, key: str, value: Any, timeout: Optional[int] = None) -> bool:
        """
        Stocke une valeur dans le cache.

        Args:
            key: Clé du cache
            value: Valeur à stocker (sérialisable en JSON)
            timeout: Durée de vie en secondes (None = default_timeout)

        Returns:
            True si succès, False sinon
        """
        if not self.is_available():
            return False

        try:
            timeout = timeout or self.default_timeout
            value_str = json.dumps(value)
            self.client.setex(key, timeout, value_str)
            logger.debug(f"📦 Cache set: {key} (TTL: {timeout}s)")
            return True
        except (redis.RedisError, TypeError) as e:
            logger.error(f"❌ Cache set error for key {key}: {e}")
            return False

    def delete(self, key: str) -> bool:
        """
        Supprime une clé du cache.

        Args:
            key: Clé à supprimer

        Returns:
            True si supprimé, False sinon
        """
        if not self.is_available():
            return False

        try:
            result = self.client.delete(key)
            if result > 0:
                logger.debug(f"🗑️ Cache deleted: {key}")
            return result > 0
        except redis.RedisError as e:
            logger.error(f"❌ Cache delete error for key {key}: {e}")
            return False

    def clear(self, pattern: str = "*") -> int:
        """
        Supprime toutes les clés correspondant à un motif.

        Args:
            pattern: Motif de correspondance (ex: "agent:*")

        Returns:
            Nombre de clés supprimées
        """
        if not self.is_available():
            return 0

        try:
            count = 0
            for key in self.client.scan_iter(pattern):
                self.client.delete(key)
                count += 1
            logger.debug(f"🧹 Cache cleared: {count} keys matching '{pattern}'")
            return count
        except redis.RedisError as e:
            logger.error(f"❌ Cache clear error for pattern {pattern}: {e}")
            return 0

    def generate_cache_key(self, *args, **kwargs) -> str:
        """
        Génère une clé de cache unique basée sur les arguments.

        Args:
            *args: Arguments positionnels
            **kwargs: Arguments nommés

        Returns:
            Clé de cache unique (hash SHA256)
        """
        # Inclure le chemin de la requête et les paramètres
        path = request.path if request else ""
        query_string = request.query_string.decode() if request else ""
        
        # Combiner tous les éléments
        key_parts = [path, query_string]
        key_parts.extend(str(arg) for arg in args)
        key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
        
        key_data = "|".join(key_parts)
        return hashlib.sha256(key_data.encode()).hexdigest()


# Instance globale du service de cache
_cache_service: Optional[CacheService] = None


def get_cache_service() -> CacheService:
    """Retourne l'instance globale du service de cache."""
    global _cache_service
    if _cache_service is None:
        _cache_service = CacheService()
    return _cache_service


def cache_response(timeout: Optional[int] = None, key_prefix: str = "api:"):
    """
    Décorateur pour mettre en cache les réponses des endpoints API.

    Args:
        timeout: Durée de vie du cache en secondes
        key_prefix: Préfixe pour la clé de cache

    Usage:
        @cache_response(timeout=300, key_prefix="agents:")
        def get_agents():
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache_service = get_cache_service()
            
            if not cache_service.is_available():
                logger.debug("⚠️ Cache disabled, executing function directly")
                return func(*args, **kwargs)

            # Générer une clé de cache unique
            cache_key = f"{key_prefix}{cache_service.generate_cache_key(*args, **kwargs)}"
            
            # Essayer de récupérer du cache
            cached_result = cache_service.get(cache_key)
            if cached_result is not None:
                logger.debug(f"✅ Cache hit for {cache_key}")
                return cached_result

            # Exécuter la fonction si non en cache
            logger.debug(f"🔄 Cache miss for {cache_key}, executing function")
            result = func(*args, **kwargs)

            # Stocker dans le cache
            cache_service.set(cache_key, result, timeout)
            
            return result
        
        return wrapper
    return decorator


def invalidate_cache(key_prefix: str = "api:"):
    """
    Décorateur pour invalider le cache après une modification.

    Args:
        key_prefix: Préfixe pour les clés de cache à invalider

    Usage:
        @invalidate_cache(key_prefix="agents:")
        def create_agent():
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            
            cache_service = get_cache_service()
            if cache_service.is_available():
                pattern = f"{key_prefix}*"
                count = cache_service.clear(pattern)
                logger.debug(f"🔄 Invalidated {count} cache entries for pattern '{pattern}'")
            
            return result
        
        return wrapper
    return decorator


# Configuration pour Flask
class CacheConfig:
    """Configuration du cache pour Flask."""
    
    @staticmethod
    def init_app(app):
        """Initialise le service de cache pour une application Flask."""
        global _cache_service
        _cache_service = CacheService(
            redis_url=app.config.get("REDIS_URL"),
            default_timeout=app.config.get("CACHE_DEFAULT_TIMEOUT", 3600)
        )
        
        # Ajouter un endpoint pour vider le cache (admin)
        @app.route("/api/cache/clear", methods=["POST"])
        def clear_cache():
            """Endpoint pour vider le cache (admin only)."""
            from flask import jsonify
            from ..services.auth_service import get_current_user
            
            # Vérifier l'authentification et les permissions
            # (À implémenter dans Épic 10 - Sécurité)
            cache_service = get_cache_service()
            if cache_service.is_available():
                count = cache_service.clear()
                return jsonify({"status": "success", "cleared_keys": count}), 200
            else:
                return jsonify({"status": "error", "message": "Cache not available"}), 503
        
        app.extensions["cache_service"] = _cache_service
