"""
M9-C48 — Operational CLI Commands.

Adds the "what should I run?" path for common engineering situations:

### Changed implementation file
    What capabilities are affected?
    What evidence is invalid?
    What should I run?
    What can be reused?

### Failing test
    Which capability does this test represent?
    What implementation surfaces are implicated?
    What additional verification is required?

### Mutation survivor
    What behavior was mutated?
    Which capability owns it?
    Which tests cover it?
    Is the survivor meaningful?
    What strengthening action is justified?

### Coverage decrease
    Which capability lost coverage?
    Which branch/path is uncovered?
    Is it behaviorally important?
    What test should be considered?

### Workflow failure
    Which verification capability failed?
    Is the failure code, test, configuration, infrastructure, or environment?
    What evidence remains valid?
    What should be rerun?

### Proposed production change
    What is the blast radius?
    Which capabilities require revalidation?
    Which evidence becomes invalid?
    What minimum verification is required?

These are derived from the existing machine-readable architecture, not
implemented as unrelated hard-coded special cases.
"""

from __future__ import annotations

import json
import sys
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from runtime.foundation.verification.capability_contract import (
    CapabilityContractRegistry,
    get_capability_contract_registry,
)
from runtime.foundation.verification.capability_resolver import (
    CapabilityResolution,
    format_resolution,
    resolve_capabilities,
)
from runtime.foundation.verification.command_inventory import (
    CommandInventory,
    get_command_inventory,
)
from runtime.foundation.verification.control_plane import (
    ControlPlanePlan,
    format_control_plane_plan,
    generate_control_plane_plan,
)
from runtime.foundation.verification.evidence_reuse import (
    ComponentMeasurement,
    PopulationSnapshot,
    c42_24_b_measurements,
    c42_25_measurements,
    c42_26_population,
)
from runtime.foundation.verification.graph_model import VerificationGraph
from runtime.foundation.verification.measurement_truth import (
    MeasurementTruthRecord,
    load_measurement_truth,
)
from runtime.foundation.verification.survivor_intel import (
    DEFAULT_INTEL_PATH,
    load_survivor_intel,
)

# ---------------------------------------------------------------------------
# Operational Query Models
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class OperationalQueryResult:
    """Result of an operational query."""

    query_type: str
    query_input: str
    answer: dict[str, Any]
    generated_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())

    def to_dict(self) -> dict:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, default=str)


# ---------------------------------------------------------------------------
# Operational Query Handlers
# ---------------------------------------------------------------------------


class OperationalQueryEngine:
    """
    Engine for answering operational verification questions.

    All answers derived from machine-readable architecture.
    """

    def __init__(
        self,
        contract_registry: CapabilityContractRegistry | None = None,
        command_inventory: CommandInventory | None = None,
        population: PopulationSnapshot | None = None,
        measurements: list[ComponentMeasurement] | None = None,
        graph: VerificationGraph | None = None,
    ):
        self._contract_registry = (
            contract_registry or get_capability_contract_registry()
        )
        self._command_inventory = command_inventory or get_command_inventory()
        self._population = population or c42_26_population()
        self._measurements = measurements or (
            c42_24_b_measurements() + c42_25_measurements()
        )
        self._graph = graph

    # ----- Query 1: Changed implementation file -----
    def query_changed_file(self, file_path: str) -> OperationalQueryResult:
        """What capabilities are affected? What evidence invalid? What should I run? What can be reused?"""
        resolution = resolve_capabilities(
            [file_path],
            contract_registry=self._contract_registry,
            graph=self._graph,
            population=self._population,
            measurements=self._measurements,
        )
        plan = generate_control_plane_plan(
            [file_path],
            contract_registry=self._contract_registry,
            population=self._population,
            measurements=self._measurements,
        )

        answer = {
            "directly_affected_capabilities": resolution.directly_affected_capabilities,
            "transitively_affected_capabilities": resolution.transitively_affected_capabilities,
            "unaffected_capabilities": resolution.unaffected_capabilities,
            "invalidated_evidence": resolution.invalidated_evidence,
            "reusable_evidence": resolution.reusable_evidence,
            "mandatory_verification": resolution.mandatory_verification,
            "optional_verification": resolution.optional_verification,
            "unnecessary_verification": resolution.unnecessary_verification,
            "control_plane_plan": plan.to_dict(),
            "recommendation": self._generate_recommendation(resolution, plan),
        }

        return OperationalQueryResult(
            query_type="changed_file",
            query_input=file_path,
            answer=answer,
        )

    # ----- Query 2: Failing test -----
    def query_failing_test(self, test_path: str) -> OperationalQueryResult:
        """Which capability does this test represent? What implementation surfaces implicated? What additional verification required?"""
        # Find capability for test
        capability = self._find_capability_for_test(test_path)

        answer = {
            "test_path": test_path,
            "capability": capability.id if capability else "UNMAPPED",
            "capability_name": capability.name if capability else "Unknown",
            "implementation_surfaces": (
                [s.to_dict() for s in capability.implementation_surfaces]
                if capability
                else []
            ),
            "test_mappings": (
                [t.to_dict() for t in capability.test_mappings] if capability else []
            ),
            "additional_verification": (
                self._get_additional_verification(capability) if capability else []
            ),
            "recommendation": (
                f"Run capability verification for {capability.id}"
                if capability
                else "Test not mapped to any capability"
            ),
        }

        return OperationalQueryResult(
            query_type="failing_test",
            query_input=test_path,
            answer=answer,
        )

    # ----- Query 3: Mutation survivor -----
    def query_mutation_survivor(self, survivor_id: str) -> OperationalQueryResult:
        """What behavior was mutated? Which capability owns it? Which tests cover it? Is the survivor meaningful? What strengthening action is justified?"""
        intel = load_survivor_intel(DEFAULT_INTEL_PATH)
        survivor = None
        for s in intel.get("survivors", []):
            if s.get("survivor_id") == survivor_id:
                survivor = s
                break

        if not survivor:
            answer = {
                "survivor_id": survivor_id,
                "found": False,
                "message": f"Survivor {survivor_id} not found in durable intelligence record",
            }
        else:
            capability = self._contract_registry.get_contract(
                survivor.get("capability", "")
            )
            answer = {
                "survivor_id": survivor_id,
                "found": True,
                "component": survivor.get("component"),
                "source_file": survivor.get("source_file"),
                "source_location": survivor.get("source_location"),
                "function": survivor.get("function"),
                "mutation_type": survivor.get("mutation_type"),
                "original_expression": survivor.get("original_expression"),
                "mutated_expression": survivor.get("mutated_expression"),
                "classification": survivor.get("classification"),
                "subclassification": survivor.get("subclassification"),
                "classification_evidence": survivor.get("classification_evidence"),
                "capability": survivor.get("capability"),
                "capabilities": survivor.get("capabilities", []),
                "covering_tests": survivor.get("covering_tests", []),
                "covering_test_surface": survivor.get("covering_test_surface", []),
                "tests_enrichment_provenance": survivor.get(
                    "tests_enrichment_provenance"
                ),
                "investigation_status": survivor.get("investigation_status"),
                "previous_proposal_status": survivor.get("previous_proposal_status"),
                "previous_validation_status": survivor.get(
                    "previous_validation_status"
                ),
                "recommended_action": survivor.get("recommended_action"),
                "evidence_fingerprint": survivor.get("evidence_fingerprint"),
                "capability_details": capability.to_dict() if capability else None,
                "is_meaningful": survivor.get("classification") in ("A", "B"),
                "strengthening_justified": survivor.get("classification") in ("A", "B")
                and len(survivor.get("covering_tests", [])) > 0,
            }

        return OperationalQueryResult(
            query_type="mutation_survivor",
            query_input=survivor_id,
            answer=answer,
        )

    # ----- Query 4: Coverage decrease -----
    def query_coverage_decrease(
        self, capability_id: str, measurement_record_path: str | None = None
    ) -> OperationalQueryResult:
        """Which capability lost coverage? Which branch/path uncovered? Is it behaviorally important? What test should be considered?"""
        # Load measurement truth record
        record = None
        if measurement_record_path:
            record = load_measurement_truth(measurement_record_path)

        contract = self._contract_registry.get_contract(capability_id)

        answer = {
            "capability_id": capability_id,
            "capability_name": contract.name if contract else "Unknown",
            "measurement_record": record.to_dict() if record else None,
            "coverage_result": record.coverage.as_dict() if record else None,
            "missing_coverage": (
                self._analyze_coverage_gaps(record, capability_id) if record else []
            ),
            "behavioral_importance": "unknown",
            "suggested_tests": [],
            "recommendation": "Run coverage measurement for the capability scope to identify gaps",
        }

        return OperationalQueryResult(
            query_type="coverage_decrease",
            query_input=capability_id,
            answer=answer,
        )

    # ----- Query 5: Workflow failure -----
    def query_workflow_failure(
        self, workflow_id: str, failure_details: dict | None = None
    ) -> OperationalQueryResult:
        """Which verification capability failed? Is the failure code, test, configuration, infrastructure, or environment? What evidence remains valid? What should be rerun?"""
        workflow = self._command_inventory.get_command(f"cmd::{workflow_id}")
        if not workflow:
            # Try to find in profiles
            for profile_cmds in self._command_inventory.profiles.values():
                for cmd_id in profile_cmds:
                    cmd = self._command_inventory.get_command(cmd_id)
                    if cmd and workflow_id in cmd.command:
                        workflow = cmd
                        break

        answer = {
            "workflow_id": workflow_id,
            "command": workflow.command if workflow else "unknown",
            "purpose": workflow.purpose if workflow else "unknown",
            "failure_semantics": (
                workflow.failure_semantics.value if workflow else "unknown"
            ),
            "failure_details": failure_details or {},
            "capabilities_served": workflow.capabilities_served if workflow else [],
            "evidence_remains_valid": [],  # Would need evidence store to determine
            "should_rerun": workflow.command if workflow else "unknown",
            "escalation_commands": workflow.escalation_commands if workflow else [],
            "recommendation": self._generate_failure_recommendation(
                workflow, failure_details
            ),
        }

        return OperationalQueryResult(
            query_type="workflow_failure",
            query_input=workflow_id,
            answer=answer,
        )

    # ----- Query 6: Proposed production change -----
    def query_proposed_change(self, changed_files: list[str]) -> OperationalQueryResult:
        """What is the blast radius? Which capabilities require revalidation? Which evidence becomes invalid? What minimum verification is required?"""
        resolution = resolve_capabilities(
            changed_files,
            contract_registry=self._contract_registry,
            graph=self._graph,
            population=self._population,
            measurements=self._measurements,
        )
        plan = generate_control_plane_plan(
            changed_files,
            contract_registry=self._contract_registry,
            population=self._population,
            measurements=self._measurements,
        )

        answer = {
            "changed_files": changed_files,
            "blast_radius": {
                "directly_affected_capabilities": resolution.directly_affected_capabilities,
                "transitively_affected_capabilities": resolution.transitively_affected_capabilities,
                "unaffected_capabilities": resolution.unaffected_capabilities,
            },
            "evidence_invalidation": {
                "invalidated": resolution.invalidated_evidence,
                "reusable": resolution.reusable_evidence,
            },
            "minimum_verification": resolution.mandatory_verification,
            "escalation_verification": resolution.optional_verification,
            "control_plane_plan": plan.to_dict(),
            "recommendation": self._generate_recommendation(resolution, plan),
        }

        return OperationalQueryResult(
            query_type="proposed_change",
            query_input=", ".join(changed_files),
            answer=answer,
        )

    # ----- Helper Methods -----
    def _find_capability_for_test(self, test_path: str):
        """Find the capability that owns a test file."""
        for contract in self._contract_registry.get_all_contracts():
            for mapping in contract.test_mappings:
                if (
                    test_path.startswith(mapping.test_path)
                    or mapping.test_path in test_path
                ):
                    return contract
        return None

    def _get_additional_verification(self, capability) -> list[str]:
        """Get additional verification commands for a capability."""
        if not capability:
            return []
        return capability.escalation_verification_commands

    def _analyze_coverage_gaps(
        self, record: MeasurementTruthRecord, capability_id: str
    ) -> list[dict]:
        """Analyze coverage gaps from measurement truth record."""
        # This would need detailed coverage data per file
        # For now, return summary
        if not record:
            return []
        return [
            {
                "lines_total": record.coverage.lines_total,
                "lines_covered": record.coverage.lines_covered,
                "line_percent": record.coverage.line_percent,
                "branches_total": record.coverage.branches_total,
                "branches_covered": record.coverage.branches_covered,
                "branch_percent": record.coverage.branch_percent,
            }
        ]

    def _generate_recommendation(
        self, resolution: CapabilityResolution, plan: ControlPlanePlan
    ) -> str:
        """Generate a human-readable recommendation."""
        if not resolution.mandatory_verification:
            return "No verification required for this change."

        if len(resolution.mandatory_verification) == 1:
            return f"Run: {resolution.mandatory_verification[0]}"

        return (
            f"Run {len(resolution.mandatory_verification)} mandatory verification tasks. "
            f"Start with: {resolution.mandatory_verification[0]}. "
            f"Consider escalation: {len(resolution.optional_verification)} optional tasks available."
        )

    def _generate_failure_recommendation(
        self, workflow, failure_details: dict | None
    ) -> str:
        """Generate recommendation for workflow failure."""
        if not workflow:
            return "Unknown workflow — cannot recommend action."

        if failure_details:
            error = failure_details.get("error", "").lower()
            if "timeout" in error:
                return f"Infrastructure timeout — increase timeout and rerun: {workflow.command}"
            if "import" in error or "module" in error:
                return f"Configuration/environment failure — check .venv and dependencies, then rerun: {workflow.command}"
            if "assert" in error or "test" in error:
                return f"Verification failure — investigate failing tests, then rerun: {workflow.command}"

        return f"Rerun workflow to confirm: {workflow.command}"


# ---------------------------------------------------------------------------
# CLI Command Handlers
# ---------------------------------------------------------------------------


def cmd_what_should_i_run(argv: list[str]) -> int:
    """Main entry point for operational queries."""
    import argparse

    parser = argparse.ArgumentParser(prog="verify.py what-should-i-run")
    subparsers = parser.add_subparsers(dest="query", required=True)

    # Changed file
    p1 = subparsers.add_parser(
        "changed-file", help="Analyze a changed implementation file"
    )
    p1.add_argument("file_path", help="Path to changed file")

    # Failing test
    p2 = subparsers.add_parser("failing-test", help="Analyze a failing test")
    p2.add_argument("test_path", help="Path to failing test")

    # Mutation survivor
    p3 = subparsers.add_parser("mutation-survivor", help="Analyze a mutation survivor")
    p3.add_argument("survivor_id", help="Mutmut survivor ID")

    # Coverage decrease
    p4 = subparsers.add_parser(
        "coverage-decrease", help="Analyze coverage decrease for a capability"
    )
    p4.add_argument("capability_id", help="Capability ID")
    p4.add_argument("--measurement-record", help="Path to measurement truth record")

    # Workflow failure
    p5 = subparsers.add_parser("workflow-failure", help="Analyze a workflow failure")
    p5.add_argument("workflow_id", help="Workflow/profile ID")
    p5.add_argument("--error", help="Error message from failure")

    # Proposed change
    p6 = subparsers.add_parser(
        "proposed-change", help="Analyze a proposed production change"
    )
    p6.add_argument("files", nargs="+", help="Files that would be changed")

    # Output format
    parser.add_argument("--json", action="store_true", help="Output JSON")
    parser.add_argument("--out", help="Output file path")

    args = parser.parse_args(argv)

    engine = OperationalQueryEngine()

    # Execute query
    if args.query == "changed-file":
        result = engine.query_changed_file(args.file_path)
    elif args.query == "failing-test":
        result = engine.query_failing_test(args.test_path)
    elif args.query == "mutation-survivor":
        result = engine.query_mutation_survivor(args.survivor_id)
    elif args.query == "coverage-decrease":
        result = engine.query_coverage_decrease(
            args.capability_id, args.measurement_record
        )
    elif args.query == "workflow-failure":
        failure_details = {"error": args.error} if args.error else None
        result = engine.query_workflow_failure(args.workflow_id, failure_details)
    elif args.query == "proposed-change":
        result = engine.query_proposed_change(args.files)
    else:
        print(f"Unknown query: {args.query}", file=sys.stderr)
        return 1

    # Output
    output = result.to_json() if args.json else format_operational_result(result)

    if args.out:
        Path(args.out).write_text(output)
        print(f"Written to {args.out}")
    else:
        print(output)

    return 0


def format_operational_result(result: OperationalQueryResult) -> str:
    """Format operational query result for human display."""
    lines = []
    lines.append("=" * 72)
    lines.append(f"  OPERATIONAL QUERY: {result.query_type.upper()}")
    lines.append("=" * 72)
    lines.append(f"  Input: {result.query_input}")
    lines.append(f"  Generated: {result.generated_at}")
    lines.append("-" * 72)

    answer = result.answer
    for key, value in answer.items():
        if isinstance(value, dict):
            lines.append(f"  {key}:")
            for k, v in value.items():
                if isinstance(v, (list, dict)):
                    lines.append(f"    {k}: {json.dumps(v, default=str)[:200]}")
                else:
                    lines.append(f"    {k}: {v}")
        elif isinstance(value, list):
            lines.append(f"  {key} ({len(value)}):")
            for item in value[:10]:
                lines.append(f"    • {item}")
            if len(value) > 10:
                lines.append(f"    ... and {len(value) - 10} more")
        else:
            lines.append(f"  {key}: {value}")

    lines.append("=" * 72)
    return "\n".join(lines)


def cmd_capability_inventory(argv: list[str]) -> int:
    """Show the canonical command/capability inventory."""
    import argparse

    parser = argparse.ArgumentParser(prog="verify.py capability-inventory")
    parser.add_argument("--capability", help="Filter by capability ID")
    parser.add_argument("--profile", help="Filter by profile name")
    parser.add_argument("--category", help="Filter by category")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--out", help="Output file path")
    args = parser.parse_args(argv)

    inventory = get_command_inventory()

    commands = inventory.commands
    if args.capability:
        commands = inventory.get_commands_for_capability(args.capability)
    if args.profile:
        commands = inventory.get_commands_for_profile(args.profile)
    if args.category:
        from runtime.foundation.verification.command_inventory import CommandCategory

        try:
            cat = CommandCategory(args.category)
            commands = [c for c in commands if c.category == cat]
        except ValueError:
            print(f"Unknown category: {args.category}", file=sys.stderr)
            return 1

    if args.json:
        output = json.dumps([c.to_dict() for c in commands], indent=2, default=str)
    else:
        from runtime.foundation.verification.command_inventory import (
            format_inventory_entry,
        )

        lines = []
        lines.append(f"COMMAND INVENTORY ({len(commands)} commands)")
        lines.append("=" * 72)
        for cmd in commands:
            lines.append(format_inventory_entry(cmd))
            lines.append("-" * 72)
        output = "\n".join(lines)

    if args.out:
        Path(args.out).write_text(output)
        print(f"Written to {args.out}")
    else:
        print(output)

    return 0


def cmd_control_plane_plan(argv: list[str]) -> int:
    """Generate and display a control plane plan."""
    import argparse

    parser = argparse.ArgumentParser(prog="verify.py control-plane-plan")
    parser.add_argument("files", nargs="+", help="Changed files")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--out", help="Output file path")
    args = parser.parse_args(argv)

    from runtime.foundation.verification.evidence_reuse import (
        c42_24_b_measurements,
        c42_25_measurements,
        c42_26_population,
    )

    pop = c42_26_population()
    measurements = c42_24_b_measurements() + c42_25_measurements()

    plan = generate_control_plane_plan(
        args.files, population=pop, measurements=measurements
    )

    output = plan.to_json() if args.json else format_control_plane_plan(plan)

    if args.out:
        Path(args.out).write_text(output)
        print(f"Written to {args.out}")
    else:
        print(output)

    return 0


def cmd_resolve_capabilities(argv: list[str]) -> int:
    """Resolve capabilities for changed files."""
    import argparse

    parser = argparse.ArgumentParser(prog="verify.py resolve-capabilities")
    parser.add_argument("files", nargs="+", help="Changed files")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--out", help="Output file path")
    args = parser.parse_args(argv)

    from runtime.foundation.verification.evidence_reuse import (
        c42_24_b_measurements,
        c42_25_measurements,
        c42_26_population,
    )

    pop = c42_26_population()
    measurements = c42_24_b_measurements() + c42_25_measurements()

    resolution = resolve_capabilities(
        args.files, population=pop, measurements=measurements
    )

    output = resolution.to_json() if args.json else format_resolution(resolution)

    if args.out:
        Path(args.out).write_text(output)
        print(f"Written to {args.out}")
    else:
        print(output)

    return 0


# Register commands with verify.py
OPERATIONAL_COMMANDS = {
    "what-should-i-run": cmd_what_should_i_run,
    "capability-inventory": cmd_capability_inventory,
    "control-plane-plan": cmd_control_plane_plan,
    "resolve-capabilities": cmd_resolve_capabilities,
}


if __name__ == "__main__":
    # Demo
    from runtime.foundation.verification.evidence_reuse import (
        c42_24_b_measurements,
        c42_25_measurements,
        c42_26_population,
    )

    pop = c42_26_population()
    measurements = c42_24_b_measurements() + c42_25_measurements()

    engine = OperationalQueryEngine(population=pop, measurements=measurements)

    # Demo: changed file
    result = engine.query_changed_file(
        "backend/src/engines/credit_card_engine/calculator.py"
    )
    print(format_operational_result(result))
