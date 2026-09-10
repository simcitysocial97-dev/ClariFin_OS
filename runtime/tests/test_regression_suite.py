"""M9-C55 — Regression Suite Tests.

Covers critical paths: scopes, mutation, regression detection, evidence cleanup.
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

import pytest


class TestRegressionSuite:
    """Regression test suite for critical verification paths."""

    def test_verify_plan_backend(self):
        result = subprocess.run(
            [sys.executable, "-m", "runtime.verify", "plan", "--scope", "backend"],
            capture_output=True, text=True, timeout=60,
        )
        assert result.returncode == 0, f"Backend plan failed: {result.stderr[:300]}"

    def test_verify_plan_frontend(self):
        result = subprocess.run(
            [sys.executable, "-m", "runtime.verify", "plan", "--scope", "frontend"],
            capture_output=True, text=True, timeout=60,
        )
        assert result.returncode == 0, f"Frontend plan failed: {result.stderr[:300]}"

    def test_verify_plan_runtime(self):
        result = subprocess.run(
            [sys.executable, "-m", "runtime.verify", "plan", "--scope", "runtime"],
            capture_output=True, text=True, timeout=60,
        )
        assert result.returncode == 0, f"Runtime plan failed: {result.stderr[:300]}"

    def test_regression_detector_stores_metrics(self):
        from runtime.foundation.verification.regression_detector import RegressionDetector, RunMetrics

        detector = RegressionDetector()
        metrics = RunMetrics(
            run_id="regression-test",
            timestamp="2024-01-01T00:00:00",
            branch="test",
            commit_sha="abc123",
            coverage_pct=80.0,
            mutation_score=85.0,
            test_count=500,
            passed=495,
            failed=5,
            duration_seconds=100,
        )

        detector.store_run_metrics("regression-test", "test", {
            "run_id": "regression-test",
            "timestamp": "2024-01-01T00:00:00",
            "branch": "test",
            "commit_sha": "abc123",
            "coverage_pct": 80.0,
            "mutation_score": 85.0,
            "test_count": 500,
            "passed": 495,
            "failed": 5,
            "duration_seconds": 100,
        })
        baseline = detector.get_baseline_metrics("test")
        assert baseline is not None
        assert baseline.get("run_id") == "regression-test"

    def test_evidence_cleanup_dry_run(self):
        result = subprocess.run(
            [sys.executable, "-m", "runtime.verify", "inspect", "evidence-cleanup", "--dry-run"],
            capture_output=True, text=True, timeout=30,
        )
        assert result.returncode == 0, f"Evidence cleanup dry-run failed: {result.stderr[:300]}"

    def test_parallel_executor_instantiates(self):
        from runtime.foundation.verification.parallel_executor import ParallelExecutor

        executor = ParallelExecutor(max_workers=2)
        assert executor.max_workers == 2

    def test_mutation_smoke_runs(self):
        result = subprocess.run(
            [sys.executable, "-m", "runtime.verify", "mutation", "--smoke"],
            capture_output=True, text=True, timeout=120,
        )
        # May pass or fail quality gate, but must not crash
        assert "Traceback" not in result.stderr, f"Mutation smoke crashed: {result.stderr[:300]}"
