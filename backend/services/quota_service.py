# ⚙️ Agent World - Quota Service
# Version: 0.8.0 (Épic 11 - US-075)
# Description: Service de gestion des quotas et coûts

"""
Quota Service for Agent World.

Ce service gère les quotas d'utilisation par utilisateur et modèle :
vérification avant appel, consommation après appel, et reporting.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from ..models.base import db
from ..models.model_quota import ModelQuota, ModelUsageLog
from .model_registry import ModelRegistry, get_model_registry

logger = logging.getLogger(__name__)


class QuotaExceededError(Exception):
    """Raised when a user's quota is exceeded."""

    def __init__(self, user_id: int, model_id: str, reason: str):
        self.user_id = user_id
        self.model_id = model_id
        self.reason = reason
        super().__init__(
            f"Quota exceeded for user {user_id} on model {model_id}: {reason}"
        )


class QuotaStatus:
    """Status of a user's quota for a specific model."""

    def __init__(
        self,
        allowed: bool,
        tokens_remaining: Optional[int],
        cost_remaining: Optional[float],
        reason: Optional[str] = None,
    ):
        self.allowed = allowed
        self.tokens_remaining = tokens_remaining
        self.cost_remaining = cost_remaining
        self.reason = reason

    def to_dict(self) -> Dict[str, Any]:
        return {
            "allowed": self.allowed,
            "tokens_remaining": self.tokens_remaining,
            "cost_remaining": self.cost_remaining,
            "reason": self.reason,
        }


class UsageSummary:
    """Aggregated usage statistics for a period."""

    def __init__(
        self,
        user_id: int,
        period: str,
        total_tokens: int,
        total_cost: float,
        total_requests: int,
        by_model: Dict[str, Dict[str, Any]],
    ):
        self.user_id = user_id
        self.period = period
        self.total_tokens = total_tokens
        self.total_cost = total_cost
        self.total_requests = total_requests
        self.by_model = by_model

    def to_dict(self) -> Dict[str, Any]:
        return {
            "user_id": self.user_id,
            "period": self.period,
            "total_tokens": self.total_tokens,
            "total_cost": round(self.total_cost, 6),
            "total_requests": self.total_requests,
            "by_model": self.by_model,
        }


class QuotaService:
    """Manages usage quotas and cost tracking per user and model."""

    def __init__(self, registry: Optional[ModelRegistry] = None):
        self.registry = registry or get_model_registry()

    # ------------------------------------------------------------------
    # Quota checking
    # ------------------------------------------------------------------

    def check_quota(self, user_id: int, model_id: str) -> QuotaStatus:
        """Check if a user has remaining quota for a model.

        Args:
            user_id: ID of the user
            model_id: Model identifier

        Returns:
            QuotaStatus indicating whether the call is allowed
        """
        resolved = self.registry.resolve_alias(model_id)
        quota = ModelQuota.get_for_user_model(user_id, resolved)

        # No quota configured → unlimited
        if quota is None:
            return QuotaStatus(
                allowed=True,
                tokens_remaining=None,
                cost_remaining=None,
            )

        # Check period expiry — auto-reset if expired
        if not quota.is_period_active:
            quota.reset()

        if quota.is_tokens_exceeded:
            return QuotaStatus(
                allowed=False,
                tokens_remaining=0,
                cost_remaining=quota.cost_remaining,
                reason="Monthly token limit exceeded",
            )

        if quota.is_cost_exceeded:
            return QuotaStatus(
                allowed=False,
                tokens_remaining=quota.tokens_remaining,
                cost_remaining=0.0,
                reason="Monthly cost limit exceeded",
            )

        return QuotaStatus(
            allowed=True,
            tokens_remaining=quota.tokens_remaining,
            cost_remaining=quota.cost_remaining,
        )

    # ------------------------------------------------------------------
    # Quota consumption
    # ------------------------------------------------------------------

    def consume_quota(
        self,
        user_id: int,
        model_id: str,
        tokens_input: int,
        tokens_output: int,
        cost_usd: float,
        execution_id: Optional[int] = None,
        latency_ms: Optional[int] = None,
    ) -> None:
        """Record usage against a user's quota.

        Args:
            user_id: ID of the user
            model_id: Model identifier
            tokens_input: Number of input tokens used
            tokens_output: Number of output tokens used
            cost_usd: Cost in USD
            execution_id: Optional related execution ID
            latency_ms: Optional latency in milliseconds
        """
        resolved = self.registry.resolve_alias(model_id)
        total_tokens = tokens_input + tokens_output

        # Update quota if it exists
        quota = ModelQuota.get_for_user_model(user_id, resolved)
        if quota is not None:
            if not quota.is_period_active:
                quota.reset()
            quota.consume(total_tokens, cost_usd)

        # Always log usage
        ModelUsageLog.create(
            user_id=user_id,
            model_id=resolved,
            execution_id=execution_id,
            tokens_input=tokens_input,
            tokens_output=tokens_output,
            cost_usd=cost_usd,
            latency_ms=latency_ms,
        )

        logger.info(
            "Usage recorded: user=%d model=%s tokens=%d cost=$%.6f",
            user_id,
            resolved,
            total_tokens,
            cost_usd,
        )

    # ------------------------------------------------------------------
    # Quota management
    # ------------------------------------------------------------------

    def set_quota_limit(
        self,
        user_id: int,
        model_id: str,
        max_tokens_per_month: Optional[int] = None,
        max_cost_per_month: Optional[float] = None,
    ) -> ModelQuota:
        """Set or update quota limits for a user/model.

        Args:
            user_id: ID of the user
            model_id: Model identifier
            max_tokens_per_month: Token limit (None = unlimited)
            max_cost_per_month: Cost limit (None = unlimited)

        Returns:
            The created or updated ModelQuota
        """
        resolved = self.registry.resolve_alias(model_id)
        quota = ModelQuota.get_for_user_model(user_id, resolved)

        if quota is None:
            quota = ModelQuota.create(
                user_id=user_id,
                model_id=resolved,
                max_tokens_per_month=max_tokens_per_month,
                max_cost_per_month=max_cost_per_month,
            )
        else:
            quota.max_tokens_per_month = max_tokens_per_month
            quota.max_cost_per_month = max_cost_per_month
            quota.updated_at = datetime.utcnow()
            db.session.commit()

        return quota

    def reset_quotas(self, user_id: Optional[int] = None) -> int:
        """Reset usage counters.

        Args:
            user_id: If provided, reset only this user's quotas.
                Otherwise reset all quotas.

        Returns:
            Number of quotas reset
        """
        if user_id is not None:
            quotas = ModelQuota.get_all_for_user(user_id)
        else:
            quotas = ModelQuota.query.all()

        for q in quotas:
            q.reset()

        return len(quotas)

    # ------------------------------------------------------------------
    # Usage reporting
    # ------------------------------------------------------------------

    def get_usage_summary(
        self, user_id: int, period: str = "month"
    ) -> UsageSummary:
        """Get aggregated usage summary for a user.

        Args:
            user_id: ID of the user
            period: Time period ("day", "week", "month")

        Returns:
            UsageSummary with totals and per-model breakdown
        """
        if period == "day":
            since = datetime.utcnow() - timedelta(days=1)
        elif period == "week":
            since = datetime.utcnow() - timedelta(weeks=1)
        else:
            since = datetime.utcnow() - timedelta(days=30)

        logs = (
            ModelUsageLog.query.filter(
                ModelUsageLog.user_id == user_id,
                ModelUsageLog.created_at >= since,
            )
            .all()
        )

        total_tokens = 0
        total_cost = 0.0
        by_model: Dict[str, Dict[str, Any]] = {}

        for log in logs:
            tokens = log.tokens_input + log.tokens_output
            total_tokens += tokens
            total_cost += log.cost_usd

            if log.model_id not in by_model:
                by_model[log.model_id] = {
                    "tokens": 0,
                    "cost_usd": 0.0,
                    "requests": 0,
                }
            by_model[log.model_id]["tokens"] += tokens
            by_model[log.model_id]["cost_usd"] = round(
                by_model[log.model_id]["cost_usd"] + log.cost_usd, 6
            )
            by_model[log.model_id]["requests"] += 1

        return UsageSummary(
            user_id=user_id,
            period=period,
            total_tokens=total_tokens,
            total_cost=total_cost,
            total_requests=len(logs),
            by_model=by_model,
        )

    def get_all_quotas(self, user_id: int) -> List[Dict[str, Any]]:
        """Get all quota configs for a user.

        Returns:
            List of quota dictionaries
        """
        quotas = ModelQuota.get_all_for_user(user_id)
        return [q.to_dict() for q in quotas]

    def get_usage_history(
        self, user_id: int, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get detailed usage history for a user.

        Returns:
            List of usage log dictionaries
        """
        logs = ModelUsageLog.get_for_user(user_id, limit=limit)
        return [log.to_dict() for log in logs]
