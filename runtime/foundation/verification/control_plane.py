"""
M9-C48 — Verification Control Plane.

Strengthens the existing planner so capability information actually controls
execution. The planner must be able to answer:

    "Given this repository change, what is the minimum defensible verification plan?"

The generated plan contains:
    change → capabilities → blast radius → affected components → invalidated evidence
    → reusable evidence → required verification surfaces → ordered verification tasks
    → escalation conditions → measurement requirements → certification requirements

The planner prefers:
1. reusable authoritative evidence
2. targeted verification
3. component-specific tests
4. capability-specific tests
5. property/invariant/contract verification where applicable
6. targeted mutation/survivor analysis when justified
7. broader verification only when dependency evidence requires escalation

A full repository mutation campaign is an EXPLICIT ESCALATION, never the default.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal, cast

from runtime.foundation.verification.capability_contract import (
    CapabilityContractRegistry,
    CapabilityMissing,
    OperationalCapability,
    get_capability_contract_registry,
)
from runtime.foundation.verification.capability_resolver import (
    CapabilityResolution,
    resolve_capabilities,
)
from runtime.foundation.verification.evidence_planner import (
    EvidenceAwarePlan,
    EvidenceAwarePlanner,
    default_planner,
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
    MeasurementKind,
)
from runtime.foundation.verification.planner import (
    VerificationPlanner,
)

# ---------------------------------------------------------------------------
# Control Plane Plan Model
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class VerificationTask:
    """A single verification task in the control plane plan."""

    task_id: str
    capability_id: str
    verification_kind: Literal[
        "unit",
        "property",
        "invariant",
        "contract",
        "coverage",
        "mutation",
        "integration",
        "golden",
        "e2e",
    ]
    command: str
    profile: str
    is_mandatory: bool
    is_escalation: bool
    reason: str
    evidence_reused: list[str] = field(default_factory=list)
    evidence_invalidated: list[str] = field(default_factory=list)
    measurement_required: list[MeasurementKind] = field(default_factory=list)
    estimated_duration_seconds: int = 0
    escalation_trigger: str = ""

    def to_dict(self) -> dict:
        return {
            **asdict(self),
            "measurement_required": [m.value for m in self.measurement_required],
        }


@dataclass(frozen=True, slots=True)
class ControlPlanePlan:
    """The complete control plane verification plan."""

    plan_id: str
    generated_at: str
    changed_files: list[str]
    capability_resolution: CapabilityResolution
    tasks: list[VerificationTask]
    total_estimated_duration_seconds: int
    escalation_conditions: list[str]
    measurement_requirements: list[dict]
    certification_requirements: list[dict]
    rationale: str

    def to_dict(self) -> dict:
        return {
            **asdict(self),
            "capability_resolution": self.capability_resolution.to_dict(),
            "tasks": [t.to_dict() for t in self.tasks],
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, default=str)


# ---------------------------------------------------------------------------
# Control Plane Planner
# ---------------------------------------------------------------------------


class ControlPlanePlanner:
    """
    The Verification Control Plane planner.

    Takes a capability resolution and produces a defensible verification plan
    that minimizes execution while maintaining certification integrity.
    """

    def __init__(
        self,
        contract_registry: CapabilityContractRegistry | None = None,
        evidence_planner: EvidenceAwarePlanner | None = None,
        base_planner: VerificationPlanner | None = None,
        graph: VerificationGraph | None = None,
        population: PopulationSnapshot | None = None,
        measurements: list[ComponentMeasurement] | None = None,
    ):
        self._contract_registry = (
            contract_registry or get_capability_contract_registry()
        )
        self._evidence_planner = evidence_planner or default_planner()
        self._base_planner = base_planner or VerificationPlanner()
        self._graph = graph
        self._population = population or c42_26_population()
        self._measurements = measurements or (
            c42_24_b_measurements() + c42_25_measurements()
        )

    def plan(self, changed_files: list[str]) -> ControlPlanePlan:
        """
        Generate a control plane verification plan from changed files.

        This is the main entry point — the answer to "what should I run?".
        """
        # 1. Resolve capabilities from changes
        resolution = resolve_capabilities(
            changed_files,
            contract_registry=self._contract_registry,
            graph=self._graph,
            population=self._population,
            measurements=self._measurements,
        )

        # 2. Get evidence-aware plan for mutation-specific decisions
        evidence_plan = self._evidence_planner.plan(changed_files)

        # 3. Build verification tasks for each affected capability
        tasks = self._build_tasks(resolution, evidence_plan)

        # 4. Determine escalation conditions
        escalation_conditions = self._determine_escalation_conditions(resolution, tasks)

        # 5. Determine measurement requirements
        measurement_reqs = self._determine_measurement_requirements(resolution, tasks)

        # 6. Determine certification requirements
        certification_reqs = self._determine_certification_requirements(
            resolution, tasks
        )

        # 7. Calculate total duration
        total_duration = sum(t.estimated_duration_seconds for t in tasks)

        # 8. Build rationale
        rationale = self._build_rationale(resolution, tasks, evidence_plan)

        plan_id = hashlib.sha256("\n".join(sorted(changed_files)).encode()).hexdigest()[
            :12
        ]

        return ControlPlanePlan(
            plan_id=plan_id,
            generated_at=datetime.now(UTC).isoformat(),
            changed_files=changed_files,
            capability_resolution=resolution,
            tasks=tasks,
            total_estimated_duration_seconds=total_duration,
            escalation_conditions=escalation_conditions,
            measurement_requirements=measurement_reqs,
            certification_requirements=certification_reqs,
            rationale=rationale,
        )

    def _build_tasks(
        self, resolution: CapabilityResolution, evidence_plan: EvidenceAwarePlan
    ) -> list[VerificationTask]:
        """Build verification tasks from capability resolution."""
        tasks = []
        task_counter = 0

        # Process mandatory verification (directly affected capabilities)
        for cap_id in resolution.directly_affected_capabilities:
            contract = self._contract_registry.get_contract(cap_id)
            if not contract:
                continue

            cap_tasks = self._build_capability_tasks(
                contract,
                resolution,
                evidence_plan,
                is_mandatory=True,
                is_escalation=False,
            )
            tasks.extend(cap_tasks)
            task_counter += len(cap_tasks)

        # Process optional/escalation verification (transitively affected)
        for cap_id in resolution.transitively_affected_capabilities:
            contract = self._contract_registry.get_contract(cap_id)
            if not contract:
                continue

            cap_tasks = self._build_capability_tasks(
                contract,
                resolution,
                evidence_plan,
                is_mandatory=False,
                is_escalation=True,
            )
            tasks.extend(cap_tasks)
            task_counter += len(cap_tasks)

        return tasks

    def _build_capability_tasks(
        self,
        contract: OperationalCapability,
        resolution: CapabilityResolution,
        evidence_plan: EvidenceAwarePlan,
        is_mandatory: bool,
        is_escalation: bool,
    ) -> list[VerificationTask]:
        """Build tasks for a single capability."""
        tasks: list[VerificationTask] = []

        # Map workflow mappings to tasks
        for wf in contract.workflow_mappings:
            # Determine verification kind from workflow
            vkind = self._workflow_to_verification_kind(wf.workflow_id)

            # Check if evidence is reusable for this capability
            reused = [
                e for e in resolution.reusable_evidence if cap_id_match(e, contract.id)
            ]
            invalidated = [
                e
                for e in resolution.invalidated_evidence
                if cap_id_match(e, contract.id)
            ]

            # Determine measurement requirements
            measurements = []
            for mm in contract.measurement_mappings:
                if mm.required_for_certification or is_mandatory:
                    measurements.append(mm.measurement_kind)

            # Build reason
            reason_parts = []
            if is_mandatory:
                reason_parts.append("Directly affected by change")
            if is_escalation:
                reason_parts.append("Transitively affected (escalation)")
            if reused:
                reason_parts.append(f"Reusing {len(reused)} evidence artifacts")
            if invalidated:
                reason_parts.append(f"Invalidated: {', '.join(invalidated)}")

            task = VerificationTask(
                task_id=f"task-{len(tasks) + 1:04d}",
                capability_id=contract.id,
                verification_kind=cast(
                    Literal[
                        "unit",
                        "property",
                        "invariant",
                        "contract",
                        "coverage",
                        "mutation",
                        "integration",
                        "golden",
                        "e2e",
                    ],
                    vkind,
                ),
                command=wf.command,
                profile=wf.profile_name,
                is_mandatory=is_mandatory,
                is_escalation=is_escalation,
                reason="; ".join(reason_parts) or "Capability verification",
                evidence_reused=reused,
                evidence_invalidated=invalidated,
                measurement_required=measurements,
                estimated_duration_seconds=wf.estimated_duration_seconds,
            )
            tasks.append(task)

        return tasks

    def _workflow_to_verification_kind(self, workflow_id: str) -> str:
        """Map workflow ID to verification kind."""
        mapping = {
            "quick": "unit",
            "backend": "unit",
            "frontend": "unit",
            "contracts": "contract",
            "property": "property",
            "mutation": "mutation",
            "integration": "integration",
            "migration": "unit",
            "repository": "unit",
            "full": "unit",
            "runtime": "unit",
            "golden": "golden",
            "playwright": "e2e",
        }
        return mapping.get(workflow_id, "unit")

    def _determine_escalation_conditions(
        self, resolution: CapabilityResolution, tasks: list[VerificationTask]
    ) -> list[str]:
        """Determine conditions that would trigger escalation."""
        conditions = []

        # Check for capabilities with mutation survivors
        for cap_id in resolution.directly_affected_capabilities:
            contract = self._contract_registry.get_contract(cap_id)
            if contract:
                for missing in contract.missing:
                    if missing == CapabilityMissing.NO_SURVIVOR_INTEL:
                        conditions.append(
                            f"Capability {cap_id} lacks survivor intelligence — "
                            "mutation escalation may be needed if survivors found"
                        )
                    if missing == CapabilityMissing.NO_MEASUREMENT_TRUTH:
                        conditions.append(
                            f"Capability {cap_id} lacks measurement truth — "
                            "authoritative mutation score cannot be certified"
                        )

        # Check for cross-capability invalidation
        if resolution.transitively_affected_capabilities:
            conditions.append(
                f"Transitive impact on {len(resolution.transitively_affected_capabilities)} capabilities — "
                "cross-capability escalation may be required if direct verification fails"
            )

        # Check for config changes
        config_changes = [
            c
            for c in resolution.classified_changes
            if c.classification.value == "config_change"
        ]
        if config_changes:
            conditions.append(
                "Configuration changes detected — full population revalidation may be required"
            )

        return conditions

    def _determine_measurement_requirements(
        self, resolution: CapabilityResolution, tasks: list[VerificationTask]
    ) -> list[dict]:
        """Determine measurement requirements for the plan."""
        requirements = []

        # Aggregate measurement kinds from tasks
        measurement_kinds = set()
        for task in tasks:
            measurement_kinds.update(task.measurement_required)

        for kind in measurement_kinds:
            # Find which capabilities require this measurement
            requiring_caps = [
                task.capability_id
                for task in tasks
                if kind in task.measurement_required
            ]

            # Check if we have authoritative evidence
            authoritative_available = False
            for cap_id in requiring_caps:
                contract = self._contract_registry.get_contract(cap_id)
                if contract:
                    for mm in contract.measurement_mappings:
                        if (
                            mm.measurement_kind == kind
                            and mm.authoritative_evidence_path
                        ):
                            authoritative_available = True
                            break

            requirements.append(
                {
                    "measurement_kind": kind.value,
                    "required_for_capabilities": requiring_caps,
                    "authoritative_evidence_available": authoritative_available,
                    "required_for_certification": any(
                        t.is_mandatory for t in tasks if kind in t.measurement_required
                    ),
                }
            )

        return requirements

    def _determine_certification_requirements(
        self, resolution: CapabilityResolution, tasks: list[VerificationTask]
    ) -> list[dict]:
        """Determine certification requirements for affected capabilities."""
        requirements = []

        for cap_id in resolution.directly_affected_capabilities:
            contract = self._contract_registry.get_contract(cap_id)
            if not contract:
                continue

            for cc in contract.certification_conditions:
                # Check if evidence is available
                evidence_available = all(
                    any(e.evidence_id == ev_id for e in contract.evidence_mappings)
                    for ev_id in cc.required_evidence
                )

                requirements.append(
                    {
                        "capability": cap_id,
                        "condition_id": cc.condition_id,
                        "description": cc.description,
                        "evidence_available": evidence_available,
                        "requires_authoritative_classification": cc.requires_authoritative_classification,
                        "minimum_mutation_score": cc.minimum_mutation_score,
                        "minimum_coverage_percent": cc.minimum_coverage_percent,
                    }
                )

        return requirements

    def _build_rationale(
        self,
        resolution: CapabilityResolution,
        tasks: list[VerificationTask],
        evidence_plan: EvidenceAwarePlan,
    ) -> str:
        """Build human-readable rationale for the plan."""
        mandatory_count = sum(1 for t in tasks if t.is_mandatory)
        escalation_count = sum(1 for t in tasks if t.is_escalation)
        reused_count = len(resolution.reusable_evidence)
        invalidated_count = len(resolution.invalidated_evidence)

        return (
            f"Plan generated for {len(resolution.changed_files)} changed file(s). "
            f"Resolved to {len(resolution.directly_affected_capabilities)} directly affected "
            f"and {len(resolution.transitively_affected_capabilities)} transitively affected capabilities. "
            f"Created {mandatory_count} mandatory and {escalation_count} escalation tasks. "
            f"Evidence: {reused_count} reusable, {invalidated_count} invalidated. "
            f"Evidence-aware planner selected {len(evidence_plan.selected_tasks)} mutation tasks "
            f"({len(evidence_plan.excluded_tasks)} excluded as reusable). "
            f"Total estimated duration: {sum(t.estimated_duration_seconds for t in tasks)}s."
        )


# ---------------------------------------------------------------------------
# Plan Formatters
# ---------------------------------------------------------------------------


def format_control_plane_plan(plan: ControlPlanePlan) -> str:
    """Format a control plane plan for human-readable output."""
    lines = []
    lines.append("=" * 80)
    lines.append("  VERIFICATION CONTROL PLAN")
    lines.append("=" * 80)
    lines.append(f"  Plan ID: {plan.plan_id}")
    lines.append(f"  Generated: {plan.generated_at}")
    lines.append(f"  Changed files: {len(plan.changed_files)}")
    lines.append(
        f"  Total estimated duration: {plan.total_estimated_duration_seconds}s"
    )
    lines.append("-" * 80)

    lines.append("  CAPABILITY RESOLUTION:")
    lines.append(
        f"    Directly affected: {len(plan.capability_resolution.directly_affected_capabilities)}"
    )
    for cap in plan.capability_resolution.directly_affected_capabilities:
        lines.append(f"      → {cap}")
    lines.append(
        f"    Transitively affected: {len(plan.capability_resolution.transitively_affected_capabilities)}"
    )
    for cap in plan.capability_resolution.transitively_affected_capabilities:
        lines.append(f"      ~ {cap}")
    lines.append(
        f"    Unaffected: {len(plan.capability_resolution.unaffected_capabilities)}"
    )

    lines.append("-" * 80)
    lines.append("  VERIFICATION TASKS:")
    mandatory_tasks = [t for t in plan.tasks if t.is_mandatory]
    escalation_tasks = [t for t in plan.tasks if t.is_escalation]

    if mandatory_tasks:
        lines.append(f"    MANDATORY ({len(mandatory_tasks)}):")
        for task in mandatory_tasks:
            lines.append(f"      [{task.verification_kind}] {task.capability_id}")
            lines.append(f"        Command: {task.command}")
            lines.append(f"        Profile: {task.profile}")
            lines.append(f"        Reason: {task.reason}")
            if task.evidence_reused:
                lines.append(f"        Reused: {', '.join(task.evidence_reused)}")
            if task.evidence_invalidated:
                lines.append(
                    f"        Invalidated: {', '.join(task.evidence_invalidated)}"
                )
            if task.measurement_required:
                lines.append(
                    f"        Measurements: {', '.join(m.value for m in task.measurement_required)}"
                )

    if escalation_tasks:
        lines.append(f"    ESCALATION ({len(escalation_tasks)}):")
        for task in escalation_tasks:
            lines.append(f"      [{task.verification_kind}] {task.capability_id}")
            lines.append(f"        Command: {task.command}")
            lines.append(f"        Profile: {task.profile}")
            lines.append(f"        Trigger: {task.reason}")

    if plan.escalation_conditions:
        lines.append("-" * 80)
        lines.append("  ESCALATION CONDITIONS:")
        for cond in plan.escalation_conditions:
            lines.append(f"    ⚠ {cond}")

    if plan.measurement_requirements:
        lines.append("-" * 80)
        lines.append("  MEASUREMENT REQUIREMENTS:")
        for mr in plan.measurement_requirements:
            lines.append(
                f"    {mr['measurement_kind']}: {', '.join(mr['required_for_capabilities'])}"
            )
            lines.append(
                f"      Authoritative evidence: {'Yes' if mr['authoritative_evidence_available'] else 'No'}"
            )
            lines.append(
                f"      Required for certification: {'Yes' if mr['required_for_certification'] else 'No'}"
            )

    if plan.certification_requirements:
        lines.append("-" * 80)
        lines.append("  CERTIFICATION REQUIREMENTS:")
        for cr in plan.certification_requirements:
            lines.append(f"    {cr['capability']}: {cr['description']}")
            lines.append(
                f"      Evidence available: {'Yes' if cr['evidence_available'] else 'No'}"
            )

    lines.append("-" * 80)
    lines.append(f"  RATIONALE: {plan.rationale}")
    lines.append("=" * 80)

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Convenience Function
# ---------------------------------------------------------------------------


def generate_control_plane_plan(
    changed_files: list[str],
    contract_registry: CapabilityContractRegistry | None = None,
    evidence_planner: EvidenceAwarePlanner | None = None,
    base_planner: VerificationPlanner | None = None,
    graph: VerificationGraph | None = None,
    population: PopulationSnapshot | None = None,
    measurements: list[ComponentMeasurement] | None = None,
) -> ControlPlanePlan:
    """Convenience function to generate a control plane plan."""
    planner = ControlPlanePlanner(
        contract_registry,
        evidence_planner,
        base_planner,
        graph,
        population,
        measurements,
    )
    return planner.plan(changed_files)


if __name__ == "__main__":
    # Demo
    from runtime.foundation.verification.evidence_reuse import (
        c42_24_b_measurements,
        c42_25_measurements,
        c42_26_population,
    )

    pop = c42_26_population()
    measurements = c42_24_b_measurements() + c42_25_measurements()

    changed = ["backend/src/engines/credit_card_engine/calculator.py"]
    plan = generate_control_plane_plan(
        changed, population=pop, measurements=measurements
    )
    print(format_control_plane_plan(plan))

    # Save to file
    out_path = (
        Path(__file__).parent.parent.parent
        / "generated"
        / "m9-c48"
        / "control-plane-plan-demo.json"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(plan.to_json())
    print(f"\nSaved to {out_path}")


def cap_id_match(evidence_id: str, cap_id: str) -> bool:
    """Check if evidence ID matches capability ID."""
    return cap_id in evidence_id
