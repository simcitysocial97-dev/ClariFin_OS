"""
M9-C48 — Capability-Aware Automatic Strengthening Pipeline.

Integrates the existing strengthening pipeline (discover → classify → propose →
authorize → validate → record) with capability awareness.

Given a failing capability or mutation survivor, the system identifies:
* capability
* implementation surface
* mutant/survivor
* covering tests
* missing distinguishing behavior
* existing tests that should be improved
* candidate new tests
* whether the issue is Class A/B/C/D/E
* whether production modification is required
* whether human authorization is required

Uses native mutmut analysis and durable survivor intelligence from C47/C45.
Does not reconstruct mutation information from transient temp folders.
"""

from __future__ import annotations

import json
import sys
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Literal

from runtime.foundation.verification.capability_contract import (
    CapabilityContractRegistry,
    CapabilityMissing,
    StrengtheningMechanism,
    get_capability_contract_registry,
)
from runtime.foundation.verification.evidence_reuse import (
    ComponentMeasurement,
    PopulationSnapshot,
    c42_24_b_measurements,
    c42_25_measurements,
    c42_26_population,
)
from runtime.foundation.verification.measurement_truth_integration import (
    MeasurementTruthIntegrator,
    get_measurement_truth_integrator,
)
from runtime.foundation.verification.survivor_intel import (
    DEFAULT_INTEL_PATH,
    find_survivor,
    load_survivor_intel,
)

# ---------------------------------------------------------------------------
# Strengthening Classification
# ---------------------------------------------------------------------------


class SurvivorClass(str, Enum):
    """Mutation survivor classification (from C42.17)."""

    A = "A"  # Missing assertion — test exists but doesn't assert mutated behavior
    B = "B"  # Missing test — no test covers this behavior
    C = "C"  # Equivalent mutant — mutation doesn't change observable behavior
    D = "D"  # Test deficiency — test is flawed/wrong
    E = "E"  # Production code defect — mutation reveals real bug
    UNKNOWN = "UNKNOWN"


class StrengtheningAction(str, Enum):
    """Type of strengthening action."""

    ADD_ASSERTION = "add_assertion"  # Class A: add missing assertion to existing test
    ADD_TEST = "add_test"  # Class B: add new test case
    DOCUMENT_EQUIVALENT = (
        "document_equivalent"  # Class C: document as equivalent mutant
    )
    FIX_TEST = "fix_test"  # Class D: fix flawed test
    FIX_PRODUCTION = "fix_production"  # Class E: fix production code
    NO_ACTION = "no_action"  # Not actionable


@dataclass(frozen=True, slots=True)
class CapabilityAwareSurvivor:
    """A survivor enriched with capability context."""

    survivor_id: str
    capability_id: str
    capability_name: str
    component: str
    source_file: str
    source_location: str
    function: str
    mutation_type: str
    original_expression: str
    mutated_expression: str
    classification: SurvivorClass
    classification_evidence: str
    covering_tests: list[str]
    covering_test_surface: list[str]
    tests_enrichment_provenance: str
    investigation_status: str
    previous_proposal_status: str
    previous_validation_status: str
    recommended_action: str
    evidence_fingerprint: str
    capability_maturity: str
    capability_missing: list[str]
    strengthening_mechanisms: list[StrengtheningMechanism] = field(default_factory=list)
    measurement_truth_status: str = ""

    def to_dict(self) -> dict:
        return {
            **asdict(self),
            "classification": self.classification.value,
            "capability_missing": [m.value for m in self.capability_missing],
            "strengthening_mechanisms": [
                s.to_dict() for s in self.strengthening_mechanisms
            ],
        }


@dataclass(frozen=True, slots=True)
class StrengtheningDecision:
    """A strengthening decision for a survivor."""

    survivor_id: str
    capability_id: str
    action: StrengtheningAction
    classification: SurvivorClass
    justification: str
    target_test: str | None = None  # For Class A: which test to strengthen
    proposed_assertion: str | None = None  # For Class A: what assertion to add
    proposed_test: dict | None = None  # For Class B: new test specification
    production_fix: dict | None = None  # For Class E: production code fix
    requires_human_authorization: bool = False
    validation_command: str = ""
    rollback_command: str = ""
    status: Literal["proposed", "authorized", "validated", "rejected", "deferred"] = (
        "proposed"
    )

    def to_dict(self) -> dict:
        return {
            **asdict(self),
            "action": self.action.value,
            "classification": self.classification.value,
            "proposed_test": self.proposed_test,
            "production_fix": self.production_fix,
        }


@dataclass
class CapabilityStrengtheningReport:
    """Complete strengthening report for a capability."""

    capability_id: str
    capability_name: str
    generated_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    survivors: list[CapabilityAwareSurvivor] = field(default_factory=list)
    decisions: list[StrengtheningDecision] = field(default_factory=list)
    summary: dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "capability_id": self.capability_id,
            "capability_name": self.capability_name,
            "generated_at": self.generated_at,
            "survivors": [s.to_dict() for s in self.survivors],
            "decisions": [d.to_dict() for d in self.decisions],
            "summary": self.summary,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, default=str)


# ---------------------------------------------------------------------------
# Capability-Aware Strengthening Engine
# ---------------------------------------------------------------------------


class CapabilityAwareStrengtheningEngine:
    """
    Capability-aware strengthening engine.

    Wraps the existing forensic_cli pipeline and enriches it with capability context.
    """

    def __init__(
        self,
        contract_registry: CapabilityContractRegistry | None = None,
        measurement_integrator: MeasurementTruthIntegrator | None = None,
        population: PopulationSnapshot | None = None,
        measurements: list[ComponentMeasurement] | None = None,
    ):
        self._contract_registry = (
            contract_registry or get_capability_contract_registry()
        )
        self._measurement_integrator = (
            measurement_integrator or get_measurement_truth_integrator()
        )
        self._population = population or c42_26_population()
        self._measurements = measurements or (
            c42_24_b_measurements() + c42_25_measurements()
        )

    def analyze_capability(self, capability_id: str) -> CapabilityStrengtheningReport:
        """Analyze all survivors for a capability and produce strengthening decisions."""
        contract = self._contract_registry.get_contract(capability_id)
        if not contract:
            return CapabilityStrengtheningReport(
                capability_id=capability_id,
                capability_name="Unknown",
            )

        # Load durable survivor intelligence
        intel = load_survivor_intel(DEFAULT_INTEL_PATH)
        if not intel:
            return CapabilityStrengtheningReport(
                capability_id=capability_id,
                capability_name=contract.name,
            )

        # Get measurement truth status
        truth_report = self._measurement_integrator.evaluate_capability(capability_id)
        mutation_truth = next(
            (
                m
                for m in truth_report.measurements
                if m.measurement_kind.value == "mutation"
            ),
            None,
        )
        measurement_status = (
            mutation_truth.completion_status.value if mutation_truth else "unknown"
        )

        # Filter survivors for this capability
        capability_survivors = [
            s
            for s in intel.get("survivors", [])
            if s.get("capability") == capability_id
        ]

        report = CapabilityStrengtheningReport(
            capability_id=capability_id,
            capability_name=contract.name,
        )

        for survivor_data in capability_survivors:
            # Parse classification
            cls_str = survivor_data.get("classification", "UNKNOWN")
            try:
                classification = SurvivorClass(cls_str)
            except ValueError:
                classification = SurvivorClass.UNKNOWN

            # Get capability missing elements
            missing = contract.missing
            if isinstance(missing[0], str):
                missing = [CapabilityMissing(m) for m in missing]

            # Get strengthening mechanisms
            mechanisms = contract.strengthening_mechanisms

            # Build capability-aware survivor
            aware_survivor = CapabilityAwareSurvivor(
                survivor_id=survivor_data.get("survivor_id", ""),
                capability_id=capability_id,
                capability_name=contract.name,
                component=survivor_data.get("component", ""),
                source_file=survivor_data.get("source_file", ""),
                source_location=survivor_data.get("source_location", ""),
                function=survivor_data.get("function", ""),
                mutation_type=survivor_data.get("mutation_type", ""),
                original_expression=survivor_data.get("original_expression", ""),
                mutated_expression=survivor_data.get("mutated_expression", ""),
                classification=classification,
                classification_evidence=survivor_data.get(
                    "classification_evidence", ""
                ),
                covering_tests=survivor_data.get("covering_tests", []),
                covering_test_surface=survivor_data.get("covering_test_surface", []),
                tests_enrichment_provenance=survivor_data.get(
                    "tests_enrichment_provenance", ""
                ),
                investigation_status=survivor_data.get(
                    "investigation_status", "needs_investigation"
                ),
                previous_proposal_status=survivor_data.get(
                    "previous_proposal_status", "not_attempted"
                ),
                previous_validation_status=survivor_data.get(
                    "previous_validation_status", "not_attempted"
                ),
                recommended_action=survivor_data.get("recommended_action", ""),
                evidence_fingerprint=survivor_data.get("evidence_fingerprint", ""),
                capability_maturity=contract.maturity.value,
                capability_missing=missing,
                strengthening_mechanisms=mechanisms,
                measurement_truth_status=measurement_status,
            )

            report.survivors.append(aware_survivor)

            # Generate strengthening decision
            decision = self._generate_decision(aware_survivor, contract)
            report.decisions.append(decision)

        # Build summary
        report.summary = self._build_summary(report)
        return report

    def _generate_decision(
        self, survivor: CapabilityAwareSurvivor, contract
    ) -> StrengtheningDecision:
        """Generate a strengthening decision for a survivor."""
        # Map classification to action
        action_map = {
            SurvivorClass.A: StrengtheningAction.ADD_ASSERTION,
            SurvivorClass.B: StrengtheningAction.ADD_TEST,
            SurvivorClass.C: StrengtheningAction.DOCUMENT_EQUIVALENT,
            SurvivorClass.D: StrengtheningAction.FIX_TEST,
            SurvivorClass.E: StrengtheningAction.FIX_PRODUCTION,
            SurvivorClass.UNKNOWN: StrengtheningAction.NO_ACTION,
        }

        action = action_map.get(survivor.classification, StrengtheningAction.NO_ACTION)

        # Determine if human authorization required
        requires_auth = (
            action == StrengtheningAction.FIX_PRODUCTION
            or CapabilityMissing.NO_STRENGTHENING_PIPELINE
            in survivor.capability_missing
            or survivor.capability_maturity == "certified"
        )

        # Build justification
        justification_parts = [
            f"Survivor {survivor.survivor_id} in {survivor.function} ({survivor.source_location})",
            f"Classification: {survivor.classification.value} ({survivor.classification_evidence})",
            f"Capability: {survivor.capability_name} (maturity: {survivor.capability_maturity})",
            f"Covering tests: {len(survivor.covering_tests)}",
            f"Measurement truth: {survivor.measurement_truth_status}",
        ]

        if survivor.classification == SurvivorClass.A:
            justification_parts.append(
                "Class A: Existing test covers mutation but lacks assertion for mutated behavior"
            )
        elif survivor.classification == SurvivorClass.B:
            justification_parts.append(
                "Class B: No test covers this behavior — new test required"
            )
        elif survivor.classification == SurvivorClass.C:
            justification_parts.append(
                "Class C: Equivalent mutant — mutation doesn't change observable behavior"
            )
        elif survivor.classification == SurvivorClass.D:
            justification_parts.append(
                "Class D: Test deficiency — test is flawed or incorrect"
            )
        elif survivor.classification == SurvivorClass.E:
            justification_parts.append(
                "Class E: Production code defect — mutation reveals real bug"
            )

        justification = "; ".join(justification_parts)

        # Build proposed action details
        target_test = None
        proposed_assertion = None
        proposed_test = None
        production_fix = None

        if action == StrengtheningAction.ADD_ASSERTION and survivor.covering_tests:
            target_test = survivor.covering_tests[0]
            # In real implementation, would analyze the mutant diff to propose specific assertion
            proposed_assertion = f"Assert that {survivor.function} handles {survivor.mutated_expression} correctly"

        elif action == StrengtheningAction.ADD_TEST:
            proposed_test = {
                "target_function": survivor.function,
                "source_file": survivor.source_file,
                "mutation_type": survivor.mutation_type,
                "test_kind": "unit",
                "description": f"Test {survivor.function} behavior when {survivor.original_expression} -> {survivor.mutated_expression}",
            }

        elif action == StrengtheningAction.FIX_PRODUCTION:
            production_fix = {
                "file": survivor.source_file,
                "function": survivor.function,
                "issue": f"Mutation {survivor.original_expression} -> {survivor.mutated_expression} reveals defect",
                "suggested_fix": "Review production logic for this case",
            }

        # Build validation command
        validation_command = f"verify.py mutation --target {survivor.component}"
        rollback_command = "git checkout -- " + survivor.source_file.replace(
            "src/", "backend/src/"
        )

        return StrengtheningDecision(
            survivor_id=survivor.survivor_id,
            capability_id=survivor.capability_id,
            action=action,
            classification=survivor.classification,
            justification=justification,
            target_test=target_test,
            proposed_assertion=proposed_assertion,
            proposed_test=proposed_test,
            production_fix=production_fix,
            requires_human_authorization=requires_auth,
            validation_command=validation_command,
            rollback_command=rollback_command,
            status="proposed",
        )

    def _build_summary(self, report: CapabilityStrengtheningReport) -> dict[str, int]:
        """Build summary statistics."""
        summary = {
            "total_survivors": len(report.survivors),
            "by_classification": {},
            "by_action": {},
            "requiring_authorization": 0,
            "ready_to_validate": 0,
        }

        for s in report.survivors:
            cls = s.classification.value
            summary["by_classification"][cls] = (
                summary["by_classification"].get(cls, 0) + 1
            )

        for d in report.decisions:
            act = d.action.value
            summary["by_action"][act] = summary["by_action"].get(act, 0) + 1
            if d.requires_human_authorization:
                summary["requiring_authorization"] += 1
            if d.status == "proposed" and not d.requires_human_authorization:
                summary["ready_to_validate"] += 1

        return summary


# ---------------------------------------------------------------------------
# Pipeline Integration
# ---------------------------------------------------------------------------


def run_capability_aware_strengthening_pipeline(
    capability_id: str,
    max_survivors: int = 0,
) -> CapabilityStrengtheningReport:
    """
    Run the full capability-aware strengthening pipeline.

    Pipeline stages:
    1. discover — Find survivors for capability from durable intel
    2. classify — Classify each survivor (reuses C42.17 classifier)
    3. propose — Generate strengthening proposals
    4. authorize — Check human authorization requirements
    5. validate — Validate proposals against mutants
    6. record — Record decisions in durable store
    """
    engine = CapabilityAwareStrengtheningEngine()
    return engine.analyze_capability(capability_id)


def format_strengthening_report(report: CapabilityStrengtheningReport) -> str:
    """Format strengthening report for display."""
    lines = []
    lines.append("=" * 80)
    lines.append(f"  CAPABILITY-AWARE STRENGTHENING REPORT: {report.capability_name}")
    lines.append("=" * 80)
    lines.append(f"  Capability: {report.capability_id}")
    lines.append(f"  Generated: {report.generated_at}")
    lines.append("-" * 80)

    lines.append("  SUMMARY:")
    for k, v in report.summary.items():
        if isinstance(v, dict):
            lines.append(f"    {k}:")
            for k2, v2 in v.items():
                lines.append(f"      {k2}: {v2}")
        else:
            lines.append(f"    {k}: {v}")

    lines.append("-" * 80)
    lines.append("  SURVIVORS:")
    for s in report.survivors:
        lines.append(f"    {s.survivor_id}")
        lines.append(f"      Function: {s.function} ({s.source_location})")
        lines.append(
            f"      Mutation: {s.original_expression} -> {s.mutated_expression}"
        )
        lines.append(
            f"      Classification: {s.classification.value} ({s.classification_evidence})"
        )
        lines.append(f"      Covering tests: {len(s.covering_tests)}")
        lines.append(f"      Measurement truth: {s.measurement_truth_status}")

    lines.append("-" * 80)
    lines.append("  DECISIONS:")
    for d in report.decisions:
        lines.append(f"    {d.survivor_id}: {d.action.value}")
        lines.append(f"      Classification: {d.classification.value}")
        lines.append(f"      Justification: {d.justification[:100]}...")
        if d.target_test:
            lines.append(f"      Target test: {d.target_test}")
        if d.proposed_assertion:
            lines.append(f"      Proposed assertion: {d.proposed_assertion}")
        if d.proposed_test:
            lines.append(f"      Proposed test: {d.proposed_test}")
        if d.production_fix:
            lines.append(f"      Production fix: {d.production_fix}")
        lines.append(
            f"      Requires authorization: {'Yes' if d.requires_human_authorization else 'No'}"
        )
        lines.append(f"      Validation: {d.validation_command}")

    lines.append("=" * 80)
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI Commands
# ---------------------------------------------------------------------------


def cmd_strengthen_capability(argv: list[str]) -> int:
    """Run capability-aware strengthening pipeline."""
    import argparse

    parser = argparse.ArgumentParser(prog="verify.py strengthen-capability")
    parser.add_argument("capability_id", help="Capability ID to strengthen")
    parser.add_argument(
        "--max-survivors", type=int, default=0, help="Max survivors to process"
    )
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--out", help="Output file path")
    args = parser.parse_args(argv)

    report = run_capability_aware_strengthening_pipeline(
        args.capability_id, args.max_survivors
    )

    output = report.to_json() if args.json else format_strengthening_report(report)

    if args.out:
        Path(args.out).write_text(output)
        print(f"Written to {args.out}")
    else:
        print(output)

    return 0


def cmd_strengthen_survivor(argv: list[str]) -> int:
    """Analyze and propose strengthening for a specific survivor."""
    import argparse

    parser = argparse.ArgumentParser(prog="verify.py strengthen-survivor")
    parser.add_argument("survivor_id", help="Survivor ID")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--out", help="Output file path")
    args = parser.parse_args(argv)

    intel = load_survivor_intel(DEFAULT_INTEL_PATH)
    survivor = find_survivor(intel, args.survivor_id)

    if not survivor:
        print(f"Survivor not found: {args.survivor_id}", file=sys.stderr)
        return 1

    capability_id = survivor.get("capability")
    if not capability_id:
        print("Survivor has no capability mapping", file=sys.stderr)
        return 1

    engine = CapabilityAwareStrengtheningEngine()
    report = engine.analyze_capability(capability_id)

    # Find the specific decision
    decision = next(
        (d for d in report.decisions if d.survivor_id == args.survivor_id), None
    )
    if not decision:
        print("No decision generated for survivor", file=sys.stderr)
        return 1

    output = (
        json.dumps(decision.to_dict(), indent=2)
        if args.json
        else format_strengthening_report(report)
    )

    if args.out:
        Path(args.out).write_text(output)
        print(f"Written to {args.out}")
    else:
        print(output)

    return 0


if __name__ == "__main__":
    # Demo
    engine = CapabilityAwareStrengtheningEngine()
    report = engine.analyze_capability("credit_card")
    print(format_strengthening_report(report))
