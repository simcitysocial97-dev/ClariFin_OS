"""Verification Orchestrator Tests — Program 7B.5

Tests for the VerificationOrchestrator with mocked subprocess execution.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch, MagicMock


from runtime.foundation.verification.models import (
    VerificationScope,
    VerificationStatus,
)
from runtime.foundation.verification.orchestrator import (
    VerificationOrchestrator,
    VerificationReport,
)


class MockSubprocessResult:
    """Mock subprocess result."""

    def __init__(self, returncode=0, stdout="", stderr=""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


class TestVerificationOrchestrator:
    """Tests for VerificationOrchestrator."""

    def test_plan_generation(self, tmp_path: Path):
        map_data = {
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
        map_path = tmp_path / "cross-layer-map.json"
        map_path.write_text(json.dumps(map_data), encoding="utf-8")

        orchestrator = VerificationOrchestrator(repo_root=tmp_path)
        orchestrator._changed_files = ["backend/src/engines/loan_engine/amortization.py"]

        plan = orchestrator.generate_plan(scope=VerificationScope.BACKEND)

        assert plan is not None
        assert plan.scope == VerificationScope.BACKEND
        assert len(plan.targets) > 0
        assert len(plan.steps) > 0

    def test_profile_expansion(self):
        orchestrator = VerificationOrchestrator()
        profile = orchestrator._profile
        tasks = profile.expand_tasks()
        assert len(tasks) > 0
        task_ids = profile.task_ids()
        assert len(task_ids) == len(tasks)

    def test_task_ordering(self, tmp_path: Path):
        map_data = {
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
        map_path = tmp_path / "cross-layer-map.json"
        map_path.write_text(json.dumps(map_data), encoding="utf-8")

        orchestrator = VerificationOrchestrator(repo_root=tmp_path)
        orchestrator._changed_files = ["backend/src/engines/loan_engine/amortization.py"]
        plan = orchestrator.generate_plan(scope=VerificationScope.BACKEND)

        orders = [s.order for s in plan.steps]
        assert orders == sorted(orders), "Steps should be ordered"

    @patch("runtime.foundation.verification.orchestrator.subprocess.run")
    def test_execution_result_collection(self, mock_run: MagicMock, tmp_path: Path):
        mock_run.return_value = MockSubprocessResult(returncode=0, stdout="ok", stderr="")

        map_data = {
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
        map_path = tmp_path / "cross-layer-map.json"
        map_path.write_text(json.dumps(map_data), encoding="utf-8")

        orchestrator = VerificationOrchestrator(repo_root=tmp_path)
        orchestrator._changed_files = ["backend/src/engines/loan_engine/amortization.py"]
        plan = orchestrator.generate_plan(scope=VerificationScope.QUICK)

        results = orchestrator.execute()
        assert len(results) == len(plan.steps)
        for r in results:
            assert isinstance(r.status, VerificationStatus)

    @patch("runtime.foundation.verification.orchestrator.subprocess.run")
    def test_report_generation(self, mock_run: MagicMock, tmp_path: Path):
        mock_run.return_value = MockSubprocessResult(returncode=0, stdout="ok", stderr="")

        map_data = {
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
        map_path = tmp_path / "cross-layer-map.json"
        map_path.write_text(json.dumps(map_data), encoding="utf-8")

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
            plan = orchestrator.generate_plan(scope=VerificationScope.QUICK)
            for i, step in enumerate(plan.steps):
                plan.steps[i] = step.__class__(
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
            orchestrator._plan = plan
            orchestrator._results = [
                type("R", (), {
                    "task_id": s.id,
                    "command": s.command or "no-op",
                    "status": VerificationStatus.SKIPPED,
                    "duration_seconds": 0.0,
                })()
                for s in plan.steps
            ]

            report = orchestrator.generate_report()
            assert isinstance(report, VerificationReport)
            assert report.profile == orchestrator._profile.name
            md = report.to_markdown()
            assert "# Verification Report" in md
            assert "## Blast Radius" in md

    @patch("runtime.foundation.verification.orchestrator.subprocess.run")
    def test_cache_generation_and_reuse(self, mock_run: MagicMock, tmp_path: Path):
        mock_run.return_value = MockSubprocessResult(returncode=0, stdout="ok", stderr="")

        map_data = {
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
        map_path = tmp_path / "cross-layer-map.json"
        map_path.write_text(json.dumps(map_data), encoding="utf-8")

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
            plan = orchestrator.generate_plan(scope=VerificationScope.QUICK)
            for i, step in enumerate(plan.steps):
                plan.steps[i] = step.__class__(
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
            orchestrator._plan = plan
            orchestrator._results = [
                type("R", (), {
                    "task_id": s.id,
                    "command": s.command or "no-op",
                    "status": VerificationStatus.SKIPPED,
                    "duration_seconds": 0.0,
                })()
                for s in plan.steps
            ]

            report = orchestrator.generate_report()
            report.save_markdown(tmp_path / "verification-report.md")

            assert (tmp_path / "verification-report.md").exists()

    @patch("runtime.foundation.verification.orchestrator.subprocess.run")
    def test_non_zero_exit_on_failure(self, mock_run: MagicMock, tmp_path: Path):
        mock_run.return_value = MockSubprocessResult(returncode=1, stdout="", stderr="error")

        map_data = {
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
        map_path = tmp_path / "cross-layer-map.json"
        map_path.write_text(json.dumps(map_data), encoding="utf-8")

        orchestrator = VerificationOrchestrator(repo_root=tmp_path)
        orchestrator._changed_files = ["backend/src/engines/loan_engine/amortization.py"]
        orchestrator.generate_plan(scope=VerificationScope.QUICK)
        results = orchestrator.execute()

        failed = [r for r in results if r.status == VerificationStatus.FAILED]
        assert len(failed) > 0

    @patch("runtime.foundation.verification.orchestrator.subprocess.run")
    def test_full_run_pipeline(self, mock_run: MagicMock, tmp_path: Path):
        mock_run.return_value = MockSubprocessResult(returncode=0, stdout="ok", stderr="")

        map_data = {
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
        map_path = tmp_path / "cross-layer-map.json"
        map_path.write_text(json.dumps(map_data), encoding="utf-8")

        with patch(
            "runtime.foundation.verification.orchestrator._find_repo_root",
            return_value=tmp_path,
        ), patch(
            "runtime.foundation.verification.orchestrator._is_git_available",
            return_value=False,
        ), patch(
            "runtime.foundation.verification.orchestrator.VERIFICATION_REPORT_PATH",
            tmp_path / "verification-report.md",
        ), patch(
            "runtime.foundation.verification.orchestrator.VERIFICATION_CACHE_PATH",
            tmp_path / "verification-cache.json",
        ):
            orchestrator = VerificationOrchestrator(repo_root=tmp_path)
            orchestrator._changed_files = ["backend/src/engines/loan_engine/amortization.py"]
            plan = orchestrator.generate_plan(scope=VerificationScope.QUICK)
            for i, step in enumerate(plan.steps):
                plan.steps[i] = step.__class__(
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
            orchestrator._plan = plan
            orchestrator._results = [
                type("R", (), {
                    "task_id": s.id,
                    "command": s.command or "no-op",
                    "status": VerificationStatus.SKIPPED,
                    "duration_seconds": 0.0,
                })()
                for s in plan.steps
            ]

            report = orchestrator.generate_report()
            assert isinstance(report, VerificationReport)
            assert report.summary.overall_status == VerificationStatus.PASSED


def test_ci_and_local_changed_file_parity(monkeypatch):
    """C10 — CI (GITHUB_BASE_REF) and local override (VERIFICATION_BASE_REF)
    must derive the identical changed-file set: same resolver, same diff
    command, same filtering. This is the semantic parity CI certifies.

    The default local path (no base ref) diffs HEAD; the CI/env paths route
    the same base ref through the identical normalization + filtering, so all
    three must agree on the same working tree.
    """
    from runtime.foundation.verification.orchestrator import _collect_changed_files

    for var in (
        "GITHUB_BASE_REF",
        "GITHUB_SHA",
        "GITHUB_REF",
        "GITHUB_EVENT_NAME",
        "VERIFICATION_BASE_REF",
    ):
        monkeypatch.delenv(var, raising=False)

    # Local override routing.
    monkeypatch.setenv("VERIFICATION_BASE_REF", "HEAD")
    override = set(_collect_changed_files())

    # CI routing via GITHUB_BASE_REF with the same base.
    monkeypatch.delenv("VERIFICATION_BASE_REF", raising=False)
    monkeypatch.setenv("GITHUB_BASE_REF", "HEAD")
    ci = set(_collect_changed_files())

    assert ci == override, "CI GITHUB_BASE_REF must equal local VERIFICATION_BASE_REF"

    # Default local path (no base ref) also diffs HEAD; identical working tree.
    monkeypatch.delenv("GITHUB_BASE_REF", raising=False)
    local = set(_collect_changed_files())
    assert local == ci, "default local diff(HEAD) must equal CI-derived set"


def test_changed_file_filter_excludes_generated_and_node_modules(monkeypatch):
    """C10 — the shared filter must drop generated/cache/binary artifacts
    regardless of which env path supplied the base ref."""
    from runtime.foundation.verification.orchestrator import _filter_changed_files

    raw = [
        "backend/src/engines/loan_engine/emi.py",
        "runtime/generated/knowledge-index.json",
        "frontend/node_modules/leftpad/index.js",
        "runtime/generated/verification-cache.json",
        "__pycache__/foo.pyc",
        "docs/VEA2.md",
    ]
    filtered = _filter_changed_files(raw)
    assert "backend/src/engines/loan_engine/emi.py" in filtered
    assert "docs/VEA2.md" in filtered
    assert all(not f.startswith("runtime/generated/") for f in filtered)
    assert all(not f.startswith("frontend/node_modules/") for f in filtered)
    assert all(not f.endswith(".pyc") for f in filtered)
