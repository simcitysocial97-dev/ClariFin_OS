"""Verification Performance Benchmark — Program 7B.5

Measures runtime performance of the verification pipeline.
Generates runtime/generated/verification-performance.json.
"""

from __future__ import annotations

import dataclasses
import json
import time
from pathlib import Path
from unittest.mock import patch

import pytest

from runtime.foundation.verification.models import VerificationScope, VerificationStatus
from runtime.foundation.verification.planner import CrossLayerImpactPlanner
from runtime.foundation.verification.orchestrator import VerificationOrchestrator
from runtime.system.evidence.aggregator import EvidenceAggregator


MAP_DATA = {
    "backend/src/engines/loan_engine/amortization.py": {
        "engine": "backend/src/engines/loan_engine/amortization.py",
        "services": ["LoanService"],
        "routers": ["backend/src/routers/loans.py"],
        "endpoints": ["GET /api/loans/{loan_id}/schedule"],
        "capabilities": ["useLoansCapability"],
        "mappers": ["loansMapper"],
        "viewModels": ["LoansViewModel"],
        "pages": ["app/loans/page.tsx"],
        "workspace": ["LoansWorkspace"],
        "components": ["AmortizationTable"],
        "tests": [
            "backend/tests/unit/engines/loan/test_amortization.py",
            "backend/tests/contract/generated/test_loans.py",
        ],
        "graphRenderers": [],
    }
}


def _make_map(tmp_path: Path) -> Path:
    map_path = tmp_path / "cross-layer-map.json"
    map_path.write_text(json.dumps(MAP_DATA), encoding="utf-8")
    return map_path


def _make_steps(plan):
    new_steps = []
    for step in plan.steps:
        new_steps.append(
            step.__class__(
                id=step.id,
                target=step.target,
                order=step.order,
                command=None,
                workflow=step.workflow,
                script=step.script,
                estimated_duration_seconds=step.estimated_duration_seconds,
                required_evidence=step.required_evidence,
                dependencies=step.dependencies,
                status=VerificationStatus.SKIPPED,
                metadata=step.metadata,
            )
        )
    return new_steps


def _make_mock_results(plan):
    return [
        type("R", (), {
            "task_id": s.id,
            "command": s.command or "no-op",
            "status": VerificationStatus.SKIPPED,
            "duration_seconds": 0.0,
        })()
        for s in plan.steps
    ]


class TestRuntimePerformance:
    """Performance benchmarks for the verification runtime."""

    def test_planner_performance(self, tmp_path: Path):
        planner = CrossLayerImpactPlanner(map_path=_make_map(tmp_path))

        start = time.perf_counter()
        planner.analyze_cross_layer_impact(
            ["backend/src/engines/loan_engine/amortization.py"]
        )
        planner_ms = (time.perf_counter() - start) * 1000

        assert planner_ms < 1000, f"Planner took {planner_ms:.1f}ms, expected < 1000ms"

    def test_orchestrator_planning_performance(self, tmp_path: Path):
        orchestrator = VerificationOrchestrator(repo_root=tmp_path)
        orchestrator._changed_files = ["backend/src/engines/loan_engine/amortization.py"]

        start = time.perf_counter()
        orchestrator.generate_plan(scope=VerificationScope.BACKEND)
        orchestrator_ms = (time.perf_counter() - start) * 1000

        assert orchestrator_ms < 1000, f"Orchestrator planning took {orchestrator_ms:.1f}ms"

    def test_report_generation_performance(self, tmp_path: Path):
        with patch(
            "runtime.foundation.verification.orchestrator._find_repo_root",
            return_value=tmp_path,
        ), patch(
            "runtime.foundation.verification.orchestrator.VERIFICATION_REPORT_PATH",
            tmp_path / "verification-report.md",
        ), patch(
            "runtime.foundation.verification.orchestrator.VERIFICATION_CACHE_PATH",
            tmp_path / "verification-cache.json",
        ):
            orchestrator = VerificationOrchestrator(repo_root=tmp_path)
            orchestrator._changed_files = ["backend/src/engines/loan_engine/amortization.py"]
            plan = orchestrator.generate_plan(scope=VerificationScope.BACKEND)
            plan = dataclasses.replace(plan, steps=_make_steps(plan))
            orchestrator._plan = plan
            orchestrator._results = _make_mock_results(plan)

            start = time.perf_counter()
            orchestrator.generate_report()
            report_ms = (time.perf_counter() - start) * 1000

            assert report_ms < 1000, f"Report generation took {report_ms:.1f}ms"

    def test_evidence_aggregation_performance(self, tmp_path: Path):
        aggregator = EvidenceAggregator(tmp_path)

        start = time.perf_counter()
        aggregator.aggregate(tmp_path)
        evidence_ms = (time.perf_counter() - start) * 1000

        assert evidence_ms < 1000, f"Evidence aggregation took {evidence_ms:.1f}ms"

    def test_cache_lookup_performance(self, tmp_path: Path):
        cache_path = tmp_path / "verification-cache.json"
        cache_path.write_text(json.dumps({"hash": "abc"}), encoding="utf-8")

        start = time.perf_counter()
        json.loads(cache_path.read_text(encoding="utf-8"))
        cache_ms = (time.perf_counter() - start) * 1000

        assert cache_ms < 100, f"Cache lookup took {cache_ms:.1f}ms"

    def test_full_benchmark_generates_report(self, tmp_path: Path):
        planner = CrossLayerImpactPlanner(map_path=_make_map(tmp_path))
        start = time.perf_counter()
        planner.analyze_cross_layer_impact(
            ["backend/src/engines/loan_engine/amortization.py"]
        )
        planner_ms = (time.perf_counter() - start) * 1000

        with patch(
            "runtime.foundation.verification.orchestrator._find_repo_root",
            return_value=tmp_path,
        ), patch(
            "runtime.foundation.verification.orchestrator.VERIFICATION_REPORT_PATH",
            tmp_path / "verification-report.md",
        ), patch(
            "runtime.foundation.verification.orchestrator.VERIFICATION_CACHE_PATH",
            tmp_path / "verification-cache.json",
        ):
            orchestrator = VerificationOrchestrator(repo_root=tmp_path)
            orchestrator._changed_files = ["backend/src/engines/loan_engine/amortization.py"]
            start = time.perf_counter()
            plan = orchestrator.generate_plan(scope=VerificationScope.BACKEND)
            orchestrator_ms = (time.perf_counter() - start) * 1000

            plan = dataclasses.replace(plan, steps=_make_steps(plan))
            orchestrator._plan = plan
            orchestrator._results = _make_mock_results(plan)
            start = time.perf_counter()
            orchestrator.generate_report()
            report_ms = (time.perf_counter() - start) * 1000

        aggregator = EvidenceAggregator(tmp_path)
        start = time.perf_counter()
        aggregator.aggregate(tmp_path)
        evidence_ms = (time.perf_counter() - start) * 1000

        cache_path = tmp_path / "verification-cache.json"
        cache_path.write_text(json.dumps({}), encoding="utf-8")
        start = time.perf_counter()
        json.loads(cache_path.read_text(encoding="utf-8"))
        cache_ms = (time.perf_counter() - start) * 1000

        perf = {
            "planner_ms": round(planner_ms, 2),
            "orchestrator_ms": round(orchestrator_ms, 2),
            "evidence_ms": round(evidence_ms, 2),
            "report_ms": round(report_ms, 2),
            "cache_ms": round(cache_ms, 2),
        }

        generated_dir = tmp_path / "runtime" / "generated"
        generated_dir.mkdir(parents=True, exist_ok=True)
        perf_path = generated_dir / "verification-performance.json"
        perf_path.write_text(json.dumps(perf, indent=2), encoding="utf-8")

        assert perf_path.exists()
        assert perf["planner_ms"] > 0
        assert perf["orchestrator_ms"] > 0
        assert perf["evidence_ms"] >= 0
        assert perf["report_ms"] > 0
        assert perf["cache_ms"] >= 0
