# runtime/foundation/verification/test_generator.py
#
# M9-C43.5 — Controlled, evidence-driven automatic test generation.
#
# ADDITIVE to the certified C42 strengthening contract
# (runtime/foundation/verification/strengthening.py). It does NOT replace or
# modify the proposal contract, the classifier, or the human authorization
# boundary. It operationalizes them:
#
#   evidence (survivor records / coverage gaps)
#       -> canonical StrengtheningProposal candidates (m9-strengthening-proposal/v1)
#       -> candidate test code (discriminating skeletons, never metric-only)
#       -> human authorization gate (NEVER self-approved; production code is
#          NEVER generated or modified here)
#
# Hard boundaries (mirrors runtime/generated/m9-c42.32-36/autonomy-boundary.json):
#   * never fabricates production behavior or requirements without evidence
#   * never invents expected values from executing production code
#   * never approves its own candidates (ApprovalDecision.approved is always
#     False at this boundary; evaluate_auto_approval_eligibility stays the
#     eligibility oracle only)
#   * never deletes or weakens existing tests
#   * only Class-A survivors and Class-A coverage gaps may produce candidates
#
# Usage:
#   from runtime.foundation.verification.test_generator import TestGenerator
#   gen = TestGenerator()
#   batch = gen.generate_from_survivor_inventory(component, inventory_path)
#   batch = gen.generate_from_coverage_gaps(component, raw_coverage_path, files)
#   ledger = gen.emit_ledger(out_path)
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from runtime.foundation.verification.strengthening import (
    RejectionRecord,
    StrengtheningProposal,
    SurvivorEvidence,
    classify_survivor,
    generate_proposal,
)

GENERATOR_SCHEMA = "m9-c43-test-generation/v1"

# Operator families that mechanically admit boundary-value discrimination.
_COMPARISON_RE = re.compile(r"(==|!=|<=|>=|<|>)")
_ARITH_RE = re.compile(r"(\+|-|\*|//|/|%)")


@dataclass(frozen=True, slots=True)
class CandidateTest:
    """Concrete generated test skeleton bound to one evidence item.

    The skeleton is discriminating-by-construction: it exercises the exact
    mutated branch/boundary and asserts one of three permitted assertion
    forms:
      INVARIANT   — semantic invariant (monotonicity/conservation/bounds)
      DIFFERENTIAL— original vs boundary-pair behavior separation
      EXACT_VALUE — value MUST be filled by authorized human review
                  (the generator never executes production code to compute it)
    """

    candidate_id: str
    evidence_kind: str  # survivor | coverage_gap
    evidence_ref: str
    module_under_test: str
    import_target: str
    input_derivation: str
    assertion_form: str
    assertion_hint: str
    code: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "evidence_kind": self.evidence_kind,
            "evidence_ref": self.evidence_ref,
            "module_under_test": self.module_under_test,
            "import_target": self.import_target,
            "input_derivation": self.input_derivation,
            "assertion_form": self.assertion_form,
            "assertion_hint": self.assertion_hint,
            "code": self.code,
        }


@dataclass(frozen=True, slots=True)
class GenerationBatch:
    schema: str
    batch_id: str
    generated_at: str
    source_evidence: dict[str, Any]
    proposals: tuple[StrengtheningProposal, ...] = ()
    rejections: tuple[RejectionRecord, ...] = ()
    candidates: tuple[CandidateTest, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "batch_id": self.batch_id,
            "generated_at": self.generated_at,
            "source_evidence": self.source_evidence,
            "proposals": [p.to_dict() for p in self.proposals],
            "rejections": [r.to_dict() for r in self.rejections],
            "candidates": [c.to_dict() for c in self.candidates],
            "counts": {
                "proposals": len(self.proposals),
                "rejections": len(self.rejections),
                "candidates": len(self.candidates),
            },
        }


def _id(*parts: str) -> str:
    return hashlib.sha256("|".join(parts).encode()).hexdigest()[:12]


# Rejection reasons for FORENSICALLY REVIEWED non-A classes (C42.17 inventories).
# These are respected directly, not re-derived by the heuristic classifier.
_REVIEWED_REJECTION_REASONS: dict[str, str] = {
    "B": (
        "survivor {sid} @ {location} reviewed as EQUIVALENT/non-discriminating; "
        "targeting it would inflate the score without improving defect detection"
    ),
    "C": (
        "survivor {sid} @ {location} reviewed as defensive/unreachable/structural; "
        "manufacturing a test here optimizes the metric, not behavior"
    ),
    "D": (
        "survivor {sid} @ {location} reviewed as a measurement/infrastructure "
        "problem; repair measurement before interpreting behavior"
    ),
    "E": (
        "survivor {sid} @ {location} reviewed as an escalation / possible "
        "production defect; requires human review (Defect Ledger), not an "
        "automatic test"
    ),
}


def _module_of(source_file: str) -> str:
    """src/engines/loan_engine/amortization.py -> src.engines.loan_engine.amortization"""
    return source_file.replace("src/", "").replace("/", ".").rsplit(".py", 1)[0]


def _derive_boundary_inputs(original: str, mutated: str) -> tuple[str, str]:
    """Mechanically derive the discrimination input + assertion hint.

    Returns (input_derivation, assertion_hint). Only boundary arithmetic on
    constants VISIBLE in the mutant text is used — nothing is executed and no
    production behavior is assumed beyond the original expression itself.
    """
    consts = [int(m) for m in re.findall(r"\b(\d+)\b", original)]
    mconsts = [int(m) for m in re.findall(r"\b(\d+)\b", mutated)]
    if consts and mconsts and consts != mconsts:
        c, mc = consts[0], mconsts[0]
        return (
            f"exercise the decision boundary around the constant {c} "
            f"(mutant moves it to {mc}); inputs just below, at, and just "
            f"above {c}",
            f"behavior at {c} must match the original constant, not {mc}",
        )
    if _COMPARISON_RE.search(original or ""):
        return (
            "exercise both sides of the comparison with values that make "
            "the comparison result decisive",
            "the branch taken must match the original comparison semantics",
        )
    if _ARITH_RE.search(original or ""):
        return (
            "exercise the arithmetic with inputs whose exact result is "
            "derivable independently of the implementation",
            "assert an independently-derived relation (e.g. conservation, "
            "monotonicity, or closed-form value filled by human review)",
        )
    return (
        "exercise the mutated line via the smallest public surface that " "reaches it",
        "assert the observable contract documented for this surface",
    )


def _render_candidate_code(
    module: str,
    candidate_id: str,
    evidence_ref: str,
    location_hint: str,
    input_derivation: str,
    assertion_hint: str,
) -> str:
    return (
        f'"""Generated candidate {candidate_id} — evidence: {evidence_ref}.\n\n'
        "M9-C43.5: this skeleton was produced by the evidence-driven test\n"
        "generator. It is NOT accepted evidence on its own: it requires\n"
        "human authorization (m9-c43-strengthening-record.json approval\n"
        "entry) and must prove behavioral discrimination (targeted mutation\n"
        "transition) before acceptance. Expected values must never be\n"
        "copied from the implementation under test.\n"
        '"""\n\n'
        "import pytest\n\n"
        f"import {module.split('.', 1)[1] if module.startswith('src.') else module} "
        f"as target_mod  # {module}\n\n\n"
        f"def test_{candidate_id}_discriminates():\n"
        f'    """Target: {location_hint}\n\n'
        f"    Input derivation: {input_derivation}\n"
        f"    Assertion: {assertion_hint}\n"
        '    """\n'
        "    pytest.skip(\n"
        '        "candidate skeleton: authorized implementation must replace '
        'this skip"\n'
        "    )\n"
    )


class TestGenerator:
    """Evidence-driven candidate generator over the C42 proposal contract."""

    def __init__(self) -> None:
        self._ledger: list[dict[str, Any]] = []

    # ── survivor-evidence driven generation ──────────────────────────────
    def generate_from_survivor_inventory(
        self,
        component: str,
        inventory_path: Path,
        capability: str,
        limit: int | None = None,
    ) -> GenerationBatch:
        data = json.loads(Path(inventory_path).read_text())
        evidence_source = {
            "kind": "survivor_inventory",
            "path": str(inventory_path),
            "component": component,
            "records": len(data.get("survivors", [])),
        }
        proposals: list[StrengtheningProposal] = []
        rejections: list[RejectionRecord] = []
        candidates: list[CandidateTest] = []

        records = data.get("survivors", [])
        if limit is not None:
            records = records[:limit]

        for i, rec in enumerate(records):
            sid = rec.get("mutant") or f"{component}-inv-{i:04d}"
            reviewed = rec.get("classification")
            location = f"{rec.get('source_file', '?')}:{rec.get('line', '?')}"
            ev = SurvivorEvidence(
                survivor_id=sid,
                component=component,
                capability=capability,
                location=location,
                mutation_operator=rec.get("mutation_operator", "unknown").split("_")[0],
                original_snippet=rec.get("original_expression", ""),
                mutated_snippet=rec.get("mutated_expression", ""),
                notes=(
                    "equivalent"
                    if reviewed is None
                    and str(rec.get("subclassification", "")).startswith("equivalent")
                    else ""
                ),
            )

            # C42.17 inventory classifications are FORENSICALLY REVIEWED.
            # The generator honors them directly (the heuristic classifier
            # cannot reconstruct reviewed judgments). Records without a
            # reviewed classification fall back to the C42 classifier.
            if reviewed in {"B", "C", "D", "E"}:
                reason = _REVIEWED_REJECTION_REASONS[reviewed].format(
                    sid=sid, location=location
                )
                rejections.append(
                    RejectionRecord(sid, reviewed, reason)  # type: ignore[arg-type]
                )
                self._ledger.append(
                    {
                        "evidence": ev.to_dict(),
                        "outcome": "rejected",
                        "classification": reviewed,
                        "reason": reason,
                        "basis": "reviewed C42.17 forensic classification",
                    }
                )
                continue

            cls = reviewed if reviewed == "A" else classify_survivor(ev)
            if reviewed is None and cls != "A":
                outcome = generate_proposal(ev)
                assert isinstance(outcome, RejectionRecord)
                rejections.append(outcome)
                self._ledger.append(
                    {
                        "evidence": ev.to_dict(),
                        "outcome": "rejected",
                        "classification": cls,
                        "reason": outcome.reason,
                        "basis": "C42 classifier (no reviewed classification)",
                    }
                )
                continue

            outcome = generate_proposal(ev)
            if isinstance(outcome, RejectionRecord):
                rejections.append(outcome)
                self._ledger.append(
                    {
                        "evidence": ev.to_dict(),
                        "outcome": "rejected",
                        "classification": cls,
                        "reason": outcome.reason,
                        "basis": "C42 classifier secondary guard "
                        "(defensive pattern in reviewed-A record)",
                    }
                )
                continue

            proposals.append(outcome)
            input_derivation, assertion_hint = _derive_boundary_inputs(
                rec.get("original_expression", ""),
                rec.get("mutated_expression", ""),
            )
            module = _module_of(rec.get("source_file", "src/unknown.py"))
            cid = _id("cand", component, sid, rec.get("source_file", ""))
            candidates.append(
                CandidateTest(
                    candidate_id=cid,
                    evidence_kind="survivor",
                    evidence_ref=f"{Path(inventory_path).name}#{sid}",
                    module_under_test=rec.get("source_file", "?"),
                    import_target=module,
                    input_derivation=input_derivation,
                    assertion_form=(
                        "DIFFERENTIAL"
                        if rec.get("mutated_expression")
                        else "EXACT_VALUE"
                    ),
                    assertion_hint=assertion_hint,
                    code=_render_candidate_code(
                        module,
                        cid,
                        f"survivor {sid} @ {ev.location}",
                        ev.location,
                        input_derivation,
                        assertion_hint,
                    ),
                )
            )
            self._ledger.append(
                {
                    "evidence": ev.to_dict(),
                    "outcome": "proposed",
                    "classification": cls,
                    "candidate_id": cid,
                }
            )

        return GenerationBatch(
            schema=GENERATOR_SCHEMA,
            batch_id=f"gen::{_id(component, str(inventory_path), 'survivors')}",
            generated_at=datetime.now(UTC).isoformat(),
            source_evidence=evidence_source,
            proposals=tuple(proposals),
            rejections=tuple(rejections),
            candidates=tuple(candidates),
        )

    # ── coverage-gap driven generation ───────────────────────────────────
    def generate_from_coverage_gaps(
        self,
        component: str,
        raw_coverage_path: Path,
        target_files: tuple[str, ...],
        capability: str,
        min_gap_items: int = 10,
    ) -> GenerationBatch:
        data = json.loads(Path(raw_coverage_path).read_text())
        files = data.get("files", {})
        evidence_source = {
            "kind": "coverage_gaps",
            "path": str(raw_coverage_path),
            "component": component,
            "target_files": list(target_files),
        }
        proposals: list[StrengtheningProposal] = []
        candidates: list[CandidateTest] = []

        for rel in target_files:
            key = rel if rel in files else f"src/{rel}"
            fdata = files.get(key)
            if fdata is None:
                continue
            summary = fdata["summary"]
            gap_items = summary["missing_lines"] + summary.get("missing_branches", 0)
            if gap_items < min_gap_items:
                continue
            missing = fdata.get("missing_lines", [])
            # evidence-derived survivor-style signal: coverage gap as an
            # unasserted-behavior surface (classification A by construction —
            # covered-only-unasserted vs never-covered handled downstream by
            # targeted mutation discrimination).
            ev = SurvivorEvidence(
                survivor_id=f"covgap::{key}::{summary['missing_lines']}",
                component=component,
                capability=capability,
                location=f"{key}:{missing[0] if missing else '?'}",
                mutation_operator="uncovered_behavior",
                original_snippet=(
                    f"{summary['missing_lines']} uncovered line(s), "
                    f"{summary.get('missing_branches', 0)} uncovered branch(es)"
                ),
                mutated_snippet="",
                notes="",
            )
            pid = _id("covprop", component, key)
            module = _module_of(key)
            proposals.append(
                StrengtheningProposal(
                    schema="m9-strengthening-proposal/v1",
                    proposal_id=f"prop::{pid}",
                    component=component,
                    capability=capability,
                    source_location=f"{key} (missing lines: "
                    f"{summary['missing_lines']})",
                    survivor_evidence=ev.to_dict(),
                    classification="A",
                    behavioral_hypothesis=(
                        f"uncovered behavior at {key} is consequential: "
                        f"{gap_items} statement/branch items are reachable by "
                        "no test, so mutations there cannot be detected"
                    ),
                    expected_invariant=(
                        "new tests execute the missing lines AND assert their "
                        "outcomes (coverage without assertion is rejected at "
                        "the targeted-mutation gate)"
                    ),
                    proposed_test_surface=(
                        f"backend/tests/unit/engines/{component}/"
                        f"test_coverage_gap_{pid}.py"
                    ),
                    proposed_test=(
                        f"def test_{pid}_covers_missing_behavior():\n"
                        "    # Exercises the uncovered surface of "
                        f"{key}; assertions must be evidence-derived.\n"
                        "    ...\n"
                    ),
                    reason=(
                        "coverage-gap evidence: reachable behavior with zero "
                        "test reach; required before mutation campaigns can "
                        "see these mutants at all"
                    ),
                    expected_mutation_discrimination=(
                        "previously un-generatable mutants in this surface "
                        "become generated AND scored; acceptance requires "
                        "kills, not coverage alone"
                    ),
                    regression_risk="low",
                    validation_command=(
                        f".venv/bin/python -m pytest backend/tests/unit/engines/"
                        f"{component} -q"
                    ),
                    acceptance_criteria=(
                        "missing lines decrease by exercising real behavior",
                        "assertions discriminate (targeted mutation shows kills)",
                        "no production source modified",
                    ),
                )
            )
            cid = _id("cand", component, key, "coverage")
            candidates.append(
                CandidateTest(
                    candidate_id=cid,
                    evidence_kind="coverage_gap",
                    evidence_ref=f"{Path(raw_coverage_path).name}::{key}",
                    module_under_test=key,
                    import_target=module,
                    input_derivation=(
                        "drive the public surface along paths reaching the "
                        f"missing lines (first missing line: "
                        f"{missing[0] if missing else '?'})"
                    ),
                    assertion_form="INVARIANT",
                    assertion_hint=(
                        "assert observable outcomes/conservation laws of the "
                        "surface — never implementation-derived values"
                    ),
                    code=_render_candidate_code(
                        module,
                        cid,
                        f"coverage gap {key}",
                        f"{key}:{missing[0] if missing else '?'}",
                        "drive public surface to missing lines",
                        "invariant/conservation assertions",
                    ),
                )
            )
            self._ledger.append(
                {
                    "evidence": ev.to_dict(),
                    "outcome": "proposed",
                    "classification": "A",
                    "candidate_id": cid,
                }
            )

        return GenerationBatch(
            schema=GENERATOR_SCHEMA,
            batch_id=f"gen::{_id(component, str(raw_coverage_path), 'coverage')}",
            generated_at=datetime.now(UTC).isoformat(),
            source_evidence=evidence_source,
            proposals=tuple(proposals),
            rejections=(),
            candidates=tuple(candidates),
        )

    # ── ledger emission ──────────────────────────────────────────────────
    def emit_ledger(self, out_path: Path) -> dict[str, Any]:
        ledger = {
            "schema": "m9-c43-test-generation-ledger/v1",
            "generated_at": datetime.now(UTC).isoformat(),
            "boundary": {
                "self_approval": "FORBIDDEN — ApprovalDecision.approved is "
                "always False at this boundary",
                "production_modification": "FORBIDDEN — generator emits "
                "candidate code only",
                "test_deletion_or_weakening": "FORBIDDEN",
                "acceptance_authority": "human authorization gate recorded in "
                "m9-c43-strengthening-record.json",
            },
            "entries": list(self._ledger),
        }
        Path(out_path).write_text(json.dumps(ledger, indent=2))
        return ledger
