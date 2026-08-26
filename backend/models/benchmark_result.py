# 🗃️ Agent World - Benchmark Result Model
# Version: 0.8.0 (Épic 11 - US-072)
# Description: Modèle pour stocker les résultats de benchmarks de modèles

"""
Benchmark Result model for Agent World.
"""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from .base import BaseModel, db


class BenchmarkResult(BaseModel):
    """Stores results of a model benchmark run.

    A benchmark run tests the same prompt on multiple models and
    records latency, token usage, and cost for comparison.
    """

    __tablename__ = "benchmark_results"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    benchmark_run_id = db.Column(
        db.String(36), nullable=False, index=True, default=lambda: str(uuid.uuid4())
    )
    model_id = db.Column(db.String(100), nullable=False)
    prompt = db.Column(db.Text, nullable=False)
    response_text = db.Column(db.Text, nullable=True)

    latency_ms = db.Column(db.Integer, nullable=True)
    tokens_input = db.Column(db.Integer, nullable=False, default=0)
    tokens_output = db.Column(db.Integer, nullable=False, default=0)
    cost_usd = db.Column(db.Float, nullable=False, default=0.0)
    quality_score = db.Column(db.Float, nullable=True)

    error_message = db.Column(db.Text, nullable=True)
    status = db.Column(
        db.String(20), nullable=False, default="completed"
    )  # completed, failed, timeout

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)

    def __repr__(self) -> str:
        return (
            f"<BenchmarkResult(run={self.benchmark_run_id[:8]}, "
            f"model={self.model_id}, latency={self.latency_ms}ms)>"
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "benchmark_run_id": self.benchmark_run_id,
            "model_id": self.model_id,
            "prompt": self.prompt,
            "response_text": self.response_text,
            "latency_ms": self.latency_ms,
            "tokens_input": self.tokens_input,
            "tokens_output": self.tokens_output,
            "cost_usd": self.cost_usd,
            "quality_score": self.quality_score,
            "error_message": self.error_message,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "created_by": self.created_by,
        }

    @classmethod
    def create(cls, **kwargs) -> "BenchmarkResult":
        result = cls(**kwargs)
        db.session.add(result)
        db.session.commit()
        return result

    @classmethod
    def get_by_run_id(cls, run_id: str) -> List["BenchmarkResult"]:
        return cls.query.filter_by(benchmark_run_id=run_id).all()

    @classmethod
    def get_all_runs(cls, limit: int = 20) -> List[str]:
        """Get distinct run IDs, most recent first."""
        rows = (
            db.session.query(cls.benchmark_run_id)
            .distinct()
            .order_by(cls.created_at.desc())
            .limit(limit)
            .all()
        )
        return [r[0] for r in rows]
