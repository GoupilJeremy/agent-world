# ⚙️ Agent World Services
# Description: Services métier et logique applicative

"""Services package for Agent World."""

from .agent_cache_service import AgentCacheService, get_agent_cache_service
from .agent_service import AgentService
from .ai_service import AIService
from .auth_service import AuthService
from .cache_service import CacheService, get_cache_service
from .db_optimization_service import DBOptimizationService, get_db_optimization_service
from .file_service import FileService
from .history_service import HistoryFilter, HistoryService
from .notification_service import (
    NotificationChannel,
    NotificationConfig,
    NotificationService,
    UserNotificationPreferences,
    notification_service,
)
from .pagination_service import PaginationResult, PaginationService
from .model_registry import ModelInfo, ModelRegistry, get_model_registry
from .model_selector import ModelSelector, SelectionStrategy
from .fallback_handler import FallbackHandler, FallbackResult
from .quota_service import QuotaService, QuotaExceededError, QuotaStatus
from .benchmark_service import BenchmarkService

__all__ = [
    "AgentCacheService",
    "AgentService",
    "AIService",
    "AuthService",
    "CacheService",
    "DBOptimizationService",
    "FileService",
    "HistoryService",
    "HistoryFilter",
    "NotificationService",
    "NotificationChannel",
    "NotificationConfig",
    "UserNotificationPreferences",
    "notification_service",
    "get_cache_service",
    "get_agent_cache_service",
    "get_db_optimization_service",
    "PaginationService",
    "PaginationResult",
    "ModelInfo",
    "ModelRegistry",
    "get_model_registry",
    "ModelSelector",
    "SelectionStrategy",
    "FallbackHandler",
    "FallbackResult",
    "QuotaService",
    "QuotaExceededError",
    "QuotaStatus",
    "BenchmarkService",
]
