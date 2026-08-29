"""
M9-C42.31 — Evidence-Driven Test Strengthening Loop (M31.x).

Closes the loop: forensic evidence → bounded, explainable
strengthening proposal → controlled approval boundary → targeted
revalidation → accept/reject.

The goal is NOT autonomous uncontrolled test generation and NEVER
score-chasing. Every action originates from classified survivor /
failure evidence, and every class-B/C/E case is explicitly refused.

Survivor classification taxonomy (closed):

    CLASS A — genuine behavioral weakness.
              Potential strengthening candidate.
    CLASS B — equivalent / observable-equivalent behavior.
              Do not chase.
    CLASS C — defensive / unreachable / infrastructure-related.
              Do not manufacture tests merely for score.
    CLASS D — infrastructure/measurement problem.
              Repair measurement before interpreting behavior.
    CLASS E — ambiguous / design / production-defect candidate.
              Escalate for human review.

The agent never converts B/C/E into artificial Class-A work.

Loop contract (per accepted proposal):
    Before -> Targeted change -> Targeted verification (C42.28 bridge,
    never a full campaign) -> After -> hypothesis validated?

Automation boundary (first version):
    detect -> diagnose -> propose -> validate.
    Production code is never modified autonomously. Even test-file
    modification stays behind the explicit approval boundary until the
    evidence system proves sufficient reliability.
"""

from __future__ import annotations

import hashlib
import sys
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

STRENGTHENING_PROPOSAL_SCHEMA = "m9-strengthening-proposal/v1"

SurvivorClass = Literal["A", "B", "C", "D", "E"]
SURVIVOR_CLASSES: tuple[SurvivorClass, ...] = ("A", "B", "C", "D", "E")

CLASS_DESCRIPTIONS: dict[SurvivorClass, str] = {
    "A": "genuine behavioral weakness; potential strengthening candidate",
    "B": "equivalent/observable-equivalent behavior; do not chase",
    "C": "defensive/unreachable/infrastructure-related; do not manufacture score",
    "D": "infrastructure/measurement problem; repair measurement first",
    "E": "ambiguous/design/production-defect candidate; escalate for human review",
}


# ===========================================================================
# Survivor evidence model (input)
# ===========================================================================


@dataclass(frozen=True, slots=True)
class SurvivorEvidence:
    """One surviving mutant (or failing verification signal) with the
    metadata the classifier needs. Derived from mutation summary
    artifacts / forensic records — never invented."""

    survivor_id: str
    component: str
    capability: str
    location: str  # file:function or file:line
    mutation_operator: str  # e.g. "comparison", "arithmetic", "boolean"
    original_snippet: str = ""
    mutated_snippet: str = ""
    status: str = "survived"  # survived|no_tests|timeout|suspicious
    notes: str = ""
    covering_tests: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "survivor_id": self.survivor_id,
            "component": self.component,
            "capability": self.capability,
            "location": self.location,
            "mutation_operator": self.mutation_operator,
            "original_snippet": self.original_snippet,
            "mutated_snippet": self.mutated_snippet,
            "status": self.status,
            "notes": self.notes,
            "covering_tests": list(self.covering_tests),
        }


# ===========================================================================
# Classification — deterministic, enumerated patterns only
# ===========================================================================

# Defensive-code patterns: mutations inside logging/observability code
# are not behavioral business logic.
DEFENSIVE_PATTERNS: tuple[str, ...] = (
    "logger.",
    "logging.",
    "console.",
    "print(",
    "metrics.",
    "_record(",
    "audit(",
)

# Measurement-integrity signals: the mutant's outcome reflects the
# measurement machinery, not product behavior.
MEASUREMENT_STATUSES: tuple[str, ...] = ("timeout", "suspicious")

# Explicit escalation markers (set upstream by forensic analysis).
ESCALATION_MARKERS: tuple[str, ...] = (
    "production_defect_candidate",
    "ambiguous_behavior",
    "design_question",
)


def classify_survivor(s: SurvivorEvidence) -> SurvivorClass:
    """Classify one survivor into exactly one of classes A–E.

    Deterministic precedence:
      D — measurement integrity problem (timeout/suspicious status)
      B — equivalence already established upstream
      C — defensive/unreachable code pattern
      E — explicit escalation marker
      A — everything else (genuine behavioral gap candidate)
    """
    if s.status in MEASUREMENT_STATUSES:
        return "D"
    if "equivalent" in s.notes.lower():
        return "B"
    if any(
        p in s.original_snippet.lower() or p in s.mutated_snippet.lower()
        for p in DEFENSIVE_PATTERNS
    ):
        return "C"
    if any(m in s.notes.lower() for m in ESCALATION_MARKERS):
        return "E"
    return "A"


# Operator → bounded behavioral-hypothesis templates. Deliberately
# narrow: the framework proposes WHAT INVARIANT to check; it does not
# invent business logic.
_HYPOTHESIS_TEMPLATES: dict[str, str] = {
    "comparison": (
        "boundary/ordering behavior at '{location}' is load-bearing: "
        "the mutated comparison would change decisions at the boundary"
    ),
    "arithmetic": (
        "numeric computation at '{location}' must preserve its exact "
        "formula; the mutated arithmetic changes financial results"
    ),
    "boolean": (
        "the condition at '{location}' gates a distinct behavior branch; "
        "inverting it silently enables/disables that behavior"
    ),
    "return": (
        "the return value at '{location}' is part of the component's "
        "observable contract"
    ),
}


# ===========================================================================
# Strengthening proposal contract + refusals
# ===========================================================================


@dataclass(frozen=True, slots=True)
class RejectionRecord:
    """Explicit refusal to chase a non-Class-A survivor."""

    survivor_id: str
    classification: SurvivorClass
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "survivor_id": self.survivor_id,
            "classification": self.classification,
            "reason": self.reason,
        }


@dataclass(frozen=True, slots=True)
class StrengtheningProposal:
    """A bounded, evidence-derived, explainable strengthening proposal."""

    schema: str
    proposal_id: str
    component: str
    capability: str
    source_location: str
    survivor_evidence: dict[str, Any]
    classification: SurvivorClass
    behavioral_hypothesis: str
    expected_invariant: str
    proposed_test_surface: str
    proposed_test: str  # concrete pytest skeleton
    reason: str
    expected_mutation_discrimination: str
    regression_risk: Literal["low", "medium", "high"]
    validation_command: str
    acceptance_criteria: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "proposal_id": self.proposal_id,
            "component": self.component,
            "capability": self.capability,
            "source_location": self.source_location,
            "survivor_evidence": dict(self.survivor_evidence),
            "classification": self.classification,
            "behavioral_hypothesis": self.behavioral_hypothesis,
            "expected_invariant": self.expected_invariant,
            "proposed_test_surface": self.proposed_test_surface,
            "proposed_test": self.proposed_test,
            "reason": self.reason,
            "expected_mutation_discrimination": (self.expected_mutation_discrimination),
            "regression_risk": self.regression_risk,
            "validation_command": self.validation_command,
            "acceptance_criteria": list(self.acceptance_criteria),
        }


def generate_proposal(s: SurvivorEvidence) -> StrengtheningProposal | RejectionRecord:
    """Convert ONE piece of survivor evidence into either a bounded
    Class-A proposal or an explicit refusal. Never fabricates work for
    B/C/D/E survivors."""
    cls = classify_survivor(s)

    if cls == "B":
        return RejectionRecord(
            s.survivor_id,
            "B",
            "equivalent/observable-equivalent behavior; targeting it "
            "would inflate the score without improving defect detection",
        )
    if cls == "C":
        return RejectionRecord(
            s.survivor_id,
            "C",
            "defensive/observability code; manufacturing a test here "
            "optimizes the metric, not behavior",
        )
    if cls == "D":
        return RejectionRecord(
            s.survivor_id,
            "D",
            "measurement integrity problem (timeout/suspicious); repair "
            "measurement before interpreting behavior",
        )
    if cls == "E":
        return RejectionRecord(
            s.survivor_id,
            "E",
            "ambiguous/design/possible production defect; requires human "
            "review before any test is written",
        )

    template = _HYPOTHESIS_TEMPLATES.get(
        s.mutation_operator,
        "the mutated expression at '{location}' changes observable behavior",
    )
    hypothesis = template.format(location=s.location)
    pid = hashlib.sha256(
        "|".join([s.survivor_id, s.component, s.location]).encode()
    ).hexdigest()[:12]
    test_dir = f"backend/tests/unit/engines/{s.component}"

    return StrengtheningProposal(
        schema=STRENGTHENING_PROPOSAL_SCHEMA,
        proposal_id=f"prop::{pid}",
        component=s.component,
        capability=s.capability,
        source_location=s.location,
        survivor_evidence=s.to_dict(),
        classification="A",
        behavioral_hypothesis=hypothesis,
        expected_invariant=(
            f"behavior at {s.location} follows the original expression "
            f"`{s.original_snippet.strip()}`; the mutated form "
            f"`{s.mutated_snippet.strip()}` must be rejected by the "
            "proposed test"
        ),
        proposed_test_surface=(f"{test_dir}/test_strengthening_{pid}.py"),
        proposed_test=(
            f"def test_{pid}():\n"
            f'    """Discriminates survivor {s.survivor_id}: '
            f'{hypothesis}"""\n'
            f"    ...  # exercise {s.location}; assert the original "
            "semantics\n"
        ),
        reason=(
            f"classified A: survivor {s.survivor_id} at {s.location} has "
            f"{len(s.covering_tests)} covering test(s) yet survives; the "
            "surface asserts less than the behavior guarantees"
            if s.covering_tests
            else f"classified A: no test reaches {s.location}; the "
            "behavior is entirely unasserted"
        ),
        expected_mutation_discrimination=(
            f"mutant {s.survivor_id} transitions survived->killed under "
            f"the proposed test for {s.component}"
        ),
        regression_risk="low",
        validation_command=(
            f".venv/bin/python -m pytest {test_dir} -q && "
            f".venv/bin/python runtime/verify.py strengthen-validate "
            f"--proposal prop::{pid} --component {s.component}"
        ),
        acceptance_criteria=(
            "proposed test fails against the mutated expression",
            "proposed test passes against the original expression",
            "targeted re-measurement shows killed>=killed_before+1 with "
            "zero kill regressions",
            "no production source modified",
        ),
    )


# ===========================================================================
# Approval boundary (explicit — section 15 of the phase directive)
# ===========================================================================


@dataclass(frozen=True, slots=True)
class ApprovalDecision:
    proposal_id: str
    approved: bool
    approver: str  # "human:<id>" | "controlled-loop"
    conditions: tuple[str, ...]
    decided_at: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "proposal_id": self.proposal_id,
            "approved": self.approved,
            "approver": self.approver,
            "conditions": list(self.conditions),
            "decided_at": self.decided_at,
        }


def evaluate_auto_approval_eligibility(p: StrengtheningProposal) -> ApprovalDecision:
    """Decide whether a proposal MAY (not must) proceed without an
    explicit human click.

    Test-file modification only where the framework can prove the
    proposed test is: deterministic, behaviorally justified, within the
    affected capability, regression-safe, and not score-only optimization.
    Production code is NEVER eligible.
    """
    conditions: list[str] = []

    if p.classification != "A":
        conditions.append("only Class-A proposals are ever eligible")
    if not p.survivor_evidence:
        conditions.append("missing survivor evidence provenance")
    if "..." in p.proposed_test and len(p.proposed_test.splitlines()) <= 3:
        # Skeleton-only proposals need human authorship of the body.
        conditions.append("test body requires human authorship")
    if p.regression_risk != "low":
        conditions.append("non-low regression risk requires human review")

    return ApprovalDecision(
        proposal_id=p.proposal_id,
        approved=False,  # the boundary itself never auto-approves execution
        approver="approval-boundary",
        conditions=tuple(conditions)
        or ("eligible for controlled-loop validation after human review",),
        decided_at=datetime.now(UTC).isoformat(),
    )


# ===========================================================================
# Targeted re-measurement (before/after via the C42.28 bridge)
# ===========================================================================

ExecutorFn = Callable[..., Any]


@dataclass(frozen=True, slots=True)
class RevalidationOutcome:
    """Before → targeted change → targeted verification → After."""

    proposal_id: str
    component: str
    before_killed: int
    before_generated: int
    after_killed: int
    after_generated: int
    target_mutant_killed: bool
    kill_regressions: int
    hypothesis_validated: bool
    accepted: bool
    rationale: str
    used_full_campaign: bool = False  # MUST remain False by construction

    def to_dict(self) -> dict[str, Any]:
        return {
            "proposal_id": self.proposal_id,
            "component": self.component,
            "before": {
                "killed": self.before_killed,
                "generated": self.before_generated,
            },
            "after": {"killed": self.after_killed, "generated": self.after_generated},
            "target_mutant_killed": self.target_mutant_killed,
            "kill_regressions": self.kill_regressions,
            "hypothesis_validated": self.hypothesis_validated,
            "accepted": self.accepted,
            "rationale": self.rationale,
            "used_full_campaign": self.used_full_campaign,
        }


def targeted_revalidation(
    proposal: StrengtheningProposal,
    *,
    before_counts: dict[str, int],
    executor: ExecutorFn,
    target_survivor_id: str | None = None,
) -> RevalidationOutcome:
    """Run AFTER-verification through the C42.28 targeted bridge only.

    ``executor`` is the canonical C42.28 task executor
    (``execute_mutation_task`` or a deterministic stub in tests). It
    receives the component and returns an object carrying ``counts``
    with generated/killed/survived plus per-mutant status mapping when
    available (``mutant_statuses`` dict).
    """
    component = proposal.component
    before_killed = int(before_counts.get("killed", 0))
    before_generated = int(before_counts.get("generated", 0))

    result = executor(component)
    counts = getattr(result, "counts", None) or {}
    after_killed = int(counts.get("killed", 0))
    after_generated = int(counts.get("generated", 0))

    statuses = getattr(result, "mutant_statuses", None) or {}
    sid = target_survivor_id or _extract_survivor_id(proposal)
    target_killed = (
        statuses.get(sid) == "killed" if statuses else (after_killed > before_killed)
    )

    regressions = (
        max(0, min(before_killed, after_generated) - after_killed)
        if after_generated < before_generated
        else max(0, before_killed - after_killed)
    )

    validated = bool(target_killed and regressions == 0)
    if regressions > 0:
        accepted = False
        rationale = (
            f"rejected: {regressions} previously-killed mutant(s) now "
            "survive; the strengthening change regressed existing "
            "discrimination"
        )
    elif validated:
        accepted = True
        rationale = (
            f"accepted: target mutant {sid} now killed with zero kill "
            "regressions; behavioral hypothesis validated"
        )
    else:
        accepted = False
        rationale = (
            f"rejected: target mutant {sid} still survives; the proposed "
            "test did not discriminate the hypothesized behavior gap"
        )

    return RevalidationOutcome(
        proposal_id=proposal.proposal_id,
        component=component,
        before_killed=before_killed,
        before_generated=before_generated,
        after_killed=after_killed,
        after_generated=after_generated,
        target_mutant_killed=bool(target_killed),
        kill_regressions=regressions,
        hypothesis_validated=validated,
        accepted=accepted,
        rationale=rationale,
        used_full_campaign=False,
    )


def _extract_survivor_id(proposal: StrengtheningProposal) -> str:
    return str((proposal.survivor_evidence or {}).get("survivor_id", ""))


# ===========================================================================
# Full-campaign discipline (section 13)
# ===========================================================================

FULL_CAMPAIGN_TRIGGERS: tuple[str, ...] = (
    "population_expansion",
    "major_verification_architecture_change",
    "mutation_infrastructure_change",
    "mutation_configuration_semantic_change",
    "significant_cross_component_architecture_change",
    "periodic_measurement_checkpoint",
    "final_certification_milestone",
)

NOT_TRIGGERS: tuple[str, ...] = (
    "test_addition",
    "test_strengthening",
    "score_improvement_desire",
)


@dataclass(frozen=True, slots=True)
class FullCampaignJustification:
    """Mandatory artifact BEFORE any full campaign may be planned."""

    trigger: str
    population_affected: tuple[str, ...]
    evidence_invalidated: tuple[str, ...]
    why_targeted_insufficient: str
    expected_information_gained: str
    estimated_resource_cost: str
    certification_consequence: str
    why_mathematical_reconciliation_cannot_answer: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "trigger": self.trigger,
            "population_affected": list(self.population_affected),
            "evidence_invalidated": list(self.evidence_invalidated),
            "why_targeted_insufficient": self.why_targeted_insufficient,
            "expected_information_gained": self.expected_information_gained,
            "estimated_resource_cost": self.estimated_resource_cost,
            "certification_consequence": self.certification_consequence,
            "why_mathematical_reconciliation_cannot_answer": (
                self.why_mathematical_reconciliation_cannot_answer
            ),
        }


@dataclass(frozen=True, slots=True)
class CampaignGateDecision:
    permitted: bool
    reason: str
    justification: dict[str, Any] | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "permitted": self.permitted,
            "reason": self.reason,
            "justification": self.justification,
        }


def gate_full_campaign(
    requested_trigger: str,
    justification: FullCampaignJustification | None,
) -> CampaignGateDecision:
    """The planner-level gate: reject any full campaign whose trigger is
    not one of the formal C42.26 triggers or which lacks complete
    justification. Test additions alone can NEVER justify one."""
    if requested_trigger in NOT_TRIGGERS:
        return CampaignGateDecision(
            False,
            f"'{requested_trigger}' is formally excluded as a trigger; "
            "targeted measurement remains the default",
            justification.to_dict() if justification else None,
        )
    if requested_trigger not in FULL_CAMPAIGN_TRIGGERS:
        return CampaignGateDecision(
            False,
            f"unknown trigger '{requested_trigger}'; valid triggers: "
            + ", ".join(FULL_CAMPAIGN_TRIGGERS),
            None,
        )
    if justification is None:
        return CampaignGateDecision(
            False,
            "full campaign requires a complete FullCampaignJustification "
            "artifact; none supplied",
            None,
        )
    d = justification.to_dict()
    incomplete = [k for k, v in d.items() if not v]
    if incomplete:
        return CampaignGateDecision(
            False,
            f"incomplete justification fields: {incomplete}",
            d,
        )
    return CampaignGateDecision(
        True,
        f"trigger '{requested_trigger}' is formal and justification is complete",
        d,
    )


__all__ = [
    "ApprovalDecision",
    "CampaignGateDecision",
    "CLASS_DESCRIPTIONS",
    "DEFENSIVE_PATTERNS",
    "FULL_CAMPAIGN_TRIGGERS",
    "FullCampaignJustification",
    "MEASUREMENT_STATUSES",
    "NOT_TRIGGERS",
    "RejectionRecord",
    "RevalidationOutcome",
    "STRENGTHENING_PROPOSAL_SCHEMA",
    "SURVIVOR_CLASSES",
    "SurvivorClass",
    "SurvivorEvidence",
    "StrengtheningProposal",
    "classify_survivor",
    "evaluate_auto_approval_eligibility",
    "gate_full_campaign",
    "generate_proposal",
    "targeted_revalidation",
]
