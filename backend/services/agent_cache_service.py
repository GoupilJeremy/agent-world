# 🤖 Agent World - Agent Result Cache Service
# Version: 0.4.2 (Épic 8 - Performance)
# Description: Service de cache des résultats des agents avec invalidation intelligente

"""
Agent Result Cache Service for Agent World API.

Ce module fournit un cache spécialisé pour les résultats des exécutions d'agents,
avec une stratégie d'invalidation basée sur :
- TTL (Time To Live) configurable par type de résultat
- Invalidation manuelle lors de la modification d'un agent
- Invalidation automatique lors de la modification de la configuration d'un agent
- Stockage des métadonnées d'exécution pour le monitoring
"""

import hashlib
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from .cache_service import get_cache_service

logger = logging.getLogger(__name__)


class AgentCacheService:
    """Service de cache dédié aux résultats des agents."""

    # Durées de vie par défaut pour différents types de cache
    DEFAULT_TTL_SECONDS = {
        "execution_result": 3600,  # 1 heure pour les résultats d'exécution
        "agent_metadata": 86400,  # 24 heures pour les métadonnées des agents
        "template_result": 7200,  # 2 heures pour les résultats de templates
    }

    def __init__(self):
        """Initialise le service de cache des agents."""
        self._cache = get_cache_service()

    def _generate_result_key(
        self,
        agent_id: int,
        input_data: Any,
        model: Optional[str] = None,
        configuration: Optional[Dict] = None,
    ) -> str:
        """
        Génère une clé de cache unique pour un résultat d'exécution d'agent.

        Args:
            agent_id: ID de l'agent
            input_data: Données d'entrée de l'exécution
            model: Modèle utilisé (optionnel)
            configuration: Configuration utilisée (optionnelle)

        Returns:
            Clé de cache unique
        """
        # Normaliser les données d'entrée
        if isinstance(input_data, dict):
            input_str = json.dumps(input_data, sort_keys=True)
        else:
            input_str = str(input_data)

        config_str = json.dumps(configuration, sort_keys=True) if configuration else ""
        model_str = model or ""

        key_data = f"{agent_id}|{input_str}|{model_str}|{config_str}"
        return f"agent:result:{hashlib.sha256(key_data.encode()).hexdigest()}"

    def _generate_agent_metadata_key(self, agent_id: int) -> str:
        """Génère une clé de cache pour les métadonnées d'un agent."""
        return f"agent:metadata:{agent_id}"

    def cache_execution_result(
        self,
        agent_id: int,
        input_data: Any,
        result: Any,
        model: Optional[str] = None,
        configuration: Optional[Dict] = None,
        ttl: Optional[int] = None,
    ) -> bool:
        """
        Met en cache le résultat d'une exécution d'agent.

        Args:
            agent_id: ID de l'agent
            input_data: Données d'entrée de l'exécution
            result: Résultat à mettre en cache
            model: Modèle utilisé
            configuration: Configuration utilisée
            ttl: Durée de vie en secondes (None = utiliser le TTL par défaut)

        Returns:
            True si le cache a réussi, False sinon
        """
        if not self._cache.is_available():
            logger.debug("⚠️ Agent cache disabled")
            return False

        key = self._generate_result_key(agent_id, input_data, model, configuration)
        ttl = ttl or self.DEFAULT_TTL_SECONDS["execution_result"]

        # Ajouter des métadonnées au résultat
        cached_data = {
            "result": result,
            "cached_at": datetime.utcnow().isoformat(),
            "agent_id": agent_id,
            "input_hash": hashlib.sha256(str(input_data).encode()).hexdigest(),
            "model": model,
            "configuration": configuration,
        }

        success = self._cache.set(key, cached_data, timeout=ttl)
        if success:
            logger.debug(f"📦 Cached agent {agent_id} execution result (TTL: {ttl}s)")
        else:
            logger.warning(f"❌ Failed to cache agent {agent_id} execution result")

        return success

    def get_execution_result(
        self,
        agent_id: int,
        input_data: Any,
        model: Optional[str] = None,
        configuration: Optional[Dict] = None,
    ) -> Optional[Any]:
        """
        Récupère un résultat d'exécution depuis le cache.

        Args:
            agent_id: ID de l'agent
            input_data: Données d'entrée de l'exécution
            model: Modèle utilisé
            configuration: Configuration utilisée

        Returns:
            Résultat en cache ou None si non trouvé
        """
        if not self._cache.is_available():
            return None

        key = self._generate_result_key(agent_id, input_data, model, configuration)
        cached_data = self._cache.get(key)

        if cached_data is None:
            logger.debug(f"🔄 Cache miss for agent {agent_id} execution")
            return None

        logger.debug(f"✅ Cache hit for agent {agent_id} execution")
        return cached_data.get("result")

    def cache_agent_metadata(
        self, agent_id: int, metadata: Dict, ttl: Optional[int] = None
    ) -> bool:
        """
        Met en cache les métadonnées d'un agent.

        Args:
            agent_id: ID de l'agent
            metadata: Métadonnées à mettre en cache
            ttl: Durée de vie en secondes

        Returns:
            True si succès, False sinon
        """
        if not self._cache.is_available():
            return False

        key = self._generate_agent_metadata_key(agent_id)
        ttl = ttl or self.DEFAULT_TTL_SECONDS["agent_metadata"]

        cached_data = {
            "metadata": metadata,
            "cached_at": datetime.utcnow().isoformat(),
            "agent_id": agent_id,
        }

        success = self._cache.set(key, cached_data, timeout=ttl)
        if success:
            logger.debug(f"📦 Cached agent {agent_id} metadata (TTL: {ttl}s)")

        return success

    def get_agent_metadata(self, agent_id: int) -> Optional[Dict]:
        """
        Récupère les métadonnées d'un agent depuis le cache.

        Args:
            agent_id: ID de l'agent

        Returns:
            Métadonnées en cache ou None
        """
        if not self._cache.is_available():
            return None

        key = self._generate_agent_metadata_key(agent_id)
        cached_data = self._cache.get(key)

        if cached_data is None:
            return None

        return cached_data.get("metadata")

    def invalidate_agent_cache(self, agent_id: int) -> int:
        """
        Invalide tout le cache lié à un agent.

        Args:
            agent_id: ID de l'agent

        Returns:
            Nombre de clés invalidées
        """
        if not self._cache.is_available():
            return 0

        # Invalider les résultats d'exécution
        pattern_result = f"agent:result:*"
        # Invalider les métadonnées
        pattern_metadata = f"agent:metadata:{agent_id}"

        count = 0

        # Invalider les résultats
        for key in self._cache.client.scan_iter(pattern_result):
            key_str = key.decode() if isinstance(key, bytes) else key
            if f"agent:result:" in key_str:
                # Vérifier si la clé correspond à cet agent
                # (Les clés de résultat contiennent le hash de l'input, pas l'agent_id directement)
                # On invalide tout pour simplifier
                self._cache.client.delete(key)
                count += 1

        # Invalider les métadonnées
        self._cache.client.delete(pattern_metadata)
        count += 1

        logger.debug(f"🧹 Invalidated {count} cache entries for agent {agent_id}")
        return count

    def invalidate_all_results(self) -> int:
        """
        Invalide tous les résultats d'exécution en cache.

        Returns:
            Nombre de clés invalidées
        """
        if not self._cache.is_available():
            return 0

        pattern = "agent:result:*"
        count = self._cache.clear(pattern)
        logger.debug(f"🧹 Invalidated {count} agent result cache entries")
        return count

    def invalidate_all_metadata(self) -> int:
        """
        Invalide toutes les métadonnées d'agents en cache.

        Returns:
            Nombre de clés invalidées
        """
        if not self._cache.is_available():
            return 0

        pattern = "agent:metadata:*"
        count = self._cache.clear(pattern)
        logger.debug(f"🧹 Invalidated {count} agent metadata cache entries")
        return count

    def clear_all_agent_cache(self) -> int:
        """
        Invalide tout le cache lié aux agents.

        Returns:
            Nombre total de clés invalidées
        """
        count_results = self.invalidate_all_results()
        count_metadata = self.invalidate_all_metadata()
        total = count_results + count_metadata
        logger.info(f"🧹 Cleared all agent cache: {total} entries")
        return total

    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Récupère les statistiques du cache des agents.

        Returns:
            Dictionnaire avec les statistiques
        """
        if not self._cache.is_available():
            return {"available": False, "error": "Cache not available"}

        try:
            client = self._cache.client
            info = client.info()

            # Compter les clés liées aux agents
            result_keys = len(list(client.scan_iter("agent:result:*")))
            metadata_keys = len(list(client.scan_iter("agent:metadata:*")))

            return {
                "available": True,
                "agent_result_keys": result_keys,
                "agent_metadata_keys": metadata_keys,
                "total_agent_keys": result_keys + metadata_keys,
                "redis_info": {
                    "used_memory": info.get("used_memory_human", "N/A"),
                    "connected_clients": info.get("connected_clients", 0),
                    "uptime": info.get("uptime_in_seconds", 0),
                },
            }
        except Exception as e:
            logger.error(f"❌ Error getting cache stats: {e}")
            return {"available": False, "error": str(e)}


# Instance globale du service
_agent_cache_service: Optional[AgentCacheService] = None


def get_agent_cache_service() -> AgentCacheService:
    """Retourne l'instance globale du service de cache des agents."""
    global _agent_cache_service
    if _agent_cache_service is None:
        _agent_cache_service = AgentCacheService()
    return _agent_cache_service
