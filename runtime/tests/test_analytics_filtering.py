"""M9-C58 — Analytics plan-only event filtering.

Verifies that VerificationCompleted events carrying ``executed=false``
(produced by the plan-only path in ``verification_write.py``) are excluded
from all analytics metrics and do not affect success_rate or total_runs.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

import runtime.system.observability.analytics as analytics_mod
import runtime.system.observability.event_store as es_mod


def _make_stores(tmp_path: Path) -> tuple[Path, Path]:
    event_path = tmp_path / "events.jsonl"
    hist_path = tmp_path / "history.json"
    es_mod.EVENT_STORE_PATH = event_path
    return event_path, hist_path


def _write_events(event_path: Path, entries: list[dict]) -> None:
    event_path.write_text(
        "\n".join(json.dumps(e) for e in entries) + "\n", encoding="utf-8"
    )


def _make_vc_event(
    event_id: str,
    status: str,
    executed: bool | None = None,
    passed: int = 0,
    failed: int = 0,
    duration: float = 10.0,
    cache_hit: bool = False,
) -> dict:
    payload: dict[str, object] = {
        "profile": "quick",
        "status": status,
        "passed": passed,
        "failed": failed,
        "skipped": 0,
        "duration_seconds": duration,
        "evidence_count": 5,
        "cache_hit": cache_hit,
        "final_decision": "certified" if status == "passed" else "failed",
    }
    if executed is not None:
        payload["executed"] = executed
    return {
        "event_id": event_id,
        "event_type": "VerificationCompleted",
        "timestamp": "2026-09-10T12:00:00+00:00",
        "execution_context": {
            "environment": "local",
            "source": "platform.verification.run",
            "runner": "developer-workstation",
            "verification_depth": "fast",
            "intent": "developer-feedback",
            "trigger": "manual",
            "commit_sha": "abc123",
            "branch": "main",
        },
        "payload": payload,
    }


class TestPlanOnlyEventFiltering:
    """Plan-only events must not pollute analytics."""

    def test_executed_false_excluded_from_metrics(
        self, tmp_path: Path
    ) -> None:
        """Events with executed=false are invisible to analytics."""
        event_path, _ = _make_stores(tmp_path)
        entries = [
            _make_vc_event("e1", "unknown", executed=False),
            _make_vc_event("e2", "unknown", executed=False),
        ]
        _write_events(event_path, entries)

        store = es_mod.EngineeringEventStore(event_path)
        engine = analytics_mod.AnalyticsEngine(store)
        report = engine.compute()
        verif = report.local["verification"]
        cache = report.local["cache"]

        assert verif.get("total_runs") == 0
        assert verif.get("passed_runs", 0) == 0
        assert verif.get("failed_runs", 0) == 0
        assert verif["success_rate"] == 0.0
        assert cache.get("total", 0) == 0
        assert cache.get("hit_rate", 0.0) == 0.0

    def test_executed_false_does_not_deflate_success_rate(
        self, tmp_path: Path
    ) -> None:
        """Mixed executed and plan-only: only executed runs count."""
        event_path, _ = _make_stores(tmp_path)
        entries = [
            _make_vc_event("e1", "passed", executed=True, passed=5, failed=0),
            _make_vc_event("e2", "unknown", executed=False),
            _make_vc_event("e3", "passed", executed=True, passed=3, failed=0),
            _make_vc_event("e4", "unknown", executed=False),
        ]
        _write_events(event_path, entries)

        store = es_mod.EngineeringEventStore(event_path)
        engine = analytics_mod.AnalyticsEngine(store)
        report = engine.compute()
        verif = report.local["verification"]

        assert verif["total_runs"] == 2
        assert verif["passed_runs"] == 2
        assert verif["failed_runs"] == 0
        assert verif["success_rate"] == 1.0

    def test_executed_absent_treated_as_executed(self, tmp_path: Path) -> None:
        """Events without the executed field are not filtered (backwards compat)."""
        event_path, _ = _make_stores(tmp_path)
        entries = [
            _make_vc_event("e1", "passed", passed=5, failed=0),
            _make_vc_event("e2", "failed", passed=0, failed=2),
        ]
        _write_events(event_path, entries)

        store = es_mod.EngineeringEventStore(event_path)
        engine = analytics_mod.AnalyticsEngine(store)
        report = engine.compute()
        verif = report.local["verification"]

        assert verif["total_runs"] == 2
        assert verif["passed_runs"] == 1
        assert verif["failed_runs"] == 1
        assert verif["success_rate"] == pytest.approx(0.5, abs=0.001)

    def test_cache_metrics_excludes_plan_only(self, tmp_path: Path) -> None:
        """Cache hit rate calculation excludes plan-only stubs."""
        event_path, _ = _make_stores(tmp_path)
        entries = [
            _make_vc_event("e1", "passed", executed=True, cache_hit=True),
            _make_vc_event("e2", "unknown", executed=False),
            _make_vc_event("e3", "failed", executed=True, cache_hit=False),
        ]
        _write_events(event_path, entries)

        store = es_mod.EngineeringEventStore(event_path)
        engine = analytics_mod.AnalyticsEngine(store)
        report = engine.compute()
        cache = report.local["cache"]

        assert cache["total"] == 2
        assert cache["hits"] == 1
        assert cache["hit_rate"] == pytest.approx(0.5, abs=0.001)
