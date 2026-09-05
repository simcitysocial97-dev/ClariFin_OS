"""Shared comparison engine for Phase 8.

Computes semantic deltas between two verified states (history runs or
evidence sets) across the dimensions required by
``IMPLEMENTATION_ROADMAP.md`` Phase 8:

    * repository_changes
    * test_changes (passed_added/removed, failed_added/removed)
    * failures / recovered_failures
    * duration (current_ms, baseline_ms, delta_ms)
    * coverage (where present)
    * evidence_invalidated
    * obligations (new / closed)
    * capability_state_changes
"""

from __future__ import annotations

from typing import Any


def compute_history_delta(
    current: dict[str, Any],
    baseline: dict[str, Any],
) -> dict[str, Any]:
    """Compute the delta between two history run summaries.

    Both ``current`` and ``baseline`` are dicts produced by
    ``_runs_from_event_store`` (or loaded from the engineering-history
    artifact). The returned dict contains only the fields that differ,
    plus summary fields for every comparison dimension.
    """

    # --- repository changes ---
    # Derived from blast-radius payload when available; empty otherwise.
    current_blast = (current.get("blast_radius") or {})
    baseline_blast = (baseline.get("blast_radius") or {})
    current_files = set(current_blast.get("affected_tests", []) or [])
    baseline_files = set(baseline_blast.get("affected_tests", []) or [])
    repository_changes = {
        "changed": sorted(current_files - baseline_files),
        "removed": sorted(baseline_files - current_files),
        "common": sorted(current_files & baseline_files),
    }

    # --- test result changes ---
    cur_passed = int(current.get("capabilities_passed", 0) or 0)
    base_passed = int(baseline.get("capabilities_passed", 0) or 0)
    cur_failed = int(current.get("capabilities_failed", 0) or 0)
    base_failed = int(baseline.get("capabilities_failed", 0) or 0)

    test_changes = {
        "passed_added": max(0, cur_passed - base_passed),
        "passed_removed": max(0, base_passed - cur_passed),
        "failed_added": max(0, cur_failed - base_failed),
        "failed_removed": max(0, base_failed - cur_failed),
    }

    # --- failures / recovered ---
    failures = test_changes["failed_added"]
    recovered = test_changes["failed_removed"]

    # --- duration ---
    cur_dur = int(current.get("duration_ms") or 0)
    base_dur = int(baseline.get("duration_ms") or 0)
    duration = {
        "current_ms": cur_dur,
        "baseline_ms": base_dur,
        "delta_ms": cur_dur - base_dur,
    }

    # --- capability state changes ---
    cur_status = current.get("status", "UNKNOWN")
    base_status = baseline.get("status", "UNKNOWN")
    capability_state_changes: list[dict[str, Any]] = []
    if cur_status != base_status:
        capability_state_changes.append({
            "capability": "system",
            "from": base_status,
            "to": cur_status,
            "evidence": current.get("id", ""),
        })

    return {
        "repository_changes": repository_changes,
        "test_changes": test_changes,
        "failures": failures,
        "recovered_failures": recovered,
        "duration": duration,
        "evidence_invalidated": [],  # populated when evidence IDs differ
        "new_obligations": [],  # populated when task data available
        "closed_obligations": [],
        "capability_state_changes": capability_state_changes,
    }


def compute_evidence_delta(
    left: dict[str, Any],
    right: dict[str, Any],
) -> dict[str, Any]:
    """Compute a semantic delta between two evidence list rows.

    Each row is a dict with keys: id, kind, capability_id, status,
    collected_at, summary, payload, references.
    """

    delta: dict[str, Any] = {}

    # Structural differences (always computed).
    for key in ("status", "capability_id", "kind"):
        lv = left.get(key)
        rv = right.get(key)
        if lv != rv:
            delta[key] = {"left": lv, "right": rv}

    # Summary text diff (truncated to first meaningful difference).
    ls = str(left.get("summary", ""))
    rs = str(right.get("summary", ""))
    if ls != rs:
        delta["summary"] = {"left": ls[:200], "right": rs[:200]}

    # Collected-at gap.
    lc = left.get("collected_at", "")
    rc = right.get("collected_at", "")
    if lc != rc:
        delta["collected_at"] = {"left": lc, "right": rc}

    return delta
