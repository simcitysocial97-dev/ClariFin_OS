"""Workspace Loader Tests — Program 9.

Tests for WorkspaceLoader with synthetic artifacts.
Deterministic. No network. No git mutation.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from runtime.foundation.workspace.models import (
    CrossLayerStatus,
    EngineeringHealth,
    ExecutionHistory,
    MetricsWorkspace,
    PendingVerification,
    PlannerStatus,
    RecentFailure,
    RepositoryStatus,
    RiskSummary,
    StatusWorkspace,
    VerificationCache,
    VerificationHistory,
    VerificationStatusInfo,
    VerificationWorkspace,
)
from runtime.foundation.workspace.workspace import WorkspaceLoader


def _write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _write_md(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


class TestWorkspaceLoader:
    """Tests for WorkspaceLoader."""

    def test_load_repository_status(self, tmp_path: Path):
        loader = WorkspaceLoader(repo_root=tmp_path)
        _write_json(
            tmp_path / "runtime" / "generated" / "verification-cache.json",
            {
                "last_commit": "abc123",
                "changed_files": ["a.py", "b.py"],
                "executed_profiles": ["quick"],
                "duration": 0.5,
                "timestamp": "2026-01-01T00:00:00+00:00",
            },
        )
        status = loader.load_repository_status()
        assert isinstance(status, RepositoryStatus)
        assert status.commit == "abc123"
        assert status.changed_files == 2
        assert status.is_dirty is True

    def test_load_repository_status_no_cache(self, tmp_path: Path):
        loader = WorkspaceLoader(repo_root=tmp_path)
        status = loader.load_repository_status()
        assert status.commit == "unknown"
        assert status.changed_files == 0
        assert status.is_dirty is False

    def test_load_verification_status(self, tmp_path: Path):
        loader = WorkspaceLoader(repo_root=tmp_path)
        _write_json(
            tmp_path / "runtime" / "generated" / "engineering-history.json",
            {
                "combined": [
                    {
                        "run_id": "run-1",
                        "timestamp": "2026-01-02T00:00:00+00:00",
                        "environment": "local",
                        "profile": "quick",
                        "status": "passed",
                        "passed": 5,
                        "failed": 0,
                        "skipped": 1,
                        "duration_seconds": 1.2,
                    }
                ]
            },
        )
        status = loader.load_verification_status()
        assert status.last_profile == "quick"
        assert status.last_status == "passed"
        assert status.passed == 5
        assert status.failed == 0
        assert status.duration_seconds == 1.2

    def test_load_engineering_health(self, tmp_path: Path):
        loader = WorkspaceLoader(repo_root=tmp_path)
        _write_json(
            tmp_path / "runtime" / "generated" / "engineering-analytics.json",
            {
                "local": {"verification": {"success_rate": 0.8, "avg_duration_seconds": 1.0}, "cache": {"hit_rate": 0.5}},
                "ci": {"verification": {"success_rate": 1.0, "avg_duration_seconds": 2.0}, "cache": {"hit_rate": 0.0}},
                "combined": {"verification": {"success_rate": 0.9, "avg_duration_seconds": 1.5}, "cache": {"hit_rate": 0.25}},
            },
        )
        health = loader.load_engineering_health()
        assert isinstance(health, EngineeringHealth)
        assert health.verification_success_rate == 0.9
        assert health.local_success_rate == 0.8
        assert health.ci_success_rate == 1.0
        assert health.cache_hit_rate == 0.25

    def test_load_recent_failures(self, tmp_path: Path):
        loader = WorkspaceLoader(repo_root=tmp_path)
        _write_json(
            tmp_path / "runtime" / "generated" / "engineering-history.json",
            {
                "local": [
                    {
                        "run_id": "run-fail",
                        "timestamp": "2026-01-03T00:00:00+00:00",
                        "environment": "local",
                        "profile": "backend",
                        "status": "failed",
                        "failed": 3,
                    }
                ],
                "ci": [],
                "combined": [],
            },
        )
        failures = loader.load_recent_failures()
        assert len(failures) == 1
        assert isinstance(failures[0], RecentFailure)
        assert failures[0].run_id == "run-fail"
        assert failures[0].failed == 3

    def test_load_verification_cache(self, tmp_path: Path):
        loader = WorkspaceLoader(repo_root=tmp_path)
        _write_json(
            tmp_path / "runtime" / "generated" / "verification-cache.json",
            {
                "last_commit": "def456",
                "changed_files": ["x.py"],
                "executed_profiles": ["quick", "backend"],
                "duration": 2.5,
                "timestamp": "2026-01-04T00:00:00+00:00",
            },
        )
        cache = loader.load_verification_cache()
        assert isinstance(cache, VerificationCache)
        assert cache.last_commit == "def456"
        assert cache.duration == 2.5
        assert cache.is_valid is True

    def test_load_risk_summary(self, tmp_path: Path):
        loader = WorkspaceLoader(
            repo_root=tmp_path, chain_map={"a.py": {}, "b.py": {}}
        )
        risk = loader.load_risk_summary()
        assert isinstance(risk, RiskSummary)
        assert risk.total_files == 2

    def test_load_status_workspace(self, tmp_path: Path):
        loader = WorkspaceLoader(repo_root=tmp_path)
        _write_json(
            tmp_path / "runtime" / "generated" / "verification-cache.json",
            {"last_commit": "abc", "changed_files": [], "executed_profiles": [], "duration": 0, "timestamp": ""},
        )
        _write_json(
            tmp_path / "runtime" / "generated" / "engineering-history.json",
            {"local": [], "ci": [], "combined": []},
        )
        _write_json(
            tmp_path / "runtime" / "generated" / "engineering-analytics.json",
            {},
        )
        _write_json(
            tmp_path / "runtime" / "generated" / "cross-layer-map.json",
            {},
        )
        workspace = loader.load_status_workspace()
        assert isinstance(workspace, StatusWorkspace)
        assert isinstance(workspace.repository, RepositoryStatus)
        assert isinstance(workspace.verification, VerificationStatusInfo)
        assert isinstance(workspace.planner, PlannerStatus)
        assert isinstance(workspace.cross_layer, CrossLayerStatus)
        assert isinstance(workspace.health, EngineeringHealth)
        assert isinstance(workspace.recent_failures, list)
        assert isinstance(workspace.cache, VerificationCache)
        assert isinstance(workspace.risk, RiskSummary)

    def test_load_verification_counts(self, tmp_path: Path):
        loader = WorkspaceLoader(repo_root=tmp_path)
        _write_json(
            tmp_path / "runtime" / "generated" / "engineering-analytics.json",
            {
                "combined": {
                    "verification": {
                        "total_runs": 10,
                        "passed_runs": 8,
                        "failed_runs": 2,
                        "skipped_runs": 0,
                        "success_rate": 0.8,
                    }
                }
            },
        )
        counts = loader.load_verification_counts()
        assert counts.total_runs == 10
        assert counts.passed_runs == 8
        assert counts.failed_runs == 2
        assert counts.success_rate == 0.8

    def test_load_cache_metrics(self, tmp_path: Path):
        loader = WorkspaceLoader(repo_root=tmp_path)
        _write_json(
            tmp_path / "runtime" / "generated" / "engineering-analytics.json",
            {
                "combined": {
                    "cache": {"hit_rate": 0.75, "hits": 15, "total": 20}
                }
            },
        )
        metrics = loader.load_cache_metrics()
        assert metrics.hit_rate == 0.75
        assert metrics.hits == 15
        assert metrics.total == 20

    def test_load_failure_rate(self, tmp_path: Path):
        loader = WorkspaceLoader(repo_root=tmp_path)
        _write_json(
            tmp_path / "runtime" / "generated" / "engineering-analytics.json",
            {
                "local": {"verification": {"total_runs": 10, "failed_runs": 2}},
                "ci": {"verification": {"total_runs": 5, "failed_runs": 0}},
                "combined": {"verification": {"total_runs": 15, "failed_runs": 2}},
            },
        )
        rate = loader.load_failure_rate()
        assert pytest.approx(rate.local) == 20.0
        assert pytest.approx(rate.ci) == 0.0
        assert pytest.approx(rate.combined) == (2 / 15 * 100.0)

    def test_load_flaky_tests(self, tmp_path: Path):
        loader = WorkspaceLoader(repo_root=tmp_path)
        _write_json(
            tmp_path / "runtime" / "generated" / "flaky-tests.json",
            {"flaky_tests": ["test_a", "test_b"]},
        )
        flaky = loader.load_flaky_tests()
        assert flaky.total_flaky == 2
        assert "test_a" in flaky.flaky_tests

    def test_load_flaky_tests_empty(self, tmp_path: Path):
        loader = WorkspaceLoader(repo_root=tmp_path)
        _write_json(tmp_path / "runtime" / "generated" / "flaky-tests.json", {})
        flaky = loader.load_flaky_tests()
        assert flaky.total_flaky == 0

    def test_load_dependency_growth(self, tmp_path: Path):
        loader = WorkspaceLoader(repo_root=tmp_path)
        _write_json(
            tmp_path / "runtime" / "generated" / "dependency-growth.json",
            {
                "engines": {"category": "engines", "current_count": 4, "previous_count": 4, "delta": 0, "growth_rate": 0.0},
            },
        )
        growth = loader.load_dependency_growth()
        assert len(growth) == 1
        assert growth[0].category == "engines"
        assert growth[0].current_count == 4

    def test_load_metrics_workspace(self, tmp_path: Path):
        loader = WorkspaceLoader(repo_root=tmp_path)
        _write_json(
            tmp_path / "runtime" / "generated" / "verification-cache.json",
            {"last_commit": "abc", "changed_files": [], "executed_profiles": [], "duration": 0, "timestamp": ""},
        )
        _write_json(
            tmp_path / "runtime" / "generated" / "engineering-history.json",
            {"local": [], "ci": [], "combined": []},
        )
        _write_json(
            tmp_path / "runtime" / "generated" / "engineering-analytics.json",
            {
                "local": {"verification": {"total_runs": 5, "passed_runs": 4, "failed_runs": 1, "skipped_runs": 0, "success_rate": 0.8, "avg_duration_seconds": 1.0, "min_duration_seconds": 0.5, "max_duration_seconds": 1.5}, "cache": {"hit_rate": 0.5, "hits": 2, "total": 4}},
                "ci": {"verification": {"total_runs": 3, "passed_runs": 3, "failed_runs": 0, "skipped_runs": 0, "success_rate": 1.0, "avg_duration_seconds": 2.0, "min_duration_seconds": 1.0, "max_duration_seconds": 3.0}, "cache": {"hit_rate": 0.0, "hits": 0, "total": 3}},
                "combined": {"verification": {"total_runs": 8, "passed_runs": 7, "failed_runs": 1, "skipped_runs": 0, "success_rate": 0.875, "avg_duration_seconds": 1.375, "min_duration_seconds": 0.5, "max_duration_seconds": 3.0}, "cache": {"hit_rate": 0.25, "hits": 2, "total": 8}},
            },
        )
        _write_json(
            tmp_path / "runtime" / "generated" / "flaky-tests.json",
            {"flaky_tests": []},
        )
        _write_json(
            tmp_path / "runtime" / "generated" / "dependency-growth.json",
            {},
        )
        _write_json(
            tmp_path / "runtime" / "generated" / "cross-layer-map.json",
            {},
        )
        workspace = loader.load_metrics_workspace()
        assert isinstance(workspace, MetricsWorkspace)
        assert workspace.verification.total_runs == 8
        assert pytest.approx(workspace.failure_rate.local) == 20.0

    def test_load_history_events(self, tmp_path: Path):
        loader = WorkspaceLoader(repo_root=tmp_path)
        _write_json(
            tmp_path / "runtime" / "generated" / "engineering-history.json",
            {
                "local": [
                    {
                        "run_id": "run-local",
                        "timestamp": "2026-01-01T00:00:00+00:00",
                        "environment": "local",
                        "profile": "quick",
                        "status": "passed",
                        "passed": 5,
                        "failed": 0,
                        "skipped": 0,
                        "duration_seconds": 1.0,
                    }
                ],
                "ci": [
                    {
                        "run_id": "run-ci",
                        "timestamp": "2026-01-02T00:00:00+00:00",
                        "environment": "ci",
                        "profile": "full",
                        "status": "failed",
                        "passed": 0,
                        "failed": 1,
                        "skipped": 0,
                        "duration_seconds": 2.0,
                    }
                ],
                "combined": [],
            },
        )
        history = loader.load_history_events()
        assert isinstance(history, VerificationHistory)
        assert len(history.local) == 1
        assert len(history.ci) == 1
        assert len(history.combined) == 2
        assert history.combined[0].run_id == "run-ci"

    def test_load_verification_profiles(self, tmp_path: Path):
        loader = WorkspaceLoader(repo_root=tmp_path)
        _write_json(
            tmp_path / "runtime" / "generated" / "verification-cache.json",
            {
                "executed_profiles": ["quick", "backend", "quick"],
                "timestamp": "2026-01-01T00:00:00+00:00",
            },
        )
        profiles = loader.load_verification_profiles()
        assert len(profiles) == 2
        assert profiles[0].name == "quick"
        assert profiles[0].executed_count == 2

    def test_load_pending_verification(self, tmp_path: Path):
        loader = WorkspaceLoader(repo_root=tmp_path)
        _write_json(
            tmp_path / "runtime" / "generated" / "verification-cache.json",
            {"executed_profiles": ["quick"]},
        )
        pending = loader.load_pending_verification()
        assert pending.pending_count == 5
        assert "backend" in pending.pending_profiles
        assert "quick" not in pending.pending_profiles

    def test_load_verification_workspace(self, tmp_path: Path):
        loader = WorkspaceLoader(repo_root=tmp_path)
        _write_json(
            tmp_path / "runtime" / "generated" / "verification-cache.json",
            {"last_commit": "abc", "changed_files": [], "executed_profiles": [], "duration": 0, "timestamp": ""},
        )
        _write_json(
            tmp_path / "runtime" / "generated" / "engineering-history.json",
            {"local": [], "ci": [], "combined": []},
        )
        workspace = loader.load_verification_workspace()
        assert isinstance(workspace, VerificationWorkspace)
        assert isinstance(workspace.profiles, list)
        assert isinstance(workspace.execution_history, ExecutionHistory)
        assert isinstance(workspace.pending, PendingVerification)

    def test_load_dependency_chain_found(self, tmp_path: Path):
        loader = WorkspaceLoader(
            repo_root=tmp_path,
            chain_map={
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
                    "tests": ["backend/tests/unit/engines/loan/test_amortization.py"],
                    "graphRenderers": [],
                }
            },
        )
        result = loader.load_dependency_chain("backend/src/engines/loan_engine/amortization.py")
        assert result.found is True
        assert result.chain is not None
        assert result.chain.engine == "backend/src/engines/loan_engine/amortization.py"
        assert result.chain.services == ["LoanService"]
        assert result.chain.tests == ["backend/tests/unit/engines/loan/test_amortization.py"]

    def test_load_dependency_chain_missing(self, tmp_path: Path):
        loader = WorkspaceLoader(repo_root=tmp_path, chain_map={})
        result = loader.load_dependency_chain("nonexistent.py")
        assert result.found is False
        assert result.chain is None

    def test_load_cross_layer_map(self, tmp_path: Path):
        data = {"a.py": {"engine": "a.py"}}
        loader = WorkspaceLoader(repo_root=tmp_path, chain_map=data)
        result = loader.load_cross_layer_map()
        assert result == data
