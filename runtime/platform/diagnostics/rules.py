"""Diagnostic rules — M9-C57 Phase 11.

Rules encode deterministic heuristics for the diagnostic ladder levels.
Each rule maps a signal → diagnosis level + recommendation.
"""

from __future__ import annotations

from typing import Any

# ---------------------------------------------------------------------------
# Rule definitions
# ---------------------------------------------------------------------------

RULES: list[dict[str, Any]] = [
    {
        "id": "error_exists_for_capability",
        "level": "L1",
        "condition": lambda ctx: bool(ctx.get("errors_for_capability")),
        "fact": "error_present_for_capability",
        "recommendation": [
            {"action": "inspect_error_detail", "target": "first_error_id"},
        ],
    },
    {
        "id": "capability_in_blast_radius",
        "level": "L2",
        "condition": lambda ctx: bool(ctx.get("blast_radius_caps")),
        "fact": "capability_in_change_blast_radius",
        "recommendation": [
            {"action": "run_targeted_verification", "target": "affected_capability"},
        ],
    },
    {
        "id": "stale_evidence_for_capability",
        "level": "L2",
        "condition": lambda ctx: bool(ctx.get("stale_evidence_ids")),
        "fact": "stale_evidence_detected",
        "recommendation": [
            {"action": "reverify_capability", "target": "first_stale_evidence_cap"},
        ],
    },
    {
        "id": "multiple_errors_same_code",
        "level": "L1",
        "condition": lambda ctx: bool(ctx.get("recurring_errors")),
        "fact": "recurring_error_pattern",
        "recommendation": [
            {"action": "inspect_recurring_error", "target": "first_recurring_code"},
        ],
    },
    {
        "id": "no_specific_signal",
        "level": "L1",
        "condition": lambda ctx: True,
        "fact": "no_matching_rule",
        "recommendation": [
            {"action": "run_blast_radius_check", "target": "all_changed_files"},
        ],
    },
]


def evaluate(ctx: dict[str, Any]) -> dict[str, Any] | None:
    """Evaluate rules against context and return the first match."""
    for rule in RULES:
        try:
            if rule["condition"](ctx):
                return {
                    "rule_id": rule["id"],
                    "level": rule["level"],
                    "fact": rule["fact"],
                    "recommendation": rule["recommendation"],
                }
        except Exception:
            # A failing rule is treated as non-matching, not fatal.
            pass
    return None
