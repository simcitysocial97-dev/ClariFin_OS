"""
M9-C50 — Canonical Blast-Radius Contract.

The single canonical deterministic contract representing change impact.
Answers the 15 questions required by the C50 spec:

1. what changed?
2. which files/surfaces changed?
3. which capabilities are affected?
4. which components are affected?
5. which shared dependencies caused expansion?
6. which verification surfaces are affected?
7. which tests are required?
8. which workflows are affected?
9. which evidence became stale?
10. what can safely be reused?
11. what must be revalidated?
12. what cannot currently be mapped?
13. why was each item included?
14. what is the minimum safe verification scope?
15. what is the escalation condition?

Every impact decision has machine-readable provenance/reasons.

This module is additive on top of the C42/C47/C48/C49 architecture.
It does not create a duplicate representation — it extends the existing
contracts (CapabilityResolution, ControlPlanePlan, ExecutionPlan) with
a unified blast-radius view.
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path

from runtime.foundation.verification.capability_contract import (
    CapabilityContractRegistry,
    get_capability_contract_registry,
)
from runtime.foundation.verification.capability_resolver import (
    CapabilityResolution,
    resolve_capabilities,
)
from runtime.foundation.verification.change_surface import (
    ChangeSurfaceAnalysis,
    SurfaceKind,
    discover_change_surfaces,
)
from runtime.foundation.verification.command_inventory import (
    CommandInventory,
    get_command_inventory,
)
from runtime.foundation.verification.evidence_reuse import (
    ComponentMeasurement,
    PopulationSnapshot,
    c42_24_b_measurements,
    c42_25_measurements,
    c42_26_population,
)
from runtime.foundation.verification.shared_impact import (
    SharedDependencyIndex,
    get_shared_dependency_index,
)

# ---------------------------------------------------------------------------
# Blast-radius taxonomy (C50 — M50.2)
# ---------------------------------------------------------------------------


class ImpactKind(str, Enum):
    """How a capability was affected."""

    DIRECTLY_AFFECTED = "directly_affected"
    TRANSITIVELY_AFFECTED = "transitively_affected"
    SHARED_INFRASTRUCTURE_AFFECTED = "shared_infrastructure_affected"
    OBSERVABLE_ONLY = "observable_only"
    TEST_ONLY = "test_only"
    CONFIGURATION_TOOLING = "configuration_tooling"
    UNMAPPED = "unmapped"


class VerificationSurfaceKind(str, Enum):
    """The kind of verification surface required."""

    UNIT = "unit"
    CONTRACT = "contract"
    INVARIANT = "invariant"
    PROPERTY = "property"
    INTEGRATION = "integration"
    FRONTEND = "frontend"
    BACKEND = "backend"
    ARCHITECTURE = "architecture"
    MUTATION = "mutation"
    WORKFLOW_CI = "workflow_ci"
    GOLDEN = "golden"
    EVIDENCE_RECONCILIATION = "evidence_reconciliation"
    SHARED_IMPACT = "shared_impact"


class EvidenceDisposition(str, Enum):
    """What to do with a piece of evidence after a blast-radius change."""

    REUSABLE = "reusable"
    STALE_REVALIDATION_REQUIRED = "stale_revalidation_required"
    MISSING_FRESH_MEASUREMENT_REQUIRED = "missing_fresh_measurement_required"
    NON_CERTIFIABLE = "non_certifiable"
    INSUFFICIENT_DATA = "insufficient_data"


# ---------------------------------------------------------------------------
# Blast-radius items (provenance-rich)
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class SurfaceImpact:
    """A single changed surface with its blast-radius impact."""

    path: str
    kind: str  # SurfaceKind value
    directly_affects_capabilities: list[str] = field(default_factory=list)
    transitively_affects_capabilities: list[str] = field(default_factory=list)
    shared_dependency_expansion: list[str] = field(default_factory=list)
    reason: str = ""
    is_unmapped: bool = False

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class CapabilityImpact:
    """A single capability's blast-radius impact with provenance."""

    capability_id: str
    impact_kind: str  # ImpactKind value
    affected_components: list[str] = field(default_factory=list)
    required_verification_surfaces: list[str] = field(default_factory=list)
    required_tests: list[str] = field(default_factory=list)
    required_workflows: list[str] = field(default_factory=list)
    invalidated_evidence: list[str] = field(default_factory=list)
    reusable_evidence: list[str] = field(default_factory=list)
    revalidation_required: list[str] = field(default_factory=list)
    sources: list[str] = field(default_factory=list)  # why included
    is_mapped: bool = True

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class VerificationSurfaceRequirement:
    """A required verification surface with its executable command."""

    surface_kind: str  # VerificationSurfaceKind value
    capability_id: str
    command: str
    profile: str
    estimated_duration_seconds: int = 0
    is_mandatory: bool = True
    is_escalation: bool = False
    authorization_required: bool = False
    reason: str = ""
    has_executable_command: bool = True

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class EvidenceInvalidation:
    """An evidence invalidation decision with rule and reason."""

    evidence_id: str
    capability_id: str
    disposition: str  # EvidenceDisposition value
    invalidation_rules: list[str] = field(default_factory=list)
    reason: str = ""
    repository_sha_match: bool = True
    record_path: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class EscalationCondition:
    """A condition that would trigger escalation."""

    condition_id: str
    description: str
    triggered: bool
    reason: str

    def to_dict(self) -> dict:
        return asdict(self)


# ---------------------------------------------------------------------------
# Canonical blast-radius contract
# ---------------------------------------------------------------------------


@dataclass
class BlastRadiusContract:
    """The single canonical blast-radius contract for a repository change.

    Answers all 15 questions from the C50 spec with machine-readable
    provenance for every decision.
    """

    contract_id: str
    generated_at: str
    repository_sha: str
    working_tree_dirty: bool
    discovery_source: str  # ChangeScope value

    # Q1+Q2: what changed and which surfaces
    change_surface: ChangeSurfaceAnalysis
    surface_impacts: list[SurfaceImpact]

    # Q3: which capabilities are affected
    capability_impacts: list[CapabilityImpact]
    directly_affected_capabilities: list[str]
    transitively_affected_capabilities: list[str]
    shared_infrastructure_affected_capabilities: list[str]
    observable_only_capabilities: list[str]
    test_only_capabilities: list[str]
    configuration_tooling_capabilities: list[str]
    unmapped_capabilities: list[str]

    # Q4: which components are affected
    affected_components: list[str]

    # Q5: which shared dependencies caused expansion
    shared_dependency_expansions: list[dict]

    # Q6+Q7+Q8: verification surfaces, tests, workflows
    verification_surface_requirements: list[VerificationSurfaceRequirement]
    required_tests: list[str]
    affected_workflows: list[str]

    # Q9+Q10+Q11: evidence state
    evidence_invalidations: list[EvidenceInvalidation]
    reusable_evidence: list[str]
    revalidation_required: list[str]

    # Q12: what cannot currently be mapped
    unmapped_surfaces: list[SurfaceImpact]

    # Q14+Q15: minimum scope + escalation
    minimum_safe_verification: list[VerificationSurfaceRequirement]
    escalation_conditions: list[EscalationCondition]

    # Q13: provenance for every decision
    decision_provenance: dict[str, list[str]]

    # Fail-closed status
    is_fail_closed: bool
    fail_closed_reasons: list[str]

    # Symbol-level change detection (M9-C50 extended)
    changed_symbols: dict[str, list[str]] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "schema": "m9-c50-blast-radius-contract/v1",
            "contract_id": self.contract_id,
            "generated_at": self.generated_at,
            "repository_sha": self.repository_sha,
            "working_tree_dirty": self.working_tree_dirty,
            "discovery_source": self.discovery_source,
            "change_surface": self.change_surface.to_dict(),
            "surface_impacts": [s.to_dict() for s in self.surface_impacts],
            "capability_impacts": [c.to_dict() for c in self.capability_impacts],
            "directly_affected_capabilities": list(self.directly_affected_capabilities),
            "transitively_affected_capabilities": list(
                self.transitively_affected_capabilities
            ),
            "shared_infrastructure_affected_capabilities": list(
                self.shared_infrastructure_affected_capabilities
            ),
            "observable_only_capabilities": list(self.observable_only_capabilities),
            "test_only_capabilities": list(self.test_only_capabilities),
            "configuration_tooling_capabilities": list(
                self.configuration_tooling_capabilities
            ),
            "unmapped_capabilities": list(self.unmapped_capabilities),
            "affected_components": list(self.affected_components),
            "shared_dependency_expansions": list(self.shared_dependency_expansions),
            "verification_surface_requirements": [
                v.to_dict() for v in self.verification_surface_requirements
            ],
            "required_tests": list(self.required_tests),
            "affected_workflows": list(self.affected_workflows),
            "evidence_invalidations": [
                e.to_dict() for e in self.evidence_invalidations
            ],
            "reusable_evidence": list(self.reusable_evidence),
            "revalidation_required": list(self.revalidation_required),
            "unmapped_surfaces": [s.to_dict() for s in self.unmapped_surfaces],
            "minimum_safe_verification": [
                v.to_dict() for v in self.minimum_safe_verification
            ],
            "escalation_conditions": [e.to_dict() for e in self.escalation_conditions],
            "decision_provenance": dict(self.decision_provenance),
            "is_fail_closed": self.is_fail_closed,
            "fail_closed_reasons": list(self.fail_closed_reasons),
            "changed_symbols": dict(self.changed_symbols),
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, default=str)

    def compute_fingerprint(self) -> str:
        """Deterministic fingerprint of the contract (content-only, no timestamps)."""
        h = hashlib.sha256()
        h.update(self.repository_sha.encode("utf-8"))
        h.update(self.discovery_source.encode("utf-8"))
        for f in sorted(self.change_surface.changed_files):
            h.update(f.encode("utf-8"))
        for c in sorted(self.directly_affected_capabilities):
            h.update(c.encode("utf-8"))
        for c in sorted(self.transitively_affected_capabilities):
            h.update(c.encode("utf-8"))
        for c in sorted(self.shared_infrastructure_affected_capabilities):
            h.update(c.encode("utf-8"))
        for c in sorted(self.unmapped_capabilities):
            h.update(c.encode("utf-8"))
        return h.hexdigest()


# ---------------------------------------------------------------------------
# Blast-radius engine
# ---------------------------------------------------------------------------


class BlastRadiusEngine:
    """The engine that computes the canonical blast-radius contract.

    Connects change surface discovery → capability resolution →
    verification surface expansion → evidence invalidation → escalation.
    """

    def __init__(
        self,
        contract_registry: CapabilityContractRegistry | None = None,
        command_inventory: CommandInventory | None = None,
        population: PopulationSnapshot | None = None,
        measurements: list[ComponentMeasurement] | None = None,
        shared_index: SharedDependencyIndex | None = None,
    ):
        self._contract_registry = (
            contract_registry or get_capability_contract_registry()
        )
        self._command_inventory = command_inventory or get_command_inventory()
        self._population = population or c42_26_population()
        self._measurements = measurements or (
            c42_24_b_measurements() + c42_25_measurements()
        )
        self._shared_index = shared_index
        if self._shared_index is None:
            try:
                self._shared_index = get_shared_dependency_index(
                    self._contract_registry
                )
            except Exception:
                self._shared_index = None

    def compute(
        self,
        explicit_files: list[str] | None = None,
        base: str | None = None,
        head: str | None = None,
    ) -> BlastRadiusContract:
        """Compute the canonical blast-radius contract."""
        # Step 1: Discover change surfaces
        change_surface = discover_change_surfaces(explicit_files, base, head)

        # Step 2: Resolve capabilities via C48 resolver
        resolution = resolve_capabilities(
            change_surface.changed_files,
            contract_registry=self._contract_registry,
            population=self._population,
            measurements=self._measurements,
            shared_index=self._shared_index,
        )

        # Step 3: Build surface impacts with provenance
        surface_impacts = self._build_surface_impacts(change_surface, resolution)

        # Step 4: Build capability impacts with provenance
        capability_impacts = self._build_capability_impacts(
            change_surface, resolution, surface_impacts
        )

        # Step 5: Determine verification surfaces
        verification_surfaces = self._build_verification_surfaces(capability_impacts)

        # Step 6: Determine evidence invalidations
        evidence_invalidations, reusable, revalidation = self._build_evidence_decisions(
            change_surface, resolution
        )

        # Step 7: Determine minimum safe scope
        minimum_safe = [
            v for v in verification_surfaces if v.is_mandatory and not v.is_escalation
        ]

        # Step 8: Determine escalation conditions
        escalation_conditions = self._determine_escalation_conditions(
            change_surface, capability_impacts, verification_surfaces
        )

        # Step 9: Determine fail-closed status
        is_fail_closed, fail_reasons = self._determine_fail_closed(
            change_surface, capability_impacts, verification_surfaces, resolution
        )

        # Build the contract
        direct = resolution.directly_affected_capabilities
        transitive = [
            c
            for c in resolution.transitively_affected_capabilities
            if c not in resolution.unmapped_blast_capabilities
        ]
        unmapped_caps = resolution.unmapped_blast_capabilities

        # Classify capabilities by impact kind
        shared_infra = self._classify_shared_infrastructure(capability_impacts)
        test_only = self._classify_test_only(capability_impacts, change_surface)
        config_tooling = self._classify_config_tooling(
            capability_impacts, change_surface
        )
        observable = self._classify_observable_only(capability_impacts, change_surface)

        # Provenance map
        provenance: dict[str, list[str]] = {}
        for ci in capability_impacts:
            provenance[ci.capability_id] = list(ci.sources)

        contract = BlastRadiusContract(
            contract_id="",  # set after construction
            generated_at=datetime.now(UTC).isoformat(),
            repository_sha=change_surface.repository_sha,
            working_tree_dirty=change_surface.working_tree_dirty,
            discovery_source=change_surface.discovery_source.value,
            change_surface=change_surface,
            surface_impacts=surface_impacts,
            capability_impacts=capability_impacts,
            directly_affected_capabilities=direct,
            transitively_affected_capabilities=transitive,
            shared_infrastructure_affected_capabilities=shared_infra,
            observable_only_capabilities=observable,
            test_only_capabilities=test_only,
            configuration_tooling_capabilities=config_tooling,
            unmapped_capabilities=unmapped_caps,
            affected_components=self._collect_affected_components(capability_impacts),
            shared_dependency_expansions=self._collect_shared_expansions(
                surface_impacts, resolution
            ),
            verification_surface_requirements=verification_surfaces,
            required_tests=self._collect_required_tests(capability_impacts),
            affected_workflows=self._collect_affected_workflows(verification_surfaces),
            evidence_invalidations=evidence_invalidations,
            reusable_evidence=reusable,
            revalidation_required=revalidation,
            unmapped_surfaces=[s for s in surface_impacts if s.is_unmapped],
            minimum_safe_verification=minimum_safe,
            escalation_conditions=escalation_conditions,
            decision_provenance=provenance,
            is_fail_closed=is_fail_closed,
            fail_closed_reasons=fail_reasons,
        )

        # Compute deterministic contract ID
        contract.contract_id = f"brc-{contract.compute_fingerprint()[:12]}"

        # Symbol-level change detection
        changed_symbols = self.compute_changed_symbols(
            [Path(f) for f in change_surface.changed_files]
        )
        contract.changed_symbols = {
            str(file): [s.name for s in symbols]
            for file, symbols in changed_symbols.items()
        }

        return contract

    def compute_changed_symbols(
        self, changed_files: list[Path]
    ) -> dict[Path, set]:
        """Determine which symbols (functions/methods/classes) changed.

        Uses git diff to get changed line ranges per file, then maps
        those lines to extracted symbols via SymbolExtractor.
        """
        from .symbol_resolver import SymbolExtractor

        extractor = SymbolExtractor()
        file_to_changed_symbols: dict[Path, set] = {}

        for file_path in changed_files:
            file_path = Path(file_path)
            if not str(file_path).endswith(".py"):
                continue

            # Get changed line ranges from git diff
            try:
                diff_output = subprocess.check_output(
                    ["git", "diff", "-U0", "HEAD", str(file_path)],
                    text=True,
                    stderr=subprocess.DEVNULL,
                )
            except subprocess.CalledProcessError:
                # File might be new or git not available — treat as fully changed
                all_symbols = extractor.extract_from_file(file_path)
                file_to_changed_symbols[file_path] = set(all_symbols)
                continue
            except Exception:
                all_symbols = extractor.extract_from_file(file_path)
                file_to_changed_symbols[file_path] = set(all_symbols)
                continue

            # Parse diff hunk headers for changed line numbers
            changed_lines: set[int] = set()
            for line in diff_output.splitlines():
                match = re.match(r"^@@\s+-\d+(?:,\d+)?\s+\+(\d+)(?:,(\d+))?\s+@@", line)
                if match:
                    start = int(match.group(1))
                    count = int(match.group(2)) if match.group(2) else 1
                    changed_lines.update(range(start, start + count))

            if not changed_lines:
                continue

            # Find symbols containing changed lines
            symbols = extractor.extract_from_file(file_path)
            changed_symbols: set = set()

            for symbol in symbols:
                if any(
                    symbol.start_line <= line <= symbol.end_line
                    for line in changed_lines
                ):
                    changed_symbols.add(symbol)

            if changed_symbols:
                file_to_changed_symbols[file_path] = changed_symbols

        return file_to_changed_symbols

    def _build_surface_impacts(
        self,
        change_surface: ChangeSurfaceAnalysis,
        resolution: CapabilityResolution,
    ) -> list[SurfaceImpact]:
        """Build per-surface impacts with provenance."""
        impacts: list[SurfaceImpact] = []
        for classified in change_surface.surfaces:
            # Map surface to capabilities
            direct: list[str] = []
            transitive: list[str] = []
            shared_exp: list[str] = []

            # From resolution: find capabilities that mention this path
            for cap_id in resolution.directly_affected_capabilities:
                if self._surface_maps_to_capability(classified.path, cap_id):
                    direct.append(cap_id)

            # Check shared-dependency expansion
            if self._shared_index is not None and classified.is_shared_infrastructure:
                dependent_caps = self._shared_index.capabilities_for_module(
                    classified.path
                )
                for cap in dependent_caps:
                    if cap not in direct and cap in (
                        set(resolution.transitively_affected_capabilities)
                        | set(resolution.directly_affected_capabilities)
                    ):
                        shared_exp.append(cap)
                        if cap not in transitive:
                            transitive.append(cap)

            # Check if this is an unmapped production surface
            is_unmapped = (
                classified.is_production
                and classified.kind
                not in (SurfaceKind.GENERATED, SurfaceKind.DOCUMENTATION)
                and not direct
                and not transitive
                and not shared_exp
            )

            reason = classified.reason
            if is_unmapped:
                reason += " | UNMAPPED: production surface with no capability mapping"

            impacts.append(
                SurfaceImpact(
                    path=classified.path,
                    kind=classified.kind.value,
                    directly_affects_capabilities=direct,
                    transitively_affects_capabilities=transitive,
                    shared_dependency_expansion=shared_exp,
                    reason=reason,
                    is_unmapped=is_unmapped,
                )
            )
        return impacts

    def _surface_maps_to_capability(self, path: str, cap_id: str) -> bool:
        """Check if a surface path maps to a capability."""
        contract = self._contract_registry.get_contract(cap_id)
        if not contract:
            return False
        norm = path.replace("\\", "/")
        for module in contract.affected_by_paths:
            if norm.startswith(module) or module in norm:
                return True
        for surface in contract.implementation_surfaces:
            if norm.startswith(surface.path) or surface.path in norm:
                return True
        return False

    def _build_capability_impacts(
        self,
        change_surface: ChangeSurfaceAnalysis,
        resolution: CapabilityResolution,
        surface_impacts: list[SurfaceImpact],
    ) -> list[CapabilityImpact]:
        """Build per-capability impacts with provenance."""
        all_affected = (
            set(resolution.directly_affected_capabilities)
            | set(resolution.transitively_affected_capabilities)
            | set(resolution.unmapped_blast_capabilities)
        )
        impacts: list[CapabilityImpact] = []

        # Collect per-capability evidence from surface impacts
        cap_to_surfaces: dict[str, list[SurfaceImpact]] = {}
        for si in surface_impacts:
            for cap in si.directly_affects_capabilities:
                cap_to_surfaces.setdefault(cap, []).append(si)
            for cap in si.transitively_affects_capabilities:
                cap_to_surfaces.setdefault(cap, []).append(si)
            for cap in si.shared_dependency_expansion:
                cap_to_surfaces.setdefault(cap, []).append(si)

        for cap_id in sorted(all_affected):
            sources: list[str] = []
            is_mapped = cap_id not in resolution.unmapped_blast_capabilities

            # Direct sources
            if cap_id in resolution.directly_affected_capabilities:
                sources.append("direct: capability contract path match")
                impact_kind = ImpactKind.DIRECTLY_AFFECTED.value
            elif cap_id in resolution.transitively_affected_capabilities:
                sources.append("transitive: capability resolution")
                impact_kind = ImpactKind.TRANSITIVELY_AFFECTED.value
            elif cap_id in resolution.unmapped_blast_capabilities:
                sources.append(
                    "unmapped: planner emitted capability with no registry mapping"
                )
                impact_kind = ImpactKind.UNMAPPED.value
            else:
                impact_kind = ImpactKind.TRANSITIVELY_AFFECTED.value

            # Add surface-level sources
            for si in cap_to_surfaces.get(cap_id, []):
                if (
                    si.shared_dependency_expansion
                    and cap_id in si.shared_dependency_expansion
                ):
                    sources.append(
                        f"shared-dependency: {si.path} transitively affects {cap_id}"
                    )
                    impact_kind = ImpactKind.SHARED_INFRASTRUCTURE_AFFECTED.value

            # Add capability source from resolution
            if cap_id in resolution.capability_sources:
                for src in resolution.capability_sources[cap_id]:
                    sources.append(f"resolver: {src}")

            # Get contract for verification surface derivation
            contract = self._contract_registry.get_contract(cap_id)
            affected_components: list[str] = []
            required_surfaces: list[str] = []
            required_tests: list[str] = []
            required_workflows: list[str] = []

            if contract:
                # Components
                for module in contract.affected_by_paths:
                    if "engine" in module:
                        comp = module.split("/")[-1].replace("_engine", "")
                        if comp not in affected_components:
                            affected_components.append(comp)

                # Verification surfaces from workflow mappings
                for wf in contract.workflow_mappings:
                    surface_kind = self._map_workflow_to_surface(wf.workflow_id)
                    if surface_kind not in required_surfaces:
                        required_surfaces.append(surface_kind)
                    if wf.profile_name not in required_workflows:
                        required_workflows.append(wf.profile_name)

                # Tests from test mappings
                for tm in contract.test_mappings:
                    if tm.test_path and tm.test_path not in required_tests:
                        required_tests.append(tm.test_path)

            # Evidence state
            invalidated: list[str] = []
            reusable: list[str] = []
            revalidation: list[str] = []
            for ev in resolution.evidence_reuse_decisions:
                if ev.get("component") in affected_components:
                    disp = ev.get("disposition", "")
                    if "invalidated" in disp:
                        invalidated.append(ev.get("component", ""))
                    elif "reusable" in disp:
                        reusable.append(ev.get("component", ""))
                    if "revalidation" in disp:
                        revalidation.append(ev.get("component", ""))

            impacts.append(
                CapabilityImpact(
                    capability_id=cap_id,
                    impact_kind=impact_kind,
                    affected_components=sorted(set(affected_components)),
                    required_verification_surfaces=sorted(set(required_surfaces)),
                    required_tests=sorted(set(required_tests)),
                    required_workflows=sorted(set(required_workflows)),
                    invalidated_evidence=sorted(set(invalidated)),
                    reusable_evidence=sorted(set(reusable)),
                    revalidation_required=sorted(set(revalidation)),
                    sources=sources,
                    is_mapped=is_mapped,
                )
            )
        return impacts

    def _map_workflow_to_surface(self, workflow_id: str) -> str:
        """Map a workflow ID to a verification surface kind."""
        mapping = {
            "quick": VerificationSurfaceKind.UNIT.value,
            "backend": VerificationSurfaceKind.BACKEND.value,
            "frontend": VerificationSurfaceKind.FRONTEND.value,
            "contracts": VerificationSurfaceKind.CONTRACT.value,
            "property": VerificationSurfaceKind.PROPERTY.value,
            "mutation": VerificationSurfaceKind.MUTATION.value,
            "integration": VerificationSurfaceKind.INTEGRATION.value,
            "migration": VerificationSurfaceKind.BACKEND.value,
            "repository": VerificationSurfaceKind.ARCHITECTURE.value,
            "full": VerificationSurfaceKind.ARCHITECTURE.value,
            "runtime": VerificationSurfaceKind.ARCHITECTURE.value,
            "golden": VerificationSurfaceKind.GOLDEN.value,
            "playwright": VerificationSurfaceKind.INTEGRATION.value,
        }
        return mapping.get(workflow_id, VerificationSurfaceKind.UNIT.value)

    def _classify_shared_infrastructure(
        self, impacts: list[CapabilityImpact]
    ) -> list[str]:
        return sorted(
            ci.capability_id
            for ci in impacts
            if ci.impact_kind == ImpactKind.SHARED_INFRASTRUCTURE_AFFECTED.value
        )

    def _classify_test_only(
        self, impacts: list[CapabilityImpact], change_surface: ChangeSurfaceAnalysis
    ) -> list[str]:
        if not change_surface.test_surfaces:
            return []
        if not change_surface.production_surfaces:
            return [ci.capability_id for ci in impacts]
        return []

    def _classify_config_tooling(
        self, impacts: list[CapabilityImpact], change_surface: ChangeSurfaceAnalysis
    ) -> list[str]:
        if not (change_surface.config_surfaces or change_surface.workflow_surfaces):
            return []
        return [ci.capability_id for ci in impacts]

    def _classify_observable_only(
        self, impacts: list[CapabilityImpact], change_surface: ChangeSurfaceAnalysis
    ) -> list[str]:
        if not change_surface.generated_surfaces:
            return []
        if not (change_surface.production_surfaces or change_surface.test_surfaces):
            return [ci.capability_id for ci in impacts]
        return []

    def _build_verification_surfaces(
        self, capability_impacts: list[CapabilityImpact]
    ) -> list[VerificationSurfaceRequirement]:
        """Build verification surface requirements from capability impacts."""
        requirements: list[VerificationSurfaceRequirement] = []
        for ci in capability_impacts:
            contract = self._contract_registry.get_contract(ci.capability_id)
            if not contract:
                # Unmapped capability — no executable command
                requirements.append(
                    VerificationSurfaceRequirement(
                        surface_kind=VerificationSurfaceKind.BACKEND.value,
                        capability_id=ci.capability_id,
                        command="",
                        profile="",
                        is_mandatory=True,
                        is_escalation=False,
                        reason=f"unmapped capability {ci.capability_id} — no executable command available",
                        has_executable_command=False,
                    )
                )
                continue
            for wf in contract.workflow_mappings:
                if not wf.command:
                    continue
                surface_kind = self._map_workflow_to_surface(wf.workflow_id)
                requirements.append(
                    VerificationSurfaceRequirement(
                        surface_kind=surface_kind,
                        capability_id=ci.capability_id,
                        command=wf.command,
                        profile=wf.profile_name or wf.workflow_id,
                        estimated_duration_seconds=wf.estimated_duration_seconds,
                        is_mandatory=bool(wf.is_minimum),
                        is_escalation=not wf.is_minimum,
                        authorization_required=(wf.workflow_id == "mutation"),
                        reason=(
                            f"capability {ci.capability_id} requires {surface_kind} "
                            f"via workflow {wf.workflow_id} (impact: {ci.impact_kind})"
                        ),
                        has_executable_command=True,
                    )
                )
        return requirements

    def _build_evidence_decisions(
        self,
        change_surface: ChangeSurfaceAnalysis,
        resolution: CapabilityResolution,
    ) -> tuple[list[EvidenceInvalidation], list[str], list[str]]:
        """Build evidence invalidation decisions."""
        invalidations: list[EvidenceInvalidation] = []
        reusable: list[str] = []
        revalidation: list[str] = []

        for decision in resolution.evidence_reuse_decisions:
            comp = decision.get("component", "")
            disp = decision.get("disposition", "")
            if "invalidated" in disp:
                invalidations.append(
                    EvidenceInvalidation(
                        evidence_id=comp,
                        capability_id=comp,
                        disposition=EvidenceDisposition.STALE_REVALIDATION_REQUIRED.value,
                        invalidation_rules=list(decision.get("invalidations", [])),
                        reason="; ".join(decision.get("reasons", [])),
                        repository_sha_match=not change_surface.working_tree_dirty,
                        record_path="",
                    )
                )
                if comp not in revalidation:
                    revalidation.append(comp)
            elif "reusable" in disp:
                if comp not in reusable:
                    reusable.append(comp)

        # Add missing evidence entries for directly affected capabilities
        for cap_id in resolution.directly_affected_capabilities:
            contract = self._contract_registry.get_contract(cap_id)
            if contract:
                for mm in contract.measurement_mappings:
                    if mm.required_for_certification:
                        has_evidence = any(
                            e.capability_id == cap_id for e in invalidations
                        )
                        if not has_evidence and not any(cap_id in r for r in reusable):
                            invalidations.append(
                                EvidenceInvalidation(
                                    evidence_id=f"{cap_id}::{mm.measurement_kind.value}",
                                    capability_id=cap_id,
                                    disposition=EvidenceDisposition.MISSING_FRESH_MEASUREMENT_REQUIRED.value,
                                    invalidation_rules=[],
                                    reason=f"no {mm.measurement_kind.value} evidence found for {cap_id}",
                                    repository_sha_match=False,
                                    record_path=mm.authoritative_evidence_path or "",
                                )
                            )
                            revalidation.append(cap_id)

        return invalidations, reusable, revalidation

    def _determine_escalation_conditions(
        self,
        change_surface: ChangeSurfaceAnalysis,
        capability_impacts: list[CapabilityImpact],
        verification_surfaces: list[VerificationSurfaceRequirement],
    ) -> list[EscalationCondition]:
        """Determine escalation conditions."""
        conditions: list[EscalationCondition] = []

        # Unmapped production surfaces
        unmapped_prod = [
            s
            for s in change_surface.production_surfaces
            if s.kind not in (SurfaceKind.GENERATED, SurfaceKind.DOCUMENTATION)
        ]
        unmapped_caps = [ci for ci in capability_impacts if not ci.is_mapped]
        if unmapped_caps:
            conditions.append(
                EscalationCondition(
                    condition_id="ESC-UNMAPPED-CAPABILITY",
                    description="Unmapped capability in blast radius — cannot determine verification requirements",
                    triggered=bool(unmapped_caps),
                    reason=f"{len(unmapped_caps)} unmapped capabilities: {[c.capability_id for c in unmapped_caps]}",
                )
            )

        # Unmapped production surfaces without capability mapping
        if unmapped_prod and not unmapped_caps:
            conditions.append(
                EscalationCondition(
                    condition_id="ESC-UNMAPPED-PRODUCTION-SURFACE",
                    description="Production surface change with no capability mapping",
                    triggered=True,
                    reason=f"{len(unmapped_prod)} production surfaces not mapped to any capability",
                )
            )

        # Shared infrastructure change
        if change_surface.shared_module_surfaces:
            conditions.append(
                EscalationCondition(
                    condition_id="ESC-SHARED-INFRASTRUCTURE",
                    description="Shared infrastructure change — conservative expansion required",
                    triggered=True,
                    reason=f"{len(change_surface.shared_module_surfaces)} shared modules changed",
                )
            )

        # Runtime infrastructure change
        if change_surface.runtime_infrastructure_surfaces:
            conditions.append(
                EscalationCondition(
                    condition_id="ESC-RUNTIME-INFRASTRUCTURE",
                    description="Runtime/verification infrastructure change — framework verification required",
                    triggered=True,
                    reason=f"{len(change_surface.runtime_infrastructure_surfaces)} runtime infrastructure files changed",
                )
            )

        # Required verification surface with no executable command
        no_cmd = [v for v in verification_surfaces if not v.has_executable_command]
        if no_cmd:
            conditions.append(
                EscalationCondition(
                    condition_id="ESC-NO-EXECUTABLE-COMMAND",
                    description="Required verification surface has no executable command",
                    triggered=True,
                    reason=f"{len(no_cmd)} verification surfaces without commands: {[v.capability_id for v in no_cmd]}",
                )
            )

        # Stale evidence (checked via evidence_invalidations below)

        return conditions

    def _determine_fail_closed(
        self,
        change_surface: ChangeSurfaceAnalysis,
        capability_impacts: list[CapabilityImpact],
        verification_surfaces: list[VerificationSurfaceRequirement],
        resolution: CapabilityResolution | None = None,
    ) -> tuple[bool, list[str]]:
        """Determine if the contract should fail closed.

        Fail-closed conditions (per C50 spec):
        1. Production surface cannot be mapped → check if C48 resolver
           found any capability for it
        2. Required verification surface has no executable command
        """
        reasons: list[str] = []

        # Build set of paths that the C48 resolver successfully mapped
        mapped_paths: set[str] = set()
        if resolution is not None:
            for cc in resolution.classified_changes:
                if (
                    cc.directly_affected_capabilities
                    or cc.transitively_affected_capabilities
                ):
                    mapped_paths.add(cc.path)
            # Also consider transitively affected via shared dependency
            for cap_id in resolution.transitively_affected_capabilities:
                for si in change_surface.surfaces:
                    if self._shared_index is not None:
                        if cap_id in self._shared_index.capabilities_for_module(
                            si.path
                        ):
                            mapped_paths.add(si.path)
                    elif si.is_shared_infrastructure:
                        mapped_paths.add(si.path)

        # 1. Production surface cannot be mapped
        unmapped_caps = {
            ci.capability_id for ci in capability_impacts if not ci.is_mapped
        }
        for s in change_surface.production_surfaces:
            if s.kind in (
                SurfaceKind.GENERATED,
                SurfaceKind.DOCUMENTATION,
                SurfaceKind.TEST,
            ):
                continue
            # If the C48 resolver mapped this path, it's not unmapped
            if s.path in mapped_paths:
                continue
            # If any capability impact has a source referencing this path, it's mapped
            if any(s.path in src for ci in capability_impacts for src in ci.sources):
                continue
            # If we have capability impacts from the resolver, the surface is mapped
            # through the resolver's classified_changes
            if resolution and resolution.classified_changes:
                for cc in resolution.classified_changes:
                    if cc.path == s.path and (
                        cc.directly_affected_capabilities
                        or cc.transitively_affected_capabilities
                    ):
                        mapped_paths.add(s.path)
                        break
            if s.path in mapped_paths:
                continue
            # If there are unmapped capabilities from the resolver, the surface
            # is genuinely unmapped
            if unmapped_caps:
                reasons.append(
                    f"unmapped production surface: {s.path} " f"(kind={s.kind.value})"
                )
            elif not capability_impacts:
                # No capabilities resolved at all → surface is unmapped
                reasons.append(
                    f"unmapped production surface: {s.path} " f"(kind={s.kind.value})"
                )

        # 2. Required verification surface has no executable command
        no_cmd = [v for v in verification_surfaces if not v.has_executable_command]
        if no_cmd:
            for v in no_cmd:
                reasons.append(
                    f"required verification surface has no executable command: "
                    f"{v.capability_id} ({v.surface_kind})"
                )

        return bool(reasons), reasons

    def _collect_affected_components(
        self, capability_impacts: list[CapabilityImpact]
    ) -> list[str]:
        comps: set[str] = set()
        for ci in capability_impacts:
            comps.update(ci.affected_components)
        return sorted(comps)

    def _collect_shared_expansions(
        self, surface_impacts: list[SurfaceImpact], resolution: CapabilityResolution
    ) -> list[dict]:
        expansions: list[dict] = []
        for si in surface_impacts:
            if si.shared_dependency_expansion:
                expansions.append(
                    {
                        "path": si.path,
                        "kind": si.kind,
                        "transitively_affected_capabilities": si.shared_dependency_expansion,
                        "reason": si.reason,
                    }
                )
        return expansions

    def _collect_required_tests(
        self, capability_impacts: list[CapabilityImpact]
    ) -> list[str]:
        tests: set[str] = set()
        for ci in capability_impacts:
            tests.update(ci.required_tests)
        return sorted(tests)

    def _collect_affected_workflows(
        self, verification_surfaces: list[VerificationSurfaceRequirement]
    ) -> list[str]:
        workflows: set[str] = set()
        for v in verification_surfaces:
            if v.profile:
                workflows.add(v.profile)
        return sorted(workflows)

    def compute_e2e_impact(
        self, changed_files: list[Path]
    ) -> dict[str, Any]:
        """Compute E2E test impact from changed frontend route files.

        Detects when frontend route files (app/**/page.tsx, layout.tsx)
        change and uses E2ERouteMapper to find affected E2E tests.

        Args:
            changed_files: List of changed file paths.

        Returns:
            Dict with affected_routes, affected_e2e_tests, has_e2e_impact.
        """
        from .e2e_route_mapper import E2ERouteMapper

        mapper = E2ERouteMapper()
        all_routes = mapper.scan_frontend_routes()

        # Filter to frontend route files that actually changed
        affected_routes: set[str] = set()
        for f in changed_files:
            fstr = str(f)
            # Match frontend/app/**/page.tsx or layout.tsx patterns
            if "frontend/app/" in fstr and fstr.endswith((".tsx",)):
                # Extract route from path
                rel = fstr.replace("frontend/app/", "").replace("/page.tsx", "").replace("/layout.tsx", "")
                route = "/" + rel if rel else "/"
                route = route.rstrip("/") or "/"
                affected_routes.add(route)

        if not affected_routes:
            return {
                "affected_routes": [],
                "affected_e2e_tests": [],
                "has_e2e_impact": False,
                "route_count": 0,
                "test_count": 0,
            }

        # Find all E2E tests that exercise affected routes
        affected_tests: set[str] = set()
        for route in affected_routes:
            tests = mapper.get_tests_for_route(route)
            affected_tests.update(tests)

        # Also check parent routes
        for route in list(affected_routes):
            parts = route.strip("/").split("/")
            for i in range(len(parts)):
                parent = "/" + "/".join(parts[:i + 1]) if i > 0 else "/"
                tests = mapper.get_tests_for_route(parent)
                affected_tests.update(tests)

        return {
            "affected_routes": sorted(affected_routes),
            "affected_e2e_tests": sorted(affected_tests),
            "has_e2e_impact": len(affected_tests) > 0,
            "route_count": len(affected_routes),
            "test_count": len(affected_tests),
        }


# ---------------------------------------------------------------------------
# Convenience functions
# ---------------------------------------------------------------------------


def compute_blast_radius(
    explicit_files: list[str] | None = None,
    base: str | None = None,
    head: str | None = None,
) -> BlastRadiusContract:
    """Compute the canonical blast-radius contract."""
    engine = BlastRadiusEngine()
    return engine.compute(explicit_files, base, head)


def format_blast_radius(contract: BlastRadiusContract) -> str:
    """Format a blast-radius contract for human display."""
    lines = []
    lines.append("=" * 72)
    lines.append("  M9-C50 — BLAST-RADIUS CONTRACT")
    lines.append("=" * 72)
    lines.append(f"  Contract ID:     {contract.contract_id}")
    lines.append(f"  Generated:       {contract.generated_at}")
    lines.append(f"  Repository SHA:  {contract.repository_sha[:12]}")
    lines.append(f"  Discovery:       {contract.discovery_source}")
    lines.append(
        f"  Working tree:    {'dirty' if contract.working_tree_dirty else 'clean'}"
    )
    lines.append("-" * 72)

    lines.append(f"  Changed files:   {len(contract.change_surface.changed_files)}")
    lines.append(
        f"  Production:      {len(contract.change_surface.production_surfaces)}"
    )
    lines.append(f"  Test:            {len(contract.change_surface.test_surfaces)}")
    lines.append(f"  Config:          {len(contract.change_surface.config_surfaces)}")
    lines.append(f"  Workflow:        {len(contract.change_surface.workflow_surfaces)}")
    lines.append(
        f"  Runtime infra:   {len(contract.change_surface.runtime_infrastructure_surfaces)}"
    )
    lines.append(
        f"  Shared modules:  {len(contract.change_surface.shared_module_surfaces)}"
    )
    lines.append(
        f"  Generated:       {len(contract.change_surface.generated_surfaces)}"
    )
    lines.append(f"  Unknown:         {len(contract.change_surface.unknown_surfaces)}")
    lines.append("-" * 72)

    lines.append("  CAPABILITY IMPACT:")
    lines.append(
        f"    Directly affected:      {len(contract.directly_affected_capabilities)}"
    )
    for c in contract.directly_affected_capabilities:
        lines.append(f"      → {c}")
    lines.append(
        f"    Transitively affected:  {len(contract.transitively_affected_capabilities)}"
    )
    for c in contract.transitively_affected_capabilities:
        lines.append(f"      ~ {c}")
    lines.append(
        f"    Shared infra affected:  {len(contract.shared_infrastructure_affected_capabilities)}"
    )
    for c in contract.shared_infrastructure_affected_capabilities:
        lines.append(f"      ≈ {c}")
    lines.append(f"    Unmapped:               {len(contract.unmapped_capabilities)}")
    for c in contract.unmapped_capabilities:
        lines.append(f"      ? {c}")
    lines.append("-" * 72)

    lines.append(f"  Affected components: {len(contract.affected_components)}")
    for c in contract.affected_components:
        lines.append(f"    • {c}")
    lines.append("-" * 72)

    lines.append(
        f"  Verification surfaces: {len(contract.verification_surface_requirements)}"
    )
    for v in contract.verification_surface_requirements:
        status = "MANDATORY" if v.is_mandatory else "ESCALATION"
        auth = " [AUTH REQUIRED]" if v.authorization_required else ""
        cmd = v.command if v.has_executable_command else "(no command)"
        lines.append(f"    [{status}] {v.surface_kind} for {v.capability_id}{auth}")
        lines.append(f"        command: {cmd}")
    lines.append("-" * 72)

    lines.append("  EVIDENCE:")
    lines.append(f"    Invalidated: {len(contract.evidence_invalidations)}")
    for e in contract.evidence_invalidations:
        lines.append(f"      ✗ {e.evidence_id} ({e.disposition})")
        lines.append(f"        reason: {e.reason}")
    lines.append(f"    Reusable:    {len(contract.reusable_evidence)}")
    for r in contract.reusable_evidence:
        lines.append(f"      ✓ {r}")
    lines.append(f"    Revalidation required: {len(contract.revalidation_required)}")
    for r in contract.revalidation_required:
        lines.append(f"      ↻ {r}")
    lines.append("-" * 72)

    if contract.escalation_conditions:
        lines.append("  ESCALATION CONDITIONS:")
        for ec in contract.escalation_conditions:
            marker = "⚠" if ec.triggered else "○"
            lines.append(f"    {marker} [{ec.condition_id}] {ec.description}")
            lines.append(f"        reason: {ec.reason}")
        lines.append("-" * 72)

    lines.append(f"  FAIL-CLOSED: {contract.is_fail_closed}")
    if contract.is_fail_closed:
        for r in contract.fail_closed_reasons:
            lines.append(f"    ✗ {r}")
    else:
        lines.append("    No fail-closed conditions triggered")
    lines.append("=" * 72)
    return "\n".join(lines)
