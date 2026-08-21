"""VEA-5 M8R — cache-hit observability (D-05).

Wires and tests that a reusable cache hit records ``cache_hit: true`` in the
engineering event/metrics store, and that a cache miss does not incorrectly
report a hit. The tests exercise ``_record_verification_event`` (the function
wired into the active profile runner path) with redirected event/metrics
stores, verifying the recorded payload — not just source inspection.

Run:
    python3 -m pytest runtime/tests/test_vea5_m8r_cache_observability.py -q
"""

from __future__ import annotations

from pathlib import Path

import runtime.system.observability.event_store as es_mod
import runtime.system.observability.repository as repo_mod
from runtime.verify import _record_verification_event


class _FakeSummary:
    def __init__(self, status: str, passed: int, failed: int, skipped: int) -> None:
        self.overall_status = type("S", (), {"value": status})()
        self.passed = passed
        self.failed = failed
        self.skipped = skipped


class _FakeReport:
    def __init__(self, status: str) -> None:
        self.summary = _FakeSummary(status, passed=3, failed=0, skipped=1)
        self.blast_radius = 2
        self.evidence_files = ["ev/a", "ev/b"]


def _make_stores(tmp_path: Path) -> tuple[Path, Path]:
    event_path = tmp_path / "events.jsonl"
    hist_path = tmp_path / "history.json"
    es_mod.EVENT_STORE_PATH = event_path
    repo_mod.HISTORY_PATH = hist_path
    return event_path, hist_path


def _recorded_events(event_path: Path) -> list[dict]:
    store = es_mod.EngineeringEventStore(event_path)
    return [e.payload for e in store.load_events()]


def test_cache_hit_records_cache_hit_true(tmp_path: Path) -> None:
    """A cache-hit observation persists cache_hit == True in the event store."""
    event_path, _ = _make_stores(tmp_path)
    _record_verification_event(None, "backend", 0.0, cache_hit=True, status="pass")

    events = _recorded_events(event_path)
    assert len(events) == 1
    assert events[0]["cache_hit"] is True
    assert events[0]["profile"] == "backend"
    assert events[0]["status"] == "pass"


def test_cache_hit_records_fail_status_when_cached_verdict_failed(
    tmp_path: Path,
) -> None:
    """A cached FAIL is recorded as a cache hit with status fail (non-zero)."""
    event_path, _ = _make_stores(tmp_path)
    _record_verification_event(None, "runtime", 0.0, cache_hit=True, status="fail")

    events = _recorded_events(event_path)
    assert len(events) == 1
    assert events[0]["cache_hit"] is True
    assert events[0]["status"] == "fail"


def test_cache_miss_records_cache_hit_false_from_report(tmp_path: Path) -> None:
    """A fresh (cache-miss) execution records cache_hit == False from the report."""
    event_path, _ = _make_stores(tmp_path)
    report = _FakeReport(status="pass")
    _record_verification_event(report, "backend", 5.5, cache_hit=False)

    events = _recorded_events(event_path)
    assert len(events) == 1
    assert events[0]["cache_hit"] is False
    assert events[0]["status"] == "pass"
    # Report-derived metrics are preserved on the miss path.
    assert events[0]["passed"] == 3
    assert events[0]["skipped"] == 1
    assert events[0]["evidence_count"] == 2


def test_cache_miss_does_not_report_hit(tmp_path: Path) -> None:
    """Explicit guard: a cache miss must never record cache_hit == True."""
    event_path, _ = _make_stores(tmp_path)
    # Simulate a miss by calling with cache_hit defaults (False) and report=None
    # but a status — no hit flag may leak through.
    _record_verification_event(None, "backend", 0.0, cache_hit=False, status="pass")

    events = _recorded_events(event_path)
    assert len(events) == 1
    assert events[0]["cache_hit"] is False
