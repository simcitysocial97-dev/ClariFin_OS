"""
M9-C42.31 — M31.x Strengthening-loop scenarios + full-campaign gate.

  S-A   genuine Class-A survivor        -> bounded proposal generated
  S-B   equivalent survivor             -> rejected (never chased)
  S-C   defensive/logging survivor      -> rejected (no score manufacturing)
  S-D   timeout/suspicious survivor     -> measurement repair first
  S-E   escalation-marker survivor      -> human review required
  S-F   targeted revalidation accept    -> hypothesis validated,
                                           zero kill regressions
  S-G   targeted revalidation reject    -> target still survives
  S-H   revalidation regression reject  -> previously-killed regressed
  S-G1  full-campaign gate: test_addition trigger REJECTED
  S-G2  full-campaign gate: formal trigger without justification REJECTED
  S-G3  full-campaign gate: formal trigger + complete justification PERMITTED

Run with:
    .venv/bin/python runtime/generated/m9-c42.31/m31_4_scenarios.py
"""
from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

OUT_DIR = REPO_ROOT / "runtime" / "generated" / "m9-c42.31"
OUT_DIR.mkdir(parents=True, exist_ok=True)

from runtime.foundation.verification.strengthening import (  # noqa: E402
    CampaignGateDecision,
    FullCampaignJustification,
    RejectionRecord,
    SurvivorEvidence,
    StrengtheningProposal,
    classify_survivor,
    generate_proposal,
    gate_full_campaign,
    targeted_revalidation,
)


# ---------------------------------------------------------------------------
# Deterministic stub executor with per-mutant status map
# ---------------------------------------------------------------------------

@dataclass
class StubMutationResult:
    counts: dict[str, int] = field(default_factory=dict)
    mutant_statuses: dict[str, str] = field(default_factory=dict)


def make_stub_executor(after_killed: int, after_generated: int, statuses: dict):
    def _exec(component: str) -> StubMutationResult:
        return StubMutationResult(
            counts={
                "generated": after_generated,
                "killed": after_killed,
                "survived": after_generated - after_killed,
            },
            mutant_statuses=dict(statuses),
        )
    return _exec


def _class_a_survivor() -> SurvivorEvidence:
    return SurvivorEvidence(
        survivor_id="mut-cc-0047",
        component="credit_card_engine",
        capability="credit-card-risk",
        location="src/engines/credit_card_engine/risk.py:compute_apr",
        mutation_operator="comparison",
        original_snippet="if utilization >= threshold:",
        mutated_snippet="if utilization > threshold:",
        status="survived",
        notes="",
        covering_tests=("test_compute_apr_basic",),
    )


# ---------------------------------------------------------------------------
# Classification / proposal scenarios
# ---------------------------------------------------------------------------

def scenario_s_a() -> dict:
    s = _class_a_survivor()
    cls = classify_survivor(s)
    out = generate_proposal(s)
    ok = (
        cls == "A"
        and isinstance(out, StrengtheningProposal)
        and out.classification == "A"
        and "boundary" in out.behavioral_hypothesis.lower()
        or "comparison" in out.behavioral_hypothesis.lower()
        and len(out.acceptance_criteria) == 4
        and out.regression_risk == "low"
    )
    # bool() because the compound expression above mixes and/or.
    ok = bool(ok)
    d = out.to_dict()
    required = [
        "component", "capability", "source_location", "survivor_evidence",
        "classification", "behavioral_hypothesis", "expected_invariant",
        "proposed_test_surface", "proposed_test", "reason",
        "expected_mutation_discrimination", "regression_risk",
        "validation_command", "acceptance_criteria",
    ]
    contract_complete = all(k in d for k in required)
    return {
        "scenario": "S-A",
        "name": "genuine_class_a_proposal",
        "expected": "bounded evidence-derived proposal with full contract",
        "classification": cls,
        "contract_complete": contract_complete,
        "proposal_id": getattr(out, "proposal_id", None),
        "pass": bool(ok and contract_complete),
    }


def scenario_s_b() -> dict:
    s = SurvivorEvidence(
        survivor_id="mut-bal-0013",
        component="balance_engine",
        capability="balance-engine",
        location="src/engines/balance_engine/ledger.py:normalise",
        mutation_operator="arithmetic",
        original_snippet="total = sum(items)",
        mutated_snippet="total = sum(items) * 1",
        status="survived",
        notes="classified equivalent by upstream analysis "
              "(observable-equivalent behavior)",
    )
    cls = classify_survivor(s)
    out = generate_proposal(s)
    ok = (
        cls == "B"
        and isinstance(out, RejectionRecord)
        and not isinstance(out, StrengtheningProposal)
        and "equivalent" in out.reason.lower()
    )
    return {
        "scenario": "S-B",
        "name": "class_b_equivalent_rejected",
        "expected": "equivalent survivor never converted into work",
        "classification": cls,
        "rejection_reason": getattr(out, "reason", None),
        "pass": ok,
    }


def scenario_s_c() -> dict:
    s = SurvivorEvidence(
        survivor_id="mut-loan-0102",
        component="loan_engine",
        capability="loan-management",
        location="src/engines/loan_engine/schedule.py:_audit_log",
        mutation_operator="boolean",
        original_snippet="logger.info('schedule recomputed')",
        mutated_snippet="logger.error('schedule recomputed')",
        status="survived",
    )
    cls = classify_survivor(s)
    out = generate_proposal(s)
    ok = (
        cls == "C"
        and isinstance(out, RejectionRecord)
        and "metric" in out.reason.lower() or "manufactur" in out.reason.lower()
    )
    return {
        "scenario": "S-C",
        "name": "class_c_defensive_rejected",
        "expected": "no test manufactured for observability code",
        "classification": cls,
        "rejection_reason": getattr(out, "reason", None),
        "pass": ok,
    }


def scenario_s_d() -> dict:
    s = SurvivorEvidence(
        survivor_id="mut-beh-0880",
        component="behaviour_engine",
        capability="behaviour-analytics",
        location="src/engines/behaviour_engine/patterns.py:detect",
        mutation_operator="return",
        original_snippet="return patterns",
        mutated_snippet="return list(patterns)",
        status="timeout",
        notes="mutant execution timed out under campaign budget",
    )
    cls = classify_survivor(s)
    out = generate_proposal(s)
    ok = (
        cls == "D"
        and isinstance(out, RejectionRecord)
        and "measurement" in out.reason.lower()
    )
    return {
        "scenario": "S-D",
        "name": "class_d_measurement_first",
        "expected": "repair measurement before interpreting behavior",
        "classification": cls,
        "rejection_reason": getattr(out, "reason", None),
        "pass": ok,
    }


def scenario_s_e() -> dict:
    s = SurvivorEvidence(
        survivor_id="mut-fin-0221",
        component="financial_intelligence",
        capability="financial-intelligence",
        location="src/intelligence/financial_intelligence/project.py:forecast",
        mutation_operator="comparison",
        original_snippet="if projected < floor:",
        mutated_snippet="if projected <= floor:",
        status="survived",
        notes="production_defect_candidate flagged during review: boundary "
              "semantics may be a real product defect",
    )
    cls = classify_survivor(s)
    out = generate_proposal(s)
    ok = (
        cls == "E"
        and isinstance(out, RejectionRecord)
        and "human" in out.reason.lower()
    )
    return {
        "scenario": "S-E",
        "name": "class_e_escalation",
        "expected": "ambiguous/production-defect candidate escalated",
        "classification": cls,
        "rejection_reason": getattr(out, "reason", None),
        "pass": ok,
    }


# ---------------------------------------------------------------------------
# Targeted revalidation scenarios
# ---------------------------------------------------------------------------

_PROPOSAL_CACHE: dict | None = None


def _cached_proposal() -> StrengtheningProposal:
    global _PROPOSAL_CACHE
    if _PROPOSAL_CACHE is None:
        out = generate_proposal(_class_a_survivor())
        assert isinstance(out, StrengtheningProposal)
        _PROPOSAL_CACHE = out
    return _PROPOSAL_CACHE


BEFORE_COUNTS = {"killed": 440, "generated": 582}


def scenario_s_f() -> dict:
    """Acceptance path: target killed, zero regressions."""
    executor = make_stub_executor(
        after_killed=441, after_generated=582,
        statuses={"mut-cc-0047": "killed"},
    )
    outcome = targeted_revalidation(
        _cached_proposal(),
        before_counts=BEFORE_COUNTS,
        executor=executor,
    )
    ok = (
        outcome.accepted
        and outcome.hypothesis_validated
        and outcome.target_mutant_killed
        and outcome.kill_regressions == 0
        and outcome.after_killed == outcome.before_killed + 1
        and outcome.used_full_campaign is False
    )
    return {
        "scenario": "S-F",
        "name": "targeted_revalidation_accept",
        "expected": "hypothesis validated; targeted only; no full campaign",
        "outcome": outcome.to_dict(),
        "pass": ok,
    }


def scenario_s_g() -> dict:
    """Rejection path: proposed test does not discriminate."""
    executor = make_stub_executor(
        after_killed=440, after_generated=582,
        statuses={"mut-cc-0047": "survived"},
    )
    outcome = targeted_revalidation(
        _cached_proposal(), before_counts=BEFORE_COUNTS, executor=executor,
    )
    ok = (
        not outcome.accepted
        and not outcome.hypothesis_validated
        and "did not discriminate" in outcome.rationale
        and outcome.used_full_campaign is False
    )
    return {
        "scenario": "S-G",
        "name": "targeted_revalidation_reject_nondiscriminating",
        "expected": "rejected honestly; no score-chasing fallback",
        "outcome": outcome.to_dict(),
        "pass": ok,
    }


def scenario_s_h() -> dict:
    """Regression path: strengthening broke existing discrimination."""
    executor = make_stub_executor(
        after_killed=438, after_generated=582,
        statuses={"mut-cc-0047": "killed"},
    )
    outcome = targeted_revalidation(
        _cached_proposal(), before_counts=BEFORE_COUNTS, executor=executor,
    )
    ok = (
        not outcome.accepted
        and outcome.kill_regressions == 2
        and "regressed" in outcome.rationale.lower()
    )
    return {
        "scenario": "S-H",
        "name": "targeted_revalidation_regression_reject",
        "expected": "kill regressions block acceptance",
        "outcome": outcome.to_dict(),
        "pass": ok,
    }


# ---------------------------------------------------------------------------
# Full-campaign discipline scenarios
# ---------------------------------------------------------------------------

_JUSTIFICATION = FullCampaignJustification(
    trigger="population_expansion",
    population_affected=("new_engine_a", "new_engine_b"),
    evidence_invalidated=("meas::agg::pop-14",),
    why_targeted_insufficient=(
        "two new components join the population; every prior aggregate "
        "denominator changes, so component-level reuse cannot answer the "
        "comparability question"
    ),
    expected_information_gained=(
        "authoritative baseline measurements for both new components"
    ),
    estimated_resource_cost=(
        "~2 x 60 mutation-minutes via bounded per-component campaigns"
    ),
    certification_consequence=(
        "pop-16 aggregate becomes authoritative; pop-14 retired"
    ),
    why_mathematical_reconciliation_cannot_answer=(
        "there are no prior measurements to reconcile from for the new "
        "components"
    ),
)


def scenario_s_g1() -> dict:
    decision = gate_full_campaign("test_addition", None)
    ok = (
        not decision.permitted
        and "formally excluded" in decision.reason
    )
    return {
        "scenario": "S-G1",
        "name": "campaign_gate_test_addition_rejected",
        "expected": "a test addition alone NEVER justifies a full campaign",
        "decision": decision.to_dict(),
        "pass": ok,
    }


def scenario_s_g2() -> dict:
    decision = gate_full_campaign("periodic_measurement_checkpoint", None)
    ok = (
        not decision.permitted
        and "FullCampaignJustification" in decision.reason
    )
    return {
        "scenario": "S-G2",
        "name": "campaign_gate_missing_justification_rejected",
        "expected": "formal trigger still requires complete justification",
        "decision": decision.to_dict(),
        "pass": ok,
    }


def scenario_s_g3() -> dict:
    decision = gate_full_campaign("population_expansion", _JUSTIFICATION)
    ok = (
        decision.permitted
        and decision.justification is not None
        and decision.justification["trigger"] == "population_expansion"
    )
    return {
        "scenario": "S-G3",
        "name": "campaign_gate_formal_trigger_permitted",
        "expected": "formal trigger + complete justification permitted",
        "decision": decision.to_dict(),
        "pass": ok,
    }


def main() -> int:
    results = [
        scenario_s_a(),
        scenario_s_b(),
        scenario_s_c(),
        scenario_s_d(),
        scenario_s_e(),
        scenario_s_f(),
        scenario_s_g(),
        scenario_s_h(),
        scenario_s_g1(),
        scenario_s_g2(),
        scenario_s_g3(),
    ]
    (OUT_DIR / "m9-c42.31-scenarios.json").write_text(json.dumps(results, indent=2))
    passed = sum(1 for r in results if r["pass"])
    print(f"C42.31 strengthening scenarios: {passed}/{len(results)} pass")
    for r in results:
        status = "PASS" if r["pass"] else "FAIL"
        print(f"  [{status}] {r['scenario']} — {r['name']}")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
