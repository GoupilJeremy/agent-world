# ⚙️ Agent World - Benchmark Service
# Version: 0.8.0 (Épic 11 - US-072)
# Description: Service de benchmarking comparatif des modèles IA

"""
Benchmark Service for Agent World.

Ce service permet de comparer les modèles IA en exécutant le même prompt
sur plusieurs modèles et en mesurant latence, tokens, et coût.
"""

import logging
import uuid
from typing import Any, Dict, List, Optional

from ..models.benchmark_result import BenchmarkResult
from .connectors.base import ConnectorError, ConnectorResponse
from .model_registry import ModelRegistry, get_model_registry

logger = logging.getLogger(__name__)


class BenchmarkService:
    """Runs benchmarks comparing multiple AI models."""

    def __init__(self, registry: Optional[ModelRegistry] = None):
        self.registry = registry or get_model_registry()

    def run_benchmark(
        self,
        prompt: str,
        model_ids: Optional[List[str]] = None,
        max_tokens: int = 500,
        temperature: float = 0.7,
        created_by: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Run a benchmark comparing models on the same prompt.

        Args:
            prompt: The prompt to test
            model_ids: List of model IDs to benchmark.
                If None, benchmarks all available models.
            max_tokens: Max tokens per response
            temperature: Sampling temperature
            created_by: User who launched the benchmark

        Returns:
            Dictionary with run_id and results
        """
        run_id = str(uuid.uuid4())

        if model_ids is None:
            models = self.registry.list_models(available_only=True)
            model_ids = [m.id for m in models]
        else:
            model_ids = [self.registry.resolve_alias(m) for m in model_ids]

        results: List[Dict[str, Any]] = []

        for model_id in model_ids:
            result = self._benchmark_single_model(
                run_id=run_id,
                prompt=prompt,
                model_id=model_id,
                max_tokens=max_tokens,
                temperature=temperature,
                created_by=created_by,
            )
            results.append(result)

        # Compute rankings
        rankings = self._compute_rankings(results)

        return {
            "run_id": run_id,
            "prompt": prompt,
            "models_tested": len(results),
            "results": results,
            "rankings": rankings,
        }

    def get_benchmark_run(self, run_id: str) -> Dict[str, Any]:
        """Get results for a specific benchmark run.

        Args:
            run_id: UUID of the benchmark run

        Returns:
            Dictionary with run details and results
        """
        db_results = BenchmarkResult.get_by_run_id(run_id)
        if not db_results:
            return {"run_id": run_id, "results": [], "error": "Run not found"}

        results = [r.to_dict() for r in db_results]
        rankings = self._compute_rankings(results)

        return {
            "run_id": run_id,
            "prompt": db_results[0].prompt if db_results else "",
            "models_tested": len(results),
            "results": results,
            "rankings": rankings,
        }

    def list_benchmark_runs(self, limit: int = 20) -> List[Dict[str, Any]]:
        """List recent benchmark runs.

        Args:
            limit: Maximum number of runs to return

        Returns:
            List of run summaries
        """
        run_ids = BenchmarkResult.get_all_runs(limit=limit)
        runs = []
        for run_id in run_ids:
            results = BenchmarkResult.get_by_run_id(run_id)
            if results:
                runs.append({
                    "run_id": run_id,
                    "models_tested": len(results),
                    "prompt_preview": results[0].prompt[:100] + "..." if len(results[0].prompt) > 100 else results[0].prompt,
                    "created_at": results[0].created_at.isoformat() if results[0].created_at else None,
                })
        return runs

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _benchmark_single_model(
        self,
        run_id: str,
        prompt: str,
        model_id: str,
        max_tokens: int,
        temperature: float,
        created_by: Optional[int],
    ) -> Dict[str, Any]:
        """Benchmark a single model and persist the result."""
        connector = self.registry.get_connector_for_model(model_id)
        model_info = self.registry.get_model(model_id)

        if connector is None or model_info is None:
            result = BenchmarkResult.create(
                benchmark_run_id=run_id,
                model_id=model_id,
                prompt=prompt,
                status="failed",
                error_message=f"No connector available for model '{model_id}'",
                created_by=created_by,
            )
            return result.to_dict()

        try:
            response = connector.generate(
                prompt=prompt,
                model=model_id,
                max_tokens=max_tokens,
                temperature=temperature,
            )

            cost = model_info.estimate_cost(
                response.tokens_input, response.tokens_output
            )

            result = BenchmarkResult.create(
                benchmark_run_id=run_id,
                model_id=model_id,
                prompt=prompt,
                response_text=response.text,
                latency_ms=response.latency_ms,
                tokens_input=response.tokens_input,
                tokens_output=response.tokens_output,
                cost_usd=cost,
                status="completed",
                created_by=created_by,
            )

            logger.info(
                "Benchmark %s model=%s latency=%dms tokens=%d cost=$%.6f",
                run_id[:8],
                model_id,
                response.latency_ms,
                response.tokens_total,
                cost,
            )

        except ConnectorError as exc:
            result = BenchmarkResult.create(
                benchmark_run_id=run_id,
                model_id=model_id,
                prompt=prompt,
                status="failed",
                error_message=str(exc),
                created_by=created_by,
            )
            logger.warning(
                "Benchmark %s model=%s FAILED: %s",
                run_id[:8],
                model_id,
                exc,
            )

        except Exception as exc:
            result = BenchmarkResult.create(
                benchmark_run_id=run_id,
                model_id=model_id,
                prompt=prompt,
                status="failed",
                error_message=str(exc),
                created_by=created_by,
            )

        return result.to_dict()

    def _compute_rankings(
        self, results: List[Dict[str, Any]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Compute rankings across different dimensions."""
        completed = [r for r in results if r.get("status") == "completed"]

        if not completed:
            return {"by_latency": [], "by_cost": [], "by_tokens": []}

        by_latency = sorted(
            completed,
            key=lambda r: r.get("latency_ms") or float("inf"),
        )
        by_cost = sorted(
            completed,
            key=lambda r: r.get("cost_usd") or float("inf"),
        )
        by_tokens = sorted(
            completed,
            key=lambda r: (r.get("tokens_output") or 0),
            reverse=True,
        )

        def rank_entry(r: Dict, rank: int) -> Dict:
            return {
                "rank": rank + 1,
                "model_id": r["model_id"],
                "value": r.get("latency_ms") or r.get("cost_usd") or 0,
            }

        return {
            "by_latency": [
                {"rank": i + 1, "model_id": r["model_id"], "latency_ms": r.get("latency_ms")}
                for i, r in enumerate(by_latency)
            ],
            "by_cost": [
                {"rank": i + 1, "model_id": r["model_id"], "cost_usd": r.get("cost_usd")}
                for i, r in enumerate(by_cost)
            ],
            "by_output_tokens": [
                {"rank": i + 1, "model_id": r["model_id"], "tokens_output": r.get("tokens_output")}
                for i, r in enumerate(by_tokens)
            ],
        }
