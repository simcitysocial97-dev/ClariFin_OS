"""Errors service adapter (Phase 2 — ``/platform/v1/errors/*``).

Aggregates the live C50 ``EvidenceIntegrityReport`` (which records every
failed/incomplete verification condition) and the live obligation set
(whose failures are open dispositions) into the Phase 1
``PlatformErrorsList``, ``PlatformErrorsFrequency``, and
``PlatformErrorsDetail`` contracts.

The adapter is read-only and deterministic. It does **not** parse log
files — it derives errors from the structured evidence-integrity and
obligation records, per ``PLATFORM_COMPONENT_MAP.md`` §4.5.
"""

from __future__ import annotations

from collections import Counter
from typing import Any

from runtime.foundation.verification.control_plane_facade import (
    ControlPlane,
    _collect_changed_files,
)
from runtime.foundation.verification.evidence_integrity import (
    build_evidence_integrity_report,
)
from runtime.foundation.verification.obligation import Disposition
from runtime.platform.api.contracts import errors as errors_contract
from runtime.platform.api.contracts._primitives import Timestamp
from runtime.platform.api.services._helpers import envelope, now_iso

__all__ = [
    "build_errors_current",
    "build_errors_recent",
    "build_errors_recurring",
    "build_errors_frequency",
    "build_errors_detail",
]


def _integrity_failures() -> list[dict[str, Any]]:
    """Project failed evidence-integrity test cases into error items."""

    report = build_evidence_integrity_report()
    items: list[dict[str, Any]] = []
    for result in report.test_results:
        if result.passed:
            continue
        items.append(
            {
                "id": f"integrity.{result.test_case.name}",
                "code": "INTEGRITY_FAILED",
                "layer": "platform.evidence",
                "message": result.test_case.description,
                "first_seen": Timestamp(report.generated_at) if report.generated_at else now_iso(),
                "last_seen": Timestamp(report.generated_at) if report.generated_at else now_iso(),
                "occurrences": 1,
                "affected_workflow": None,
            }
        )
    return items


def _obligation_failures() -> list[dict[str, Any]]:
    """Project open/failed obligations into error items."""

    cp = ControlPlane()
    files = _collect_changed_files()
    plan = cp.planner.plan(files)
    oset = cp._plan_to_obligations(plan, files)

    items: list[dict[str, Any]] = []
    for o in oset.obligations:
        if o.disposition != Disposition.OPEN:
            continue
        req = getattr(o, "requirement", None)
        cap = getattr(o, "capability", None)
        items.append(
            {
                "id": f"obligation.{o.obligation_id}",
                "code": "OBLIGATION_OPEN",
                "layer": "platform.tasks",
                "message": (
                    req.rationale if req else o.obligation_id
                ),
                "first_seen": Timestamp(o.created_at) if o.created_at else now_iso(),
                "last_seen": Timestamp(o.created_at) if o.created_at else now_iso(),
                "occurrences": 1,
                "affected_workflow": (
                    cap.capability_id if cap else None
                ),
            }
        )
    return items


def _list_envelope(kind: str, window: str, items: list[dict[str, Any]]) -> dict[str, Any]:
    return envelope(
        kind=kind,
        data={"window": window, "count": len(items), "items": items},
    )


def build_errors_current() -> dict[str, Any]:
    """Build the ``platform.errors_current`` envelope (last hour proxy)."""

    items = _integrity_failures() + _obligation_failures()
    return _list_envelope(
        errors_contract.ERRORS_CURRENT_KIND,
        "1h",
        items,
    )


def build_errors_recent() -> dict[str, Any]:
    """Build the ``platform.errors_recent`` envelope (24h proxy)."""

    items = _integrity_failures() + _obligation_failures()
    return _list_envelope(
        errors_contract.ERRORS_RECENT_KIND,
        "24h",
        items,
    )


def build_errors_recurring() -> dict[str, Any]:
    """Build the ``platform.errors_recurring`` envelope.

    A "recurring" error is one whose code appears more than once across
    the live integrity + obligation failures.
    """

    items = _integrity_failures() + _obligation_failures()
    counter: Counter[str] = Counter(it["code"] for it in items)
    recurring = [it for it in items if counter[it["code"]] > 1]
    return _list_envelope(
        errors_contract.ERRORS_RECURRING_KIND,
        "7d",
        recurring,
    )


def build_errors_frequency() -> dict[str, Any]:
    """Build the ``platform.errors_frequency`` envelope."""

    items = _integrity_failures() + _obligation_failures()
    counter: Counter[tuple[str, str]] = Counter(
        (it["code"], it["layer"]) for it in items
    )
    buckets = [
        {"code": code, "layer": layer, "count": count}
        for (code, layer), count in sorted(counter.items())
    ]
    data = {"window": "7d", "total": sum(counter.values()), "buckets": buckets}
    return envelope(
        kind=errors_contract.ERRORS_FREQUENCY_KIND,
        data=data,
    )


def build_errors_detail(error_id: str) -> dict[str, Any] | None:
    """Build the ``platform.errors_detail`` envelope for one error id."""

    items = _integrity_failures() + _obligation_failures()
    for it in items:
        if it["id"] == error_id:
            data = {
                "item": it,
                "recent_occurrences": [it["last_seen"]],
                "related_capabilities": (
                    [it["affected_workflow"]]
                    if it.get("affected_workflow")
                    else []
                ),
                "related_evidence": [],
            }
            return envelope(
                kind=errors_contract.ERRORS_DETAIL_KIND,
                data=data,
            )
    return None
