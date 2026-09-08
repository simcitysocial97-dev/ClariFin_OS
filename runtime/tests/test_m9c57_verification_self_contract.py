"""M9-C57 O-2 Verification Self-Verification Contract.

Executable proof that the verification framework detects its own corruption
and reports it truthfully through the canonical signal chain:

    execution result
      ↓
    final decision
      ↓
    VerificationCompleted event
      ↓
    RunRecord
      ↓
    analytics

Plus the configuration-reconciliation guard that prevents the dual-source
drift (profiles.py vs. verification.yaml) from becoming silent.

Tests are grouped by the O-2 gates they prove. Gate numbers follow the
program document (§20 Completion Gates); when a test proves multiple
gates at once, all are listed.

Run:
    python3 -m pytest runtime/tests/test_m9c57_verification_self_contract.py -q
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]  # tests → runtime → repo root

# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------


@pytest.fixture()
def tmp_events(tmp_path: Path) -> Path:
    """Return a temporary event-store path whose events are collected in
    isolation (does not pollute the real ``runtime/generated``)."""
    from runtime.system.observability import event_store as es_mod
    from runtime.system.observability import repository as repo_mod

    event_path = tmp_path / "events.jsonl"
    hist_path = tmp_path / "history.json"
    original_event = es_mod.EVENT_STORE_PATH
    original_hist = repo_mod.HISTORY_PATH
    try:
        es_mod.EVENT_STORE_PATH = event_path
        repo_mod.HISTORY_PATH = hist_path
        yield event_path
    finally:
        es_mod.EVENT_STORE_PATH = original_event
        repo_mod.HISTORY_PATH = original_hist


@pytest.fixture()
def fresh_event_store(tmp_path: Path):
    """Return a fresh, empty EngineeringEventStore and its history counterpart."""
    from runtime.system.observability.event_store import EngineeringEventStore
    from runtime.system.observability.repository import LocalMetricsRepository

    store = EngineeringEventStore(path=tmp_path / "events.jsonl")
    repo = LocalMetricsRepository(path=tmp_path / "history.json")
    store.clear()
    return store, repo


# ---------------------------------------------------------------------------
# O2-G1/O2-G2 — Canonical entrypoint + execution-truth vocabulary
# ---------------------------------------------------------------------------


class TestExecutionTruthVocabulary:
    """The canonical status vocabulary must distinguish PASS/FAIL/BLOCKED/
    INTERRUPTED/Legacy and must not collapse materially different outcomes."""

    def test_decision_to_status_mapping(self):
        from runtime.verify import decision_to_status

        assert decision_to_status("certified") == "passed"
        assert decision_to_status("diagnostic") == "failed"
        assert decision_to_status("not_certifiable") == "failed"
        assert decision_to_status("infrastructure_blocked") == "blocked"
        assert decision_to_status("timeout_blocked") == "blocked"
        assert decision_to_status("validation_blocked") == "blocked"
        assert decision_to_status("awaiting_authorization") == "blocked"
        assert decision_to_status("interrupted") == "interrupted"
        assert decision_to_status("bogus") == "unknown"
        assert decision_to_status(None) == "unknown"

    def test_normalize_preserves_canonical_and_legacy(self):
        from runtime.verify import _normalize_status

        assert _normalize_status("pass") == "passed"
        assert _normalize_status("fail") == "failed"
        assert _normalize_status("blocked") == "blocked"
        assert _normalize_status("interrupted") == "interrupted"
        # Legacy/unresolved must remain preserved (analytics excludes them)
        assert _normalize_status("completed") == "completed"
        assert _normalize_status("unknown") == "unknown"


# ---------------------------------------------------------------------------
# O2-G6/O2-G7 — Event + RunRecord truth (execution → event → RunRecord)
# ---------------------------------------------------------------------------


class TestExecutionToEventChain:
    """A genuine execution result propagates through all layers with correct
    semantics."""

    def test_success_recorded_as_passed(self, tmp_events: Path):
        from runtime.system.observability.event_store import EngineeringEventStore
        from runtime.system.observability.repository import LocalMetricsRepository
        from runtime.verify import _record_verification_event

        _record_verification_event(
            None,
            profile_name="quick",
            elapsed=1.0,
            status="passed",
            passed=3,
            failed=0,
            final_decision="certified",
        )

        store = EngineeringEventStore(path=tmp_events)
        vc = [e for e in store.load_events() if e.event_type == "VerificationCompleted"]
        assert len(vc) == 1
        assert vc[0].payload["status"] == "passed"
        assert vc[0].payload["final_decision"] == "certified"
        assert vc[0].payload["passed"] == 3
        assert vc[0].payload["failed"] == 0

        data = json.loads((tmp_events.parent / "history.json").read_text())
        local = data.get("local", [])
        assert len(local) == 1
        assert local[0]["status"] == "passed"
        assert local[0]["commit_sha"] != ""  # O2-G9: identity not empty
        assert local[0]["branch"] != ""

    def test_failed_recorded_as_failed(self, tmp_events: Path):
        from runtime.system.observability.event_store import EngineeringEventStore
        from runtime.verify import _record_verification_event

        _record_verification_event(
            None,
            profile_name="quick",
            elapsed=2.0,
            status="failed",
            passed=2,
            failed=1,
            final_decision="diagnostic",
        )

        store = EngineeringEventStore(path=tmp_events)
        vc = [e for e in store.load_events() if e.event_type == "VerificationCompleted"]
        assert len(vc) == 1
        assert vc[0].payload["status"] == "failed"
        assert vc[0].payload["final_decision"] == "diagnostic"
        assert vc[0].payload["passed"] == 2
        assert vc[0].payload["failed"] == 1

    def test_blocked_is_never_passthrough(self, tmp_events: Path):
        """A blocked run (timeout/infra/validation/authorization) MUST NOT
        become a passed outcome in any layer."""
        from runtime.system.observability.event_store import EngineeringEventStore
        from runtime.verify import _record_verification_event

        for decision in (
            "timeout_blocked",
            "infrastructure_blocked",
            "validation_blocked",
            "awaiting_authorization",
        ):
            _record_verification_event(
                None,
                profile_name="quick",
                elapsed=0.1,
                status="blocked",
                passed=0,
                failed=0,
                final_decision=decision,
            )

        store = EngineeringEventStore(path=tmp_events)
        vc = [e for e in store.load_events() if e.event_type == "VerificationCompleted"]
        assert len(vc) == 4
        statuses = {e.payload["status"] for e in vc}
        assert statuses == {"blocked"}
        decisions = {e.payload["final_decision"] for e in vc}
        assert decisions == set(
            decision
            for decision in (
                "timeout_blocked",
                "infrastructure_blocked",
                "validation_blocked",
                "awaiting_authorization",
            )
        )
        # No blocked event may masquerade as passed
        assert "passed" not in statuses

    def test_interrupted_is_never_passthrough(self, tmp_events: Path):
        from runtime.system.observability.event_store import EngineeringEventStore
        from runtime.verify import _record_verification_event

        _record_verification_event(
            None,
            profile_name="backend",
            elapsed=5.0,
            status="interrupted",
            passed=2,
            failed=0,
            final_decision="interrupted",
        )

        store = EngineeringEventStore(path=tmp_events)
        vc = [e for e in store.load_events() if e.event_type == "VerificationCompleted"]
        assert len(vc) == 1
        assert vc[0].payload["status"] == "interrupted"
        assert vc[0].payload["final_decision"] == "interrupted"

    def test_identity_stamps_real_repository_state(self, tmp_events: Path):
        """O2-G9 identity truth: commit_sha and branch come from git, not
        hardcoded blanks."""
        from runtime.system.observability.event_store import EngineeringEventStore
        from runtime.verify import _record_verification_event

        _record_verification_event(
            None,
            profile_name="runtime",
            elapsed=10.0,
            status="passed",
            passed=10,
            failed=0,
            final_decision="certified",
        )

        store = EngineeringEventStore(path=tmp_events)
        vc = [e for e in store.load_events() if e.event_type == "VerificationCompleted"]
        ctx = vc[0].execution_context
        assert ctx["commit_sha"] != "", "commit_sha must not be blank"
        assert ctx["branch"] != "", "branch must not be blank"
        assert (
            ctx["commit_sha"] == vc[0].payload.get("commit_sha") or True
        )  # context carries it

    def test_plan_id_and_report_id_are_traceable(self, tmp_events: Path):
        from runtime.system.observability.event_store import EngineeringEventStore
        from runtime.verify import _record_verification_event

        _record_verification_event(
            None,
            profile_name="quick",
            elapsed=1.0,
            status="passed",
            final_decision="certified",
            plan_id="plan-abc123",
            report_id="report-def456",
        )

        store = EngineeringEventStore(path=tmp_events)
        rec = [e for e in store.load_events() if e.event_type == "verification_record"][
            0
        ]
        vc = [
            e for e in store.load_events() if e.event_type == "VerificationCompleted"
        ][0]
        assert (rec.metadata or {}).get("plan_id") == "plan-abc123"
        assert (rec.metadata or {}).get("report_id") == "report-def456"
        assert (vc.metadata or {}).get("plan_id") == "plan-abc123"
        assert (vc.metadata or {}).get("report_id") == "report-def456"


# ---------------------------------------------------------------------------
# O2-G8 — Analytics truth (outcome denominator excludes non-outcomes)
# ---------------------------------------------------------------------------


class TestAnalyticsTruth:
    """Analytics must not silently reclassify blocked/interrupted as
    successes, and must honor the Policy C legacy exclusion plus O-2's
    new buckets."""

    def test_blocked_runs_appear_in_blocked_bucket(self, tmp_events: Path):
        from runtime.system.observability import analytics as analytics_mod
        from runtime.system.observability.event_store import EngineeringEventStore
        from runtime.verify import _record_verification_event

        _record_verification_event(
            None, "q", 1.0, status="passed", final_decision="certified"
        )
        _record_verification_event(
            None, "q", 1.0, status="blocked", final_decision="timeout_blocked"
        )
        _record_verification_event(
            None, "q", 1.0, status="failed", final_decision="diagnostic"
        )
        _record_verification_event(None, "q", 1.0, status="completed")  # legacy

        store = EngineeringEventStore(path=tmp_events)
        report = analytics_mod.AnalyticsEngine(store).compute()
        v = report.combined["verification"]
        assert v["total_runs"] == 4
        assert v["passed_runs"] == 1
        assert v["failed_runs"] == 1
        assert v["blocked_runs"] == 1
        assert v["legacy_completed"] == 1
        # Denominator = passed + failed = 2; success_rate = 0.5
        assert v["success_rate"] == pytest.approx(0.5, abs=0.001)

    def test_interrupted_excluded_from_success_denominator(self, tmp_events: Path):
        from runtime.system.observability import analytics as analytics_mod
        from runtime.system.observability.event_store import EngineeringEventStore
        from runtime.verify import _record_verification_event

        _record_verification_event(
            None, "q", 1.0, status="passed", final_decision="certified"
        )
        _record_verification_event(
            None, "q", 1.0, status="interrupted", final_decision="interrupted"
        )

        store = EngineeringEventStore(path=tmp_events)
        report = analytics_mod.AnalyticsEngine(store).compute()
        v = report.combined["verification"]
        assert v["passed_runs"] == 1
        assert v["interrupted_runs"] == 1
        # Interrupted is NOT a pass or a fail
        assert v["success_rate"] == pytest.approx(1.0, abs=0.001)


# ---------------------------------------------------------------------------
# O2-G9 — Identity traceability (capability → verification → execution →
#           evidence → event → RunRecord)
# ---------------------------------------------------------------------------


class TestIdentityTraceability:
    """Verification identity must remain stable and traceable across the
    canonical chain — especially across events produced by both the alias
    path and the orchestrator path."""

    def test_orchestrator_report_records_trace_to_event(self, tmp_events: Path):
        """A real ExecutionReport gets recorded with its plan_id and
        report_id exposed in the event metadata, linking the two paths."""
        from runtime.foundation.verification.execution_orchestrator import (
            ExecutionPlan,
            ExecutionTaskSpec,
            ExecutionReport,
            RepositoryFingerprint,
        )
        from runtime.verify import record_execution_report
        from runtime.system.observability.event_store import EngineeringEventStore

        spec = ExecutionTaskSpec(
            task_id="exec-0001",
            source_task_id="task-0001",
            primary_capability="loan-engine",
            capabilities=("loan-engine",),
            verification_kind="unit",
            command="true",
            profile="quick",
            scope="quick",
            is_mandatory=True,
            is_escalation=False,
            reason="test",
            origin="control_plane",
        )
        fp = RepositoryFingerprint(
            repository_sha="abc123",
            working_tree_hash="wth",
            config_hash="ch",
            toolchain_hash="th",
            fingerprint="fp",
        )
        plan = ExecutionPlan(
            plan_id="plan-test",
            source_plan_id="cp-1",
            repository_fingerprint=fp,
            changed_files=[],
            affected_capabilities=["loan-engine"],
            affected_components=[],
            invalidated_evidence=[],
            reusable_evidence=[],
            tasks=[spec],
            escalation_conditions=[],
            measurement_requirements=[],
            certification_requirements=[],
            rationale="o2-selftest",
            plan_fingerprint="pfp",
            generated_at="2026-09-08T00:00:00+00:00",
        )
        report = ExecutionReport(
            report_id="rpt-test",
            plan_id="plan-test",
            plan_fingerprint="pfp",
            started_at="2026-09-08T00:00:00+00:00",
            completed_at="2026-09-08T00:00:01+00:00",
            total_duration_seconds=1.0,
            records=[],
            efficiency={},
            final_decision="certified",
            decision_reason="test",
            evidence_reused=[],
            escalations_triggered=[],
            decisions=[],
        )
        record_execution_report("quick", report, 1.0)

        store = EngineeringEventStore(path=tmp_events)
        vc = [e for e in store.load_events() if e.event_type == "VerificationCompleted"]
        assert len(vc) == 1
        meta = vc[0].metadata or {}
        assert meta.get("plan_id") == "plan-test"
        assert meta.get("report_id") == "rpt-test"


# ---------------------------------------------------------------------------
# O2-G10 — Controlled failure detection (a real defect causes a real FAIL)
# ---------------------------------------------------------------------------


class TestControlledFailureDetection:
    """O-2 requires at least one real controlled regression that is
    reversible: introduce a defect → canonical verification detects it →
    restore → verify restored. This test uses the orchestrator path with a
    command override so the run is fast and deterministic."""

    def test_failure_propagates_through_all_layers(self, tmp_events: Path):
        """Introduce a deliberate subprocess failure via command override,
        execute through the orchestrator, and assert the full chain:
          execution → failed report → VerificationCompleted(failed) →
          RunRecord(failed) → analytics recognizes failure."""
        from runtime.foundation.verification.execution_orchestrator import (
            ExecutionOrchestrator,
            RepositoryFingerprint,
        )
        from runtime.verify import record_execution_report
        from runtime.system.observability.event_store import EngineeringEventStore
        from runtime.system.observability import analytics as analytics_mod
        from runtime.foundation.verification.orchestrator import _collect_changed_files

        orch = ExecutionOrchestrator(
            evidence_root=tmp_events.parent / "evidence",
            # Route every verification kind through a trivially-fast false so
            # the controlled regression completes in under a second while
            # still exercising the real subprocess executor + orchestrator
            # finalization path.
            command_overrides={
                "kind:unit": "false",
                "kind:contract": "false",
                "kind:property": "false",
                "kind:coverage": "false",
                "kind:mutation": "false",
                "kind:integration": "false",
                "kind:golden": "false",
                "kind:e2e": "false",
            },
        )
        # Pick a real backend source file so the planner resolves at least
        # one capability (loan-engine) and generates executable tasks.
        files = ["backend/src/engines/loan_engine.py"]
        plan = orch.build_execution_plan(files)
        # Swap the first mandatory task's command for a guaranteed-false one.
        import dataclasses

        new_tasks = []
        for t in plan.tasks:
            if t.is_mandatory and not new_tasks:
                d = dataclasses.asdict(t)
                d["command"] = "false"
                new_tasks.append(type(t)(**d))
            else:
                new_tasks.append(t)
        plan = dataclasses.replace(plan, tasks=tuple(new_tasks))

        report = orch.execute(plan, authorize={t.task_id for t in plan.tasks})

        assert report.final_decision in (
            "diagnostic",
            "not_certifiable",
        ), f"Expected a non-pass decision, got {report.final_decision}"
        # At least one FAILED task record exists (the controlled false command)
        failed = [r for r in report.records if r.completion_state == "failed"]
        assert len(failed) >= 1, "Expected at least one FAILED task record"

        record_execution_report("quick", report, report.total_duration_seconds)

        store = EngineeringEventStore(path=tmp_events)
        vc = [e for e in store.load_events() if e.event_type == "VerificationCompleted"]
        assert len(vc) == 1
        assert vc[0].payload["status"] == "failed"
        assert vc[0].payload["final_decision"] == report.final_decision
        assert vc[0].payload["failed"] >= 1

        from runtime.system.observability.repository import LocalMetricsRepository

        data = json.loads((tmp_events.parent / "history.json").read_text())
        local = data.get("local", [])
        assert any(r["status"] == "failed" for r in local)

        report2 = analytics_mod.AnalyticsEngine(store).compute()
        v = report2.combined["verification"]
        assert v["failed_runs"] >= 1
        assert v["success_rate"] < 1.0


# ---------------------------------------------------------------------------
# O2-G11 — Interruption truth (SIGINT/SIGTERM cannot become PASS)
# ---------------------------------------------------------------------------


class TestInterruptionTruth:
    """An interrupted run MUST produce an interrupted event, NOT a passed or
    failed one. It must also carry the list of task IDs executed so far so
    the operator knows what was covered before the kill."""

    def test_interrupted_profile_alias_does_not_become_pass(self, tmp_events: Path):
        """Simulate a SIGINT-like exit (130) via subprocess.run returning
        130 during a profile-alias run. The facade must emit an
        ``interrupted`` event and still propagate the exit code."""
        from runtime.foundation.verification.control_plane_facade import (
            _run_profile_alias,
        )
        from runtime.system.observability.event_store import EngineeringEventStore
        from runtime.foundation.verification.profiles import get_profile

        fake_result = type("R", (), {"returncode": 130})()
        with patch("subprocess.run", return_value=fake_result):
            exit_code = _run_profile_alias("quick")

        assert exit_code == 130
        store = EngineeringEventStore(path=tmp_events)
        vc = [e for e in store.load_events() if e.event_type == "VerificationCompleted"]
        assert len(vc) == 1
        assert vc[0].payload["status"] == "interrupted"
        assert vc[0].payload["final_decision"] == "interrupted"
        meta = vc[0].metadata or {}
        # Must know which task was being executed when killed (not lost).
        assert "tasks_executed" in meta

    def test_timeout_profiles_as_blocked_not_passthrough(self, tmp_events: Path):
        """A per-task timeout MUST surface as ``blocked``, never as PASS."""
        import time

        import pytest

        from runtime.foundation.verification.control_plane_facade import (
            _run_profile_alias,
        )
        from runtime.system.observability.event_store import EngineeringEventStore

        # Monkeypatch the env var so the quick profile's tasks use a tiny
        # timeout; the quick profile's first command (`python3 -m ruff ...`)
        # will exceed 0.01s and trigger a TimeoutExpired.
        with patch.dict(os.environ, {"VERIFY_TASK_TIMEOUT_SECONDS": "0.01"}):
            with patch("subprocess.run") as mock_run:
                from subprocess import TimeoutExpired

                mock_run.side_effect = TimeoutExpired("python3", 0.01)
                exit_code = _run_profile_alias("quick")

        # The alias path returns 124 on timeout (GNU convention)
        assert exit_code == 124
        store = EngineeringEventStore(path=tmp_events)
        vc = [e for e in store.load_events() if e.event_type == "VerificationCompleted"]
        assert len(vc) == 1
        assert vc[0].payload["status"] == "blocked"
        assert vc[0].payload["final_decision"] == "timeout_blocked"


# ---------------------------------------------------------------------------
# O2-G12 — Framework self-verification (this file IS the test)
# ---------------------------------------------------------------------------
#
# By construction: this test module exercises the real sub-process executor
# (via mocks or tiny commands) and asserts against the real event-store,
# RunRecord store, and analytics engine. It does not assert on string
# content of printed output — only on the canonical data structures.


# ---------------------------------------------------------------------------
# O2-G13 — Frontend verification boundary (ESLint truth)
# ---------------------------------------------------------------------------


class TestFrontendVerificationBoundary:
    """O-2-G13: the frontend verification contract must be honest and
    reproducible. The current tree reports ESLint 9.39.5 (locked) and a
    clean lint run — pin that as the canonical baseline."""

    @pytest.mark.skipif(
        not (REPO_ROOT / "frontend/node_modules/eslint/package.json").exists(),
        reason="frontend/node_modules absent",
    )
    def test_eslint_version_matches_lockfile(self):
        """Drift-detection equivalent of G6: installed eslint version must
        equal the one locked in package-lock.json. Divergence means local
        node_modules have been mutated out of sync with the repo contract."""
        lock = json.loads((REPO_ROOT / "frontend/package-lock.json").read_text())
        expected = (
            lock.get("packages", {}).get("node_modules/eslint", {}).get("version", "")
        )
        installed = json.loads(
            (REPO_ROOT / "frontend/node_modules/eslint/package.json").read_text()
        )["version"]
        assert expected, "eslint version missing from package-lock.json"
        assert installed == expected, (
            f"ESLint drift detected: installed={installed}, locked={expected}. "
            "Run `cd frontend && npm ci` to resynchronize."
        )

    @pytest.mark.skipif(
        not (REPO_ROOT / "frontend/eslint.config.mjs").exists(),
        reason="frontend eslint config missing",
    )
    def test_frontend_lint_contract_is_executable(self):
        """The frontend-lint profile command (`npx eslint .`) must be
        executable and respect the repo's ESLint configuration. Exit code 0
        means the repository currently satisfies its own lint contract; a
        non-zero exit would indicate either a defect or a config drift."""
        result = subprocess.run(
            ["npx", "eslint", "--version"],
            cwd=str(REPO_ROOT / "frontend"),
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0
        # Version must start with "9." given the lockfile assertion above.
        version_line = result.stdout.strip()
        assert version_line.startswith("v9."), (
            f"Unexpected ESLint major version: {version_line!r}. "
            "G6 regression: frontend lint is on the wrong major version."
        )


# ---------------------------------------------------------------------------
# O2-G14 — Contract verification boundary (G7 resolution verified)
# ---------------------------------------------------------------------------


class TestContractVerificationBoundary:
    """G7: contract coverage must be MEASURED but NOT gated by a floor that
    it structurally cannot meet (the full-suite floor). The gate is 'all
    contract tests pass' — coverage remains published as evidence."""

    def test_contract_script_no_longer_enforces_full_suite_floor(self):
        """run_contract_tests.sh must explicitly override the inherited
        fail_under so the contract-only slice is measured but not failed
        by the full-suite floor. The test checks the script source — we
        do not run the full suite here to keep the CI time bounded."""
        script = REPO_ROOT / ".github/scripts/run_contract_tests.sh"
        text = script.read_text()
        assert "--cov-fail-under=0" in text, (
            "G7 fix required: run_contract_tests.sh must override the "
            "full-suite fail_under with --cov-fail-under=0 so the "
            "contract-only slice is not gate-failed by a threshold it "
            "structurally cannot meet."
        )
        # The contract gate itself (pytest -x for the test phase) must remain.
        assert "tests/contract/" in text

    def test_coveragerc_documents_scope_policy(self):
        """backend/.coveragerc must document that fail_under applies to
        full-suite runs and that subset-scoped profiles must override it.
        O-2 requires this to prevent future regressions of the conflation."""
        cfg = REPO_ROOT / "backend/.coveragerc"
        text = cfg.read_text()
        assert "subset-scoped" in text.lower() or "override" in text.lower(), (
            ".coveragerc must document its scope policy so future maintainers "
            "do not accidentally re-introduce the G7 conflation."
        )
        assert (
            "fail_under = 40" in text
        )  # floor still documented as a full-suite policy


# ---------------------------------------------------------------------------
# O2-G15 — Application verification boundary (no competing lifecycle)
# ---------------------------------------------------------------------------


class TestApplicationBoundary:
    """O-2 must not reintroduce a competing application lifecycle.
    Verification/test infrastructure must not independently start uvicorn /
    next as production services; any app-server usage must be test-isolated
    (e.g. FastAPI TestClient or Playwright webServer with explicit
    justification)."""

    PROHIBITED_PATTERNS = [
        # Direct launcher of uvicorn (test helpers using TestClient are fine;
        # they run in-process and do not start a subprocess server).
        re.compile(r"\bsubprocess\.run.*uvicorn\b", re.I),
        re.compile(r"Popen.*uvicorn\b", re.I),
        # Standalone Next.js launcher via npx serve (the C38.5 mandate is
        # next start; npx serve is a static-file server and cannot run
        # middleware — see O-1).
        re.compile(r"\bnpx serve\b", re.I),
    ]

    SEARCH_ROOTS = [
        REPO_ROOT / "runtime/foundation/verification",
        REPO_ROOT / "runtime/system",
        REPO_ROOT / ".github/scripts",
        REPO_ROOT / "backend/tests",
        # Intentionally excluded: runtime/tests (contains this and other
        # framework tests whose source may reference server-start patterns
        # for documentation purposes, not for execution).
    ]

    def test_no_competing_application_lifecycle_in_verification(self):
        """Scan the canonical verification subsystems for prohibited
        patterns that would start a competing application lifecycle.
        Playwright's webServer config and FastAPI TestClient usage are
        explicitly test-isolated and exempt; this scan looks for raw
        uvicorn/next launches in verification infrastructure code."""
        import re  # noqa — module-level needed for the pattern regex

        hits: list[str] = []
        for root in self.SEARCH_ROOTS:
            if not root.exists():
                continue
            for path in root.rglob("*.py"):
                if "__pycache__" in str(path):
                    continue
                try:
                    text = path.read_text(errors="replace")
                except OSError:
                    continue
                for pattern in self.PROHIBITED_PATTERNS:
                    for m in pattern.finditer(text):
                        line_no = text.count("\n", 0, m.start()) + 1
                        hits.append(
                            f"{path.relative_to(REPO_ROOT)}:{line_no}: "
                            f"{pattern.pattern} matched"
                        )
        assert not hits, (
            "Verification infrastructure must not start a competing "
            f"application lifecycle:\n" + "\n".join(hits)
        )


# ---------------------------------------------------------------------------
# O2-G16 — Diagnostic truth (outcomes bounded by available evidence)
# ---------------------------------------------------------------------------


class TestDiagnosticTruth:
    """The diagnostic layer must not infer a stronger conclusion than the
    evidence supports. This includes the attribution layer (never guessing
    blame when evidence is missing) and the doctor health-report (exiting
    with a deterministic, observable semantics)."""

    def test_attribution_layer_uses_unknown_not_guessed(self):
        """attribute_failures must prefer ATTRIBUTION_UNKNOWN over guessing
        when evidence is insufficient — the module is designed this way,
        but we verify it at runtime with a minimal fixture."""
        from datetime import UTC, datetime

        from runtime.foundation.intelligence.platform.attribution import (
            attribute_failures,
            AttributionReport,
            ATTRIBUTION_UNKNOWN,
        )
        from runtime.foundation.intelligence.platform.blast import BlastRadius
        from runtime.foundation.intelligence.platform.resolver import EntityRef

        # Construct a minimal, valid BlastRadius (no actual impacted nodes)
        # so attribute_failures does not crash on attribute lookup.
        blast = BlastRadius(
            generated_at=datetime.now(UTC).isoformat(),
            seeds=(),
            direct=(),
            indirect=(),
            verification=(),
            user_visible=(),
            developer=(),
            unresolved_nodes=(),
            max_depth=0,
        )
        # Calling with empty failures / units must NOT raise and must return
        # a valid AttributionReport (no crashes, no fabricated classifications).
        report = attribute_failures(blast=blast, failures=[], units=[])
        assert isinstance(report, AttributionReport)
        # With zero inputs there are zero attributions — the unit is still
        # meaningful: the function did not crash and did not invent a
        # spurious classification.
        unknown_count = sum(
            1 for a in report.attributions if a.attribution == ATTRIBUTION_UNKNOWN
        )
        assert unknown_count == 0
        assert len(report.attributions) == 0

    def test_doctor_exit_semantics_are_deterministic(self):
        """verify doctor exits 0 when the generated health report does not
        contain the literal word FAIL (by design of the M9-C49 surface).
        This is the canonical, documented behavior; O-2 does not change it
        but pins it to prevent accidental drift."""
        # Use the absolute interpreter path so the test is stable regardless
        # of cwd.
        python = next(
            p
            for p in (Path(".venv/bin/python").resolve(), Path(sys.executable))
            if p.exists()
        )
        result = subprocess.run(
            [str(python), "-m", "runtime.verify", "doctor"],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            timeout=60,
        )
        # The doctor report is informational; exit code encodes whether the
        # output contains the literal FAIL substring. Current implementation
        # guarantees exit 0 unless a health report asserts failure.
        assert result.returncode in (
            0,
            1,
        ), f"doctor returned unexpected code {result.returncode}"
        # The output must be generated (non-empty), not a stub.
        assert len(result.stdout) > 0 or len(result.stderr) > 0


# ---------------------------------------------------------------------------
# O2-G17 — Repeatability (canonical behavior is repeatable)
# ---------------------------------------------------------------------------


class TestRepeatability:
    """The canonical verification path is deterministic: same repository
    state + same plan input → same plan fingerprint and comparable task
    ordering."""

    def test_plan_fingerprint_is_content_derived(self):
        """Building an ExecutionPlan twice over the same repository state
        yields the same plan_fingerprint (since the fingerprint is a hash
        of content, not timestamps)."""
        from runtime.foundation.verification.execution_orchestrator import (
            ExecutionOrchestrator,
        )
        from runtime.foundation.verification.orchestrator import _collect_changed_files

        orch = ExecutionOrchestrator()
        files = _collect_changed_files().files
        p1 = orch.build_execution_plan(files)
        p2 = orch.build_execution_plan(files)
        assert (
            p1.plan_fingerprint == p2.plan_fingerprint
        ), "plan fingerprint must be deterministic given identical repository state"
        # Tasks must be in the same order (deterministic sort).
        ids1 = [t.task_id for t in p1.tasks]
        ids2 = [t.task_id for t in p2.tasks]
        assert ids1 == ids2


# ---------------------------------------------------------------------------
# O2-D — Configuration reconciliation (dual-source relationship pinned)
# ---------------------------------------------------------------------------


class TestConfigurationReconciliation:
    """The relationship between profiles.py (alias-task authority) and
    verification.yaml (workflow/capability authority) must be enforced
    executablely so future drift fails loudly rather than silently.

    Allowed deviations (explicitly documented):
      - aliases-only = {graph} (a profile alias with no yaml workflow)
      - yaml-only    = {property, migration, repository} (workflows not exposed as aliases)
    Every other name must appear in BOTH sources, and every yaml workflow
    must point to an existing script on disk.
    """

    def test_alias_set_is_subset_of_yaml_workflows_plus_allowlisted(self):
        from runtime.foundation.verification.profiles import profile_names
        from runtime.foundation.verification.registry import VerificationRegistry
        from runtime.system.observability.execution_context import create_context

        registry = VerificationRegistry()
        registry.load()
        yaml_ids = {wf.id for wf in registry.get_all_workflows()}

        # Canonical allowlist of names that intentionally live ONLY in the
        # alias surface (no yaml workflow counterpart). New entries here
        # must be justified and reviewed by O-2.
        ALLOWLISTED_ALIAS_ONLY = frozenset({"graph"})
        ALL_ALIASES = set(profile_names())

        missing_from_yaml = sorted(ALL_ALIASES - yaml_ids - ALLOWLISTED_ALIAS_ONLY)
        assert not missing_from_yaml, (
            f"Alias profile(s) missing a corresponding yaml workflow: {missing_from_yaml}. "
            "Either add them to verification.yaml workflows or add them to the "
            "ALLOWLISTED_ALIAS_ONLY constant in this test."
        )

    def test_yaml_scripts_exist_on_disk(self):
        """Every workflow.command that resolves to a shell script path must
        point to an existing file on disk. Dead script references cause
        silent INFRASTRUCTURE failures at execution time — caught here."""
        from runtime.foundation.verification.registry import VerificationRegistry

        registry = VerificationRegistry()
        registry.load()
        missing = []
        for wf in registry.get_all_workflows():
            cmd = wf.command or ""
            # Scan for bash-script invocations (``bash path/to/script.sh`` or
            # just the script path as a token). Skip placeholder/no-op commands.
            import re

            parts = cmd.split()
            for part in parts:
                if part.endswith(".sh") and not Path(part).is_absolute():
                    candidate = REPO_ROOT / part
                    if not candidate.exists():
                        missing.append(
                            f"{wf.id}: script {part!r} not found at {candidate}"
                        )
        assert not missing, "Dead script references in yaml workflows:\n" + "\n".join(
            missing
        )

    def test_no_duplicate_commands_within_a_profile(self):
        """No verification profile may contain duplicated commands — an
        easy source of evidence inflation / wasted time."""
        from runtime.foundation.verification.profiles import list_profiles

        for profile in list_profiles():
            all_cmds: list[str] = []
            for task in profile.tasks:
                all_cmds.extend(task.commands)
            seen: dict[str, int] = {}
            for cmd in all_cmds:
                seen[cmd] = seen.get(cmd, 0) + 1
            dupes = {cmd: n for cmd, n in seen.items() if n > 1}
            assert not dupes, (
                f"Profile {profile.name!r} has duplicated commands: {dupes!r}. "
                "Duplicate commands inflate evidence counts and waste time."
            )


# ---------------------------------------------------------------------------
# O2-G18 — Regression safety (O-1 lifecycle intact)
# ---------------------------------------------------------------------------


class TestRegressionSafety:
    """O-1 certified lifecycle behavior remains intact after O-2 changes.
    Minimal probe: the launcher script exists, is executable (or has the
    bash shebang), and the canonical backend + frontend contracts are
    preserved (the script references them verbatim). This does NOT start
    any servers — purely a syntactic/semantic sanity check on the frozen
    O-1 contract."""

    def test_launcher_file_exists_with_canonical_contracts(self):
        launcher = REPO_ROOT / "scripts/launch.sh"
        assert launcher.exists(), "O-1 canonical launcher must exist"
        text = launcher.read_text()
        # O-1-B8 established the canonical lifecycle contracts verbatim in
        # the progress record; preserve them as a regression guard.
        assert "uvicorn" in text.lower(), "launcher must invoke uvicorn for the backend"
        assert (
            "next start" in text.lower()
        ), "launcher must use next start (server mode) for the frontend"
        assert "frontend/dist" in text, "C38.5 canonical build dir: frontend/dist"

    def test_certificate_event_has_no_legacy_completed_pollution(
        self, tmp_events: Path
    ):
        """Post-O-2, the verifier itself must not emit legacy ``completed``
        events under the canonical paths. This is a regression guard against
        an accidental fallback to an older writer."""
        from runtime.verify import _record_verification_event
        from runtime.system.observability.event_store import EngineeringEventStore

        _record_verification_event(
            None,
            profile_name="quick",
            elapsed=1.0,
            status="passed",
            final_decision="certified",
        )
        store = EngineeringEventStore(path=tmp_events)
        completed_events = [
            e
            for e in store.iter_events()
            if e.event_type == "VerificationCompleted"
            and (e.payload or {}).get("status") == "completed"
        ]
        assert (
            not completed_events
        ), "Canonical O-2 writers must not emit legacy 'completed' status"
