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

import subprocess
import sys
from pathlib import Path
from typing import Any

from runtime.foundation.verification.control_plane_facade import (
    main as canonical_main,
)

#: Repository root (runtime/verify.py → repo root).
_REPO_ROOT = Path(__file__).resolve().parent.parent

# ---------------------------------------------------------------------------
# Canonical outcome vocabulary (O-2)
# ---------------------------------------------------------------------------
#
# The event/RunRecord ``status`` field is the single semantic truth consumed
# by analytics, history, diagnostics and the Platform AI. It is a CLOSED
# vocabulary:
#
#   passed      — successful verification outcome
#   failed      — unsuccessful verification outcome (defect detected)
#   blocked     — execution could not (fully) happen (infrastructure,
#                 timeout, validation/scope, authorization); never a pass
#   interrupted — the operator terminated the run (SIGINT/SIGTERM); never a
#                 pass and distinct from a failure
#   completed   — legacy lifecycle state (pre-O-2 writers); unresolved
#   unknown     — unresolved (planned-but-not-executed, or unknown writer)
#
# Policy C (certified, M9-C57 outcome reconciliation) remains authoritative:
# ``completed``/``unknown`` are never counted as successful outcomes. O-2
# adds the same rule for ``blocked`` and ``interrupted``: they are never
# counted as successes and are tracked in their own analytics buckets.


def _normalize_status(status: str) -> str:
    """Normalize verification status to the canonical outcome vocabulary.

    Legacy writers may pass ``"pass"`` / ``"fail"``; they converge to
    ``"passed"`` / ``"failed"``. Every other value — including the canonical
    ``blocked``/``interrupted`` and the legacy ``completed``/``unknown`` — is
    preserved verbatim so it is visible, never silently reinterpreted.
    """
    if status in ("pass", "passed"):
        return "passed"
    if status in ("fail", "failed"):
        return "failed"
    return status


#: Mapping from the orchestrator's closed FinalDecision vocabulary to the
#: canonical event/RunRecord outcome. The orchestrator's fine-grained
#: decision is ALSO carried verbatim in the event payload
#: (``final_decision``); this mapping only selects the outcome bucket.
_ORCHESTRATOR_DECISION_TO_STATUS: dict[str, str] = {
    "certified": "passed",
    "diagnostic": "failed",
    "not_certifiable": "failed",
    "infrastructure_blocked": "blocked",
    "timeout_blocked": "blocked",
    "validation_blocked": "blocked",
    "awaiting_authorization": "blocked",
    "interrupted": "interrupted",
}


def decision_to_status(final_decision: str) -> str:
    """Map an orchestrator FinalDecision to the canonical outcome status."""
    return _ORCHESTRATOR_DECISION_TO_STATUS.get(final_decision or "unknown", "unknown")


def _resolve_repository_identity() -> tuple[str, str]:
    """Resolve the real (commit_sha, branch) for event/RunRecord stamping.

    O-2 identity truth (O2-G9): a verification record must identify the
    repository state it describes. The commit SHA and branch are read from
    git at record time. Empty strings are returned only when git itself is
    unavailable — a record must never be stamped with a fabricated identity
    (the pre-O-2 ``commit_sha=""`` / ``branch="local"`` hardcoding is
    eliminated).
    """
    commit_sha = ""
    branch = ""
    try:
        commit_sha = (
            subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=str(_REPO_ROOT),
                capture_output=True,
                text=True,
                timeout=5,
            ).stdout.strip()
            or ""
        )
        branch = (
            subprocess.run(
                ["git", "branch", "--show-current"],
                cwd=str(_REPO_ROOT),
                capture_output=True,
                text=True,
                timeout=5,
            ).stdout.strip()
            or ""
        )
    except Exception:
        pass
    return commit_sha, branch


def _record_verification_event(
    report: Any | None,
    profile_name: str,
    elapsed: float,
    *,
    cache_hit: bool = False,
    status: str | None = None,
    passed: int | None = None,
    failed: int | None = None,
    skipped: int | None = None,
    evidence_count: int | None = None,
    plan_id: str | None = None,
    report_id: str | None = None,
    final_decision: str | None = None,
    extra_metadata: dict[str, Any] | None = None,
) -> None:
    """Record a verification event for observability tracking.

    Contract (exercised by
    ``runtime/tests/test_vea5_m8r_cache_observability.py`` and
    ``runtime/tests/test_m9c57_outcome_semantic_contract.py``):
    the recorded event payload carries ``profile``, ``status``, ``passed``,
    ``failed``, ``skipped``, ``evidence_count`` and ``cache_hit``. A fresh
    report (cache miss) contributes its summary metrics; a cache replay
    (report is None) records the supplied outcome with the supplied
    counters. Failures are logged, never raised — observability must not
    break verification.

    Additionally emits a ``VerificationCompleted`` event so the analytics
    engine (which reads only that event type) can attribute the run to
    total_runs / passed_runs / success_rate.

    O-2 invariants:
      * the event context carries the REAL repository identity
        (commit_sha, branch) resolved at record time — identity truth;
      * ``status`` uses the canonical closed vocabulary (passed / failed /
        blocked / interrupted / legacy completed / unknown) — a run that
        was not a successful verification is never recorded ``passed``;
      * ``final_decision`` is carried verbatim when supplied, so the
        fine-granded orchestrator decision (e.g. ``timeout_blocked``) is
        preserved next to the outcome bucket;
      * ``plan_id``/``report_id`` are carried in metadata so the record is
        traceable back to the execution plan and report (O2-G9).
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
            _passed = passed if passed is not None else 0
            _failed = failed if failed is not None else 0
            _skipped = skipped if skipped is not None else 0
            _evidence = evidence_count if evidence_count is not None else 0

        _commit_sha, _branch = _resolve_repository_identity()
        ctx = create_context(commit_sha=_commit_sha, branch=_branch)
        event_store = EngineeringEventStore()

        metadata: dict[str, Any] = dict(extra_metadata or {})
        if plan_id:
            metadata["plan_id"] = plan_id
        if report_id:
            metadata["report_id"] = report_id

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
            metadata=metadata,
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
                "final_decision": final_decision
                or ("certified" if _status == "passed" else _status),
            },
            metadata=metadata,
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
                commit_sha=_commit_sha,
                branch=_branch,
                profile=profile_name,
                status=_status,
                passed=_passed,
                failed=_failed,
                skipped=_skipped,
                duration_seconds=elapsed,
                evidence_count=_evidence,
                cache_hit=cache_hit,
                metadata=metadata,
            )
        )
    except Exception as exc:
        import logging

        logging.getLogger(__name__).warning(
            "Failed to record verification event: %s", exc
        )


def record_execution_report(
    profile_name: str,
    report: Any,
    elapsed: float,
) -> None:
    """Record the outcome of an orchestrator ``ExecutionReport`` through the
    canonical signal chain (execution → event → RunRecord → analytics).

    This closes the O-2 signal-chain gap: ``verify check`` / ``verify run``
    produced an ExecutionReport that was printed but never recorded, so the
    primary verification entrypoints were invisible to observability.

    The outcome bucket is derived from the report's closed
    ``FinalDecision`` vocabulary via :func:`decision_to_status`; the
    decision itself is preserved verbatim in the payload. Counter fields
    carry executed-TASK counts (the orchestrator's unit of execution); the
    full per-state distribution is preserved in metadata.
    """
    decision = getattr(report, "final_decision", None) or "unknown"
    status = decision_to_status(decision)
    records = getattr(report, "records", None) or []

    passed = 0
    failed = 0
    skipped = 0
    states: dict[str, int] = {}
    artifacts: set[str] = set()
    for r in records:
        state = getattr(r, "completion_state", "unknown")
        states[state] = states.get(state, 0) + 1
        if state in ("pass", "reused"):
            passed += 1
        elif state == "failed":
            failed += 1
        elif state == "skipped":
            skipped += 1
        for a in getattr(r, "artifacts", None) or []:
            artifacts.add(a)

    evidence_count = sum(1 for a in artifacts if Path(a).exists())
    plan_id = getattr(report, "plan_id", None)
    report_id = getattr(report, "report_id", None)
    _record_verification_event(
        None,
        profile_name,
        elapsed,
        status=status,
        passed=passed,
        failed=failed,
        skipped=skipped,
        evidence_count=evidence_count,
        plan_id=plan_id,
        report_id=report_id,
        final_decision=decision,
        extra_metadata={"task_states": states} if states else None,
    )


def main() -> int:
    """Single dispatcher: all commands flow through the canonical control plane."""
    return canonical_main()


if __name__ == "__main__":
    sys.exit(main())
