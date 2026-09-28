"""
M9-C48 — Capability Operational Contract.

Extends the existing VerificationCapability architecture so every registered
capability can answer, machine-readably:

* What is this capability?
* Which implementation surfaces realize it?
* Which repository paths affect it?
* What other capabilities can be affected by its change?
* Which tests verify it?
* Which verification profile verifies it?
* Which workflow(s) exercise it?
* Which measurement(s) are required?
* Which evidence is authoritative?
* Which evidence can be reused?
* What invalidates that evidence?
* What is the minimum verification command?
* What stronger verification is required when the minimum fails?
* What mutation/survivor evidence exists?
* What strengthening mechanism applies?
* What certification conditions apply?
* What is currently missing?

This module is additive — it extends the existing C42 registry/profile/planner/
evidence architecture without introducing a second capability registry.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any, Literal, cast

from runtime.foundation.verification.measurement_truth import (
    EvidenceClassification,
    MeasurementKind,
)
from runtime.foundation.verification.models import (
    VerificationCategory,
    VerificationScope,
)

# ---------------------------------------------------------------------------
# Capability Operational Contract Enums
# ---------------------------------------------------------------------------


class CapabilityMaturity(str, Enum):
    """Maturity level of capability verification."""

    EXPERIMENTAL = "experimental"  # No systematic verification
    DESCRIPTIVE = "descriptive"  # Metadata only, no executable verification
    OPERATIONAL = "operational"  # Minimum verification executable
    MEASURED = "measured"  # Measurement truth integrated
    CERTIFIED = "certified"  # Certification conditions satisfied


class EvidenceReusability(str, Enum):
    """Reusability classification for capability evidence."""

    ALWAYS_REUSABLE = "always_reusable"  # Evidence never invalidates
    REUSABLE_UNTIL_SOURCE_CHANGE = "reusable_until_source_change"
    REUSABLE_UNTIL_CONFIG_CHANGE = "reusable_until_config_change"
    REUSABLE_WITH_REVALIDATION = "reusable_with_revalidation"
    NEVER_REUSABLE = "never_reusable"  # Must re-measure every time


class VerificationEscalation(str, Enum):
    """Escalation levels when minimum verification fails."""

    NONE = "none"  # Minimum verification is sufficient
    TARGETED_MUTATION = "targeted_mutation"  # Run targeted mutation on capability
    EXTENDED_PROPERTY = "extended_property"  # Run extended property tests
    CONTRACT_STRENGTHENING = "contract_strengthening"  # Strengthen contract tests
    FULL_CAPABILITY_SUITE = "full_capability_suite"  # All workflows for capability
    CROSS_CAPABILITY = "cross_capability"  # Include dependent capabilities
    REPOSITORY_WIDE = "repository_wide"  # Full repository mutation campaign


class CapabilityMissing(str, Enum):
    """What is missing for this capability."""

    NOTHING = "nothing"
    NO_EXECUTABLE_VERIFICATION = "no_executable_verification"
    NO_MEASUREMENT_TRUTH = "no_measurement_truth"
    NO_SURVIVOR_INTEL = "no_survivor_intel"
    NO_STRENGTHENING_PIPELINE = "no_strengthening_pipeline"
    NO_CERTIFICATION_CRITERIA = "no_certification_criteria"
    INCOMPLETE_TEST_MAPPING = "incomplete_test_mapping"
    INCOMPLETE_EVIDENCE_MAPPING = "incomplete_evidence_mapping"
    INCOMPLETE_INVALDATION_MAPPING = "incomplete_invalidation_mapping"


# ---------------------------------------------------------------------------
# Extended Capability Contract
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class ImplementationSurface:
    """An implementation surface that realizes a capability."""

    id: str
    path: str  # repo-relative path
    kind: Literal["engine", "service", "router", "model", "core", "common", "frontend"]
    fingerprint: str = ""  # sha256 of file contents
    description: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class TestMapping:
    """Maps a capability to its verifying tests."""

    test_path: str  # repo-relative path to test file/directory
    test_kind: Literal[
        "unit",
        "property",
        "invariant",
        "contract",
        "integration",
        "golden",
        "e2e",
        "mutation",
    ]
    capability_id: str
    covers_functions: list[str] = field(default_factory=list)
    description: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class WorkflowMapping:
    """Maps a capability to its verification workflows."""

    workflow_id: str  # registry workflow ID
    profile_name: str  # verify.py profile name
    command: str
    estimated_duration_seconds: int
    scopes: list[VerificationScope]
    is_minimum: bool = False  # True if this is the minimum sufficient verification
    escalation_order: int = (
        0  # Order of escalation (0 = minimum, 1 = first escalation, etc.)
    )

    def to_dict(self) -> dict:
        return {
            **asdict(self),
            "scopes": [s.value for s in self.scopes],
        }


@dataclass(frozen=True, slots=True)
class MeasurementMapping:
    """Maps a capability to its required measurements."""

    measurement_kind: MeasurementKind
    scope: str  # e.g., "credit_card_engine" or "full"
    required_for_certification: bool = False
    authoritative_evidence_path: str = ""
    reusable_evidence_path: str = ""
    completion_requirements: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            **asdict(self),
            "measurement_kind": self.measurement_kind.value,
        }


@dataclass(frozen=True, slots=True)
class EvidenceMapping:
    """Maps a capability to its evidence."""

    evidence_id: str
    evidence_kind: Literal[
        "unit_pass",
        "property_pass",
        "invariant_pass",
        "contract_pass",
        "integration_pass",
        "golden_pass",
        "e2e_pass",
        "mutation_score",
        "coverage",
        "derived_aggregate",
    ]
    component_id: str
    measurement_record: str | None = None  # Path to MeasurementTruthRecord
    classification: EvidenceClassification = EvidenceClassification.DERIVED
    fingerprint: str = ""
    is_authoritative: bool = False
    reusable: bool = False
    invalidation_triggers: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            **asdict(self),
            "evidence_kind": self.evidence_kind,
            "classification": self.classification.value,
        }


@dataclass(frozen=True, slots=True)
class InvalidationMapping:
    """What invalidates capability evidence."""

    rule_id: str
    description: str
    scope: Literal["component", "capability", "task", "evidence", "population"]
    triggers_on: Literal[
        "source_change",
        "test_change",
        "config_change",
        "toolchain_change",
        "dependency_change",
        "environment_change",
        "capability_mapping_change",
        "evidence_schema_change",
        "infra_change",
        "population_change",
    ]
    affected_evidence: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class StrengtheningMechanism:
    """How to strengthen capability verification when minimum fails."""

    mechanism_id: str
    name: str
    description: str
    trigger_condition: Literal[
        "mutation_survivor",
        "coverage_decrease",
        "contract_failure",
        "property_failure",
        "test_failure",
        "manual_request",
    ]
    applies_to: list[str]  # capability IDs or "all"
    steps: list[str] = field(default_factory=list)
    requires_human_authorization: bool = False
    produces_evidence: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class CertificationCondition:
    """Certification conditions for a capability."""

    condition_id: str
    description: str
    required_evidence: list[str]  # evidence IDs
    required_measurements: list[MeasurementKind]
    minimum_mutation_score: float | None = None
    minimum_coverage_percent: float | None = None
    requires_authoritative_classification: bool = True
    requires_no_survivors: bool = False
    requires_no_coverage_gaps: bool = False

    def to_dict(self) -> dict:
        return {
            **asdict(self),
            "required_measurements": [m.value for m in self.required_measurements],
        }


@dataclass
class OperationalCapability:
    """
    The complete operational contract for a capability.

    Extends VerificationCapability with machine-readable operational fields.
    """

    # Core identity (from VerificationCapability)
    id: str
    name: str
    description: str
    category: VerificationCategory

    # Operational contract
    maturity: CapabilityMaturity = CapabilityMaturity.DESCRIPTIVE
    implementation_surfaces: list[ImplementationSurface] = field(default_factory=list)
    affected_by_paths: list[str] = field(default_factory=list)  # repo-relative paths
    transitive_capabilities: list[str] = field(
        default_factory=list
    )  # capability IDs affected by this one's change

    # Verification mappings
    test_mappings: list[TestMapping] = field(default_factory=list)
    workflow_mappings: list[WorkflowMapping] = field(default_factory=list)
    measurement_mappings: list[MeasurementMapping] = field(default_factory=list)

    # Evidence & invalidation
    evidence_mappings: list[EvidenceMapping] = field(default_factory=list)
    invalidation_mappings: list[InvalidationMapping] = field(default_factory=list)

    # Strengthening & certification
    strengthening_mechanisms: list[StrengtheningMechanism] = field(default_factory=list)
    certification_conditions: list[CertificationCondition] = field(default_factory=list)

    # Gaps
    missing: list[CapabilityMissing] = field(default_factory=list)

    # Verification commands
    minimum_verification_command: str = ""
    minimum_verification_profile: str = ""
    escalation_verification_commands: list[str] = field(default_factory=list)
    escalation_verification_profiles: list[str] = field(default_factory=list)

    # Metadata
    metadata: dict[str, Any] = field(default_factory=dict)
    generated_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "category": self.category.value,
            "maturity": self.maturity.value,
            "implementation_surfaces": [
                s.to_dict() for s in self.implementation_surfaces
            ],
            "affected_by_paths": self.affected_by_paths,
            "transitive_capabilities": self.transitive_capabilities,
            "test_mappings": [t.to_dict() for t in self.test_mappings],
            "workflow_mappings": [w.to_dict() for w in self.workflow_mappings],
            "measurement_mappings": [m.to_dict() for m in self.measurement_mappings],
            "evidence_mappings": [e.to_dict() for e in self.evidence_mappings],
            "invalidation_mappings": [i.to_dict() for i in self.invalidation_mappings],
            "strengthening_mechanisms": [
                s.to_dict() for s in self.strengthening_mechanisms
            ],
            "certification_conditions": [
                c.to_dict() for c in self.certification_conditions
            ],
            "missing": [m.value for m in self.missing],
            "minimum_verification_command": self.minimum_verification_command,
            "minimum_verification_profile": self.minimum_verification_profile,
            "escalation_verification_commands": self.escalation_verification_commands,
            "escalation_verification_profiles": self.escalation_verification_profiles,
            "metadata": self.metadata,
            "generated_at": self.generated_at,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, default=str)


# ---------------------------------------------------------------------------
# Capability Contract Registry
# ---------------------------------------------------------------------------


class CapabilityContractRegistry:
    """
    Registry for OperationalCapability contracts.

    Loads from verification.yaml and builds operational contracts by enriching
    the existing VerificationCapability registry with machine-readable fields.
    """

    def __init__(self, config_path: Path | None = None):
        from runtime.foundation.verification.registry import get_registry

        self._registry = get_registry(config_path)
        self._contracts: dict[str, OperationalCapability] = {}
        self._loaded = False

    def load(self) -> None:
        """Load and build operational capability contracts."""
        if self._loaded:
            return

        self._registry.load()

        # Build operational contracts from registered capabilities
        for cap in self._registry.get_all_capabilities():
            self._contracts[cap.id] = self._build_operational_contract(cap)

        self._loaded = True

    def _build_operational_contract(self, cap) -> OperationalCapability:
        """Build an OperationalCapability from a VerificationCapability."""
        # Determine maturity
        maturity = self._determine_maturity(cap)

        # Build implementation surfaces from modules
        impl_surfaces = self._build_implementation_surfaces(cap)

        # Build test mappings from requirements
        test_mappings = self._build_test_mappings(cap)

        # Build workflow mappings from workflows/scripts
        workflow_mappings = self._build_workflow_mappings(cap)

        # Build measurement mappings
        measurement_mappings = self._build_measurement_mappings(cap)

        # Build evidence mappings
        evidence_mappings = self._build_evidence_mappings(cap)

        # Build invalidation mappings
        invalidation_mappings = self._build_invalidation_mappings(cap)

        # Build strengthening mechanisms
        strengthening_mechanisms = self._build_strengthening_mechanisms(cap)

        # Build certification conditions
        certification_conditions = self._build_certification_conditions(cap)

        # Determine missing elements
        missing = self._determine_missing(
            cap,
            maturity,
            test_mappings,
            measurement_mappings,
            evidence_mappings,
            invalidation_mappings,
            strengthening_mechanisms,
            certification_conditions,
        )

        # Determine minimum verification command/profile
        min_cmd, min_profile = self._determine_minimum_verification(
            cap, workflow_mappings
        )

        # Determine escalation commands/profiles
        esc_cmds, esc_profiles = self._determine_escalation_verification(
            cap, workflow_mappings
        )

        return OperationalCapability(
            id=cap.id,
            name=cap.name,
            description=cap.description,
            category=cap.category,
            maturity=maturity,
            implementation_surfaces=impl_surfaces,
            affected_by_paths=cap.modules,
            transitive_capabilities=self._compute_transitive_capabilities(cap),
            test_mappings=test_mappings,
            workflow_mappings=workflow_mappings,
            measurement_mappings=measurement_mappings,
            evidence_mappings=evidence_mappings,
            invalidation_mappings=invalidation_mappings,
            strengthening_mechanisms=strengthening_mechanisms,
            certification_conditions=certification_conditions,
            missing=missing,
            minimum_verification_command=min_cmd,
            minimum_verification_profile=min_profile,
            escalation_verification_commands=esc_cmds,
            escalation_verification_profiles=esc_profiles,
            metadata=cap.metadata,
        )

    def _determine_maturity(self, cap) -> CapabilityMaturity:
        """Determine capability maturity based on what's implemented."""
        has_workflows = len(cap.workflows) > 0
        has_scripts = len(cap.scripts) > 0
        has_requirements = len(cap.requirements) > 0

        if not has_workflows and not has_scripts and not has_requirements:
            return CapabilityMaturity.DESCRIPTIVE

        if has_workflows or has_scripts:
            # Check if measurement truth is integrated
            has_mutation = any(w == "mutation" for w in cap.workflows)
            has_property = any(w == "property" for w in cap.workflows)

            if has_mutation and has_property:
                return CapabilityMaturity.MEASURED
            return CapabilityMaturity.OPERATIONAL

        return CapabilityMaturity.EXPERIMENTAL

    def _build_implementation_surfaces(self, cap) -> list[ImplementationSurface]:
        """Build implementation surfaces from capability modules."""
        surfaces = []
        for module in cap.modules:
            if not module:
                continue
            kind = "engine"
            if "service" in module:
                kind = "service"
            elif "router" in module:
                kind = "router"
            elif "model" in module:
                kind = "model"
            elif "common" in module:
                kind = "common"
            elif module.startswith("frontend/"):
                kind = "frontend"
            elif module == "runtime":
                kind = "core"

            surfaces.append(
                ImplementationSurface(
                    id=f"surf::{module}",
                    path=module,
                    kind=cast(
                        Literal[
                            "engine",
                            "service",
                            "router",
                            "model",
                            "core",
                            "common",
                            "frontend",
                        ],
                        kind,
                    ),
                    description=f"{cap.name} implementation surface",
                )
            )
        return surfaces

    def _build_test_mappings(self, cap) -> list[TestMapping]:
        """Build test mappings from capability requirements."""
        mappings = []
        for req in cap.requirements:
            # Determine test kind from category
            test_kind_map = {
                VerificationCategory.CONTRACT: "contract",
                VerificationCategory.CONTRACT_FRONTEND: "contract",
                VerificationCategory.CONTRACT_BACKEND: "contract",
                VerificationCategory.PROPERTY: "property",
                VerificationCategory.INVARIANT: "invariant",
                VerificationCategory.CAPABILITY: "unit",
                VerificationCategory.INTEGRATION: "integration",
                VerificationCategory.MIGRATION: "unit",
                VerificationCategory.ARCHITECTURAL: "unit",
                VerificationCategory.MUTATION: "mutation",
            }
            test_kind = test_kind_map.get(req.category, "unit")

            # Estimate test path from module
            test_path = ""
            if req.module:
                if req.module.startswith("backend/src/"):
                    test_path = req.module.replace(
                        "backend/src/", "backend/tests/unit/"
                    )
                elif req.module.startswith("frontend/"):
                    test_path = req.module.replace("frontend/", "frontend/tests/")

            mappings.append(
                TestMapping(
                    test_path=test_path,
                    test_kind=cast(
                        Literal[
                            "unit",
                            "property",
                            "invariant",
                            "contract",
                            "integration",
                            "golden",
                            "e2e",
                            "mutation",
                        ],
                        test_kind,
                    ),
                    capability_id=req.capability or cap.id,
                    description=f"{req.category.value} tests for {req.capability or cap.id}",
                )
            )
        return mappings

    def _build_workflow_mappings(self, cap) -> list[WorkflowMapping]:
        """Build workflow mappings from capability workflows/scripts."""
        mappings = []
        for wf_id in cap.workflows:
            wf = self._registry.get_workflow(wf_id)
            if not wf:
                continue

            is_minimum = wf_id in ("quick", "backend") and cap.id in [
                "loan-engine",
                "reconciliation",
                "ledger",
            ]
            escalation_order = 0 if is_minimum else 1

            mappings.append(
                WorkflowMapping(
                    workflow_id=wf.id,
                    profile_name=wf.id,
                    command=wf.command or "",
                    estimated_duration_seconds=wf.estimated_duration_seconds,
                    scopes=wf.scopes,
                    is_minimum=is_minimum,
                    escalation_order=escalation_order,
                )
            )

        # Add scripts as fallback
        for script_id in cap.scripts:
            script = self._registry.get_script(script_id)
            if not script:
                continue

            # Check if already covered by workflow
            if any(m.workflow_id == script_id for m in mappings):
                continue

            mappings.append(
                WorkflowMapping(
                    workflow_id=script.id,
                    profile_name=script.id,
                    command=f"bash {script.path}",
                    estimated_duration_seconds=script.estimated_duration_seconds,
                    scopes=[script.scope],
                    is_minimum=False,
                    escalation_order=2,
                )
            )

        return mappings

    def _build_measurement_mappings(self, cap) -> list[MeasurementMapping]:
        """Build measurement mappings from capability."""
        mappings = []

        # Mutation measurement for financial engines
        if cap.id in [
            "loan-engine",
            "reconciliation",
            "ledger",
            "credit_card",
            "account_engine",
        ]:
            mappings.append(
                MeasurementMapping(
                    measurement_kind=MeasurementKind.MUTATION,
                    scope=(
                        f"{cap.id}_engine" if not cap.id.endswith("_engine") else cap.id
                    ),
                    required_for_certification=True,
                    authoritative_evidence_path=f"backend/tests/generated/mutation/measurement-truth-{cap.id}.json",
                    reusable_evidence_path="backend/tests/generated/mutation/mutation-survivor-intel.json",
                    completion_requirements={
                        "minimum_score": 80,
                        "completion": "AUTHORITATIVE_COMPLETE",
                    },
                )
            )

        # Coverage measurement
        if cap.modules:
            mappings.append(
                MeasurementMapping(
                    measurement_kind=MeasurementKind.COVERAGE,
                    scope=cap.modules[0] if cap.modules else "full",
                    required_for_certification=False,
                    authoritative_evidence_path="runtime/generated/m9-c47/coverage/measurement-truth-coverage.json",
                    completion_requirements={"minimum_line_percent": 40},
                )
            )

        return mappings

    def _build_evidence_mappings(self, cap) -> list[EvidenceMapping]:
        """Build evidence mappings from capability."""
        mappings = []
        for req in cap.requirements:
            mappings.append(
                EvidenceMapping(
                    evidence_id=f"ev::{req.category.value}::{req.capability or cap.id}",
                    evidence_kind=req.category.value.lower().replace("_", "_"),
                    component_id=req.module or cap.id,
                    classification=EvidenceClassification.DERIVED,
                    is_authoritative=False,
                    reusable=True,
                    invalidation_triggers=["source_change", "config_change"],
                )
            )
        return mappings

    def _build_invalidation_mappings(self, cap) -> list[InvalidationMapping]:
        """Build invalidation mappings from capability."""
        from runtime.foundation.verification.evidence_reuse import INVALIDATION_RULES

        # Map InvalidationRule.scope (C42.27 vocabulary) to the contract's
        # finer-grained scope vocabulary.
        scope_map = {
            "INVALIDATES_POPULATION": "population",
            "INVALIDATES_CAPABILITY": "capability",
            "INVALIDATES_COMPONENT": "component",
            "INVALIDATES_TASK": "task",
            "INVALIDATES_EVIDENCE_ONLY": "evidence",
            "DOES_NOT_INVALIDATE": "evidence",
        }
        trigger_map = {
            "source": "source_change",
            "test": "test_change",
            "config": "config_change",
            "toolchain": "toolchain_change",
            "dependency": "dependency_change",
            "population": "population_change",
            "capability_mapping": "capability_mapping_change",
            "evidence_schema": "evidence_schema_change",
            "environment": "environment_change",
            "infrastructure": "infra_change",
        }

        mappings = []
        for rule in INVALIDATION_RULES:
            mappings.append(
                InvalidationMapping(
                    rule_id=rule.rule_id,
                    description=rule.description,
                    scope=cast(
                        Literal[
                            "component", "capability", "task", "evidence", "population"
                        ],
                        scope_map.get(rule.scope, "evidence"),
                    ),
                    triggers_on=cast(
                        Literal[
                            "source_change",
                            "test_change",
                            "config_change",
                            "toolchain_change",
                            "dependency_change",
                            "environment_change",
                            "capability_mapping_change",
                            "evidence_schema_change",
                            "infra_change",
                            "population_change",
                        ],
                        trigger_map.get(rule.category, "source_change"),
                    ),
                    affected_evidence=[],
                )
            )
        return mappings

    def _build_strengthening_mechanisms(self, cap) -> list[StrengtheningMechanism]:
        """Build strengthening mechanisms for capability."""
        mechanisms = []

        # Mutation survivor strengthening
        if cap.id in [
            "loan-engine",
            "reconciliation",
            "ledger",
            "credit_card",
            "account_engine",
        ]:
            mechanisms.append(
                StrengtheningMechanism(
                    mechanism_id=f"strengthen::{cap.id}::mutation",
                    name=f"Mutation Survivor Strengthening for {cap.name}",
                    description="Strengthen existing tests to kill surviving mutants",
                    trigger_condition="mutation_survivor",
                    applies_to=[cap.id],
                    steps=[
                        "Load durable survivor-intel record",
                        "Identify Class A/B survivors with covering tests",
                        "Propose behavioral assertions for missing distinguishing behavior",
                        "Validate proposed strengthening against mutant",
                        "Record strengthening decision",
                    ],
                    requires_human_authorization=True,
                    produces_evidence=["strengthened_test", "mutation_revalidation"],
                )
            )

        # Coverage decrease strengthening
        mechanisms.append(
            StrengtheningMechanism(
                mechanism_id=f"strengthen::{cap.id}::coverage",
                name=f"Coverage Regression Strengthening for {cap.name}",
                description="Add tests for uncovered branches/lines",
                trigger_condition="coverage_decrease",
                applies_to=[cap.id],
                steps=[
                    "Identify uncovered branches/lines from coverage measurement",
                    "Determine behavioral importance of uncovered code",
                    "Propose targeted test additions",
                    "Validate coverage improvement",
                    "Record strengthening decision",
                ],
                requires_human_authorization=False,
                produces_evidence=["coverage_improvement", "new_tests"],
            )
        )

        return mechanisms

    def _build_certification_conditions(self, cap) -> list[CertificationCondition]:
        """Build certification conditions for capability."""
        conditions = []

        if cap.id in [
            "loan-engine",
            "reconciliation",
            "ledger",
            "credit_card",
            "account_engine",
        ]:
            conditions.append(
                CertificationCondition(
                    condition_id=f"cert::{cap.id}::mutation",
                    description=f"Mutation score >= 80% with authoritative classification for {cap.name}",
                    required_evidence=[f"ev::mutation::{cap.id}"],
                    required_measurements=[MeasurementKind.MUTATION],
                    minimum_mutation_score=80.0,
                    requires_authoritative_classification=True,
                    requires_no_survivors=False,
                )
            )

        return conditions

    def _determine_missing(
        self,
        cap,
        maturity: CapabilityMaturity,
        test_mappings: list[TestMapping],
        measurement_mappings: list[MeasurementMapping],
        evidence_mappings: list[EvidenceMapping],
        invalidation_mappings: list[InvalidationMapping],
        strengthening_mechanisms: list[StrengtheningMechanism],
        certification_conditions: list[CertificationCondition],
    ) -> list[CapabilityMissing]:
        """Determine what's missing for this capability."""
        missing = []

        if maturity == CapabilityMaturity.DESCRIPTIVE:
            missing.append(CapabilityMissing.NO_EXECUTABLE_VERIFICATION)

        if not any(
            m.measurement_kind == MeasurementKind.MUTATION for m in measurement_mappings
        ):
            missing.append(CapabilityMissing.NO_MEASUREMENT_TRUTH)

        if cap.id in [
            "loan-engine",
            "reconciliation",
            "ledger",
            "credit_card",
            "account_engine",
        ]:
            # Check for survivor intel
            survivor_intel_path = Path(
                "backend/tests/generated/mutation/mutation-survivor-intel.json"
            )
            if not survivor_intel_path.exists():
                missing.append(CapabilityMissing.NO_SURVIVOR_INTEL)

        if not strengthening_mechanisms:
            missing.append(CapabilityMissing.NO_STRENGTHENING_PIPELINE)

        if not certification_conditions:
            missing.append(CapabilityMissing.NO_CERTIFICATION_CRITERIA)

        if not test_mappings:
            missing.append(CapabilityMissing.INCOMPLETE_TEST_MAPPING)

        if not evidence_mappings:
            missing.append(CapabilityMissing.INCOMPLETE_EVIDENCE_MAPPING)

        if not invalidation_mappings:
            missing.append(CapabilityMissing.INCOMPLETE_INVALDATION_MAPPING)

        if not missing:
            missing.append(CapabilityMissing.NOTHING)

        return missing

    def _compute_transitive_capabilities(self, cap) -> list[str]:
        """Compute capabilities affected by changes to this capability."""
        # For now, use the ENGINE_TO_CAPABILITY mapping to find cross-capability impacts
        from runtime.foundation.verification.evidence_reuse import ENGINE_TO_CAPABILITY
        from runtime.foundation.verification.survivor_intel import MULTI_CAPABILITY

        transitive = []
        for comp, capability in ENGINE_TO_CAPABILITY.items():
            if capability != cap.id and comp in cap.modules:
                transitive.append(capability)

        # Add multi-capability components
        for _comp, caps in MULTI_CAPABILITY.items():
            if cap.id in caps:
                transitive.extend([c for c in caps if c != cap.id])

        return list(set(transitive))

    def _determine_minimum_verification(
        self, cap, workflow_mappings: list[WorkflowMapping]
    ) -> tuple[str, str]:
        """Determine the minimum verification command and profile."""
        # Prefer quick for quick capabilities, backend for engine capabilities
        for wf in workflow_mappings:
            if wf.is_minimum:
                return wf.command, wf.profile_name

        # Fallback to first workflow
        if workflow_mappings:
            return workflow_mappings[0].command, workflow_mappings[0].profile_name

        return "", ""

    def _determine_escalation_verification(
        self, cap, workflow_mappings: list[WorkflowMapping]
    ) -> tuple[list[str], list[str]]:
        """Determine escalation verification commands and profiles."""
        esc_cmds = []
        esc_profiles = []
        for wf in sorted(workflow_mappings, key=lambda x: x.escalation_order):
            if not wf.is_minimum and wf.command:
                esc_cmds.append(wf.command)
                esc_profiles.append(wf.profile_name)
        return esc_cmds, esc_profiles

    def get_contract(self, capability_id: str) -> OperationalCapability | None:
        """Get operational capability contract by ID."""
        self.load()
        return self._contracts.get(capability_id)

    def get_all_contracts(self) -> list[OperationalCapability]:
        """Get all operational capability contracts."""
        self.load()
        return list(self._contracts.values())

    def get_contracts_by_maturity(
        self, maturity: CapabilityMaturity
    ) -> list[OperationalCapability]:
        """Get contracts by maturity level."""
        self.load()
        return [c for c in self._contracts.values() if c.maturity == maturity]

    def to_dict(self) -> dict:
        """Export all contracts as dictionary."""
        self.load()
        return {
            "schema": "m9-c48-capability-contract/v1",
            "generated_at": datetime.now(UTC).isoformat(),
            "contracts": {
                cid: contract.to_dict() for cid, contract in self._contracts.items()
            },
        }

    def save(self, path: Path | str) -> Path:
        """Save contracts to file."""
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(
            json.dumps(self.to_dict(), indent=2, default=str) + "\n", encoding="utf-8"
        )
        return p


# Global instance
_contract_registry: CapabilityContractRegistry | None = None


def get_capability_contract_registry(
    config_path: Path | None = None,
) -> CapabilityContractRegistry:
    """Get the global capability contract registry."""
    global _contract_registry
    if _contract_registry is None:
        _contract_registry = CapabilityContractRegistry(config_path)
    return _contract_registry


def reset_capability_contract_registry() -> None:
    """Reset the global registry (for testing)."""
    global _contract_registry
    _contract_registry = None


if __name__ == "__main__":
    # Demo: build and save contracts
    registry = get_capability_contract_registry()
    registry.load()
    out_path = (
        Path(__file__).parent.parent.parent
        / "generated"
        / "m9-c48"
        / "capability-contracts.json"
    )
    registry.save(out_path)
    print(f"Saved {len(registry._contracts)} capability contracts to {out_path}")
