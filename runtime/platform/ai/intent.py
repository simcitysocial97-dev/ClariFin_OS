"""Intent Resolver (Phase 13).

Maps user requests to capability clusters and determines the required
authority level. No LLM - uses deterministic keyword matching and
capability catalog lookup.
"""

from __future__ import annotations

import re
from typing import Any

from runtime.foundation.verification.capability_catalog import (
    get_capability_catalog,
)

# ---------------------------------------------------------------------------
# Intent classification
# ---------------------------------------------------------------------------


class IntentType(str):
    OBSERVE = "observe"
    ANALYZE = "analyze"
    DIAGNOSE = "diagnose"
    VERIFY = "verify"
    DEVELOP = "develop"
    OPERATE = "operate"
    ADMINISTER = "administer"


class ResolvedIntent:
    """Resolved user intent with required authority level and capabilities."""

    def __init__(
        self,
        intent_type: str,
        confidence: float,
        required_level: int,
        capabilities: list[str],
        rationale: str,
    ):
        self.intent_type = intent_type
        self.confidence = confidence
        self.required_level = required_level
        self.capabilities = capabilities
        self.rationale = rationale


# ---------------------------------------------------------------------------
# Keyword patterns for intent classification
# ---------------------------------------------------------------------------

INTENT_PATTERNS: list[tuple[str, str, int, list[str]]] = [
    # (pattern, intent_type, required_level, suggested_capabilities)
    # Order matters - more specific patterns first
    (
        r"\b(verify|run.verification|execute.verification)\b",
        "verify",
        1,
        ["execute.verification-run"],
    ),
    (r"\b(run|check|test|exec|execute)\b", "verify", 1, ["execute.verification-run"]),
    (
        r"\b(diagnos|root.cause|why|what.caused|investigat)\b",
        "diagnose",
        1,
        ["execute.diagnostic-engine"],
    ),
    (
        r"\b(change|diff|delta|compare|affected)\b",
        "analyze",
        1,
        ["discover.blast-radius", "discover.what-should-i-run"],
    ),
    (
        r"\b(history|past|previous|last|baseline|compare)\b",
        "analyze",
        1,
        ["discover.blast-radius"],
    ),
    (
        r"\b(evidence|proof|artifact|integrity)\b",
        "analyze",
        1,
        ["execute.evidence-collection"],
    ),
    (
        r"\b(patch|fix|create|write|modify|refactor|implement|add|delete)\b",
        "develop",
        2,
        [],
    ),
    (
        r"\b(test|coverage|mutation|property)\b",
        "develop",
        2,
        ["execute.test-generation"],
    ),
    (r"\b(deploy|migrate|rollback|backup|restore|provision)\b", "operate", 3, []),
    (r"\b(admin|authoriz|policy|security|secret|credential)\b", "administer", 4, []),
    (
        r"\b(health|status|overview|summary|dashboard)\b",
        "observe",
        0,
        ["discover.blast-radius"],
    ),
    (r"\b(capabilit(y|ies)|list|show|enumerate)\b", "observe", 0, []),
    (
        r"\b(architecture|boundar(y|ies)|duplicate|bypass|deprecat|unmapped)\b",
        "observe",
        0,
        ["discover.blast-radius"],
    ),
    (
        r"\b(error|fail|issue|bug|problem|recurring)\b",
        "diagnose",
        1,
        ["execute.diagnostic-engine"],
    ),
]


# ---------------------------------------------------------------------------
# Intent resolver
# ---------------------------------------------------------------------------


def resolve_intent(
    user_input: str, *, context: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Resolve a natural language request to a structured intent.

    Returns a dict with: intent_type, confidence, required_level, capabilities, rationale.
    """
    text = user_input.lower()
    matches: list[tuple[str, float, int, list[str], str]] = []

    for pattern, intent_type, level, caps in INTENT_PATTERNS:
        match_count = len(re.findall(pattern, text))
        if match_count > 0:
            # Simple scoring: more matches = higher confidence
            confidence = min(0.5 + (match_count * 0.15), 1.0)
            matches.append(
                (
                    intent_type,
                    confidence,
                    level,
                    caps,
                    f"matched '{pattern}' {match_count}x",
                )
            )

    if not matches:
        return {
            "intent_type": "observe",
            "confidence": 0.3,
            "required_level": 0,
            "capabilities": [],
            "rationale": "no pattern matched - defaulting to observe",
        }

    # Sort by confidence descending, then by level ascending (prefer lower authority)
    matches.sort(key=lambda m: (-m[1], m[2]))
    best = matches[0]

    # Also look at capability catalog for direct capability mentions
    catalog_caps = []
    try:
        catalog = get_capability_catalog()
        for entry in catalog.entries:
            if entry.capability_id.lower() in text:
                catalog_caps.append(entry.capability_id)
    except Exception:
        pass

    return {
        "intent_type": best[0],
        "confidence": best[1],
        "required_level": best[2],
        "capabilities": list(set(best[3] + catalog_caps)),
        "rationale": best[4],
    }


def infer_mode_from_intent(intent_type: str, required_level: int) -> str:
    """Determine the appropriate AI mode from intent."""
    if required_level >= 2:
        return "AUTONOMOUS"
    elif required_level == 1:
        return "ASSISTED"
    else:
        return "MANUAL"
