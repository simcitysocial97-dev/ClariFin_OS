"""
M9-C48 — Automatic Capability Resolution from Repository Changes.

Implements the change-impact path so that a changed file/function/module can
resolve to:

    changed surface → capability(s) → affected components → affected verification surfaces
    → invalidated evidence → required verification

This uses existing C42 blast-radius and invalidation mechanisms.
The result is machine-readable and inspectable through the existing CLI.

For every detected change, the system distinguishes:
* directly affected capabilities
* transitively affected capabilities
* unaffected capabilities
* evidence that remains reusable
* evidence invalidated by the change
* verification that is mandatory
* verification that is optional/escalated
* verification that is unnecessary

Does not simply map files to tests — the capability graph remains the
controlling abstraction.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path

from runtime.foundation.verification.capability_contract import (
    CapabilityContractRegistry,
    get_capability_contract_registry,
)
from runtime.foundation.verification.evidence_reuse import (
    Change,
    ComponentMeasurement,
    PopulationSnapshot,
    decide_reuse,
)
from runtime.foundation.verification.graph_model import (
    VerificationGraph,
    source_id,
)
from runtime.foundation.verification.planner import (
    CrossLayerImpactPlanner,
    ImpactReport,
)
from runtime.foundation.verification.shared_impact import (
    SharedDependencyIndex,
    get_shared_dependency_index,
)

# ---------------------------------------------------------------------------
# Planner vocabulary bridge (M9-C49)
# ---------------------------------------------------------------------------
# The CrossLayerImpactPlanner resolves endpoint chains through the knowledge
# graph, whose capability vocabulary is the *frontend* capability naming
# (``useLoansCapability``). The verification registry uses *verification*
# capability IDs (``loan-engine``). This deterministic alias table bridges the
# two vocabularies so blast radius is never silently dropped on an ID mismatch.
PLANNER_CAPABILITY_ALIASES: dict[str, str] = {
    "useLoansCapability": "loan-engine",
}


# ---------------------------------------------------------------------------
# Change Classification
# ---------------------------------------------------------------------------


class ChangeClassification(str, Enum):
    """Classification of a file change."""

    SOURCE_CHANGE = "source_change"
    TEST_CHANGE = "test_change"
    CONFIG_CHANGE = "config_change"
    DOCUMENTATION_CHANGE = "documentation_change"
    INFRASTRUCTURE_CHANGE = "infrastructure_change"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class ClassifiedChange:
    """A single changed file with its classification and capability mapping."""

    path: str
    classification: ChangeClassification
    directly_affected_capabilities: list[str] = field(default_factory=list)
    transitively_affected_capabilities: list[str] = field(default_factory=list)
    affected_components: list[str] = field(default_factory=list)
    affected_surfaces: list[str] = field(default_factory=list)
    reason: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


# ---------------------------------------------------------------------------
# Resolution Result
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class CapabilityResolution:
    """Complete capability resolution for a set of changes."""

    changed_files: list[str]
    classified_changes: list[ClassifiedChange]
    directly_affected_capabilities: list[str]
    transitively_affected_capabilities: list[str]
    unaffected_capabilities: list[str]
    all_affected_capabilities: list[str]
    invalidated_evidence: list[str]
    reusable_evidence: list[str]
    mandatory_verification: list[str]
    optional_verification: list[str]
    unnecessary_verification: list[str]
    blast_radius_report: ImpactReport | None = None
    evidence_reuse_decisions: list[dict] = field(default_factory=list)
    # M9-C49: provenance for how each transitively affected capability was
    # derived (deterministic, machine-readable):
    #   capability id -> list of "source" strings, e.g.
    #     "blast:useLoansCapability -> loan-engine"
    #     "shared-import:backend/src/common/formatting.py"
    capability_sources: dict[str, list[str]] = field(default_factory=dict)
    # Planner-emitted capability IDs with no verification-registry mapping.
    unmapped_blast_capabilities: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            **asdict(self),
            "classified_changes": [c.to_dict() for c in self.classified_changes],
            "blast_radius_report": (
                self.blast_radius_report.to_dict() if self.blast_radius_report else None
            ),
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, default=str)


# ---------------------------------------------------------------------------
# Capability Resolver
# ---------------------------------------------------------------------------


class CapabilityResolver:
    """
    Resolves repository changes to capabilities and verification requirements.

    Uses:
    - CapabilityContractRegistry for capability metadata
    - CrossLayerImpactPlanner for blast-radius analysis
    - EvidenceReuse for invalidation/reuse decisions
    - VerificationGraph for capability→surface mappings
    """

    def __init__(
        self,
        contract_registry: CapabilityContractRegistry | None = None,
        graph: VerificationGraph | None = None,
        population: PopulationSnapshot | None = None,
        measurements: list[ComponentMeasurement] | None = None,
        shared_index: SharedDependencyIndex | None = None,
    ):
        self._contract_registry = (
            contract_registry or get_capability_contract_registry()
        )
        self._graph = graph
        self._population = population
        self._measurements_by_component: dict[str, ComponentMeasurement] = {
            m.component: m for m in (measurements or [])
        }
        self._impact_planner = CrossLayerImpactPlanner()
        # M9-C49: deterministic shared-module dependency index (lazy).
        self._shared_index = shared_index
        if self._shared_index is None:
            try:
                self._shared_index = get_shared_dependency_index(
                    self._contract_registry
                )
            except Exception:
                self._shared_index = None

    def resolve(self, changed_files: list[str]) -> CapabilityResolution:
        """
        Resolve changed files to capabilities and verification requirements.

        This is the main entry point — given a list of changed files,
        returns a complete capability resolution with all derived information.
        """
        # 1. Classify each change
        classified = [self._classify_change(f) for f in changed_files]

        # 2. Collect directly affected capabilities
        direct_caps = set()
        for c in classified:
            direct_caps.update(c.directly_affected_capabilities)

        # 3. Get blast radius from cross-layer impact planner
        blast_report = self._impact_planner.analyze_cross_layer_impact(changed_files)

        # 4. Normalize planner vocabulary + compute transitive capabilities.
        #    Two deterministic sources, each with explicit provenance:
        #      a. planner blast chains (frontend capability vocabulary, bridged
        #         via PLANNER_CAPABILITY_ALIASES),
        #      b. shared-module import dependencies (AST index over the tree).
        capability_sources: dict[str, list[str]] = {}
        unmapped: list[str] = []
        registry_caps = {c.id for c in self._contract_registry.get_all_contracts()}
        transitive_caps: set[str] = set()

        for raw_cap in sorted(set(blast_report.affected_capabilities)):
            norm = PLANNER_CAPABILITY_ALIASES.get(raw_cap, raw_cap)
            if norm == raw_cap and norm not in registry_caps:
                unmapped.append(raw_cap)
                continue
            if norm in direct_caps:
                continue
            transitive_caps.add(norm)
            label = (
                f"blast:{raw_cap}" if raw_cap == norm else f"blast:{raw_cap} -> {norm}"
            )
            capability_sources.setdefault(norm, []).append(label)

        for norm_path in sorted({f.replace("\\", "/") for f in changed_files}):
            if self._shared_index is None:
                break
            for cap in self._shared_index.capabilities_for_module(norm_path):
                if cap in direct_caps or cap in transitive_caps:
                    continue
                if cap not in registry_caps:
                    unmapped.append(cap)
                    continue
                transitive_caps.add(cap)
                capability_sources.setdefault(cap, []).append(
                    f"shared-import:{norm_path}"
                )

        # 5. Determine all registered capabilities
        all_caps = [c.id for c in self._contract_registry.get_all_contracts()]

        # 6. Identify unaffected capabilities
        all_affected = direct_caps | transitive_caps
        unaffected = [c for c in all_caps if c not in all_affected]

        # 7. Evidence reuse/invalidation decisions
        invalidated, reusable, reuse_decisions = self._decide_evidence(
            list(all_affected), classified
        )

        # 8. Determine verification requirements
        mandatory, optional, unnecessary = self._determine_verification(
            list(direct_caps), list(transitive_caps), list(unaffected)
        )

        return CapabilityResolution(
            changed_files=changed_files,
            classified_changes=classified,
            directly_affected_capabilities=sorted(direct_caps),
            transitively_affected_capabilities=sorted(transitive_caps),
            unaffected_capabilities=sorted(unaffected),
            all_affected_capabilities=sorted(all_affected),
            invalidated_evidence=invalidated,
            reusable_evidence=reusable,
            mandatory_verification=mandatory,
            optional_verification=optional,
            unnecessary_verification=unnecessary,
            blast_radius_report=blast_report,
            evidence_reuse_decisions=reuse_decisions,
            capability_sources=capability_sources,
            unmapped_blast_capabilities=sorted(unmapped),
        )

    def _classify_change(self, file_path: str) -> ClassifiedChange:
        """Classify a single file change and determine affected capabilities."""
        norm_path = file_path.replace("\\", "/")

        # Determine classification
        if norm_path.startswith("backend/tests/") and not norm_path.startswith(
            "backend/tests/generated/"
        ):
            classification = ChangeClassification.TEST_CHANGE
        elif norm_path.endswith(
            (
                ".yaml",
                ".yml",
                ".toml",
                ".ini",
                "pyproject.toml",
                "package.json",
                "tsconfig.json",
            )
        ):
            classification = ChangeClassification.CONFIG_CHANGE
        elif norm_path.startswith(".github/") or norm_path.startswith("scripts/"):
            classification = ChangeClassification.INFRASTRUCTURE_CHANGE
        elif norm_path.endswith((".md", ".rst", ".txt")):
            classification = ChangeClassification.DOCUMENTATION_CHANGE
        elif (
            norm_path.startswith("backend/src/")
            or norm_path.startswith("frontend/src/")
            or norm_path.startswith("runtime/")
        ):
            classification = ChangeClassification.SOURCE_CHANGE
        else:
            classification = ChangeClassification.UNKNOWN

        # Find directly affected capabilities via contract registry
        direct_caps = []
        affected_components = []
        affected_surfaces = []

        for contract in self._contract_registry.get_all_contracts():
            # Check if file matches capability's affected_by_paths
            for cap_path in contract.affected_by_paths:
                if norm_path.startswith(cap_path) or cap_path in norm_path:
                    if contract.id not in direct_caps:
                        direct_caps.append(contract.id)
                    # Extract component from path
                    if "engine" in cap_path:
                        comp = cap_path.split("/")[-1].replace("_engine", "")
                        if comp not in affected_components:
                            affected_components.append(comp)

            # Check implementation surfaces
            for surface in contract.implementation_surfaces:
                if norm_path.startswith(surface.path) or surface.path in norm_path:
                    if contract.id not in direct_caps:
                        direct_caps.append(contract.id)
                    affected_surfaces.append(surface.id)

        # If no direct match, try blast-radius planner
        if not direct_caps and self._graph:
            # Use graph to find capability for source
            src_id = source_id(norm_path)
            caps = self._graph.capabilities_for_source(src_id)
            for cap in caps:
                if cap.id not in direct_caps:
                    direct_caps.append(cap.id)

        # Build reason
        reason_parts = []
        if direct_caps:
            reason_parts.append(f"Directly affects: {', '.join(direct_caps)}")
        if affected_components:
            reason_parts.append(f"Components: {', '.join(affected_components)}")
        if not reason_parts:
            reason_parts.append(f"Classification: {classification.value}")

        return ClassifiedChange(
            path=file_path,
            classification=classification,
            directly_affected_capabilities=direct_caps,
            affected_components=affected_components,
            affected_surfaces=affected_surfaces,
            reason="; ".join(reason_parts),
        )

    def _decide_evidence(
        self,
        affected_capabilities: list[str],
        classified_changes: list[ClassifiedChange],
    ) -> tuple[list[str], list[str], list[dict]]:
        """Decide which evidence is invalidated and which is reusable."""
        if not self._population or not self._measurements_by_component:
            return [], [], []

        invalidated = []
        reusable = []
        decisions = []

        # Build change objects for affected components
        changes_by_component: dict[str, Change] = {}
        for c in classified_changes:
            for comp in c.affected_components:
                if comp not in changes_by_component:
                    changes_by_component[comp] = Change(
                        kind=(
                            "source_change"
                            if c.classification == ChangeClassification.SOURCE_CHANGE
                            else c.classification.value
                        ),
                        target=comp,
                    )

        # For each component in population, decide reuse
        for comp in self._population.components:
            change = changes_by_component.get(
                comp, Change(kind="no_change", target=comp)
            )
            measurement = self._measurements_by_component.get(comp)
            reuse = decide_reuse(comp, change, measurement, self._population)

            decision = {
                "component": comp,
                "disposition": reuse.disposition,
                "measurement_id": reuse.measurement_id,
                "invalidations": list(reuse.invalidations),
                "reasons": list(reuse.reasons),
            }
            decisions.append(decision)

            if reuse.disposition in (
                "invalidated_component",
                "invalidated_capability",
                "invalidated_task",
                "invalidated_evidence_only",
            ):
                invalidated.append(comp)
            elif reuse.disposition in (
                "reusable",
                "reusable_aggregate",
                "reusable_with_revalidation",
            ):
                reusable.append(comp)

        return invalidated, reusable, decisions

    def _determine_verification(
        self,
        direct_caps: list[str],
        transitive_caps: list[str],
        unaffected_caps: list[str],
    ) -> tuple[list[str], list[str], list[str]]:
        """Determine mandatory, optional, and unnecessary verification."""
        mandatory = []
        optional = []
        unnecessary = []

        # Directly affected capabilities → mandatory
        for cap_id in direct_caps:
            contract = self._contract_registry.get_contract(cap_id)
            if contract and contract.minimum_verification_command:
                mandatory.append(
                    f"{cap_id}: {contract.minimum_verification_command} ({contract.minimum_verification_profile})"
                )

        # Transitively affected → optional (escalation)
        for cap_id in transitive_caps:
            contract = self._contract_registry.get_contract(cap_id)
            if contract and contract.escalation_verification_commands:
                for cmd, profile in zip(
                    contract.escalation_verification_commands,
                    contract.escalation_verification_profiles,
                    strict=False,
                ):
                    optional.append(f"{cap_id}: {cmd} ({profile})")
            elif contract and contract.minimum_verification_command:
                optional.append(
                    f"{cap_id}: {contract.minimum_verification_command} ({contract.minimum_verification_profile}) [escalated]"
                )

        # Unaffected → unnecessary
        for cap_id in unaffected_caps:
            contract = self._contract_registry.get_contract(cap_id)
            if contract and contract.minimum_verification_command:
                unnecessary.append(
                    f"{cap_id}: {contract.minimum_verification_command} ({contract.minimum_verification_profile})"
                )

        return mandatory, optional, unnecessary


# ---------------------------------------------------------------------------
# Convenience Functions
# ---------------------------------------------------------------------------


def resolve_capabilities(
    changed_files: list[str],
    contract_registry: CapabilityContractRegistry | None = None,
    graph: VerificationGraph | None = None,
    population: PopulationSnapshot | None = None,
    measurements: list[ComponentMeasurement] | None = None,
    shared_index: SharedDependencyIndex | None = None,
) -> CapabilityResolution:
    """Convenience function to resolve capabilities from changed files."""
    resolver = CapabilityResolver(
        contract_registry, graph, population, measurements, shared_index
    )
    return resolver.resolve(changed_files)


def format_resolution(resolution: CapabilityResolution) -> str:
    """Format a capability resolution for human-readable output."""
    lines = []
    lines.append("=" * 72)
    lines.append("  CAPABILITY RESOLUTION")
    lines.append("=" * 72)
    lines.append(f"  Changed files: {len(resolution.changed_files)}")
    lines.append(
        f"  Directly affected capabilities: {len(resolution.directly_affected_capabilities)}"
    )
    lines.append(
        f"  Transitively affected capabilities: {len(resolution.transitively_affected_capabilities)}"
    )
    lines.append(
        f"  Unaffected capabilities: {len(resolution.unaffected_capabilities)}"
    )
    lines.append("-" * 72)

    if resolution.directly_affected_capabilities:
        lines.append("  DIRECTLY AFFECTED:")
        for cap in resolution.directly_affected_capabilities:
            lines.append(f"    • {cap}")

    if resolution.transitively_affected_capabilities:
        lines.append("  TRANSITIVELY AFFECTED:")
        for cap in resolution.transitively_affected_capabilities:
            lines.append(f"    • {cap}")

    if resolution.unaffected_capabilities:
        lines.append("  UNAFFECTED:")
        for cap in resolution.unaffected_capabilities[:10]:
            lines.append(f"    • {cap}")
        if len(resolution.unaffected_capabilities) > 10:
            lines.append(
                f"    ... and {len(resolution.unaffected_capabilities) - 10} more"
            )

    lines.append("-" * 72)
    lines.append("  EVIDENCE:")
    lines.append(f"    Invalidated: {len(resolution.invalidated_evidence)}")
    for comp in resolution.invalidated_evidence:
        lines.append(f"      ✗ {comp}")
    lines.append(f"    Reusable: {len(resolution.reusable_evidence)}")
    for comp in resolution.reusable_evidence:
        lines.append(f"      ✓ {comp}")

    lines.append("-" * 72)
    lines.append("  VERIFICATION:")
    lines.append(f"    Mandatory: {len(resolution.mandatory_verification)}")
    for v in resolution.mandatory_verification:
        lines.append(f"      → {v}")
    lines.append(f"    Optional (escalation): {len(resolution.optional_verification)}")
    for v in resolution.optional_verification:
        lines.append(f"      ~ {v}")
    lines.append(f"    Unnecessary: {len(resolution.unnecessary_verification)}")

    lines.append("=" * 72)
    return "\n".join(lines)


if __name__ == "__main__":
    # Demo: resolve capabilities for a sample change
    from runtime.foundation.verification.evidence_reuse import (
        c42_24_b_measurements,
        c42_25_measurements,
        c42_26_population,
    )

    pop = c42_26_population()
    measurements = c42_24_b_measurements() + c42_25_measurements()

    # Test with a credit card engine change
    changed = ["backend/src/engines/credit_card_engine/calculator.py"]
    resolution = resolve_capabilities(
        changed, population=pop, measurements=measurements
    )
    print(format_resolution(resolution))

    # Save to file
    out_path = (
        Path(__file__).parent.parent.parent
        / "generated"
        / "m9-c48"
        / "capability-resolution-demo.json"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(resolution.to_json())
    print(f"\nSaved to {out_path}")
