"""
M9-C48 — Canonical Command/Capability Inventory.

Creates a machine-readable inventory of ALL verification capabilities from the
actual implementation (not maintained prose). Exposes for every verification
capability:

* command
* purpose
* accepted scope
* prerequisites
* evidence produced
* evidence consumed
* failure semantics
* escalation behavior
* whether it is certifiable
* whether it mutates the repository
* whether human authorization is required

The inventory is generated/validated from executable registration wherever
practical rather than maintained as disconnected prose.

Adds a canonical inspection command through `verify.py` if the existing CLI
architecture supports it.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any, Literal, cast

from runtime.foundation.verification.capability_contract import (
    CapabilityContractRegistry,
    get_capability_contract_registry,
)
from runtime.foundation.verification.models import (
    VerificationCategory,
    VerificationScope,
)
from runtime.foundation.verification.registry import (
    VerificationRegistry,
    get_registry,
)

# ---------------------------------------------------------------------------
# Command Inventory Models
# ---------------------------------------------------------------------------


class CommandCategory(str, Enum):
    """Category of verification command."""

    QUALITY_GATE = "quality_gate"
    UNIT_TEST = "unit_test"
    CONTRACT_TEST = "contract_test"
    PROPERTY_TEST = "property_test"
    MUTATION_TEST = "mutation_test"
    INTEGRATION_TEST = "integration_test"
    E2E_TEST = "e2e_test"
    COVERAGE_MEASUREMENT = "coverage_measurement"
    STATIC_ANALYSIS = "static_analysis"
    ARCHITECTURAL = "architectural"
    MIGRATION = "migration"
    RECONCILIATION = "reconciliation"
    DIAGNOSTIC = "diagnostic"
    INTELLIGENCE = "intelligence"
    CERTIFICATION = "certification"


class FailureSemantics(str, Enum):
    """What a failure means for this command."""

    VERIFICATION_FAILED = "verification_failed"  # Actual defect found
    INFRASTRUCTURE_FAILED = "infrastructure_failed"  # Could not execute
    EVIDENCE_FAILED = "evidence_failed"  # Execution occurred but evidence incomplete
    SCOPE_FAILED = "scope_failed"  # Scope mismatch
    CONFIGURATION_FAILED = "configuration_failed"  # Misconfigured
    CERTIFICATION_FAILED = (
        "certification_failed"  # Evidence exists but criteria not met
    )


@dataclass(frozen=True, slots=True)
class CommandInventoryEntry:
    """One entry in the canonical command inventory."""

    # Identity
    command_id: str
    command: str  # The exact CLI command
    profile_name: str | None = None  # verify.py profile name

    # Purpose & Scope
    purpose: str = ""
    accepted_scope: list[VerificationScope] = field(default_factory=list)
    category: CommandCategory = CommandCategory.QUALITY_GATE

    # Prerequisites
    prerequisites: list[str] = field(
        default_factory=list
    )  # e.g., [".venv", "backend/pyproject.toml"]
    requires_git: bool = False
    requires_docker: bool = False
    requires_network: bool = False

    # Evidence
    evidence_produced: list[str] = field(
        default_factory=list
    )  # Evidence kinds produced
    evidence_consumed: list[str] = field(
        default_factory=list
    )  # Evidence kinds consumed/reused
    measurement_kinds: list[str] = field(
        default_factory=list
    )  # "coverage", "mutation", "contract", etc.

    # Failure & Escalation
    failure_semantics: FailureSemantics = FailureSemantics.VERIFICATION_FAILED
    escalation_behavior: Literal[
        "none",
        "targeted_mutation",
        "full_capability",
        "cross_capability",
        "repository_wide",
    ] = "none"
    escalation_commands: list[str] = field(default_factory=list)

    # Certification & Safety
    is_certifiable: bool = False  # Can produce certification evidence
    mutates_repository: bool = False  # Modifies source files (e.g., mutation runner)
    requires_human_authorization: bool = False  # Needs explicit human approval

    # Metadata
    estimated_duration_seconds: int = 0
    capabilities_served: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    generated_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())

    def to_dict(self) -> dict:
        return {
            **asdict(self),
            "accepted_scope": [s.value for s in self.accepted_scope],
            "category": self.category.value,
            "failure_semantics": self.failure_semantics.value,
        }


@dataclass
class CommandInventory:
    """Complete canonical command inventory."""

    schema: str = "m9-c48-command-inventory/v1"
    generated_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    commands: list[CommandInventoryEntry] = field(default_factory=list)
    profiles: dict[str, list[str]] = field(
        default_factory=dict
    )  # profile_name -> command_ids
    capabilities_index: dict[str, list[str]] = field(
        default_factory=dict
    )  # capability_id -> command_ids

    def to_dict(self) -> dict:
        return {
            "schema": self.schema,
            "generated_at": self.generated_at,
            "commands": [c.to_dict() for c in self.commands],
            "profiles": self.profiles,
            "capabilities_index": self.capabilities_index,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, default=str)

    def get_command(self, command_id: str) -> CommandInventoryEntry | None:
        """Get command by ID."""
        for cmd in self.commands:
            if cmd.command_id == command_id:
                return cmd
        return None

    def get_commands_for_capability(
        self, capability_id: str
    ) -> list[CommandInventoryEntry]:
        """Get all commands that serve a capability."""
        command_ids = self.capabilities_index.get(capability_id, [])
        return [c for c in self.commands if c.command_id in command_ids]

    def get_commands_for_profile(
        self, profile_name: str
    ) -> list[CommandInventoryEntry]:
        """Get all commands for a profile."""
        command_ids = self.profiles.get(profile_name, [])
        return [c for c in self.commands if c.command_id in command_ids]


# ---------------------------------------------------------------------------
# Inventory Builder
# ---------------------------------------------------------------------------


class CommandInventoryBuilder:
    """Builds the canonical command inventory from executable registrations."""

    def __init__(
        self,
        verification_registry: VerificationRegistry | None = None,
        contract_registry: CapabilityContractRegistry | None = None,
    ):
        self._verification_registry = verification_registry or get_registry()
        self._contract_registry = (
            contract_registry or get_capability_contract_registry()
        )

    def build(self) -> CommandInventory:
        """Build the complete command inventory."""
        inventory = CommandInventory()
        self._verification_registry.load()
        self._contract_registry.load()

        # Build from verification registry workflows
        for workflow in self._verification_registry.get_all_workflows():
            entry = self._build_from_workflow(workflow)
            inventory.commands.append(entry)

            # Index by profile
            if workflow.id not in inventory.profiles:
                inventory.profiles[workflow.id] = []
            inventory.profiles[workflow.id].append(entry.command_id)

            # Index by capabilities
            for cap in workflow.capabilities:
                if cap not in inventory.capabilities_index:
                    inventory.capabilities_index[cap] = []
                if entry.command_id not in inventory.capabilities_index[cap]:
                    inventory.capabilities_index[cap].append(entry.command_id)

        # Add standalone CLI commands from verify.py
        self._add_standalone_commands(inventory)

        # Add capability-specific commands from contract registry
        self._add_capability_commands(inventory)

        return inventory

    def _build_from_workflow(self, workflow) -> CommandInventoryEntry:
        """Build inventory entry from a verification workflow."""
        # Determine category
        category_map = {
            VerificationCategory.CAPABILITY: CommandCategory.QUALITY_GATE,
            VerificationCategory.CONTRACT: CommandCategory.CONTRACT_TEST,
            VerificationCategory.CONTRACT_FRONTEND: CommandCategory.CONTRACT_TEST,
            VerificationCategory.CONTRACT_BACKEND: CommandCategory.CONTRACT_TEST,
            VerificationCategory.PROPERTY: CommandCategory.PROPERTY_TEST,
            VerificationCategory.MUTATION: CommandCategory.MUTATION_TEST,
            VerificationCategory.INTEGRATION: CommandCategory.INTEGRATION_TEST,
            VerificationCategory.MIGRATION: CommandCategory.MIGRATION,
            VerificationCategory.ARCHITECTURAL: CommandCategory.ARCHITECTURAL,
        }
        category = category_map.get(workflow.category, CommandCategory.QUALITY_GATE)

        # Determine failure semantics
        failure_semantics = FailureSemantics.VERIFICATION_FAILED
        if workflow.id == "mutation":
            failure_semantics = FailureSemantics.INFRASTRUCTURE_FAILED

        # Determine escalation
        escalation = "none"
        escalation_cmds = []
        if workflow.id in ("quick", "backend"):
            escalation = "targeted_mutation"
            escalation_cmds = ["verify.py mutation --target <engine>"]
        elif workflow.id == "property":
            escalation = "full_capability"
            escalation_cmds = ["verify.py backend"]
        elif workflow.id == "contracts":
            escalation = "cross_capability"
            escalation_cmds = ["verify.py backend", "verify.py frontend"]

        # Certifiable check
        is_certifiable = workflow.id in ("mutation", "backend", "full", "repository")

        # Mutates repository
        mutates = workflow.id == "mutation"

        # Human authorization
        human_auth = workflow.id == "mutation"

        # Evidence produced/consumed per workflow type
        if workflow.id == "mutation":
            evidence_produced = [
                "mutation_score",
                "survivor_intel",
                "measurement_truth",
            ]
            evidence_consumed = ["test_suite", "source_code"]
            measurement_kinds = ["mutation"]
        elif workflow.id in ("backend", "quick", "property", "contracts"):
            evidence_produced = ["unit_pass", "contract_pass", "property_pass"]
            evidence_consumed = ["source_code", "test_suite"]
            measurement_kinds = ["coverage"]
        elif workflow.id == "coverage":
            evidence_produced = ["measurement_truth"]
            evidence_consumed = []
            measurement_kinds = ["coverage"]
        elif workflow.id == "integration":
            evidence_produced = ["integration_pass"]
            evidence_consumed = ["source_code", "test_suite"]
            measurement_kinds = []
        elif workflow.id == "golden":
            evidence_produced = ["golden_pass"]
            evidence_consumed = ["source_code", "test_suite"]
            measurement_kinds = []
        elif workflow.id == "playwright":
            evidence_produced = ["e2e_pass"]
            evidence_consumed = ["source_code", "test_suite"]
            measurement_kinds = []
        else:
            evidence_produced = []
            evidence_consumed = []
            measurement_kinds = []

        return CommandInventoryEntry(
            command_id=f"cmd::{workflow.id}",
            command=workflow.command or f"verify.py {workflow.id}",
            profile_name=workflow.id,
            purpose=workflow.description,
            accepted_scope=workflow.scopes,
            category=category,
            prerequisites=[".venv", "backend/pyproject.toml"],
            requires_git=True,
            failure_semantics=failure_semantics,
            escalation_behavior=cast(
                Literal[
                    "none",
                    "targeted_mutation",
                    "full_capability",
                    "cross_capability",
                    "repository_wide",
                ],
                escalation,
            ),
            escalation_commands=escalation_cmds,
            is_certifiable=is_certifiable,
            mutates_repository=mutates,
            requires_human_authorization=human_auth,
            estimated_duration_seconds=workflow.estimated_duration_seconds,
            capabilities_served=workflow.capabilities,
            evidence_produced=evidence_produced,
            evidence_consumed=evidence_consumed,
            measurement_kinds=measurement_kinds,
            metadata={
                "workflow_id": workflow.id,
                "scope": workflow.scope.value,
                "script": workflow.script,
            },
        )

    def _add_standalone_commands(self, inventory: CommandInventory) -> None:
        """Add standalone CLI commands from verify.py."""
        standalone_commands = [
            CommandInventoryEntry(
                command_id="cmd::status",
                command="verify.py status",
                purpose="Show workspace status",
                category=CommandCategory.DIAGNOSTIC,
                prerequisites=[".venv"],
                estimated_duration_seconds=5,
            ),
            CommandInventoryEntry(
                command_id="cmd::metrics",
                command="verify.py metrics",
                purpose="Show verification metrics",
                category=CommandCategory.DIAGNOSTIC,
                prerequisites=[".venv"],
                estimated_duration_seconds=5,
            ),
            CommandInventoryEntry(
                command_id="cmd::diagnose",
                command="verify.py diagnose",
                purpose="Diagnose impact of changed files",
                category=CommandCategory.DIAGNOSTIC,
                prerequisites=[".venv"],
                requires_git=True,
                estimated_duration_seconds=10,
            ),
            CommandInventoryEntry(
                command_id="cmd::affected",
                command="verify.py affected",
                purpose="Show affected components and verification plan",
                category=CommandCategory.DIAGNOSTIC,
                prerequisites=[".venv"],
                requires_git=True,
                estimated_duration_seconds=10,
            ),
            CommandInventoryEntry(
                command_id="cmd::plan",
                command="verify.py plan --tier <local|pr|deep>",
                purpose="Emit tier-aware verification plan manifest",
                category=CommandCategory.DIAGNOSTIC,
                prerequisites=[".venv"],
                requires_git=True,
                estimated_duration_seconds=10,
            ),
            CommandInventoryEntry(
                command_id="cmd::mutation",
                command="verify.py mutation [--smoke|--target <engine>|--restore]",
                purpose="Run mutation testing (authoritative full campaign or targeted)",
                category=CommandCategory.MUTATION_TEST,
                prerequisites=[".venv", "backend/pyproject.toml"],
                requires_git=True,
                failure_semantics=FailureSemantics.INFRASTRUCTURE_FAILED,
                escalation_behavior="repository_wide",
                is_certifiable=True,
                mutates_repository=True,
                requires_human_authorization=True,
                estimated_duration_seconds=5400,
                measurement_kinds=["mutation"],
                evidence_produced=[
                    "mutation_score",
                    "survivor_intel",
                    "measurement_truth",
                ],
                capabilities_served=["mutation-analysis"],
            ),
            CommandInventoryEntry(
                command_id="cmd::measurement_truth",
                command="verify.py measurement-truth <record.json> [--json]",
                purpose="Inspect a measurement truth record",
                category=CommandCategory.DIAGNOSTIC,
                prerequisites=[".venv"],
                estimated_duration_seconds=5,
                evidence_consumed=["measurement_truth"],
            ),
            CommandInventoryEntry(
                command_id="cmd::measurement_coverage",
                command="verify.py measurement coverage <scope>",
                purpose="Measure coverage for a scope and produce measurement truth record",
                category=CommandCategory.COVERAGE_MEASUREMENT,
                prerequisites=[".venv", "backend/pyproject.toml"],
                requires_git=True,
                estimated_duration_seconds=1800,
                measurement_kinds=["coverage"],
                evidence_produced=["measurement_truth"],
            ),
            CommandInventoryEntry(
                command_id="cmd::mutation_intel",
                command="verify.py mutation-intel [survivor_id] [--json]",
                purpose="Inspect durable survivor intelligence",
                category=CommandCategory.INTELLIGENCE,
                prerequisites=[".venv"],
                estimated_duration_seconds=5,
                evidence_consumed=["survivor_intel"],
            ),
            CommandInventoryEntry(
                command_id="cmd::forensic_diagnose",
                command="verify.py forensic-diagnose <engine>",
                purpose="Forensic diagnosis of mutation survivors",
                category=CommandCategory.INTELLIGENCE,
                prerequisites=[".venv"],
                requires_git=True,
                estimated_duration_seconds=300,
                evidence_consumed=["survivor_intel", "measurement_truth"],
            ),
            CommandInventoryEntry(
                command_id="cmd::strengthen_analyze",
                command="verify.py strengthen-analyze <engine>",
                purpose="Analyze survivors for strengthening opportunities",
                category=CommandCategory.INTELLIGENCE,
                prerequisites=[".venv"],
                requires_git=True,
                estimated_duration_seconds=300,
                requires_human_authorization=True,
                evidence_consumed=["survivor_intel"],
                evidence_produced=["strengthening_proposal"],
            ),
            CommandInventoryEntry(
                command_id="cmd::env_check",
                command="verify.py env-check",
                purpose="Verify canonical .venv environment",
                category=CommandCategory.DIAGNOSTIC,
                prerequisites=[".venv"],
                estimated_duration_seconds=10,
            ),
            CommandInventoryEntry(
                command_id="cmd::env_contract",
                command="verify.py env-contract",
                purpose="Build authoritative environment contract for reproducible verification (C55)",
                category=CommandCategory.DIAGNOSTIC,
                prerequisites=[".venv"],
                estimated_duration_seconds=5,
            ),
            CommandInventoryEntry(
                command_id="cmd::audit",
                command="verify.py audit",
                purpose="Run engineering platform certification audit",
                category=CommandCategory.CERTIFICATION,
                prerequisites=[".venv"],
                requires_git=True,
                estimated_duration_seconds=300,
                is_certifiable=True,
            ),
            CommandInventoryEntry(
                command_id="cmd::api_contracts",
                command="verify.py api-contracts",
                purpose="Run API contract integrity gate",
                category=CommandCategory.CONTRACT_TEST,
                prerequisites=[".venv"],
                requires_git=True,
                estimated_duration_seconds=180,
                is_certifiable=True,
                capabilities_served=["api-contracts"],
            ),
            CommandInventoryEntry(
                command_id="cmd::contract_governance",
                command="verify.py contract-governance",
                purpose="Run contract governance certification",
                category=CommandCategory.CERTIFICATION,
                prerequisites=[".venv"],
                requires_git=True,
                estimated_duration_seconds=600,
                is_certifiable=True,
            ),
        ]

        for cmd in standalone_commands:
            inventory.commands.append(cmd)
            # These don't map to profiles in the same way
            if "standalone" not in inventory.profiles:
                inventory.profiles["standalone"] = []
            inventory.profiles["standalone"].append(cmd.command_id)

    def _add_capability_commands(self, inventory: CommandInventory) -> None:
        """Add capability-specific commands from contract registry."""
        for contract in self._contract_registry.get_all_contracts():
            if contract.minimum_verification_command:
                entry = CommandInventoryEntry(
                    command_id=f"cmd::capability::{contract.id}::minimum",
                    command=contract.minimum_verification_command,
                    purpose=f"Minimum verification for {contract.name}",
                    profile_name=contract.minimum_verification_profile,
                    category=CommandCategory.QUALITY_GATE,
                    prerequisites=[".venv", "backend/pyproject.toml"],
                    requires_git=True,
                    failure_semantics=FailureSemantics.VERIFICATION_FAILED,
                    escalation_behavior="targeted_mutation",
                    escalation_commands=contract.escalation_verification_commands,
                    is_certifiable=any(
                        cc.requires_authoritative_classification
                        for cc in contract.certification_conditions
                    ),
                    mutates_repository=False,
                    requires_human_authorization=False,
                    estimated_duration_seconds=sum(
                        wf.estimated_duration_seconds
                        for wf in contract.workflow_mappings
                        if not wf.is_minimum
                    ),
                    capabilities_served=[contract.id],
                    metadata={
                        "capability_id": contract.id,
                        "verification_type": "minimum",
                    },
                )
                inventory.commands.append(entry)

                # Index by capability
                if contract.id not in inventory.capabilities_index:
                    inventory.capabilities_index[contract.id] = []
                inventory.capabilities_index[contract.id].append(entry.command_id)

            # Add escalation commands
            for i, (cmd, profile) in enumerate(
                zip(
                    contract.escalation_verification_commands,
                    contract.escalation_verification_profiles,
                    strict=False,
                )
            ):
                entry = CommandInventoryEntry(
                    command_id=f"cmd::capability::{contract.id}::escalation::{i}",
                    command=cmd,
                    purpose=f"Escalation verification for {contract.name} (level {i+1})",
                    profile_name=profile,
                    category=CommandCategory.QUALITY_GATE,
                    prerequisites=[".venv", "backend/pyproject.toml"],
                    requires_git=True,
                    failure_semantics=FailureSemantics.VERIFICATION_FAILED,
                    escalation_behavior=(
                        "cross_capability" if i == 0 else "repository_wide"
                    ),
                    is_certifiable=True,
                    mutates_repository=False,
                    requires_human_authorization=i > 0,
                    estimated_duration_seconds=300 * (i + 1),
                    capabilities_served=[contract.id],
                    metadata={
                        "capability_id": contract.id,
                        "verification_type": "escalation",
                        "escalation_level": i + 1,
                    },
                )
                inventory.commands.append(entry)
                inventory.capabilities_index[contract.id].append(entry.command_id)


# ---------------------------------------------------------------------------
# Global Instance & CLI
# ---------------------------------------------------------------------------


_inventory: CommandInventory | None = None


def get_command_inventory() -> CommandInventory:
    """Get or build the global command inventory."""
    global _inventory
    if _inventory is None:
        builder = CommandInventoryBuilder()
        _inventory = builder.build()
    return _inventory


def reset_command_inventory() -> None:
    """Reset the global inventory (for testing)."""
    global _inventory
    _inventory = None


def format_inventory_entry(entry: CommandInventoryEntry) -> str:
    """Format a single inventory entry for display."""
    lines = []
    lines.append(f"  Command: {entry.command}")
    lines.append(f"  ID: {entry.command_id}")
    lines.append(f"  Purpose: {entry.purpose}")
    lines.append(f"  Category: {entry.category.value}")
    lines.append(
        f"  Scope: {', '.join(s.value for s in entry.accepted_scope) or 'any'}"
    )
    lines.append(f"  Prerequisites: {', '.join(entry.prerequisites) or 'none'}")
    lines.append(f"  Evidence produced: {', '.join(entry.evidence_produced) or 'none'}")
    lines.append(f"  Evidence consumed: {', '.join(entry.evidence_consumed) or 'none'}")
    lines.append(f"  Measurements: {', '.join(entry.measurement_kinds) or 'none'}")
    lines.append(f"  Failure semantics: {entry.failure_semantics.value}")
    lines.append(f"  Escalation: {entry.escalation_behavior}")
    if entry.escalation_commands:
        lines.append(f"  Escalation commands: {', '.join(entry.escalation_commands)}")
    lines.append(f"  Certifiable: {'Yes' if entry.is_certifiable else 'No'}")
    lines.append(f"  Mutates repository: {'Yes' if entry.mutates_repository else 'No'}")
    lines.append(
        f"  Requires human authorization: {'Yes' if entry.requires_human_authorization else 'No'}"
    )
    lines.append(
        f"  Capabilities served: {', '.join(entry.capabilities_served) or 'none'}"
    )
    lines.append(f"  Duration: {entry.estimated_duration_seconds}s")
    return "\n".join(lines)


def format_inventory(inventory: CommandInventory) -> str:
    """Format entire inventory for display."""
    lines = []
    lines.append("=" * 80)
    lines.append("  CANONICAL COMMAND/CAPABILITY INVENTORY")
    lines.append("=" * 80)
    lines.append(f"  Generated: {inventory.generated_at}")
    lines.append(f"  Total commands: {len(inventory.commands)}")
    lines.append(f"  Profiles: {len(inventory.profiles)}")
    lines.append(f"  Capabilities indexed: {len(inventory.capabilities_index)}")
    lines.append("-" * 80)

    # Group by category
    by_category: dict[CommandCategory, list[CommandInventoryEntry]] = {}
    for cmd in inventory.commands:
        by_category.setdefault(cmd.category, []).append(cmd)

    for category in sorted(CommandCategory):
        if category not in by_category:
            continue
        lines.append(
            f"\n  {category.value.upper()} ({len(by_category[category])} commands):"
        )
        for cmd in by_category[category]:
            lines.append(f"    • {cmd.command_id}: {cmd.command}")
            lines.append(f"      Purpose: {cmd.purpose}")
            lines.append(
                f"      Capabilities: {', '.join(cmd.capabilities_served) or 'none'}"
            )

    lines.append("\n" + "=" * 80)
    return "\n".join(lines)


if __name__ == "__main__":
    # Build and save inventory
    inventory = get_command_inventory()
    out_path = (
        Path(__file__).parent.parent.parent
        / "generated"
        / "m9-c48"
        / "command-inventory.json"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(inventory.to_json())
    print(f"Saved command inventory ({len(inventory.commands)} commands) to {out_path}")
    print(format_inventory(inventory))
