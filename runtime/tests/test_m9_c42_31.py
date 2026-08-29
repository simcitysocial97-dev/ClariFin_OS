"""
M9-C42.31 — Test suite for the evidence-driven strengthening loop.

Covers:
  * Survivor classification A–E (deterministic precedence)
  * Proposal contract completeness (14 fields)
  * Class B/C/D/E refusals (never converted to Class-A work)
  * Targeted revalidation: accept / reject / regression-reject
  * Full-campaign discipline gate
  * Automation boundary (approval never auto-executes)

Run with:
    .venv/bin/python -m pytest runtime/tests/test_m9_c42_31.py -v
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from runtime.foundation.verification.strengthening import (  # noqa: E402
    CLASS_DESCRIPTIONS,
    FULL_CAMPAIGN_TRIGGERS,
    NOT_TRIGGERS,
    STRENGTHENING_PROPOSAL_SCHEMA,
    SURVIVOR_CLASSES,
    FullCampaignJustification,
    RejectionRecord,
    StrengtheningProposal,
    SurvivorEvidence,
    classify_survivor,
    evaluate_auto_approval_eligibility,
    gate_full_campaign,
    generate_proposal,
    targeted_revalidation,
)


def _class_a(**kw) -> SurvivorEvidence:
    defaults = {
        "survivor_id": "mut-cc-0001",
        "component": "credit_card_engine",
        "capability": "credit-card-risk",
        "location": "risk.py:compute_apr",
        "mutation_operator": "comparison",
        "original_snippet": "if utilization >= threshold:",
        "mutated_snippet": "if utilization > threshold:",
        "status": "survived",
        "covering_tests": ("t1",),
    }
    defaults.update(kw)
    return SurvivorEvidence(**defaults)


@dataclass
class StubResult:
    counts: dict = field(default_factory=dict)
    mutant_statuses: dict = field(default_factory=dict)


def _proposal() -> StrengtheningProposal:
    out = generate_proposal(_class_a())
    assert isinstance(out, StrengtheningProposal)
    return out


# ---------------------------------------------------------------------------
# Classification
# ---------------------------------------------------------------------------


class TestClassification:
    def test_class_taxonomy_closed_and_documented(self) -> None:
        assert SURVIVOR_CLASSES == ("A", "B", "C", "D", "E")
        for c in SURVIVOR_CLASSES:
            assert c in CLASS_DESCRIPTIONS

    def test_genuine_gap_is_class_a(self) -> None:
        assert classify_survivor(_class_a()) == "A"

    def test_equivalent_is_class_b(self) -> None:
        s = _class_a(notes="classified equivalent upstream")
        assert classify_survivor(s) == "B"

    def test_defensive_is_class_c(self) -> None:
        s = _class_a(
            original_snippet="logger.info('x')",
            mutated_snippet="logger.error('x')",
        )
        assert classify_survivor(s) == "C"

    def test_timeout_is_class_d(self) -> None:
        s = _class_a(status="timeout")
        assert classify_survivor(s) == "D"

    def test_suspicious_is_class_d(self) -> None:
        s = _class_a(status="suspicious")
        assert classify_survivor(s) == "D"

    def test_escalation_marker_is_class_e(self) -> None:
        s = _class_a(notes="production_defect_candidate per review")
        assert classify_survivor(s) == "E"

    def test_measurement_status_outranks_equivalence(self) -> None:
        # D precedes B: a timeout must not be dismissed as equivalent.
        s = _class_a(status="timeout", notes="equivalent")
        assert classify_survivor(s) == "D"


# ---------------------------------------------------------------------------
# Proposals + refusals
# ---------------------------------------------------------------------------


class TestProposals:
    def test_contract_complete_for_class_a(self) -> None:
        p = _proposal()
        d = p.to_dict()
        required = [
            "component",
            "capability",
            "source_location",
            "survivor_evidence",
            "classification",
            "behavioral_hypothesis",
            "expected_invariant",
            "proposed_test_surface",
            "proposed_test",
            "reason",
            "expected_mutation_discrimination",
            "regression_risk",
            "validation_command",
            "acceptance_criteria",
        ]
        missing = [k for k in required if k not in d or d[k] in (None, "", [])]
        assert not missing
        assert p.schema == STRENGTHENING_PROPOSAL_SCHEMA

    def test_proposal_explains_why_test_should_exist(self) -> None:
        p = _proposal()
        assert "survives" in p.reason or "unasserted" in p.reason
        assert p.expected_invariant
        assert len(p.acceptance_criteria) >= 3

    def test_class_b_rejected(self) -> None:
        out = generate_proposal(_class_a(notes="equivalent"))
        assert isinstance(out, RejectionRecord)
        assert out.classification == "B"
        assert not isinstance(out, StrengtheningProposal)

    def test_class_c_rejected(self) -> None:
        out = generate_proposal(
            _class_a(original_snippet="print(x)", mutated_snippet="print(y)")
        )
        assert isinstance(out, RejectionRecord)
        assert out.classification == "C"

    def test_class_d_rejected_measurement_first(self) -> None:
        out = generate_proposal(_class_a(status="timeout"))
        assert isinstance(out, RejectionRecord)
        assert "measurement" in out.reason.lower()

    def test_class_e_rejected_with_human_review(self) -> None:
        out = generate_proposal(_class_a(notes="ambiguous_behavior flagged"))
        assert isinstance(out, RejectionRecord)
        assert "human" in out.reason.lower()


# ---------------------------------------------------------------------------
# Targeted revalidation
# ---------------------------------------------------------------------------


class TestTargetedRevalidation:
    def test_accept_when_target_killed_no_regressions(self) -> None:
        executor = lambda component: StubResult(  # noqa: E731
            counts={"generated": 582, "killed": 441},
            mutant_statuses={"mut-cc-0001": "killed"},
        )
        outcome = targeted_revalidation(
            _proposal(),
            before_counts={"killed": 440, "generated": 582},
            executor=executor,
        )
        assert outcome.accepted
        assert outcome.hypothesis_validated
        assert outcome.used_full_campaign is False
        assert outcome.kill_regressions == 0

    def test_reject_when_target_still_survives(self) -> None:
        executor = lambda component: StubResult(  # noqa: E731
            counts={"generated": 582, "killed": 440},
            mutant_statuses={"mut-cc-0001": "survived"},
        )
        outcome = targeted_revalidation(
            _proposal(),
            before_counts={"killed": 440, "generated": 582},
            executor=executor,
        )
        assert not outcome.accepted
        assert "did not discriminate" in outcome.rationale

    def test_reject_on_kill_regression(self) -> None:
        executor = lambda component: StubResult(  # noqa: E731
            counts={"generated": 582, "killed": 438},
            mutant_statuses={"mut-cc-0001": "killed"},
        )
        outcome = targeted_revalidation(
            _proposal(),
            before_counts={"killed": 440, "generated": 582},
            executor=executor,
        )
        assert not outcome.accepted
        assert outcome.kill_regressions == 2


# ---------------------------------------------------------------------------
# Full-campaign discipline
# ---------------------------------------------------------------------------


def _justification() -> FullCampaignJustification:
    return FullCampaignJustification(
        trigger="population_expansion",
        population_affected=("new_engine",),
        evidence_invalidated=("agg::pop-14",),
        why_targeted_insufficient="no prior measurements exist",
        expected_information_gained="authoritative baseline",
        estimated_resource_cost="60 mutation-minutes",
        certification_consequence="pop-15 becomes authoritative",
        why_mathematical_reconciliation_cannot_answer=("nothing to reconcile from"),
    )


class TestCampaignGate:
    def test_test_addition_never_triggers(self) -> None:
        decision = gate_full_campaign("test_addition", None)
        assert not decision.permitted
        assert "formally excluded" in decision.reason

    def test_score_chasing_never_triggers(self) -> None:
        decision = gate_full_campaign("score_improvement_desire", None)
        assert not decision.permitted

    def test_formal_trigger_without_justification_rejected(self) -> None:
        decision = gate_full_campaign("population_expansion", None)
        assert not decision.permitted
        assert "FullCampaignJustification" in decision.reason

    def test_incomplete_justification_rejected(self) -> None:
        j = _justification()
        incomplete = FullCampaignJustification(
            trigger=j.trigger,
            population_affected=j.population_affected,
            evidence_invalidated=(),
            why_targeted_insufficient="",
            expected_information_gained=j.expected_information_gained,
            estimated_resource_cost=j.estimated_resource_cost,
            certification_consequence=j.certification_consequence,
            why_mathematical_reconciliation_cannot_answer=(
                j.why_mathematical_reconciliation_cannot_answer
            ),
        )
        decision = gate_full_campaign("population_expansion", incomplete)
        assert not decision.permitted
        assert "incomplete" in decision.reason

    def test_formal_trigger_with_complete_justification_permitted(self) -> None:
        decision = gate_full_campaign("population_expansion", _justification())
        assert decision.permitted
        assert decision.justification is not None

    def test_unknown_trigger_rejected(self) -> None:
        decision = gate_full_campaign("i_feel_like_it", None)
        assert not decision.permitted

    def test_trigger_lists_disjoint(self) -> None:
        assert not set(FULL_CAMPAIGN_TRIGGERS) & set(NOT_TRIGGERS)


# ---------------------------------------------------------------------------
# Automation boundary
# ---------------------------------------------------------------------------


class TestAutomationBoundary:
    def test_approval_never_auto_executes(self) -> None:
        decision = evaluate_auto_approval_eligibility(_proposal())
        # Even for an eligible proposal the boundary itself never flips
        # to approved=True; it only states eligibility conditions.
        assert decision.approved is False

    def test_eligible_proposal_conditions_positive(self) -> None:
        decision = evaluate_auto_approval_eligibility(_proposal())
        # Skeleton-only bodies always require human authorship first:
        # the boundary must never fabricate the actual test code.
        assert any("human authorship" in c for c in decision.conditions)

    def test_non_low_risk_requires_human(self) -> None:
        from dataclasses import replace

        p = replace(_proposal(), regression_risk="medium")
        decision = evaluate_auto_approval_eligibility(p)
        assert any("human review" in c for c in decision.conditions)
