# 📡 Agent World - Benchmarks Routes
# Version: 0.8.0 (Épic 11 - US-072)
# Description: Endpoints REST pour le benchmarking des modèles IA

"""
Benchmarks Routes for Agent World API.
"""

from flask import current_app, request
from flask_restful import Resource


class BenchmarkRunResource(Resource):
    """POST /api/benchmarks — Run a new benchmark.
    GET /api/benchmarks — List recent benchmark runs.
    """

    def post(self):
        from ..services.benchmark_service import BenchmarkService

        data = request.get_json(silent=True) or {}
        prompt = data.get("prompt")
        if not prompt:
            return {"error": "prompt is required"}, 400

        model_ids = data.get("models")
        max_tokens = data.get("max_tokens", 500)
        temperature = data.get("temperature", 0.7)
        created_by = data.get("created_by")

        service = BenchmarkService()
        result = service.run_benchmark(
            prompt=prompt,
            model_ids=model_ids,
            max_tokens=max_tokens,
            temperature=temperature,
            created_by=created_by,
        )

        return result, 201

    def get(self):
        from ..services.benchmark_service import BenchmarkService

        limit = request.args.get("limit", 20, type=int)

        service = BenchmarkService()
        runs = service.list_benchmark_runs(limit=limit)

        return {"runs": runs, "total": len(runs)}, 200


class BenchmarkDetailResource(Resource):
    """GET /api/benchmarks/<run_id> — Get details of a benchmark run."""

    def get(self, run_id: str):
        from ..services.benchmark_service import BenchmarkService

        service = BenchmarkService()
        result = service.get_benchmark_run(run_id)

        if not result.get("results"):
            return {"error": f"Benchmark run '{run_id}' not found"}, 404

        return result, 200


def register_benchmark_resources(api):
    """Register benchmark resources with the Flask-RESTful API."""
    api.add_resource(BenchmarkRunResource, "/benchmarks")
    api.add_resource(BenchmarkDetailResource, "/benchmarks/<string:run_id>")
