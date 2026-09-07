"""M9-C57 Verification Outcome Semantic Contract — G4/G5/G6 tests.

Validates the authoritative outcome policy established during verification
outcome reconciliation:

  G4 — Outcome normalisation: ``pass``/``fail`` converge to ``passed``/``failed``.
  G5 — Legacy ``completed`` status is excluded from the outcome denominator.
  G6 — Canonical failed execution records ``status=failed`` end-to-end
       (event → RunRecord → analytics).

Run:
    python3 -m pytest runtime/tests/test_m9c57_outcome_semantic_contract.py -q
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

import runtime.system.observability.analytics as analytics_mod
import runtime.system.observability.event_store as es_mod
import runtime.system.observability.repository as repo_mod
from runtime.verify import _record_verification_event, _normalize_status

# ---------------------------------------------------------------------------
# G4 — Outcome normalisation
# ---------------------------------------------------------------------------


class TestOutcomeNormalization:
    """G4: status values are normalised to canonical vocabulary."""

    def test_pass_converges_to_passed(self) -> None:
        assert _normalize_status("pass") == "passed"
        assert _normalize_status("passed") == "passed"

    def test_fail_converges_to_failed(self) -> None:
        assert _normalize_status("fail") == "failed"
        assert _normalize_status("failed") == "failed"

    def test_unknown_is_preserved(self) -> None:
        assert _normalize_status("unknown") == "unknown"
        assert _normalize_status("completed") == "completed"

    def test_record_event_normalises_pass_to_passed_in_both_events(
        self, tmp_path: Path
    ) -> None:
        event_path, hist_path = _make_stores(tmp_path)
        _record_verification_event(None, "quick", 1.0, status="pass")

        store = es_mod.EngineeringEventStore(event_path)
        completed = [
            e for e in store.load_events() if e.event_type == "VerificationCompleted"
        ]
        assert len(completed) == 1
        assert completed[0].payload["status"] == "passed"

    def test_record_event_normalises_fail_to_failed_in_both_events(
        self, tmp_path: Path
    ) -> None:
        event_path, hist_path = _make_stores(tmp_path)
        _record_verification_event(None, "quick", 1.0, status="fail")

        store = es_mod.EngineeringEventStore(event_path)
        completed = [
            e for e in store.load_events() if e.event_type == "VerificationCompleted"
        ]
        assert len(completed) == 1
        assert completed[0].payload["status"] == "failed"


# ---------------------------------------------------------------------------
# G5 — Legacy completed handling in analytics
# ---------------------------------------------------------------------------


def _make_stores(tmp_path: Path) -> tuple[Path, Path]:
    event_path = tmp_path / "events.jsonl"
    hist_path = tmp_path / "history.json"
    es_mod.EVENT_STORE_PATH = event_path
    repo_mod.HISTORY_PATH = hist_path
    return event_path, hist_path


def _write_events(event_path: Path, entries: list[dict]) -> None:
    event_path.write_text(
        "\n".join(json.dumps(e) for e in entries) + "\n", encoding="utf-8"
    )


def _make_vc_event(
    event_id: str, status: str, passed: int = 0, failed: int = 0
) -> dict:
    return {
        "event_id": event_id,
        "event_type": "VerificationCompleted",
        "timestamp": "2026-09-07T12:00:00+00:00",
        "execution_context": {
            "environment": "local",
            "runner": "developer-workstation",
            "verification_depth": "fast",
            "intent": "developer-feedback",
            "trigger": "manual",
            "commit_sha": "",
            "branch": "local",
        },
        "payload": {
            "profile": "quick",
            "status": status,
            "passed": passed,
            "failed": failed,
            "skipped": 0,
            "duration_seconds": 10.0,
            "evidence_count": 0,
            "cache_hit": False,
            "final_decision": "certified" if status == "passed" else "failed",
        },
    }


class TestLegacyCompletedAnalytics:
    """G5: legacy ``completed`` events are excluded from outcome denominator."""

    def test_completed_excluded_from_success_rate_denominator(
        self, tmp_path: Path
    ) -> None:
        """Mixed passed/failed/completed: success_rate uses only passed+failed."""
        event_path, _ = _make_stores(tmp_path)
        entries = [
            _make_vc_event("e1", "passed", passed=5, failed=0),
            _make_vc_event("e2", "passed", passed=3, failed=0),
            _make_vc_event("e3", "failed", passed=0, failed=2),
            _make_vc_event("e4", "completed"),  # legacy, no counts
            _make_vc_event("e5", "completed"),
        ]
        _write_events(event_path, entries)

        store = es_mod.EngineeringEventStore(event_path)
        engine = analytics_mod.AnalyticsEngine(store)
        report = engine.compute()
        verif = report.combined["verification"]

        assert verif["total_runs"] == 5
        assert verif["passed_runs"] == 2
        assert verif["failed_runs"] == 1
        assert verif["legacy_completed"] == 2
        # Denominator = passed + failed = 3, not 5
        assert verif["success_rate"] == pytest.approx(2 / 3, abs=0.001)

    def test_all_completed_yields_zero_success_rate(self, tmp_path: Path) -> None:
        """When all events are legacy completed, success_rate is 0.0."""
        event_path, _ = _make_stores(tmp_path)
        entries = [
            _make_vc_event("e1", "completed"),
            _make_vc_event("e2", "completed"),
        ]
        _write_events(event_path, entries)

        store = es_mod.EngineeringEventStore(event_path)
        engine = analytics_mod.AnalyticsEngine(store)
        report = engine.compute()
        verif = report.combined["verification"]

        assert verif["passed_runs"] == 0
        assert verif["failed_runs"] == 0
        assert verif["legacy_completed"] == 2
        assert verif["success_rate"] == 0.0

    def test_no_completed_uses_all_records(self, tmp_path: Path) -> None:
        """When no legacy completed exists, denominator equals total_runs."""
        event_path, _ = _make_stores(tmp_path)
        entries = [
            _make_vc_event("e1", "passed", passed=5, failed=0),
            _make_vc_event("e2", "failed", passed=0, failed=2),
        ]
        _write_events(event_path, entries)

        store = es_mod.EngineeringEventStore(event_path)
        engine = analytics_mod.AnalyticsEngine(store)
        report = engine.compute()
        verif = report.combined["verification"]

        assert verif["total_runs"] == 2
        assert verif["passed_runs"] == 1
        assert verif["failed_runs"] == 1
        assert verif["legacy_completed"] == 0
        assert verif["success_rate"] == pytest.approx(0.5, abs=0.001)

    def test_unknown_status_treated_as_legacy(self, tmp_path: Path) -> None:
        """Status 'unknown' is grouped with legacy_completed."""
        event_path, _ = _make_stores(tmp_path)
        entries = [
            _make_vc_event("e1", "passed", passed=5, failed=0),
            _make_vc_event("e2", "unknown"),
        ]
        _write_events(event_path, entries)

        store = es_mod.EngineeringEventStore(event_path)
        engine = analytics_mod.AnalyticsEngine(store)
        report = engine.compute()
        verif = report.combined["verification"]

        assert verif["legacy_completed"] == 1
        assert verif["success_rate"] == pytest.approx(1.0, abs=0.001)


# ---------------------------------------------------------------------------
# G6 — Canonical failed execution end-to-end
# ---------------------------------------------------------------------------


class TestCanonicalFailedExecution:
    """G6: a genuine verification failure propagates through all layers."""

    def test_failed_record_event_produces_failed_event_and_run_record(
        self, tmp_path: Path
    ) -> None:
        """Calling _record_verification_event with status='fail' produces:
        - VerificationCompleted(status='failed')
        - RunRecord(status='failed')
        """
        event_path, hist_path = _make_stores(tmp_path)
        _record_verification_event(None, "quick", 5.0, status="fail")

        # Check event
        store = es_mod.EngineeringEventStore(event_path)
        completed = [
            e for e in store.load_events() if e.event_type == "VerificationCompleted"
        ]
        assert len(completed) == 1
        assert completed[0].payload["status"] == "failed"
        assert completed[0].payload["final_decision"] == "failed"

        # Check RunRecord
        data = json.loads(hist_path.read_text())
        local = data.get("local", [])
        assert len(local) == 1
        assert local[0]["status"] == "failed"
        assert local[0]["profile"] == "quick"

    def test_failed_run_record_reflected_in_analytics(self, tmp_path: Path) -> None:
        """A failed run contributes to failed_runs and reduces success_rate."""
        event_path, hist_path = _make_stores(tmp_path)

        # One pass, one fail
        _record_verification_event(None, "quick", 1.0, status="pass")
        _record_verification_event(None, "quick", 2.0, status="fail")

        store = es_mod.EngineeringEventStore(event_path)
        engine = analytics_mod.AnalyticsEngine(store)
        report = engine.compute()
        verif = report.combined["verification"]

        assert verif["passed_runs"] == 1
        assert verif["failed_runs"] == 1
        assert verif["success_rate"] == pytest.approx(0.5, abs=0.001)

    def test_mix_of_passed_failed_and_legacy_completed(self, tmp_path: Path) -> None:
        """Realistic mix: legacy completed from platform API + new canonical runs."""
        event_path, _ = _make_stores(tmp_path)

        # Simulate 3 legacy completed events (platform API source)
        legacy_events = [_make_vc_event(f"legacy-{i}", "completed") for i in range(3)]
        # Simulate 2 canonical passed + 1 canonical failed
        canonical_events = [
            _make_vc_event("can-pass-1", "passed", passed=10, failed=0),
            _make_vc_event("can-pass-2", "passed", passed=10, failed=0),
            _make_vc_event("can-fail-1", "failed", passed=0, failed=2),
        ]
        _write_events(event_path, legacy_events + canonical_events)

        store = es_mod.EngineeringEventStore(event_path)
        engine = analytics_mod.AnalyticsEngine(store)
        report = engine.compute()
        verif = report.combined["verification"]

        assert verif["total_runs"] == 6
        assert verif["passed_runs"] == 2
        assert verif["failed_runs"] == 1
        assert verif["legacy_completed"] == 3
        # success_rate = 2 / (2 + 1) = 0.666...
        assert verif["success_rate"] == pytest.approx(2 / 3, abs=0.001)

    def test_no_artificial_inflation_or_deflation(self, tmp_path: Path) -> None:
        """Legacy completed must not be counted as passed or failed."""
        event_path, _ = _make_stores(tmp_path)
        entries = [
            _make_vc_event("e1", "completed"),
            _make_vc_event("e2", "completed"),
            _make_vc_event("e3", "completed"),
        ]
        _write_events(event_path, entries)

        store = es_mod.EngineeringEventStore(event_path)
        engine = analytics_mod.AnalyticsEngine(store)
        report = engine.compute()
        verif = report.combined["verification"]

        assert verif["passed_runs"] == 0
        assert verif["failed_runs"] == 0
        assert verif["legacy_completed"] == 3
        # Must not inflate passed count
        assert verif["passed_runs"] + verif["failed_runs"] != verif["total_runs"]


# ---------------------------------------------------------------------------
# Idempotency guard (retained from prior objective)
# ---------------------------------------------------------------------------


class TestIdempotency:
    """One recording call → one VerificationCompleted → one RunRecord."""

    def test_single_call_one_of_each(self, tmp_path: Path) -> None:
        event_path, hist_path = _make_stores(tmp_path)
        _record_verification_event(None, "quick", 1.0, status="pass")

        store = es_mod.EngineeringEventStore(event_path)
        events = store.load_events()
        vc = [e for e in events if e.event_type == "VerificationCompleted"]
        vr = [e for e in events if e.event_type == "verification_record"]
        assert len(vc) == 1
        assert len(vr) == 1

        data = json.loads(hist_path.read_text())
        assert len(data.get("local", [])) == 1

    def test_two_calls_two_of_each(self, tmp_path: Path) -> None:
        event_path, hist_path = _make_stores(tmp_path)
        _record_verification_event(None, "quick", 1.0, status="pass")
        _record_verification_event(None, "quick", 2.0, status="fail")

        store = es_mod.EngineeringEventStore(event_path)
        vc = [e for e in store.load_events() if e.event_type == "VerificationCompleted"]
        assert len(vc) == 2

        data = json.loads(hist_path.read_text())
        assert len(data.get("local", [])) == 2
