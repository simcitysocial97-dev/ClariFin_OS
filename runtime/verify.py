#!/usr/bin/env python3
"""
ClariFin OS — Autonomous Verification Runtime (Program 7B)
M9-C49: Control Plane Consolidation

This is the THIN COMPATIBILITY SHIM for the verification runtime.
All operator/AI commands flow through the SINGLE canonical control plane
defined in runtime/foundation/verification/canonical_control_plane.py.

Legacy commands (~97 tokens) are routed through the canonical control plane
with explicit deprecation warnings — no second semantic authority exists.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from runtime.foundation.verification.control_plane_facade import (
    main as canonical_main,
)


def _record_verification_event(
    report: Any | None,
    profile_name: str,
    elapsed: float,
    *,
    cache_hit: bool = False,
    status: str | None = None,
) -> None:
    """Record a verification event for observability tracking."""
    try:
        from runtime.system.observability.event_store import (
            EngineeringEventStore,
            create_event,
        )
        from runtime.system.observability.execution_context import create_context
        from runtime.system.observability.repository import (
            LocalMetricsRepository,
        )

        store = EngineeringEventStore()
        metrics = LocalMetricsRepository()
        event_ctx = create_context(commit_sha="", branch="local")
        event = create_event(
            type="verification_record",
            payload={
                "report": report,
                "profile_name": profile_name,
                "elapsed": elapsed,
                "cache_hit": cache_hit,
                "status": status,
            },
            execution_context=event_ctx,
        )
        store.append(event)
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
