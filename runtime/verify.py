#!/usr/bin/env python3
"""
ClariFin OS — Autonomous Verification Runtime (Program 7B)
M9-C49: Control Plane Consolidation
M9-C57: Canonical Runtime & Reproducible Environment Convergence

This is the THIN COMPATIBILITY SHIM for the verification runtime.
All operator/AI commands flow through the SINGLE canonical control plane
defined in runtime/foundation/verification/canonical_control_plane.py.

Legacy commands (~97 tokens) are routed through the canonical control plane
with explicit deprecation warnings — no second semantic authority exists.

Canonical execution contract (M9-C57)
-------------------------------------
This module MUST be executed as a module from the repository root, through
the repository-managed interpreter:

    python -m runtime.verify <command>        # canonical

Do NOT execute this file directly (`python runtime/verify.py`). Direct script
execution makes CPython place `runtime/` at sys.path[0], which shadows the
stdlib `platform` module with the internal `runtime/platform` package — the
exact failure class M9-C57 eliminates. Under module execution with cwd =
repo root, `import platform` resolves to the stdlib by architecture and
`runtime.platform` resolves through its explicit package path; no sys.path
manipulation is required or performed in this entry point.
"""

from __future__ import annotations

import sys
from typing import Any

from runtime.foundation.verification.control_plane_facade import (
    main as canonical_main,
)


def _normalize_status(status: str) -> str:
    """Normalize verification status to the canonical analytics vocabulary.

    Analytics (_compute_verification_metrics) counts ``status == "passed"`` as
    successful and ``status == "failed"`` as unsuccessful. Legacy callers may
    pass ``"pass"`` / ``"fail"``; normalise them so both histories converge.
    """
    if status in ("pass", "passed"):
        return "passed"
    if status in ("fail", "failed"):
        return "failed"
    return status


def _record_verification_event(
    report: Any | None,
    profile_name: str,
    elapsed: float,
    *,
    cache_hit: bool = False,
    status: str | None = None,
) -> None:
    """Record a verification event for observability tracking.

    Contract (exercised by runtime/tests/test_vea5_m8r_cache_observability.py):
    the recorded event payload carries ``profile``, ``status``, ``passed``,
    ``skipped``, ``evidence_count`` and ``cache_hit``. A fresh report (cache
    miss) contributes its summary metrics; a cache replay (report is None)
    records the stored verdict with zeroed counters. Failures are logged,
    never raised — observability must not break verification.

    Additionally emits a ``VerificationCompleted`` event so the analytics
    engine (which reads only that event type) can attribute the run to
    total_runs / passed_runs / success_rate.
    """
    try:
        from runtime.system.observability.event_store import (
            EngineeringEventStore,
            create_event,
        )
        from runtime.system.observability.execution_context import create_context
        from runtime.system.observability.repository import (
            LocalMetricsRepository,
            RunRecord,
        )

        if report is not None:
            _status = _normalize_status(report.summary.overall_status.value)
            _passed = report.summary.passed
            _failed = report.summary.failed
            _skipped = report.summary.skipped
            _evidence = len(report.evidence_files)
        else:
            _status = _normalize_status(status or "unknown")
            _passed = 0
            _failed = 0
            _skipped = 0
            _evidence = 0

        ctx = create_context(commit_sha="", branch="local")
        event_store = EngineeringEventStore()

        # --- verification_record event (legacy path — preserved for tests) ---
        record_event = create_event(
            "verification_record",
            ctx.to_dict(),
            {
                "profile": profile_name,
                "status": _status,
                "passed": _passed,
                "failed": _failed,
                "skipped": _skipped,
                "duration_seconds": elapsed,
                "evidence_count": _evidence,
                "cache_hit": cache_hit,
            },
        )
        event_store.append(record_event)

        # --- VerificationCompleted event (analytics-visible path) ----------
        completed_event = create_event(
            "VerificationCompleted",
            ctx.to_dict(),
            {
                "profile": profile_name,
                "status": _status,
                "passed": _passed,
                "failed": _failed,
                "skipped": _skipped,
                "duration_seconds": elapsed,
                "evidence_count": _evidence,
                "cache_hit": cache_hit,
                "final_decision": "certified" if _status == "passed" else "failed",
            },
        )
        event_store.append(completed_event)

        LocalMetricsRepository().append(
            RunRecord(
                run_id=record_event.event_id,
                timestamp=record_event.timestamp,
                environment=ctx.environment.value,
                runner=ctx.runner.value,
                verification_depth=ctx.verification_depth.value,
                intent=ctx.intent.value,
                trigger=ctx.trigger.value,
                commit_sha=ctx.commit_sha,
                branch=ctx.branch,
                profile=profile_name,
                status=_status,
                passed=_passed,
                failed=_failed,
                skipped=_skipped,
                duration_seconds=elapsed,
                evidence_count=_evidence,
                cache_hit=cache_hit,
            )
        )
    except Exception as exc:
        import logging

        logging.getLogger(__name__).warning(
            "Failed to record verification event: %s", exc
        )


def main() -> int:
    """Single dispatcher: all commands flow through the canonical control plane."""
    return canonical_main()


if __name__ == "__main__":
    sys.exit(main())
