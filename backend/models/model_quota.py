# 🗃️ Agent World - Model Quota Models
# Version: 0.8.0 (Épic 11 - US-075)
# Description: Modèles pour la gestion des quotas et coûts par modèle IA

"""
Model Quota and Usage Log models for Agent World.

Ces modèles stockent les limites de quota par utilisateur/modèle
et l'historique d'utilisation détaillé.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from .base import BaseModel, db


class ModelQuota(BaseModel):
    """Per-user, per-model usage quota.

    Tracks how many tokens and how much cost a user is allowed
    to consume for each model within a billing period.
    """

    __tablename__ = "model_quotas"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    model_id = db.Column(db.String(100), nullable=False)

    # Limits (None = unlimited)
    max_tokens_per_month = db.Column(db.Integer, nullable=True)
    max_cost_per_month = db.Column(db.Float, nullable=True)

    # Current usage within the period
    tokens_used = db.Column(db.Integer, nullable=False, default=0)
    cost_used = db.Column(db.Float, nullable=False, default=0.0)

    # Billing period
    period_start = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    period_end = db.Column(
        db.DateTime,
        nullable=False,
        default=lambda: datetime.utcnow() + timedelta(days=30),
    )

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Unique constraint: one quota row per user per model
    __table_args__ = (
        db.UniqueConstraint("user_id", "model_id", name="uq_user_model_quota"),
    )

    def __repr__(self) -> str:
        return (
            f"<ModelQuota(user={self.user_id}, model={self.model_id}, "
            f"tokens={self.tokens_used}/{self.max_tokens_per_month})>"
        )

    @property
    def is_period_active(self) -> bool:
        """Check if the current billing period is still active."""
        now = datetime.utcnow()
        return self.period_start <= now <= self.period_end

    @property
    def tokens_remaining(self) -> Optional[int]:
        """Tokens remaining in the current period (None if unlimited)."""
        if self.max_tokens_per_month is None:
            return None
        return max(0, self.max_tokens_per_month - self.tokens_used)

    @property
    def cost_remaining(self) -> Optional[float]:
        """Cost remaining in the current period (None if unlimited)."""
        if self.max_cost_per_month is None:
            return None
        return max(0.0, self.max_cost_per_month - self.cost_used)

    @property
    def is_tokens_exceeded(self) -> bool:
        """True if the token quota has been exceeded."""
        if self.max_tokens_per_month is None:
            return False
        return self.tokens_used >= self.max_tokens_per_month

    @property
    def is_cost_exceeded(self) -> bool:
        """True if the cost quota has been exceeded."""
        if self.max_cost_per_month is None:
            return False
        return self.cost_used >= self.max_cost_per_month

    def consume(self, tokens: int, cost: float) -> None:
        """Record consumption of tokens and cost."""
        self.tokens_used += tokens
        self.cost_used = round(self.cost_used + cost, 6)
        self.updated_at = datetime.utcnow()
        db.session.commit()

    def reset(self) -> None:
        """Reset usage counters and start a new period."""
        self.tokens_used = 0
        self.cost_used = 0.0
        self.period_start = datetime.utcnow()
        self.period_end = datetime.utcnow() + timedelta(days=30)
        self.updated_at = datetime.utcnow()
        db.session.commit()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "model_id": self.model_id,
            "max_tokens_per_month": self.max_tokens_per_month,
            "max_cost_per_month": self.max_cost_per_month,
            "tokens_used": self.tokens_used,
            "cost_used": self.cost_used,
            "tokens_remaining": self.tokens_remaining,
            "cost_remaining": self.cost_remaining,
            "is_tokens_exceeded": self.is_tokens_exceeded,
            "is_cost_exceeded": self.is_cost_exceeded,
            "period_start": self.period_start.isoformat() if self.period_start else None,
            "period_end": self.period_end.isoformat() if self.period_end else None,
        }

    @classmethod
    def get_for_user_model(cls, user_id: int, model_id: str) -> Optional["ModelQuota"]:
        """Get the quota for a specific user and model."""
        return cls.query.filter_by(user_id=user_id, model_id=model_id).first()

    @classmethod
    def get_all_for_user(cls, user_id: int) -> List["ModelQuota"]:
        """Get all quotas for a user."""
        return cls.query.filter_by(user_id=user_id).all()

    @classmethod
    def create(cls, **kwargs) -> "ModelQuota":
        quota = cls(**kwargs)
        db.session.add(quota)
        db.session.commit()
        return quota


class ModelUsageLog(BaseModel):
    """Detailed log of each model usage event.

    Records every API call with token counts, cost, and timing
    for analytics and auditing.
    """

    __tablename__ = "model_usage_logs"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    model_id = db.Column(db.String(100), nullable=False)
    execution_id = db.Column(
        db.Integer, db.ForeignKey("executions.id"), nullable=True
    )

    tokens_input = db.Column(db.Integer, nullable=False, default=0)
    tokens_output = db.Column(db.Integer, nullable=False, default=0)
    cost_usd = db.Column(db.Float, nullable=False, default=0.0)
    latency_ms = db.Column(db.Integer, nullable=True)

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self) -> str:
        return (
            f"<ModelUsageLog(user={self.user_id}, model={self.model_id}, "
            f"tokens={self.tokens_input + self.tokens_output}, "
            f"cost=${self.cost_usd:.4f})>"
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "model_id": self.model_id,
            "execution_id": self.execution_id,
            "tokens_input": self.tokens_input,
            "tokens_output": self.tokens_output,
            "tokens_total": self.tokens_input + self.tokens_output,
            "cost_usd": self.cost_usd,
            "latency_ms": self.latency_ms,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    @classmethod
    def create(cls, **kwargs) -> "ModelUsageLog":
        log = cls(**kwargs)
        db.session.add(log)
        db.session.commit()
        return log

    @classmethod
    def get_for_user(
        cls, user_id: int, limit: int = 100
    ) -> List["ModelUsageLog"]:
        return (
            cls.query.filter_by(user_id=user_id)
            .order_by(cls.created_at.desc())
            .limit(limit)
            .all()
        )

    @classmethod
    def get_for_model(
        cls, model_id: str, limit: int = 100
    ) -> List["ModelUsageLog"]:
        return (
            cls.query.filter_by(model_id=model_id)
            .order_by(cls.created_at.desc())
            .limit(limit)
            .all()
        )
