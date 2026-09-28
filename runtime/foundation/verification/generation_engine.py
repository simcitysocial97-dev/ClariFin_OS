# runtime/foundation/verification/generation_engine.py
#
# M9-C53 — Automatic Test Generation & Evidence-Driven Strengthening Engine.
#
# The central orchestrator for the C53 pipeline. It composes the certified
# C42/C50/C51/C52 components into one coherent generation→validation→
# authorization→revalidation flow:
#
#   VerificationDecision (C52)
#       ↓
#   Gap Classification (A–G)
#       ↓
#   Generation Eligibility Decision
#       ↓
#   Test Generation Strategy
#       ↓
#   Candidate Test
#       ↓
#   Static Validation (8 dimensions)
#       ↓
#   Focused Execution
#       ↓
#   Regression Validation
#       ↓
#   Coverage Measurement
#       ↓
#   Mutation / Distinguishing Validation
#       ↓
#   Evidence Reconciliation
#       ↓
#   Human Authorization Boundary
#       ↓
#   Targeted Revalidation
#       ↓
#   Candidate Accepted / Rejected
#       ↓
#   Updated Certification Evidence
#
# Every stage has: explicit input, explicit output, authority, failure
# behavior, evidence, audit trail, and deterministic refusal conditions.

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from runtime.foundation.verification.authorization_boundary import (
    AuthorizationRecord,
    AuthorizationState,
    evaluate_authorization,
)
from runtime.foundation.verification.candidate_validation import (
    CandidateValidationResult,
    validate_candidate,
)
from runtime.foundation.verification.gap_classification import (
    GapClassificationResult,
    GapEvidence,
    classify_gap,
)
from runtime.foundation.verification.generation_eligibility import (
    EligibilityDecision,
    determine_eligibility,
)
from runtime.foundation.verification.strengthening import (
    StrengtheningProposal,
)
from runtime.foundation.verification.test_generator import (
    CandidateTest,
)

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent

GENERATION_SCHEMA = "m9-c53-generation/v1"


@dataclass(frozen=True, slots=True)
class GenerationStageResult:
    """Result of one generation pipeline stage."""

    stage: str
    status: str  # "completed" | "refused" | "failed"
    output: dict[str, Any]
    evidence: str
    refusal_reason: str = ""
    refusal_code: str = ""
    duration_seconds: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "stage": self.stage,
            "status": self.status,
            "output": self.output,
            "evidence": self.evidence,
            "refusal_reason": self.refusal_reason,
            "refusal_code": self.refusal_code,
            "duration_seconds": self.duration_seconds,
        }


@dataclass(frozen=True, slots=True)
class GenerationResult:
    """Complete result of one generation pipeline execution."""

    generation_id: str
    schema: str
    generated_at: str
    source_evidence: dict[str, Any]
    stages: list[GenerationStageResult]
    classification: GapClassificationResult | None = None
    eligibility: EligibilityDecision | None = None
    candidate: CandidateTest | None = None
    validation: CandidateValidationResult | None = None
    authorization: list[AuthorizationRecord] = field(default_factory=list)
    proposal: StrengtheningProposal | None = None
    final_state: str = "INCOMPLETE"
    certification_impact: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "generation_id": self.generation_id,
            "schema": self.schema,
            "generated_at": self.generated_at,
            "source_evidence": self.source_evidence,
            "stages": [s.to_dict() for s in self.stages],
            "classification": (
                self.classification.to_dict() if self.classification else None
            ),
            "eligibility": self.eligibility.to_dict() if self.eligibility else None,
            "candidate": self.candidate.to_dict() if self.candidate else None,
            "validation": self.validation.to_dict() if self.validation else None,
            "authorization": [r.to_dict() for r in self.authorization],
            "proposal": self.proposal.to_dict() if self.proposal else None,
            "final_state": self.final_state,
            "certification_impact": self.certification_impact,
        }


@dataclass(frozen=True, slots=True)
class GenerationBatchResult:
    """Result of a batch generation run over multiple gaps."""

    batch_id: str
    schema: str
    generated_at: str
    total_gaps: int
    results: list[GenerationResult]
    summary: dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "batch_id": self.batch_id,
            "schema": self.schema,
            "generated_at": self.generated_at,
            "total_gaps": self.total_gaps,
            "results": [r.to_dict() for r in self.results],
            "summary": self.summary,
        }


def _id(*parts: str) -> str:
    return hashlib.sha256("|".join(parts).encode()).hexdigest()[:12]


def _render_candidate_code(
    module: str,
    candidate_id: str,
    evidence_ref: str,
    location_hint: str,
    input_derivation: str,
    assertion_hint: str,
    strategy: str,
) -> str:
    """Render candidate test code based on the generation strategy."""
    header = (
        f'"""Generated candidate {candidate_id} — evidence: {evidence_ref}.\n\n'
        "M9-C53: this skeleton was produced by the evidence-driven test\n"
        "generation engine. It is NOT accepted evidence on its own: it requires\n"
        "human authorization and must prove behavioral discrimination before\n"
        "acceptance. Expected values must never be copied from the implementation\n"
        "under test.\n\n"
        f"Generation strategy: {strategy}\n"
        '"""\n\n'
        "import pytest\n\n"
    )

    if module.startswith("src."):
        import_target = module.split(".", 1)[1] if "." in module else module
    else:
        import_target = module

    body = (
        f"import {import_target} as target_mod  # {module}\n\n\n"
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

    return header + body


def _derive_boundary_inputs(original: str, mutated: str) -> tuple[str, str]:
    """Mechanically derive the discrimination input + assertion hint."""
    import re

    consts = [int(m) for m in re.findall(r"\b(\d+)\b", original)]
    mconsts = [int(m) for m in re.findall(r"\b(\d+)\b", mutated)]
    if consts and mconsts and consts != mconsts:
        c, mc = consts[0], mconsts[0]
        return (
            f"exercise the decision boundary around the constant {c} "
            f"(mutant moves it to {mc}); inputs just below, at, and just above {c}",
            f"behavior at {c} must match the original constant, not {mc}",
        )
    comparison_re = re.compile(r"(==|!=|<=|>=|<|>)")
    arith_re = re.compile(r"(\+|-|\*|//|/|%)")
    if comparison_re.search(original or ""):
        return (
            "exercise both sides of the comparison with values that make the comparison result decisive",
            "the branch taken must match the original comparison semantics",
        )
    if arith_re.search(original or ""):
        return (
            "exercise the arithmetic with inputs whose exact result is derivable independently",
            "assert an independently-derived relation (conservation, monotonicity, or closed-form value)",
        )
    return (
        "exercise the mutated line via the smallest public surface that reaches it",
        "assert the observable contract documented for this surface",
    )


def _module_of(source_file: str) -> str:
    """src/engines/loan_engine/amortization.py -> src.engines.loan_engine.amortization"""
    return source_file.replace("src/", "").replace("/", ".").rsplit(".py", 1)[0]


class GenerationEngine:
    """M9-C53 automatic test generation engine.

    Composes the certified C42/C50/C51/C52 components into one coherent
    generation pipeline. Does NOT duplicate any certified component.
    """

    def __init__(self) -> None:
        self._ledger: list[dict[str, Any]] = []

    def generate_from_gap(
        self,
        gap: GapEvidence,
        *,
        scope_capability: str | None = None,
    ) -> GenerationResult:
        """Execute the full generation pipeline for one gap.

        This is the canonical entry point. It runs all stages:
        classification → eligibility → generation → validation →
        authorization → certification impact.
        """
        start = time.time()
        generation_id = f"gen::{_id(gap.gap_id, gap.source, gap.component)}"
        stages: list[GenerationStageResult] = []

        # ── Stage 1: Gap Classification ─────────────────────────────────
        t0 = time.time()
        classification = classify_gap(gap)
        stages.append(
            GenerationStageResult(
                stage="gap_classification",
                status="completed",
                output=classification.to_dict(),
                evidence=f"gap classified as {classification.gap_class.value}: {classification.reason}",
                duration_seconds=time.time() - t0,
            )
        )

        # ── Stage 2: Generation Eligibility ─────────────────────────────
        t0 = time.time()
        eligibility = determine_eligibility(
            classification,
            scope_capability=scope_capability,
        )
        stages.append(
            GenerationStageResult(
                stage="generation_eligibility",
                status="refused" if eligibility.generation_refused else "completed",
                output=eligibility.to_dict(),
                evidence=(
                    "generation permitted"
                    if eligibility.generation_allowed
                    else f"generation refused: {eligibility.refusal_reason}"
                ),
                refusal_reason=eligibility.refusal_reason,
                refusal_code=eligibility.refusal_code,
                duration_seconds=time.time() - t0,
            )
        )

        # If refused, stop here
        if eligibility.generation_refused:
            return GenerationResult(
                generation_id=generation_id,
                schema=GENERATION_SCHEMA,
                generated_at=datetime.now(UTC).isoformat(),
                source_evidence=gap.to_dict(),
                stages=stages,
                classification=classification,
                eligibility=eligibility,
                final_state="REFUSED",
                certification_impact={
                    "impact": "none",
                    "reason": f"generation refused: {eligibility.refusal_code}",
                },
            )

        # ── Stage 3: Test Generation Strategy ───────────────────────────
        t0 = time.time()
        strategy = eligibility.strategy

        # Generate the candidate test
        candidate = self._generate_candidate(
            gap, classification, strategy, generation_id
        )
        stages.append(
            GenerationStageResult(
                stage="test_generation",
                status="completed",
                output=candidate.to_dict(),
                evidence=f"candidate generated using strategy={strategy}",
                duration_seconds=time.time() - t0,
            )
        )

        # ── Stage 4: Candidate Validation ───────────────────────────────
        t0 = time.time()
        validation = validate_candidate(
            candidate_code=candidate.code,
            candidate_id=candidate.candidate_id,
            generation_id=generation_id,
            capability=gap.capability,
            location=gap.location,
            gap_class=classification.gap_class.value,
            evidence_detail=gap.evidence_detail,
        )
        stages.append(
            GenerationStageResult(
                stage="candidate_validation",
                status="completed" if validation.overall_passed else "failed",
                output=validation.to_dict(),
                evidence=(
                    "candidate passed all 8 validation dimensions"
                    if validation.overall_passed
                    else f"candidate failed validation: {validation.refusal_reason}"
                ),
                duration_seconds=time.time() - t0,
            )
        )

        # ── Stage 5: Authorization Boundary ─────────────────────────────
        t0 = time.time()
        auth_records = evaluate_authorization(
            candidate_id=candidate.candidate_id,
            generation_id=generation_id,
            validation_passed=validation.overall_passed,
            gap_class=classification.gap_class.value,
            authorization_required=eligibility.authorization_required,
            evidence={
                "classification": classification.to_dict(),
                "eligibility": eligibility.to_dict(),
                "validation": validation.to_dict(),
            },
        )
        final_auth_state = auth_records[-1].state if auth_records else "INCOMPLETE"
        stages.append(
            GenerationStageResult(
                stage="authorization_boundary",
                status="completed",
                output={
                    "final_state": final_auth_state,
                    "records": [r.to_dict() for r in auth_records],
                },
                evidence=f"authorization state: {final_auth_state}",
                duration_seconds=time.time() - t0,
            )
        )

        # ── Stage 6: Certification Impact ───────────────────────────────
        t0 = time.time()
        cert_impact = self._assess_certification_impact(
            classification, eligibility, validation, final_auth_state
        )
        stages.append(
            GenerationStageResult(
                stage="certification_impact",
                status="completed",
                output=cert_impact,
                evidence=f"certification impact: {cert_impact.get('impact', 'unknown')}",
                duration_seconds=time.time() - t0,
            )
        )

        # Determine final state
        if final_auth_state == AuthorizationState.AWAITING_HUMAN_AUTHORIZATION:
            final_state = "AWAITING_HUMAN_AUTHORIZATION"
        elif final_auth_state == AuthorizationState.AUTHORIZED:
            final_state = "AUTHORIZED"
        elif final_auth_state == AuthorizationState.REJECTED:
            final_state = "REJECTED"
        else:
            final_state = final_auth_state

        total_duration = time.time() - start
        stages.append(
            GenerationStageResult(
                stage="pipeline_complete",
                status="completed",
                output={
                    "final_state": final_state,
                    "total_duration_seconds": total_duration,
                },
                evidence=f"pipeline completed in {total_duration:.2f}s with state={final_state}",
                duration_seconds=total_duration,
            )
        )

        return GenerationResult(
            generation_id=generation_id,
            schema=GENERATION_SCHEMA,
            generated_at=datetime.now(UTC).isoformat(),
            source_evidence=gap.to_dict(),
            stages=stages,
            classification=classification,
            eligibility=eligibility,
            candidate=candidate,
            validation=validation,
            authorization=auth_records,
            final_state=final_state,
            certification_impact=cert_impact,
        )

    def _generate_candidate(
        self,
        gap: GapEvidence,
        classification: GapClassificationResult,
        strategy: str,
        generation_id: str,
    ) -> CandidateTest:
        """Generate a candidate test from a gap using the specified strategy."""
        cid = _id("cand", gap.gap_id, generation_id)
        module = (
            _module_of(gap.location.split(":")[0])
            if ":" in gap.location
            else gap.location
        )

        input_derivation, assertion_hint = _derive_boundary_inputs(
            gap.evidence_detail, ""
        )

        # Refine based on strategy
        if strategy == "regression_test":
            input_derivation = (
                "exercise the regression scenario that previously lacked a durable test"
            )
            assertion_hint = (
                "assert the correct behavior that the regression would have caught"
            )
            assertion_form = "EXACT_VALUE"
        elif strategy == "boundary_test":
            assertion_form = "DIFFERENTIAL"
        elif strategy == "property_based":
            input_derivation = "generate inputs that should satisfy the property"
            assertion_hint = "assert the property holds for all generated inputs"
            assertion_form = "INVARIANT"
        elif strategy == "example_based_unit":
            # Refine based on source type
            if gap.source == "property_failure":
                input_derivation = "generate inputs that should satisfy the property"
                assertion_hint = "assert the property holds for all generated inputs"
                assertion_form = "INVARIANT"
            elif gap.source == "contract_failure":
                input_derivation = (
                    "exercise the contract endpoint with valid and invalid inputs"
                )
                assertion_hint = "assert the contract schema and invariants hold"
                assertion_form = "INVARIANT"
            else:
                assertion_form = "DIFFERENTIAL"
        else:
            assertion_form = "DIFFERENTIAL"

        code = _render_candidate_code(
            module=module,
            candidate_id=cid,
            evidence_ref=f"{gap.source}#{gap.gap_id}",
            location_hint=gap.location,
            input_derivation=input_derivation,
            assertion_hint=assertion_hint,
            strategy=strategy,
        )

        return CandidateTest(
            candidate_id=cid,
            evidence_kind=gap.source,
            evidence_ref=f"{gap.source}#{gap.gap_id}",
            module_under_test=(
                gap.location.split(":")[0] if ":" in gap.location else gap.location
            ),
            import_target=module,
            input_derivation=input_derivation,
            assertion_form=assertion_form,
            assertion_hint=assertion_hint,
            code=code,
        )

    def _assess_certification_impact(
        self,
        classification: GapClassificationResult,
        eligibility: EligibilityDecision,
        validation: CandidateValidationResult,
        auth_state: str,
    ) -> dict[str, Any]:
        """Assess the certification impact of a generation result."""
        if auth_state == AuthorizationState.AUTHORIZED:
            return {
                "impact": "positive",
                "dimension_improved": "behavioral_assurance",
                "mutation_effectiveness": "potentially_improved",
                "coverage": "potentially_improved",
                "note": (
                    "candidate authorized: behavioral assurance improved through "
                    "evidence-driven test generation"
                ),
            }
        elif auth_state == AuthorizationState.AWAITING_HUMAN_AUTHORIZATION:
            return {
                "impact": "pending",
                "dimension_improved": "none_yet",
                "note": (
                    "candidate awaiting human authorization: no certification "
                    "impact until authorized"
                ),
            }
        elif auth_state == AuthorizationState.REJECTED:
            return {
                "impact": "none",
                "note": "candidate rejected: no certification impact",
            }
        else:
            return {
                "impact": "none",
                "note": f"final state {auth_state}: no certification impact",
            }

    def generate_batch(
        self,
        gaps: list[GapEvidence],
        *,
        scope_capability: str | None = None,
    ) -> GenerationBatchResult:
        """Run the generation pipeline over multiple gaps."""
        results: list[GenerationResult] = []
        for gap in gaps:
            try:
                result = self.generate_from_gap(gap, scope_capability=scope_capability)
                results.append(result)
            except Exception as e:
                # Record the failure but continue with other gaps
                results.append(
                    GenerationResult(
                        generation_id=f"gen::{_id(gap.gap_id, 'error')}",
                        schema=GENERATION_SCHEMA,
                        generated_at=datetime.now(UTC).isoformat(),
                        source_evidence=gap.to_dict(),
                        stages=[],
                        final_state="ERROR",
                        certification_impact={"error": str(e)},
                    )
                )

        # Build summary
        summary: dict[str, int] = {
            "total": len(results),
            "authorized": sum(1 for r in results if r.final_state == "AUTHORIZED"),
            "awaiting_authorization": sum(
                1 for r in results if r.final_state == "AWAITING_HUMAN_AUTHORIZATION"
            ),
            "refused": sum(1 for r in results if r.final_state == "REFUSED"),
            "error": sum(1 for r in results if r.final_state == "ERROR"),
        }

        return GenerationBatchResult(
            batch_id=f"batch::{_id(str(len(gaps)), datetime.now(UTC).isoformat())}",
            schema=GENERATION_SCHEMA,
            generated_at=datetime.now(UTC).isoformat(),
            total_gaps=len(gaps),
            results=results,
            summary=summary,
        )

    def emit_ledger(self, out_path: Path) -> dict[str, Any]:
        """Emit the generation ledger."""
        ledger = {
            "schema": "m9-c53-generation-ledger/v1",
            "generated_at": datetime.now(UTC).isoformat(),
            "boundary": {
                "self_approval": "FORBIDDEN",
                "production_modification": "FORBIDDEN",
                "test_deletion_or_weakening": "FORBIDDEN",
                "acceptance_authority": "human authorization gate",
            },
            "entries": list(self._ledger),
        }
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(ledger, indent=2))
        return ledger


def main() -> int:
    """CLI: verify.py generate-test --gap-id <id> [--scope <capability>]"""
    import argparse
    import sys

    parser = argparse.ArgumentParser(prog="verify.py generate-test", add_help=False)
    parser.add_argument("--gap-id", help="Gap ID to generate a test for")
    parser.add_argument("--scope", help="Capability scope restriction")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--out", help="Output file path")
    args = parser.parse_args(sys.argv[2:])

    # Create a sample gap for demonstration
    gap = GapEvidence(
        gap_id=args.gap_id or "demo-gap-001",
        source="survivor",
        component="credit_card",
        capability="measure.mutation",
        location="backend/src/engines/credit_card_engine/core.py:42",
        description="Genuine behavioral gap in credit card interest calculation",
        evidence_kind="comparison",
        evidence_detail="if balance > 0:",
        status="survived",
        notes="",
    )

    engine = GenerationEngine()
    result = engine.generate_from_gap(gap, scope_capability=args.scope)

    output = json.dumps(result.to_dict(), indent=2, default=str)

    if args.out:
        Path(args.out).write_text(output)
    if args.json or args.out:
        print(output)
    else:
        print(f"Generation ID: {result.generation_id}")
        print(f"Final state: {result.final_state}")
        for stage in result.stages:
            print(f"  {stage.stage}: {stage.status} — {stage.evidence}")

    return 0 if result.final_state != "ERROR" else 1


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "GenerationStageResult",
    "GenerationResult",
    "GenerationBatchResult",
    "GenerationEngine",
    "GENERATION_SCHEMA",
]
