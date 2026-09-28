"""Canonical verification-outcome → platform status mapping (O-2).

Single semantic authority for translating the closed verification-outcome
vocabulary (see ``runtime/verify.py`` — passed / failed / blocked /
interrupted / legacy completed / unknown) into the Platform API
``Status`` labels.

O-2 signal-truth rule: every consumer (history, verification projections,
diagnostics, the Platform AI context builder) MUST derive run health from
the event's canonical ``status`` field through this mapping — never by
re-interpreting raw counters (e.g. ``passed`` truthiness), which produced
divergent and incorrect health classifications.
"""

from __future__ import annotations

#: Closed canonical outcome vocabulary.
OUTCOME_PASSED = "passed"
OUTCOME_FAILED = "failed"
OUTCOME_BLOCKED = "blocked"
OUTCOME_INTERRUPTED = "interrupted"
OUTCOME_LEGACY_COMPLETED = "completed"
OUTCOME_UNKNOWN = "unknown"

CANONICAL_OUTCOMES = frozenset(
    {
        OUTCOME_PASSED,
        OUTCOME_FAILED,
        OUTCOME_BLOCKED,
        OUTCOME_INTERRUPTED,
        OUTCOME_LEGACY_COMPLETED,
        OUTCOME_UNKNOWN,
    }
)


def outcome_to_platform_status(outcome: str | None) -> str:
    """Map a canonical outcome to the Platform API status label.

    * passed      → HEALTHY   (a verified success)
    * failed      → UNHEALTHY (a verified failure: the defect was detected)
    * blocked     → DEGRAD    (ran, but could not complete — not a pass)
    * interrupted → DEGRAD    (user-terminated — not a pass)
    * completed   → DEGRAD    (legacy lifecycle state; unresolved)
    * unknown/None→ UNKNOWN   (no outcome information; never healthy)

    The returned value is the ``Status`` enum VALUE (string); consumers wrap
    it with ``Status(...)``. This module deliberately depends on no other
    layer so it can be reused from anywhere in the runtime.
    """
    if outcome == OUTCOME_PASSED:
        return "HEALTHY"
    if outcome == OUTCOME_FAILED:
        return "UNHEALTHY"
    if outcome in (OUTCOME_BLOCKED, OUTCOME_INTERRUPTED, OUTCOME_LEGACY_COMPLETED):
        return "DEGRAD"
    return "UNKNOWN"
