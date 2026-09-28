"""
M9-C50 — Latent Capability Protection.

Audits C50 implementation changes for accidental capability loss.
Before removing/changing:

* imports
* registries
* command matchers
* capability mappings
* runtime modules
* apparently unused helpers
* integration hooks

determine whether they are referenced indirectly through the control
plane. If something is genuinely unused, record the evidence; do not
delete it as part of C50 unless deletion is explicitly necessary and
separately authorized.

This module exists specifically because previous repository cleanup
repeatedly risked destroying latent capabilities.
"""

from __future__ import annotations

import subprocess
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent


class ProtectionVerdict(str, Enum):
    """Verdict for a latent capability audit."""

    PROTECTED = "protected"  # Capability is referenced through control plane
    POTENTIALLY_ORPHANED = "potentially_orphaned"  # Not directly referenced
    GENUINELY_UNUSED = "genuinely_unused"  # No references found
    EVIDENCE_INSUFFICIENT = "evidence_insufficient"  # Cannot determine


@dataclass(frozen=True, slots=True)
class LatentCapability:
    """A potentially latent capability identified during audit."""

    name: str
    path: str
    kind: str  # import, registry, command_matcher, mapping, etc.
    direct_references: list[str] = field(default_factory=list)
    indirect_references: list[str] = field(default_factory=list)
    verdict: str = ProtectionVerdict.EVIDENCE_INSUFFICIENT.value
    reason: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class LatentCapabilityReport:
    """Complete latent capability protection report."""

    audited_paths: list[str]
    latent_capabilities: list[LatentCapability]
    protected_count: int
    potentially_orphaned_count: int
    genuinely_unused_count: int
    deletion_recommendations: list[str]

    def to_dict(self) -> dict:
        return {
            "schema": "m9-c50-latent-capability-report/v1",
            "audited_paths": list(self.audited_paths),
            "latent_capabilities": [c.to_dict() for c in self.latent_capabilities],
            "protected_count": self.protected_count,
            "potentially_orphaned_count": self.potentially_orphaned_count,
            "genuinely_unused_count": self.genuinely_unused_count,
            "deletion_recommendations": list(self.deletion_recommendations),
        }


def _grep_repo(pattern: str, paths: list[str] | None = None) -> list[str]:
    """Search for a pattern in the repository."""
    try:
        cmd = ["grep", "-rn", "--include=*.py", pattern, str(REPO_ROOT)]
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        results = []
        for line in out.stdout.splitlines():
            if not line:
                continue
            # Filter out the file being audited itself
            if paths and any(p in line for p in paths):
                continue
            results.append(line.strip())
        return results
    except Exception:
        return []


def audit_latent_capabilities(
    changed_paths: list[str] | None = None,
) -> LatentCapabilityReport:
    """Audit the repository for latent capabilities that might be at risk.

    Checks:
    1. Imports in C50 modules are still referenced by the control plane
    2. Registry entries are still consumed
    3. Command matchers are still wired
    4. Capability mappings are still resolved
    5. Runtime modules are still imported
    """
    if changed_paths is None:
        changed_paths = [
            "runtime/foundation/verification/change_surface.py",
            "runtime/foundation/verification/blast_radius.py",
            "runtime/foundation/verification/blast_radius_cli.py",
        ]

    latent: list[LatentCapability] = []

    # Audit 1: C50 module imports are referenced by control plane
    c50_imports = [
        "BlastRadiusContract",
        "BlastRadiusEngine",
        "compute_blast_radius",
        "format_blast_radius",
        "ChangeSurfaceDiscovery",
        "discover_change_surfaces",
        "format_surface_analysis",
    ]

    for name in c50_imports:
        refs = _grep_repo(name, paths=changed_paths)
        if refs:
            latent.append(
                LatentCapability(
                    name=name,
                    path="runtime/foundation/verification/blast_radius.py",
                    kind="import",
                    direct_references=refs,
                    indirect_references=[],
                    verdict=ProtectionVerdict.PROTECTED.value,
                    reason=f"Found {len(refs)} references in control plane",
                )
            )
        else:
            latent.append(
                LatentCapability(
                    name=name,
                    path="runtime/foundation/verification/blast_radius.py",
                    kind="import",
                    direct_references=[],
                    indirect_references=[],
                    verdict=ProtectionVerdict.POTENTIALLY_ORPHANED.value,
                    reason="No direct references found — may be used through CLI",
                )
            )

    # Audit 2: verify.py CLI commands are wired
    cli_commands = ["blast-radius", "what-should-i-run"]
    for cmd in cli_commands:
        refs = _grep_repo(f'"{cmd}"', paths=["runtime/verify.py"])
        if refs:
            latent.append(
                LatentCapability(
                    name=f"cli:{cmd}",
                    path="runtime/verify.py",
                    kind="command_matcher",
                    direct_references=refs,
                    verdict=ProtectionVerdict.PROTECTED.value,
                    reason=f"CLI command {cmd!r} is wired in verify.py",
                )
            )
        else:
            latent.append(
                LatentCapability(
                    name=f"cli:{cmd}",
                    path="runtime/verify.py",
                    kind="command_matcher",
                    verdict=ProtectionVerdict.EVIDENCE_INSUFFICIENT.value,
                    reason=f"CLI command {cmd!r} not found in verify.py",
                )
            )

    # Audit 3: C49 modules still referenced
    c49_modules = [
        "ExecutionOrchestrator",
        "ExecutionPlan",
        "ExecutionReport",
        "RepositoryFingerprint",
        "CAPABILITY_TO_MUTATION_TARGET",
    ]
    for mod in c49_modules:
        refs = _grep_repo(mod, paths=changed_paths)
        if refs:
            latent.append(
                LatentCapability(
                    name=mod,
                    path="runtime/foundation/verification/execution_orchestrator.py",
                    kind="registry",
                    direct_references=refs[:5],
                    indirect_references=refs[5:] if len(refs) > 5 else [],
                    verdict=ProtectionVerdict.PROTECTED.value,
                    reason=f"Found {len(refs)} references — C49 module still active",
                )
            )

    # Audit 4: C48 modules still referenced
    c48_modules = [
        "CapabilityResolver",
        "resolve_capabilities",
        "PLANNER_CAPABILITY_ALIASES",
        "SharedDependencyIndex",
        "get_shared_dependency_index",
        "CapabilityContractRegistry",
        "get_capability_contract_registry",
    ]
    for mod in c48_modules:
        refs = _grep_repo(mod, paths=changed_paths)
        if refs:
            latent.append(
                LatentCapability(
                    name=mod,
                    path="runtime/foundation/verification/capability_resolver.py",
                    kind="registry",
                    direct_references=refs[:5],
                    indirect_references=refs[5:] if len(refs) > 5 else [],
                    verdict=ProtectionVerdict.PROTECTED.value,
                    reason=f"Found {len(refs)} references — C48 module still active",
                )
            )

    # Audit 5: C47 measurement truth still referenced
    c47_modules = [
        "MeasurementTruthRecord",
        "certification_gate",
        "MeasurementKind",
    ]
    for mod in c47_modules:
        refs = _grep_repo(mod, paths=changed_paths)
        if refs:
            latent.append(
                LatentCapability(
                    name=mod,
                    path="runtime/foundation/verification/measurement_truth.py",
                    kind="registry",
                    direct_references=refs[:5],
                    verdict=ProtectionVerdict.PROTECTED.value,
                    reason=f"Found {len(refs)} references — C47 module still active",
                )
            )

    protected = sum(1 for c in latent if c.verdict == ProtectionVerdict.PROTECTED.value)
    potentially_orphaned = sum(
        1 for c in latent if c.verdict == ProtectionVerdict.POTENTIALLY_ORPHANED.value
    )
    genuinely_unused = sum(
        1 for c in latent if c.verdict == ProtectionVerdict.GENUINELY_UNUSED.value
    )

    # Deletion recommendations: only for genuinely unused
    deletion_recs = [
        c.name for c in latent if c.verdict == ProtectionVerdict.GENUINELY_UNUSED.value
    ]

    return LatentCapabilityReport(
        audited_paths=list(changed_paths),
        latent_capabilities=latent,
        protected_count=protected,
        potentially_orphaned_count=potentially_orphaned,
        genuinely_unused_count=genuinely_unused,
        deletion_recommendations=deletion_recs,
    )


def format_latent_capability_report(report: LatentCapabilityReport) -> str:
    """Format a latent capability protection report."""
    lines = []
    lines.append("=" * 72)
    lines.append("  M9-C50 — LATENT CAPABILITY PROTECTION REPORT")
    lines.append("=" * 72)
    lines.append(f"  Audited paths: {len(report.audited_paths)}")
    lines.append(f"  Protected: {report.protected_count}")
    lines.append(f"  Potentially orphaned: {report.potentially_orphaned_count}")
    lines.append(f"  Genuinely unused: {report.genuinely_unused_count}")
    lines.append("-" * 72)
    for c in report.latent_capabilities:
        marker = "✓" if c.verdict == ProtectionVerdict.PROTECTED.value else "?"
        lines.append(f"  {marker} [{c.verdict}] {c.name} ({c.kind})")
        if c.direct_references:
            lines.append(f"      refs: {len(c.direct_references)}")
        lines.append(f"      {c.reason}")
    lines.append("-" * 72)
    if report.deletion_recommendations:
        lines.append("  DELETION RECOMMENDATIONS (genuinely unused):")
        for d in report.deletion_recommendations:
            lines.append(f"    ✗ {d}")
    else:
        lines.append("  NO DELETIONS RECOMMENDED")
        lines.append("  All audited capabilities are referenced or potentially active")
    lines.append("=" * 72)
    return "\n".join(lines)
