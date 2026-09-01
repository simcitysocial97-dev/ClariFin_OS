# runtime/foundation/verification/capability_catalog.py
#
# M9-C51 — Canonical Capability Catalog (M51.1 / M51.2).
#
# M51.1 freezes the ACTUAL verification surface (inspected implementation, not
# historical documentation) into a machine-readable inventory of
#
#     capability -> command -> implementation -> inputs -> outputs
#           -> evidence -> consumer
#
# M51.2 extends the existing C48 capability metadata model
# (CommandInventoryEntry / OperationalCapability) with the discovery metadata
# a human or agent needs to answer:
#
#     "I have this problem. Which existing capability should I use?"
#
# This module is strictly additive on top of C42.38 / C47 / C48 / C49 / C50:
#   * it composes (does not replace) the C48 CommandInventoryEntry model;
#   * profile capabilities are derived from the executable registration in
#     verification.yaml via VerificationRegistry;
#   * the data table (one _Registration row per real capability) lives in
#     `capability_catalog_data.py` so the model is small and inspectable;
#   * no second capability registry and no parallel command inventory exist.
#
# The closed stage vocabulary (C51.2) is:
#     discovery | planning | execution | measurement | diagnosis |
#     strengthening | evidence_inspection | certification

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent

from runtime.foundation.verification.command_inventory import (  # noqa: E402
    CommandCategory,
    CommandInventoryEntry,
)

_VERIFY_PY = REPO_ROOT / "runtime" / "verify.py"


# ---------------------------------------------------------------------------
# C51.2 — closed metadata vocabulary
# ---------------------------------------------------------------------------


class CapabilityStage(str, Enum):
    """Lifecycle stage a verification capability occupies (C51.2)."""

    DISCOVERY = "discovery"
    PLANNING = "planning"
    EXECUTION = "execution"
    MEASUREMENT = "measurement"
    DIAGNOSIS = "diagnosis"
    STRENGTHENING = "strengthening"
    EVIDENCE_INSPECTION = "evidence_inspection"
    CERTIFICATION = "certification"


class CostClass(str, Enum):
    """Deterministic cost classification for operator/agent selection."""

    NEGLIGIBLE = "negligible"  # < 10 s
    LOW = "low"  # < 60 s
    MODERATE = "moderate"  # < 10 min
    HIGH = "high"  # < 60 min
    EXTREME = "extreme"  # >= 60 min / campaign-grade


class AuthorizationLevel(str, Enum):
    """Who may authorize executing the capability (C51.2 authorization)."""

    NONE = "none"
    OPERATOR = "operator"
    HUMAN = "human"
    CI_ONLY = "ci_only"


class CliReachability(str, Enum):
    """How the capability is reachable from the operator surface."""

    CLI = "cli"
    API_ONLY = "api_only"
    BOTH = "both"


# Problem-type vocabulary consumed by the C51.3 discovery resolver.
PROBLEM_CHANGED_FILE = "changed_file"
PROBLEM_TEST_FAILURE = "test_failure"
PROBLEM_MUTATION_SURVIVOR = "mutation_survivor"
PROBLEM_COVERAGE_DROP = "coverage_drop"
PROBLEM_WORKFLOW_FAILURE = "workflow_failure"
PROBLEM_QUALITY_FAILURE = "quality_failure"
PROBLEM_PROPOSED_CHANGE = "proposed_change"
PROBLEM_STALE_EVIDENCE = "stale_evidence"
PROBLEM_UNKNOWN_FAILURE = "unknown_failure"

PROBLEM_TYPES: tuple[str, ...] = (
    PROBLEM_CHANGED_FILE,
    PROBLEM_TEST_FAILURE,
    PROBLEM_MUTATION_SURVIVOR,
    PROBLEM_COVERAGE_DROP,
    PROBLEM_WORKFLOW_FAILURE,
    PROBLEM_QUALITY_FAILURE,
    PROBLEM_PROPOSED_CHANGE,
    PROBLEM_STALE_EVIDENCE,
    PROBLEM_UNKNOWN_FAILURE,
)

# Closed evidence-kind vocabulary.
EVIDENCE_KINDS: tuple[str, ...] = (
    "environment_fingerprint",
    "lint_report",
    "format_report",
    "typecheck_report",
    "test_pass",
    "property_pass",
    "contract_pass",
    "invariant_pass",
    "integration_pass",
    "e2e_pass",
    "golden_pass",
    "coverage_measurement",
    "mutation_score",
    "survivor_intel",
    "strengthening_proposal",
    "forensic_report",
    "diagnostic_report",
    "capability_resolution",
    "blast_radius_contract",
    "control_plane_plan",
    "execution_plan",
    "tier_plan_manifest",
    "evidence_invalidations",
    "execution_report",
    "reconciliation_report",
    "certification_report",
    "capability_catalog",
)


# ---------------------------------------------------------------------------
# C51.2 contract — extended capability metadata (composes C48 base entry)
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class VerificationCapabilityMetadata:
    """Machine-readable discovery metadata for one verification capability.

    Composes the C48 CommandInventoryEntry (base identity, purpose, scope,
    failure semantics, escalation, certifiability, mutation safety,
    authorization, duration) and extends it with the C51.2 fields required
    for deterministic capability discovery.
    """

    capability_id: str
    name: str
    stage: CapabilityStage
    purpose: str
    command: str
    implementation: str
    category: CommandCategory
    trigger_conditions: tuple[str, ...] = ()
    input_types: tuple[str, ...] = ("none",)
    input_sources: tuple[str, ...] = ("none",)
    produces: tuple[str, ...] = ()
    consumes: tuple[str, ...] = ()
    evidence_type: str = "none"
    measurement_kind: str = ""
    authorization: AuthorizationLevel = AuthorizationLevel.NONE
    cost_class: CostClass = CostClass.LOW
    failure_states: tuple[str, ...] = ()
    preconditions: tuple[str, ...] = ()
    related_capabilities: tuple[str, ...] = ()
    supersedes_or_replaces: tuple[str, ...] = ()
    configuration_authority: tuple[str, ...] = ()
    reachability: CliReachability = CliReachability.CLI
    notes: tuple[str, ...] = ()
    profile_name: str = ""
    entry: CommandInventoryEntry = field(
        default_factory=lambda: CommandInventoryEntry(
            command_id="cmd::unregistered",
            command="",
        )
    )

    def __post_init__(self) -> None:
        # M9-C52.1 defect fix: catalog_data passed plain strings into the
        # tuple-typed `notes` field; `list(str)` silently exploded notes into
        # per-character lists in the inventory artifact. Normalize at the single
        # model boundary so every consumer (to_dict, JSON, graph) gets a clean
        # tuple. A bare str becomes a one-element tuple; non-str sequences are
        # passed through unchanged.
        if isinstance(self.notes, str):
            object.__setattr__(self, "notes", (self.notes,))

    @property
    def command_id(self) -> str:
        return self.entry.command_id

    def to_dict(self) -> dict[str, Any]:
        return {
            "capability_id": self.capability_id,
            "name": self.name,
            "stage": self.stage.value,
            "purpose": self.purpose,
            "command": self.command,
            "command_id": self.command_id,
            "implementation": self.implementation,
            "category": self.category.value,
            "trigger_conditions": list(self.trigger_conditions),
            "input_types": list(self.input_types),
            "input_sources": list(self.input_sources),
            "produces": list(self.produces),
            "consumes": list(self.consumes),
            "evidence_type": self.evidence_type,
            "measurement_kind": self.measurement_kind,
            "authorization": self.authorization.value,
            "cost_class": self.cost_class.value,
            "failure_states": list(self.failure_states),
            "preconditions": list(self.preconditions),
            "related_capabilities": list(self.related_capabilities),
            "supersedes_or_replaces": list(self.supersedes_or_replaces),
            "configuration_authority": list(self.configuration_authority),
            "reachability": self.reachability.value,
            "profile_name": self.profile_name,
            "notes": list(self.notes),
            "c48_entry": self.entry.to_dict(),
        }


# ---------------------------------------------------------------------------
# Catalog (M51.1)
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class CatalogIssue:
    """A validation finding against the catalog."""

    severity: str  # "error" | "warning"
    kind: str
    capability_id: str
    message: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class CapabilityCatalog:
    """The frozen verification-surface catalog (C51.1)."""

    generated_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    entries: list[VerificationCapabilityMetadata] = field(default_factory=list)
    issues: list[CatalogIssue] = field(default_factory=list)
    cli_routes: list[str] = field(default_factory=list)
    profiles: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        self._index = {e.capability_id: e for e in self.entries}

    def get(self, capability_id: str) -> VerificationCapabilityMetadata | None:
        return self._index.get(capability_id)

    def by_stage(self, stage: CapabilityStage) -> list[VerificationCapabilityMetadata]:
        return [e for e in self.entries if e.stage == stage]

    def producers_of(self, evidence_kind: str) -> list[VerificationCapabilityMetadata]:
        return [e for e in self.entries if evidence_kind in e.produces]

    def consumers_of(self, evidence_kind: str) -> list[VerificationCapabilityMetadata]:
        return [e for e in self.entries if evidence_kind in e.consumes]

    def for_problem(self, problem_type: str) -> list[VerificationCapabilityMetadata]:
        return [e for e in self.entries if problem_type in e.trigger_conditions]

    def has_unresolved_references(self) -> bool:
        return any(i.severity == "error" for i in self.issues)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": "m9-c51-capability-catalog/v1",
            "generated_at": self.generated_at,
            "stages": [s.value for s in CapabilityStage],
            "cli_routes": list(self.cli_routes),
            "profiles": list(self.profiles),
            "total_capabilities": len(self.entries),
            "stage_counts": {s.value: len(self.by_stage(s)) for s in CapabilityStage},
            "entries": [e.to_dict() for e in self.entries],
            "issues": [i.to_dict() for i in self.issues],
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, default=str)


# ---------------------------------------------------------------------------
# CLI route discovery (shared with the C51.11 latent audit)
# ---------------------------------------------------------------------------

_CMD_RE = re.compile(r'^\s+if command == "([^"]+)"', re.MULTILINE)
_SUB_RE = re.compile(r'^\s+if sub_command == "([^"]+)"', re.MULTILINE)
_KNOWN_SUB_PARENTS = ("knowledge", "measurement")


def parse_verify_cli_routes() -> list[str]:
    """Statically parse the actual command routes handled by runtime/verify.py.

    Deterministic scan of the real implementation (not of documentation):
      * top-level `if command == "X"` routes,
      * `if sub_command == "Y"` routes under their parent command
        (e.g. `knowledge endpoint`, `measurement coverage`),
      * verification profile names from the executable registration
        (they fall through to profile dispatch at the end of main()).
    """
    source = _VERIFY_PY.read_text(encoding="utf-8")
    routes: list[str] = []
    for match in _CMD_RE.finditer(source):
        routes.append(match.group(1))

    parent = ""
    for line in source.splitlines():
        cmd_match = re.search(r'^\s+if command == "([^"]+)"', line)
        if cmd_match:
            parent = cmd_match.group(1)
        sub_match = re.search(r'^\s+if sub_command == "([^"]+)"', line)
        if sub_match and parent in _KNOWN_SUB_PARENTS:
            routes.append(f"{parent} {sub_match.group(1)}")

    try:
        from runtime.foundation.verification.registry import get_registry

        registry = get_registry()
        registry.load()
        routes.extend(w.id for w in registry.get_all_workflows())
    except Exception:
        pass

    seen: set[str] = set()
    ordered: list[str] = []
    for route in routes:
        if route not in seen:
            seen.add(route)
            ordered.append(route)
    return ordered


# ---------------------------------------------------------------------------
# Builder (C51.1) — derives the catalog from the executable registration
# ---------------------------------------------------------------------------


def _duration_class(seconds: int) -> CostClass:
    if seconds < 10:
        return CostClass.NEGLIGIBLE
    if seconds < 60:
        return CostClass.LOW
    if seconds < 600:
        return CostClass.MODERATE
    if seconds < 3600:
        return CostClass.HIGH
    return CostClass.EXTREME


@dataclass(frozen=True, slots=True)
class _Registration:
    """One frozen inventory row (C51.1). All C51.2 fields are explicit."""

    capability_id: str
    name: str
    stage: CapabilityStage
    purpose: str
    command: str
    implementation: str
    category: CommandCategory
    trigger_conditions: tuple[str, ...] = ()
    input_types: tuple[str, ...] = ("none",)
    input_sources: tuple[str, ...] = ("none",)
    produces: tuple[str, ...] = ()
    consumes: tuple[str, ...] = ()
    evidence_type: str = "none"
    measurement_kind: str = ""
    authorization: AuthorizationLevel = AuthorizationLevel.NONE
    preconditions: tuple[str, ...] = ()
    related_capabilities: tuple[str, ...] = ()
    supersedes_or_replaces: tuple[str, ...] = ()
    configuration_authority: tuple[str, ...] = ()
    reachability: CliReachability = CliReachability.CLI
    notes: tuple[str, ...] = ()
    profile_name: str = ""
    estimated_duration_seconds: int = 10

    def to_metadata(self) -> VerificationCapabilityMetadata:
        seconds = int(self.estimated_duration_seconds)
        return VerificationCapabilityMetadata(
            capability_id=self.capability_id,
            name=self.name,
            stage=self.stage,
            purpose=self.purpose,
            command=self.command,
            implementation=self.implementation,
            category=self.category,
            trigger_conditions=self.trigger_conditions,
            input_types=self.input_types,
            input_sources=self.input_sources,
            produces=self.produces,
            consumes=self.consumes,
            evidence_type=self.evidence_type,
            measurement_kind=self.measurement_kind,
            authorization=self.authorization,
            cost_class=_duration_class(seconds),
            preconditions=self.preconditions,
            related_capabilities=self.related_capabilities,
            supersedes_or_replaces=self.supersedes_or_replaces,
            configuration_authority=self.configuration_authority,
            reachability=self.reachability,
            notes=self.notes,
            profile_name=self.profile_name,
            entry=CommandInventoryEntry(
                command_id=f"cmd::{self.capability_id}",
                command=self.command,
                profile_name=self.profile_name or None,
                purpose=self.purpose,
                category=self.category,
                prerequisites=list(self.configuration_authority),
                evidence_produced=list(self.produces),
                evidence_consumed=list(self.consumes),
                measurement_kinds=(
                    [self.measurement_kind] if self.measurement_kind else []
                ),
                requires_human_authorization=(
                    self.authorization
                    in (AuthorizationLevel.HUMAN, AuthorizationLevel.CI_ONLY)
                ),
                is_certifiable=True,
                estimated_duration_seconds=seconds,
                capabilities_served=[self.capability_id],
            ),
        )


# ---------------------------------------------------------------------------
# Profile capability derivation
# ---------------------------------------------------------------------------


def _profile_entries() -> list[_Registration]:
    """Build a registration row per verification profile in verification.yaml.

    Profiles are derived from the executable registration (the registry), not
    maintained as a separate hand-written list. Each profile is treated as a
    single EXECUTION capability whose surface is `verify.py <profile>` and
    whose command is the workflow's underlying bash script.
    """
    from runtime.foundation.verification.registry import get_registry

    try:
        registry = get_registry()
        registry.load()
    except Exception:
        return []

    rows: list[_Registration] = []
    for wf in registry.get_all_workflows():
        # Skip the mutation profile — it is already covered by measure.mutation
        # (authoritative C47 entry). The profile route still works, but listing
        # it twice would create a duplicate command under two stage labels.
        if wf.id == "mutation":
            continue
        rows.append(
            _Registration(
                capability_id=f"exec.profile.{wf.id}",
                name=f"Profile: {wf.name}",
                stage=CapabilityStage.EXECUTION,
                purpose=(
                    wf.description
                    + " — exposed as a verify.py profile that selects and runs the workflow."
                ),
                command=f"python runtime/verify.py {wf.id}",
                implementation=(
                    f"runtime.foundation.verification.orchestrator:"
                    f"VerificationOrchestrator.run(profile={wf.id!r})"
                ),
                category=CommandCategory.QUALITY_GATE,
                trigger_conditions=(PROBLEM_CHANGED_FILE,),
                input_types=("changed_files",),
                input_sources=("git_working_tree", "explicit_argument"),
                produces=("execution_report", "test_pass"),
                consumes=(),
                evidence_type="execution_report",
                configuration_authority=(
                    "runtime/foundation/verification/verification.yaml",
                ),
                profile_name=wf.id,
                estimated_duration_seconds=int(wf.estimated_duration_seconds),
            )
        )
    return rows


# ---------------------------------------------------------------------------
# Catalog builder + validation
# ---------------------------------------------------------------------------


class CapabilityCatalogBuilder:
    """Build the canonical capability catalog from registered descriptors."""

    def __init__(self) -> None:
        self._issues: list[CatalogIssue] = []

    def build(self) -> CapabilityCatalog:
        # Lazy import to avoid import cycles (capability_catalog_data is
        # an implementation detail of the catalog).
        from runtime.foundation.verification.capability_catalog_data import (
            REGISTRATIONS,
        )

        all_rows: list[_Registration] = list(REGISTRATIONS) + _profile_entries()

        # Validate references among the in-memory rows first.
        all_ids = {row.capability_id for row in all_rows}
        entries: list[VerificationCapabilityMetadata] = []
        for row in all_rows:
            self._validate_row(row, all_ids)
            entries.append(row.to_metadata())

        # Re-validate cross-references after metadata is built.
        metadata_ids = {e.capability_id for e in entries}
        for entry in entries:
            for pre in entry.preconditions:
                if pre not in metadata_ids:
                    self._issues.append(
                        CatalogIssue(
                            severity="warning",
                            kind="dangling_precondition",
                            capability_id=entry.capability_id,
                            message=(
                                f"preconditions refers to unknown capability {pre!r}"
                            ),
                        )
                    )

        return CapabilityCatalog(
            entries=entries,
            issues=self._issues,
            cli_routes=parse_verify_cli_routes(),
            profiles=sorted({e.profile_name for e in entries if e.profile_name}),
        )

    def _validate_row(self, row: _Registration, known_ids: set[str]) -> None:
        # Configuration authority must point at existing config files (or
        # directories — workflows live in .github/actions/ and .github/workflows).
        for path_str in row.configuration_authority:
            abs_path = REPO_ROOT / path_str
            if not abs_path.exists():
                self._issues.append(
                    CatalogIssue(
                        severity="warning",
                        kind="missing_config_authority",
                        capability_id=row.capability_id,
                        message=(
                            f"configuration_authority path {path_str!r} "
                            f"does not exist on disk"
                        ),
                    )
                )

        for target in row.supersedes_or_replaces:
            if target not in known_ids:
                self._issues.append(
                    CatalogIssue(
                        severity="warning",
                        kind="unknown_supersedes_target",
                        capability_id=row.capability_id,
                        message=(
                            f"supersedes_or_replaces refers to "
                            f"unknown capability {target!r}"
                        ),
                    )
                )

        for evidence in row.produces + row.consumes:
            if evidence not in EVIDENCE_KINDS:
                self._issues.append(
                    CatalogIssue(
                        severity="warning",
                        kind="unknown_evidence_kind",
                        capability_id=row.capability_id,
                        message=(
                            f"evidence kind {evidence!r} is not in the "
                            f"closed EVIDENCE_KINDS vocabulary"
                        ),
                    )
                )


# ---------------------------------------------------------------------------
# Global getter + CLI
# ---------------------------------------------------------------------------


_catalog: CapabilityCatalog | None = None


def get_capability_catalog() -> CapabilityCatalog:
    """Return the singleton catalog, building it on first access."""
    global _catalog
    if _catalog is None:
        _catalog = CapabilityCatalogBuilder().build()
    return _catalog


def reset_capability_catalog() -> None:
    """Reset the singleton (used by tests)."""
    global _catalog
    _catalog = None


def format_catalog(
    catalog: CapabilityCatalog,
    *,
    stage: CapabilityStage | None = None,
) -> str:
    """Render a human-readable table of capabilities for the operator."""
    entries = catalog.by_stage(stage) if stage is not None else catalog.entries
    lines: list[str] = []
    lines.append("=" * 78)
    lines.append("  CANONICAL VERIFICATION CAPABILITY CATALOG  (M9-C51)")
    lines.append("=" * 78)
    lines.append(f"  Generated:   {catalog.generated_at}")
    lines.append(
        f"  Capabilities:{len(catalog.entries)}  "
        f"Profiles: {len(catalog.profiles)}  "
        f"Issues: {len(catalog.issues)}"
    )
    lines.append("-" * 78)
    if stage is not None:
        lines.append(f"  Filter: stage={stage.value}  ({len(entries)} entries)")
        lines.append("-" * 78)

    # Group by stage.
    by_stage: dict[CapabilityStage, list[VerificationCapabilityMetadata]] = {}
    for e in entries:
        by_stage.setdefault(e.stage, []).append(e)
    for st in CapabilityStage:
        if st not in by_stage:
            continue
        lines.append(f"\n  {st.value.upper()}  ({len(by_stage[st])})")
        for e in by_stage[st]:
            lines.append(f"    [{e.capability_id}]  {e.name}")
            lines.append(f"        command:    {e.command}")
            lines.append(f"        stage:      {e.stage.value}")
            lines.append(
                f"        authority:  {', '.join(e.configuration_authority) or '-'}"
            )
            lines.append(
                f"        triggers:   {', '.join(e.trigger_conditions) or '-'}"
            )
            lines.append(f"        produces:   {', '.join(e.produces) or '-'}")
            lines.append(
                f"        authorization: {e.authorization.value}  "
                f"cost: {e.cost_class.value}"
            )

    lines.append("-" * 78)
    if catalog.issues:
        lines.append(f"  ISSUES ({len(catalog.issues)}):")
        for i in catalog.issues[:20]:
            lines.append(
                f"    [{i.severity.upper()}] {i.capability_id}  "
                f"{i.kind} — {i.message}"
            )
        if len(catalog.issues) > 20:
            lines.append(
                f"    ... and {len(catalog.issues) - 20} more "
                "(see capability-inventory.json)"
            )
    lines.append("=" * 78)
    return "\n".join(lines)


def cmd_capabilities(argv: list[str]) -> int:
    """verify.py capabilities  — list all canonical capabilities.

    Usage:
        verify.py capabilities [--stage discovery|planning|...] [--json] [--out PATH]
    """
    import argparse

    parser = argparse.ArgumentParser(prog="verify.py capabilities", add_help=False)
    parser.add_argument(
        "--stage",
        default=None,
        choices=[s.value for s in CapabilityStage],
        help="filter by capability stage",
    )
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--out", default=None, help="output file path")
    args = parser.parse_args(argv)

    catalog = get_capability_catalog()
    stage = CapabilityStage(args.stage) if args.stage else None

    if args.json:
        out = catalog.to_dict()
        if stage is not None:
            out["entries"] = [e for e in out["entries"] if e["stage"] == stage.value]
        rendered = json.dumps(out, indent=2, default=str)
    else:
        rendered = format_catalog(catalog, stage=stage)

    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(rendered, encoding="utf-8")
        print(f"Written to {args.out}")
    else:
        print(rendered)
    return 0


if __name__ == "__main__":  # pragma: no cover
    import sys

    sys.exit(cmd_capabilities(sys.argv[1:]))
