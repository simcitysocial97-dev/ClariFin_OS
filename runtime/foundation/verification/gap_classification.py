# runtime/foundation/verification/gap_classification.py
#
# M9-C53 — Verification Gap Classification Taxonomy (A–G).
#
# Extends the certified C42.31 survivor classification (A–E) with two
# additional gap classes (F, G) required by the C53 evidence-driven test
# generation pipeline. This module does NOT replace the C42 classifier —
# it wraps and extends it for the broader gap-classification context
# (mutation survivors, coverage gaps, contract failures, property failures,
# historical regressions, etc.).
#
# Taxonomy (closed):
#
#   A — Genuine Behavioral Verification Gap
#       A real behavioral path lacks a distinguishing assertion/test.
#       Potentially eligible for test generation.
#
#   B — Equivalent / Non-distinguishable Mutation
#       Do NOT generate a test merely to kill it.
#       Record the equivalence determination and preserve the evidence.
#
#   C — Defensive / Intentional Behavior
#       Do NOT generate a test merely because a mutation survives.
#
#   D — Discovery / Test-Selection Gap
#       The verification system failed to discover or select the appropriate
#       test surface. Fixed at discovery/planning level, not by generation.
#
#   E — Historical / Repeated Survivor
#       Use the existing historical evidence machinery. Generation depends
#       on accumulated evidence and authorization rules, not survivor count.
#
#   F — Measurement / Infrastructure Failure
#       Do NOT generate a test. Repair or classify the measurement problem.
#
#   G — Legitimate Missing Regression
#       A known behavioral regression lacks a durable regression test.
#       Potentially eligible for generation, subject to authorization.
#
# Deterministic precedence (highest priority first):
#   F — measurement/infrastructure failure
#   B — equivalent / non-distinguishable
#   C — defensive / intentional
#   D — discovery / test-selection gap
#   E — historical / repeated (with insufficient evidence for A)
#   G — legitimate missing regression (evidence-backed)
#   A — genuine behavioral gap (default when evidence supports it)

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from runtime.foundation.verification.strengthening import (
    SurvivorEvidence,
    classify_survivor,
)

REPO_ROOT = (
    __import__("pathlib", fromlist=["Path"])
    .Path(__file__)
    .resolve()
    .parent.parent.parent.parent
)


class GapClass(str, Enum):
    """Closed gap classification taxonomy (A–G)."""

    A_GENUINE_BEHAVIORAL = "A"
    EQUIVALENT = "B"
    DEFENSIVE = "C"
    DISCOVERY_GAP = "D"
    HISTORICAL = "E"
    MEASUREMENT_FAILURE = "F"
    MISSING_REGRESSION = "G"


GAP_CLASS_DESCRIPTIONS: dict[GapClass, str] = {
    GapClass.A_GENUINE_BEHAVIORAL: (
        "genuine behavioral verification gap; potentially eligible for test generation"
    ),
    GapClass.EQUIVALENT: (
        "equivalent/non-distinguishable mutation; do not generate a test"
    ),
    GapClass.DEFENSIVE: (
        "defensive/intentional behavior; do not manufacture a test for score"
    ),
    GapClass.DISCOVERY_GAP: (
        "discovery/test-selection gap; fix at discovery/planning level"
    ),
    GapClass.HISTORICAL: (
        "historical/repeated survivor; generation depends on accumulated evidence"
    ),
    GapClass.MEASUREMENT_FAILURE: (
        "measurement/infrastructure failure; repair measurement, do not generate"
    ),
    GapClass.MISSING_REGRESSION: (
        "legitimate missing regression; potentially eligible, subject to authorization"
    ),
}

# Source types that can produce gaps
GapSource = str  # "survivor" | "coverage_gap" | "contract_failure" | "property_failure" | "historical_regression" | "capability_evidence_gap" | "cross_capability_failure"


@dataclass(frozen=True, slots=True)
class GapEvidence:
    """One piece of evidence describing a verification gap.

    This is the canonical input to the gap classifier. It generalizes
    SurvivorEvidence to cover all C53 gap sources.
    """

    gap_id: str
    source: GapSource
    component: str
    capability: str
    location: str
    description: str
    evidence_kind: str = (
        ""  # mutation_operator | uncovered_branch | contract_rule | property_name | regression_id
    )
    evidence_detail: str = ""  # original/mutated snippet, contract rule, etc.
    status: str = (
        "survived"  # survived | no_tests | timeout | suspicious | uncovered | failed
    )
    notes: str = ""
    covering_tests: tuple[str, ...] = ()
    historical_count: int = 1  # how many times this gap has been observed
    historical_evidence_refs: tuple[str, ...] = ()
    authorization_required: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "gap_id": self.gap_id,
            "source": self.source,
            "component": self.component,
            "capability": self.capability,
            "location": self.location,
            "description": self.description,
            "evidence_kind": self.evidence_kind,
            "evidence_detail": self.evidence_detail,
            "status": self.status,
            "notes": self.notes,
            "covering_tests": list(self.covering_tests),
            "historical_count": self.historical_count,
            "historical_evidence_refs": list(self.historical_evidence_refs),
            "authorization_required": self.authorization_required,
        }


@dataclass(frozen=True, slots=True)
class GapClassificationResult:
    """The complete classification of one gap."""

    gap_id: str
    gap_class: GapClass
    description: str
    source: GapSource
    component: str
    capability: str
    location: str
    eligible_for_generation: bool
    reason: str
    evidence: GapEvidence
    classified_at: str = ""
    c42_class: str = ""  # the underlying C42 classification (when applicable)

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "classified_at",
            self.classified_at or datetime.now(UTC).isoformat(),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "gap_id": self.gap_id,
            "gap_class": self.gap_class.value,
            "description": GAP_CLASS_DESCRIPTIONS[self.gap_class],
            "source": self.source,
            "component": self.component,
            "capability": self.capability,
            "location": self.location,
            "eligible_for_generation": self.eligible_for_generation,
            "reason": self.reason,
            "evidence": self.evidence.to_dict(),
            "classified_at": self.classified_at,
            "c42_class": self.c42_class,
        }


# Measurement-integrity signals (from C42)
_MEASUREMENT_STATUSES: tuple[str, ...] = ("timeout", "suspicious")
_EQUIVALENCE_MARKERS: tuple[str, ...] = (
    "equivalent",
    "non-distinguishable",
    "observable-equivalent",
)
_DEFENSIVE_MARKERS: tuple[str, ...] = (
    "logger.",
    "logging.",
    "console.",
    "print(",
    "metrics.",
    "_record(",
    "audit(",
)
_DISCOVERY_GAP_MARKERS: tuple[str, ...] = (
    "no_test_surface",
    "discovery_failure",
    "test_selection_failure",
    "unmapped_capability",
)
_HISTORICAL_MARKERS: tuple[str, ...] = (
    "repeated_survivor",
    "historical_survivor",
    "persistent_gap",
)
_REGRESSION_MARKERS: tuple[str, ...] = (
    "regression",
    "known_regression",
    "missing_regression_test",
)


def classify_gap(evidence: GapEvidence) -> GapClassificationResult:
    """Classify one gap into exactly one of classes A–G.

    Deterministic precedence (highest priority first):
      F — measurement/infrastructure failure
      B — equivalent / non-distinguishable
      C — defensive / intentional
      D — discovery / test-selection gap
      E — historical / repeated (with insufficient evidence)
      G — legitimate missing regression
      A — genuine behavioral gap (default)
    """
    # F — measurement/infrastructure failure
    if evidence.status in _MEASUREMENT_STATUSES:
        return GapClassificationResult(
            gap_id=evidence.gap_id,
            gap_class=GapClass.MEASUREMENT_FAILURE,
            description=GAP_CLASS_DESCRIPTIONS[GapClass.MEASUREMENT_FAILURE],
            source=evidence.source,
            component=evidence.component,
            capability=evidence.capability,
            location=evidence.location,
            eligible_for_generation=False,
            reason=(
                f"measurement/infrastructure failure (status={evidence.status}); "
                "repair measurement before interpreting behavior"
            ),
            evidence=evidence,
        )

    # B — equivalent / non-distinguishable
    if any(m in evidence.notes.lower() for m in _EQUIVALENCE_MARKERS):
        return GapClassificationResult(
            gap_id=evidence.gap_id,
            gap_class=GapClass.EQUIVALENT,
            description=GAP_CLASS_DESCRIPTIONS[GapClass.EQUIVALENT],
            source=evidence.source,
            component=evidence.component,
            capability=evidence.capability,
            location=evidence.location,
            eligible_for_generation=False,
            reason=(
                "equivalent/non-distinguishable behavior; targeting it would "
                "inflate the score without improving defect detection"
            ),
            evidence=evidence,
        )

    # C — defensive / intentional
    if any(m in evidence.evidence_detail.lower() for m in _DEFENSIVE_MARKERS):
        return GapClassificationResult(
            gap_id=evidence.gap_id,
            gap_class=GapClass.DEFENSIVE,
            description=GAP_CLASS_DESCRIPTIONS[GapClass.DEFENSIVE],
            source=evidence.source,
            component=evidence.component,
            capability=evidence.capability,
            location=evidence.location,
            eligible_for_generation=False,
            reason=(
                "defensive/intentional behavior; manufacturing a test here "
                "optimizes the metric, not behavior"
            ),
            evidence=evidence,
        )

    # D — discovery / test-selection gap
    if any(m in evidence.notes.lower() for m in _DISCOVERY_GAP_MARKERS):
        return GapClassificationResult(
            gap_id=evidence.gap_id,
            gap_class=GapClass.DISCOVERY_GAP,
            description=GAP_CLASS_DESCRIPTIONS[GapClass.DISCOVERY_GAP],
            source=evidence.source,
            component=evidence.component,
            capability=evidence.capability,
            location=evidence.location,
            eligible_for_generation=False,
            reason=(
                "discovery/test-selection gap; the verification system failed to "
                "discover or select the appropriate test surface. Fix at "
                "discovery/planning level, not by generating a test."
            ),
            evidence=evidence,
        )

    # G — legitimate missing regression (must be detected before A)
    if evidence.source == "historical_regression" or any(
        m in evidence.notes.lower() for m in _REGRESSION_MARKERS
    ):
        return GapClassificationResult(
            gap_id=evidence.gap_id,
            gap_class=GapClass.MISSING_REGRESSION,
            description=GAP_CLASS_DESCRIPTIONS[GapClass.MISSING_REGRESSION],
            source=evidence.source,
            component=evidence.component,
            capability=evidence.capability,
            location=evidence.location,
            eligible_for_generation=True,
            reason=(
                "legitimate missing regression; a known behavioral regression "
                "lacks a durable regression test. Eligible for generation, "
                "subject to authorization."
            ),
            evidence=evidence,
        )

    # E — historical / repeated (with insufficient evidence for A)
    if evidence.historical_count >= 3 or any(
        m in evidence.notes.lower() for m in _HISTORICAL_MARKERS
    ):
        return GapClassificationResult(
            gap_id=evidence.gap_id,
            gap_class=GapClass.HISTORICAL,
            description=GAP_CLASS_DESCRIPTIONS[GapClass.HISTORICAL],
            source=evidence.source,
            component=evidence.component,
            capability=evidence.capability,
            location=evidence.location,
            eligible_for_generation=False,
            reason=(
                f"historical/repeated survivor (count={evidence.historical_count}); "
                "generation depends on accumulated evidence and authorization "
                "rules, not survivor count alone."
            ),
            evidence=evidence,
        )

    # For survivor sources, cross-check with the C42 classifier
    if evidence.source == "survivor":
        c4_survivor = SurvivorEvidence(
            survivor_id=evidence.gap_id,
            component=evidence.component,
            capability=evidence.capability,
            location=evidence.location,
            mutation_operator=evidence.evidence_kind,
            original_snippet=evidence.evidence_detail,
            mutated_snippet="",
            status=evidence.status,
            notes=evidence.notes,
            covering_tests=evidence.covering_tests,
        )
        c42_cls = classify_survivor(c4_survivor)
        if c42_cls in ("B", "C", "D", "E"):
            gap_class = {
                "B": GapClass.EQUIVALENT,
                "C": GapClass.DEFENSIVE,
                "D": GapClass.MEASUREMENT_FAILURE,
                "E": GapClass.HISTORICAL,
            }[c42_cls]
            return GapClassificationResult(
                gap_id=evidence.gap_id,
                gap_class=gap_class,
                description=GAP_CLASS_DESCRIPTIONS[gap_class],
                source=evidence.source,
                component=evidence.component,
                capability=evidence.capability,
                location=evidence.location,
                eligible_for_generation=False,
                reason=(
                    f"C42 classifier confirms class {c42_cls}: "
                    f"{GAP_CLASS_DESCRIPTIONS[gap_class]}"
                ),
                evidence=evidence,
                c42_class=c42_cls,
            )

    # A — genuine behavioral gap (default)
    return GapClassificationResult(
        gap_id=evidence.gap_id,
        gap_class=GapClass.A_GENUINE_BEHAVIORAL,
        description=GAP_CLASS_DESCRIPTIONS[GapClass.A_GENUINE_BEHAVIORAL],
        source=evidence.source,
        component=evidence.component,
        capability=evidence.capability,
        location=evidence.location,
        eligible_for_generation=True,
        reason=(
            "genuine behavioral verification gap; a real behavioral path lacks "
            "a distinguishing assertion/test. Potentially eligible for generation."
        ),
        evidence=evidence,
        c42_class="A",
    )


def classify_gaps(evidences: list[GapEvidence]) -> list[GapClassificationResult]:
    """Classify multiple gaps. Returns results in the same order."""
    return [classify_gap(e) for e in evidences]


def _id(*parts: str) -> str:
    return hashlib.sha256("|".join(parts).encode()).hexdigest()[:12]


__all__ = [
    "GapClass",
    "GAP_CLASS_DESCRIPTIONS",
    "GapEvidence",
    "GapClassificationResult",
    "GapSource",
    "classify_gap",
    "classify_gaps",
]
