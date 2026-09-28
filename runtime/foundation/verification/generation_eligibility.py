# runtime/foundation/verification/generation_eligibility.py
#
# M9-C53 — Generation Eligibility Decision Engine.
#
# Determines whether a classified gap is eligible for automatic test
# generation. This is the critical control point: it enforces the safety
# rules from the C53 specification (section 7) and produces explicit
# refusal reasons for every ineligible case.
#
# The refusal path is as important as the generation path.

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from runtime.foundation.verification.gap_classification import (
    GapClass,
    GapClassificationResult,
)

REPO_ROOT = (
    __import__("pathlib", fromlist=["Path"])
    .Path(__file__)
    .resolve()
    .parent.parent.parent.parent
)


@dataclass(frozen=True, slots=True)
class EligibilityDecision:
    """Machine-readable eligibility decision for one gap."""

    gap_id: str
    generation_allowed: bool
    generation_refused: bool
    refusal_reason: str
    refusal_code: str
    gap_class: GapClass
    source_evidence: str
    capability: str
    component: str
    strategy: str  # the generation strategy that would apply (if allowed)
    authorization_required: bool
    decided_at: str = ""
    evidence: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "decided_at", self.decided_at or datetime.now(UTC).isoformat()
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "gap_id": self.gap_id,
            "generation_allowed": self.generation_allowed,
            "generation_refused": self.generation_refused,
            "refusal_reason": self.refusal_reason,
            "refusal_code": self.refusal_code,
            "gap_class": self.gap_class.value,
            "source_evidence": self.source_evidence,
            "capability": self.capability,
            "component": self.component,
            "strategy": self.strategy,
            "authorization_required": self.authorization_required,
            "decided_at": self.decided_at,
            "evidence": self.evidence,
        }


# Refusal codes (closed vocabulary)
class RefusalCode:
    EQUIVALENT_SURVIVOR = "EQUIVALENT_SURVIVOR"
    DEFENSIVE_SURVIVOR = "DEFENSIVE_SURVIVOR"
    MEASUREMENT_FAILURE = "MEASUREMENT_FAILURE"
    STALE_EVIDENCE = "STALE_EVIDENCE"
    MISSING_CAPABILITY = "MISSING_CAPABILITY"
    MISSING_TEST_SURFACE = "MISSING_TEST_SURFACE"
    AMBIGUOUS_OWNERSHIP = "AMBIGUOUS_OWNERSHIP"
    SCOPE_DRIFT = "SCOPE_DRIFT"
    REPOSITORY_SHA_MISMATCH = "REPOSITORY_SHA_MISMATCH"
    CONFIGURATION_MISMATCH = "CONFIGURATION_MISMATCH"
    TOOLCHAIN_MISMATCH = "TOOLCHAIN_MISMATCH"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    HUMAN_AUTHORIZATION_REQUIRED = "HUMAN_AUTHORIZATION_REQUIRED"
    DISCOVERY_GAP = "DISCOVERY_GAP"
    HISTORICAL_INSUFFICIENT = "HISTORICAL_INSUFFICIENT"
    SCORE_PRESSURE = "SCORE_PRESSURE"
    NONE = "NONE"  # not refused


# Gap class → default generation strategy
CLASS_STRATEGY: dict[GapClass, str] = {
    GapClass.A_GENUINE_BEHAVIORAL: "example_based_unit",
    GapClass.EQUIVALENT: "NONE",
    GapClass.DEFENSIVE: "NONE",
    GapClass.DISCOVERY_GAP: "NONE",
    GapClass.HISTORICAL: "NONE",
    GapClass.MEASUREMENT_FAILURE: "NONE",
    GapClass.MISSING_REGRESSION: "regression_test",
}


def determine_eligibility(
    classification: GapClassificationResult,
    *,
    repository_sha: str | None = None,
    configuration_fingerprint: str | None = None,
    toolchain_fingerprint: str | None = None,
    scope_capability: str | None = None,
) -> EligibilityDecision:
    """Determine whether a classified gap is eligible for test generation.

    This is the central safety gate. It applies the C53 safety rules
    (section 7) and produces explicit refusal reasons.

    Args:
        classification: The gap classification result.
        repository_sha: Expected repository SHA (None = skip check).
        configuration_fingerprint: Expected config fingerprint (None = skip).
        toolchain_fingerprint: Expected toolchain fingerprint (None = skip).
        scope_capability: The capability scope of the current generation run.

    Returns:
        EligibilityDecision with explicit allow/refuse reasoning.
    """
    gap_id = classification.gap_id
    gap_class = classification.gap_class
    evidence = classification.evidence

    # ── Gap-class-based refusal (deterministic) ──────────────────────

    if gap_class == GapClass.EQUIVALENT:
        return EligibilityDecision(
            gap_id=gap_id,
            generation_allowed=False,
            generation_refused=True,
            refusal_reason=(
                "equivalent/non-distinguishable mutation; generating a test "
                "would inflate the score without improving defect detection"
            ),
            refusal_code=RefusalCode.EQUIVALENT_SURVIVOR,
            gap_class=gap_class,
            source_evidence=evidence.source,
            capability=classification.capability,
            component=classification.component,
            strategy="NONE",
            authorization_required=False,
            evidence=classification.to_dict(),
        )

    if gap_class == GapClass.DEFENSIVE:
        return EligibilityDecision(
            gap_id=gap_id,
            generation_allowed=False,
            generation_refused=True,
            refusal_reason=(
                "defensive/intentional behavior; manufacturing a test here "
                "optimizes the metric, not behavior"
            ),
            refusal_code=RefusalCode.DEFENSIVE_SURVIVOR,
            gap_class=gap_class,
            source_evidence=evidence.source,
            capability=classification.capability,
            component=classification.component,
            strategy="NONE",
            authorization_required=False,
            evidence=classification.to_dict(),
        )

    if gap_class == GapClass.MEASUREMENT_FAILURE:
        return EligibilityDecision(
            gap_id=gap_id,
            generation_allowed=False,
            generation_refused=True,
            refusal_reason=(
                "measurement/infrastructure failure; repair measurement before "
                "interpreting behavior. Do not generate a test."
            ),
            refusal_code=RefusalCode.MEASUREMENT_FAILURE,
            gap_class=gap_class,
            source_evidence=evidence.source,
            capability=classification.capability,
            component=classification.component,
            strategy="NONE",
            authorization_required=False,
            evidence=classification.to_dict(),
        )

    if gap_class == GapClass.DISCOVERY_GAP:
        return EligibilityDecision(
            gap_id=gap_id,
            generation_allowed=False,
            generation_refused=True,
            refusal_reason=(
                "discovery/test-selection gap; the verification system failed "
                "to discover or select the appropriate test surface. Fix at "
                "discovery/planning level, not by generating a test."
            ),
            refusal_code=RefusalCode.DISCOVERY_GAP,
            gap_class=gap_class,
            source_evidence=evidence.source,
            capability=classification.capability,
            component=classification.component,
            strategy="NONE",
            authorization_required=False,
            evidence=classification.to_dict(),
        )

    if gap_class == GapClass.HISTORICAL:
        return EligibilityDecision(
            gap_id=gap_id,
            generation_allowed=False,
            generation_refused=True,
            refusal_reason=(
                f"historical/repeated survivor (count={evidence.historical_count}); "
                "generation depends on accumulated evidence and authorization "
                "rules, not survivor count alone."
            ),
            refusal_code=RefusalCode.HISTORICAL_INSUFFICIENT,
            gap_class=gap_class,
            source_evidence=evidence.source,
            capability=classification.capability,
            component=classification.component,
            strategy="NONE",
            authorization_required=True,
            evidence=classification.to_dict(),
        )

    # ── Eligible classes (A, G) — apply additional safety checks ────

    strategy = CLASS_STRATEGY.get(gap_class, "example_based_unit")

    # Scope check: gap must be within the authorized capability scope
    if scope_capability and classification.capability != scope_capability:
        return EligibilityDecision(
            gap_id=gap_id,
            generation_allowed=False,
            generation_refused=True,
            refusal_reason=(
                f"scope drift: gap capability '{classification.capability}' "
                f"is outside the authorized scope '{scope_capability}'"
            ),
            refusal_code=RefusalCode.SCOPE_DRIFT,
            gap_class=gap_class,
            source_evidence=evidence.source,
            capability=classification.capability,
            component=classification.component,
            strategy=strategy,
            authorization_required=True,
            evidence=classification.to_dict(),
        )

    # Missing capability check
    if not classification.capability or classification.capability == "unknown":
        return EligibilityDecision(
            gap_id=gap_id,
            generation_allowed=False,
            generation_refused=True,
            refusal_reason="missing capability: cannot resolve gap to a capability",
            refusal_code=RefusalCode.MISSING_CAPABILITY,
            gap_class=gap_class,
            source_evidence=evidence.source,
            capability=classification.capability,
            component=classification.component,
            strategy=strategy,
            authorization_required=True,
            evidence=classification.to_dict(),
        )

    # Missing test surface check
    if not classification.location or classification.location == "?":
        return EligibilityDecision(
            gap_id=gap_id,
            generation_allowed=False,
            generation_refused=True,
            refusal_reason="missing test surface: cannot determine where to generate the test",
            refusal_code=RefusalCode.MISSING_TEST_SURFACE,
            gap_class=gap_class,
            source_evidence=evidence.source,
            capability=classification.capability,
            component=classification.component,
            strategy=strategy,
            authorization_required=True,
            evidence=classification.to_dict(),
        )

    # ── Eligible — authorization required ────────────────────────────

    return EligibilityDecision(
        gap_id=gap_id,
        generation_allowed=True,
        generation_refused=False,
        refusal_reason="",
        refusal_code=RefusalCode.NONE,
        gap_class=gap_class,
        source_evidence=evidence.source,
        capability=classification.capability,
        component=classification.component,
        strategy=strategy,
        authorization_required=evidence.authorization_required,
        evidence=classification.to_dict(),
    )


def determine_eligibility_batch(
    classifications: list[GapClassificationResult],
    **kwargs: Any,
) -> list[EligibilityDecision]:
    """Determine eligibility for multiple classified gaps."""
    return [determine_eligibility(c, **kwargs) for c in classifications]


__all__ = [
    "EligibilityDecision",
    "RefusalCode",
    "CLASS_STRATEGY",
    "determine_eligibility",
    "determine_eligibility_batch",
]
