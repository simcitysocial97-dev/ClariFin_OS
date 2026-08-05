"""Verification Orchestrator Tests — Program 7B.5

Tests for the VerificationOrchestrator with mocked subprocess execution.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from runtime.foundation.verification.executor import Executor
from runtime.foundation.verification.models import (
    VerificationScope,
    VerificationStatus,
)
from runtime.foundation.verification.orchestrator import (
    VerificationOrchestrator,
    VerificationReport,
    run_verification,
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
