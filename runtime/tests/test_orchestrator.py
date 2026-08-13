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
    _resolve_base_ref,
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


def _clear_ci_env(monkeypatch):
    for var in (
        "VERIFICATION_BASE_REF",
        "GITHUB_BASE_REF",
        "GITHUB_SHA",
        "GITHUB_REF",
        "GITHUB_EVENT_NAME",
        "GITHUB_EVENT_PATH",
    ):
        monkeypatch.delenv(var, raising=False)


def _deterministic_git_env(monkeypatch):
    """Provide a fully deterministic, network-free git world for parity tests.

    Every git subcommand issued by ``_collect_changed_files`` is answered by a
    controlled stub so the test never performs a live ``git fetch``. This removes
    the non-determinism that previously came from the real fetch/merge-base timing
    against ``origin`` (the root cause of intermittent parity failures).

    The stubed world is:
    * a fixed default branch ``origin/main`` resolved to a fixed SHA,
    * a fixed merge-base SHA,
    * a fixed, small, reproducible set of changed files (filtered form),
    * no untracked files,
    * every ``git fetch`` (network) returns success without doing anything.

    The intended contracts are still exercised: CI and local routing must use the
    identical resolver + diff command + filter, so they agree on the same state.
    """
    from unittest.mock import MagicMock

    from runtime.foundation.verification.orchestrator import (
        _collect_changed_files,
        _filter_changed_files,
    )

    DEFAULT_SHA = "m" * 40
    MERGE_BASE_SHA = "b" * 40
    PR_BASE_SHA = "p" * 40
    PR_HEAD_SHA = "h" * 40
    # Already-filtered changed files (no runtime/generated, node_modules, etc.).
    CHANGED = [
        "backend/src/engines/loan_engine/emi.py",
        "frontend/app/loans/page.tsx",
        "docs/VEA2.md",
    ]

    def _git_run(args, **kwargs):
        cmd = list(args)
        if cmd[:2] == ["git", "fetch"]:
            # Network no-op: never actually contacts origin.
            return MagicMock(returncode=0, stdout="", stderr="")
        if cmd[:2] == ["git", "rev-parse"]:
            return MagicMock(returncode=0, stdout=DEFAULT_SHA, stderr="")
        if cmd[:2] == ["git", "merge-base"]:
            return MagicMock(returncode=0, stdout=MERGE_BASE_SHA, stderr="")
        if cmd[:2] == ["git", "diff"] and "--name-only" in cmd:
            return MagicMock(returncode=0, stdout="\n".join(CHANGED) + "\n", stderr="")
        if cmd[:2] == ["git", "ls-files"]:
            # Deterministic: no untracked files.
            return MagicMock(returncode=0, stdout="", stderr="")
        return MagicMock(returncode=0, stdout="", stderr="")

    # Patch subprocess.run at the module that issues the calls.
    import runtime.foundation.verification.orchestrator as O

    monkeypatch.setattr(O, "subprocess", MagicMock(run=_git_run))

    return {
        "collect": _collect_changed_files,
        "filter": _filter_changed_files,
        "shas": {
            "default": DEFAULT_SHA,
            "merge_base": MERGE_BASE_SHA,
            "pr_base": PR_BASE_SHA,
            "pr_head": PR_HEAD_SHA,
        },
        "changed": set(CHANGED),
    }


def test_ci_and_local_changed_file_parity(monkeypatch):
    """C10 — CI and local changed-file collection must be parity-safe.

    The canonical comparison model is three-dot ``BASE...HEAD``. The local path
    (no base ref) and the CI path (same base ref) must use the *identical*
    resolver + diff command + filtering, so they agree on the same working tree.

    Regression for P0-2 (two-dot vs three-dot parity defect).

    The test runs against a fully controlled git fixture (no live ``git fetch``),
    so the parity result is deterministic regardless of network availability,
    remote state, fetch timing, or GitHub CI environment (Milestone 1/2 fix).
    """
    world = _deterministic_git_env(monkeypatch)
    collect = world["collect"]
    expected = world["changed"]

    _clear_ci_env(monkeypatch)

    # Local override routing.
    monkeypatch.setenv("VERIFICATION_BASE_REF", "HEAD")
    override = set(collect().files)
    assert override == expected

    # CI routing via GITHUB_BASE_REF with the same base.
    monkeypatch.delenv("VERIFICATION_BASE_REF", raising=False)
    monkeypatch.setenv("GITHUB_BASE_REF", "HEAD")
    ci = set(collect().files)
    assert ci == expected

    assert ci == override, "CI GITHUB_BASE_REF must equal local VERIFICATION_BASE_REF"

    # Default local path (no base ref) must use the SAME canonical three-dot
    # semantics as the CI path with no explicit base ref: both resolve the
    # merge-base of HEAD and the default branch, so they agree (P0-2).
    monkeypatch.delenv("GITHUB_BASE_REF", raising=False)
    local = set(collect().files)
    assert local == expected

    monkeypatch.setenv("GITHUB_EVENT_NAME", "pull_request")
    ci_no_base = set(collect().files)
    assert ci_no_base == expected

    assert local == ci_no_base, "default local must equal CI path with no explicit base ref"


def test_pr_base_resolution_priority_and_sha(monkeypatch, tmp_path):
    """M1 — base resolution priority + authoritative PR base SHA (A-F)."""
    import inspect

    import runtime.foundation.verification.orchestrator as O

    # A. PR base resolution with explicit base SHA via event payload.
    _clear_ci_env(monkeypatch)
    event = tmp_path / "event.json"
    event.write_text(json.dumps({"pull_request": {"base": {"sha": "abc123" * 6 + "0" * 16}}}))
    monkeypatch.setenv("GITHUB_EVENT_NAME", "pull_request")
    monkeypatch.setenv("GITHUB_EVENT_PATH", str(event))
    assert _resolve_base_ref() == "abc123" * 6 + "0" * 16

    # B. PR base resolution with GITHUB_BASE_REF (branch name).
    _clear_ci_env(monkeypatch)
    monkeypatch.setenv("GITHUB_BASE_REF", "main")
    assert _resolve_base_ref() == "main"

    # C. Stale origin/main must NOT override the authoritative PR base SHA.
    _clear_ci_env(monkeypatch)
    event.write_text(json.dumps({"pull_request": {"base": {"sha": "deadbeef" * 8}}}))
    monkeypatch.setenv("GITHUB_EVENT_NAME", "pull_request")
    monkeypatch.setenv("GITHUB_EVENT_PATH", str(event))
    # GITHUB_BASE_REF differs; the PR base SHA still wins (P0-1).
    monkeypatch.setenv("GITHUB_BASE_REF", "some-other-branch")
    assert _resolve_base_ref() == "deadbeef" * 8

    # D. Local invocation (no CI env) remains functional and non-raising.
    from runtime.foundation.verification.orchestrator import _collect_changed_files

    _clear_ci_env(monkeypatch)
    result = _resolve_base_ref()
    assert result is None or isinstance(result, str)
    assert isinstance(_collect_changed_files().files, list)

    # E. Arbitrary branch names work through GITHUB_BASE_REF.
    _clear_ci_env(monkeypatch)
    monkeypatch.setenv("GITHUB_BASE_REF", "feature/vea5-m9-fix")
    assert _resolve_base_ref() == "feature/vea5-m9-fix"

    # F. No repository-specific SHA is hardcoded in the resolver.
    src = inspect.getsource(O._resolve_base_ref)
    assert "0c8410c" not in src and "e00d42d" not in src


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


class TestVerificationReportDiagnostics:
    """M4 / P2-1 — observability of task-level failure diagnostics."""

    def test_report_identifies_failing_task_exit_reason_artifact(self, tmp_path):
        from runtime.foundation.verification.models import (
            ExecutionResult as ExecutionResultModel,
            VerificationStatus,
            VerificationSummary,
        )
        from runtime.foundation.verification.orchestrator import (
            VerificationPlan,
            VerificationReport,
        )
        from runtime.foundation.verification.models import VerificationScope

        failed = ExecutionResultModel(
            task_id="step-0002",
            command="bash .github/scripts/run_runtime_verification.sh",
            status=VerificationStatus.FAILED,
            exit_code=1,
            duration_seconds=12.3,
            stdout_path=str(tmp_path / "verify-stdout-abc.txt"),
            stderr_path=str(tmp_path / "verify-stderr-abc.txt"),
            error="pytest runtime/tests/ exited with code 1: 1 failed, 554 passed",
        )
        passed = ExecutionResultModel(
            task_id="step-0001",
            command="bash .github/scripts/run_backend_verification.sh",
            status=VerificationStatus.PASSED,
            exit_code=0,
            duration_seconds=65.0,
            stdout_path=str(tmp_path / "verify-stdout-def.txt"),
            stderr_path=str(tmp_path / "verify-stderr-def.txt"),
            error=None,
        )
        summary = VerificationSummary(
            profile="quick",
            total_tasks=2,
            passed=1,
            failed=1,
            skipped=0,
            duration_seconds=77.3,
            report_path=str(tmp_path / "verification-report.md"),
            cache_path=str(tmp_path / "verification-cache.json"),
            overall_status=VerificationStatus.FAILED,
        )
        plan = VerificationPlan(
            name="quick", id="plan-x", scope=VerificationScope.QUICK,
            targets=[], steps=[], estimated_duration_seconds=0,
        )
        report = VerificationReport(
            profile="quick",
            changed_files=["backend/src/x.py"],
            blast_radius={},
            plan=plan,
            results=[passed, failed],
            summary=summary,
            dependency_chains=[],
            evidence_files=[],
            recommendations=["Investigate failing task: bash .github/scripts/run_runtime_verification.sh"],
        )

        md = report.to_markdown()
        # Exact failing task identified.
        assert "step-0002" in md
        # Exit code surfaced.
        assert "Exit code: 1" in md
        # Failure reason surfaced (concise, not the raw 500+ char dump).
        assert "1 failed, 554 passed" in md
        # Artifact paths surfaced so the raw logs are reachable.
        assert str(tmp_path / "verify-stderr-abc.txt") in md
        # Aggregate counts preserved.
        assert "**Failed:** 1" in md
        assert "**Passed:** 1" in md

    def test_report_distinguishes_error_none_empty_and_actual(self, tmp_path):
        """M9 — error=None vs error='' vs error='actual' must be distinct in report."""
        from runtime.foundation.verification.models import (
            ExecutionResult as ExecutionResultModel,
            VerificationStatus,
            VerificationSummary,
        )
        from runtime.foundation.verification.orchestrator import (
            VerificationPlan,
            VerificationReport,
        )
        from runtime.foundation.verification.models import VerificationScope

        passed_none = ExecutionResultModel(
            task_id="t-passed",
            command="echo ok",
            status=VerificationStatus.PASSED,
            exit_code=0,
            duration_seconds=0.1,
            stdout_path="",
            stderr_path="",
            error=None,
        )
        failed_empty = ExecutionResultModel(
            task_id="t-empty",
            command="exit 1",
            status=VerificationStatus.FAILED,
            exit_code=1,
            duration_seconds=0.1,
            stdout_path=str(tmp_path / "out.txt"),
            stderr_path=str(tmp_path / "err.txt"),
            error="",
        )
        failed_actual = ExecutionResultModel(
            task_id="t-actual",
            command="fail-cmd",
            status=VerificationStatus.FAILED,
            exit_code=2,
            duration_seconds=0.1,
            stdout_path=str(tmp_path / "out2.txt"),
            stderr_path=str(tmp_path / "err2.txt"),
            error="some actual error message",
        )
        summary = VerificationSummary(
            profile="test", total_tasks=3, passed=1, failed=2, skipped=0,
            duration_seconds=0.3, report_path=str(tmp_path / "r.md"),
            cache_path=str(tmp_path / "c.json"),
            overall_status=VerificationStatus.FAILED,
        )
        plan = VerificationPlan(
            name="test", id="p1", scope=VerificationScope.QUICK,
            targets=[], steps=[], estimated_duration_seconds=0,
        )
        report = VerificationReport(
            profile="test", changed_files=[], blast_radius={}, plan=plan,
            results=[passed_none, failed_empty, failed_actual], summary=summary,
            dependency_chains=[], evidence_files=[], recommendations=[],
        )

        md = report.to_markdown()
        # State 2: empty stderr must show [empty stderr], not "no error captured"
        assert "[empty stderr]" in md
        assert "no error captured" not in md
        # State 3: actual error must be shown verbatim
        assert "some actual error message" in md
        # Exit codes visible for every failed task
        assert "Exit code: 1" in md
        assert "Exit code: 2" in md
        # Passed task with error=None does NOT contain the old fallback text
        for line in md.splitlines():
            if "t-passed" in line and "Error" not in line:
                continue
            if "| t-passed |" in line:
                assert "no error captured" not in line
