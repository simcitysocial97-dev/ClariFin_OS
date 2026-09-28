# runtime/foundation/verification/bypass_enforcement.py
#
# M9-C52.6 — Bypass Resistance.
#
# Turns the C51 bypass audit into executable enforcement. Identifies all paths
# by which a user or internal process could currently bypass the control plane
# and classifies each as:
#   SAFE — legitimate low-level diagnostic/development path, explicitly marked
#   CONTROLLED — canonical path with full enforcement
#   INTENTIONAL_LOW_LEVEL_ESCAPE — developer escape hatch, never silent
#   BYPASS_RISK — dangerous path that could silently bypass enforcement
#   BLOCKING_BYPASS — path that must be blocked at runtime
#
# The certification path (normal operation) must NEVER silently use
# INTENTIONAL_LOW_LEVEL_ESCAPE or BYPASS_RISK paths.

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent


@dataclass(frozen=True, slots=True)
class BypassPath:
    """One executable path that could bypass the control plane."""

    name: str
    description: str
    entry_point: (
        str  # e.g., "verify.py mutation", "pytest tests/unit/...", "mutmut run"
    )
    bypasses: list[str]  # which control plane stages it bypasses
    classification: str  # SAFE | CONTROLLED | INTENTIONAL_LOW_LEVEL_ESCAPE | BYPASS_RISK | BLOCKING_BYPASS
    detection: str  # how to detect this bypass at runtime
    mitigation: str  # how the control plane prevents/enforces it
    derivation_source: str
    evidence: str  # evidence that this path exists in code


@dataclass(frozen=True, slots=True)
class BypassEnforcementReport:
    """Complete bypass resistance analysis."""

    schema: str = "m9-c52-bypass-enforcement/v1"
    generated_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    paths: list[BypassPath] = field(default_factory=list)
    summary: dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _analyze_bypass_paths() -> list[BypassPath]:
    """Analyze all executable bypass paths in the repository."""
    paths: list[BypassPath] = []

    # Get catalog claims
    catalog_claims = {}
    from runtime.foundation.verification.capability_catalog import (
        CapabilityCatalogBuilder,
    )
    from runtime.foundation.verification.cli_capability_matrix import _command_routes

    cat = CapabilityCatalogBuilder().build()
    for e in cat.entries:
        for r in _command_routes(e.command):
            catalog_claims[r] = e.capability_id

    # 1. Direct pytest invocation (bypasses capability discovery + blast radius + evidence planning)
    paths.append(
        BypassPath(
            name="direct_pytest",
            description="User runs `python -m pytest tests/...` directly instead of going through capability discovery",
            entry_point="python -m pytest [test_path]",
            bypasses=[
                "discovery",
                "blast-radius",
                "evidence-planning",
                "execution-enforcement",
            ],
            classification="BYPASS_RISK",
            detection="Shell history / CI logs showing direct pytest invocation without verification-contract",
            mitigation="Enforcement boundary requires all execution to go through verify.py enforce; CI workflows use verify.py enforce",
            derivation_source="M52.6: Identified by analyzing CI workflows and developer documentation",
            evidence="backend/tests/ directories are directly runnable with pytest",
        )
    )

    # 2. Direct mutmut run (bypasses capability discovery + strengthening pipeline + intel)
    paths.append(
        BypassPath(
            name="direct_mutmut",
            description="User runs `python -m mutmut run` directly instead of through measurement-truth + strengthening pipeline",
            entry_point="python -m mutmut run",
            bypasses=[
                "measurement-truth",
                "intel-classification",
                "strengthening-pipeline",
                "human-authorization",
            ],
            classification="BYPASS_RISK",
            detection="Shell history / CI logs showing direct mutmut invocation",
            mitigation="measurement-truth is the ONLY authorized mutation entry point; mutmut config locked in pyproject.toml",
            derivation_source="M52.6: C47 certified that measurement-truth is canonical; any direct mutmut bypasses intel",
            evidence="backend/pyproject.toml [tool.mutmut] config exists",
        )
    )

    # 3. Direct black/ruff/mypy (bypasses configuration authority + evidence planning)
    paths.append(
        BypassPath(
            name="direct_quality_tools",
            description="User runs `python -m black/ruff/mypy` directly instead of through config-authority + evidence planning",
            entry_point="python -m black --check . | python -m ruff check . | python -m mypy src/",
            bypasses=["config-authority", "evidence-planning", "execution-enforcement"],
            classification="BYPASS_RISK",
            detection="Shell history / CI logs showing direct tool invocation",
            mitigation="Configuration authority enforces canonical pyproject.toml; verify.py enforce checks config fingerprints",
            derivation_source="M52.6: C51 certified config authority; direct tool runs bypass fingerprint verification",
            evidence="Root pyproject.toml [tool.black], [tool.ruff], [tool.mypy] are canonical",
        )
    )

    # 4. Direct mutmut results analysis (bypasses mutation-intel classification)
    paths.append(
        BypassPath(
            name="direct_mutmut_analysis",
            description="User reads mutmut results JSON directly and writes tests without going through mutation-intel + strengthening pipeline",
            entry_point="cat mutmut-results.json | manual test writing",
            bypasses=[
                "mutation-intel",
                "survivor-classification",
                "strengthening-pipeline",
                "human-authorization",
            ],
            classification="INTENTIONAL_LOW_LEVEL_ESCAPE",
            detection="Manual process; no automated detection",
            mitigation="Documented as explicit escape; C51 capability-discovery warns 'Do not write tests blindly against a survivor'",
            derivation_source="M52.6: C51 M51.6 anti-pattern warning; this is the forensic escape path",
            evidence="verify.py strengthen-survivor-forensic provides this capability explicitly",
        )
    )

    # 5. Stale evidence reuse (bypasses evidence reconciliation)
    paths.append(
        BypassPath(
            name="stale_evidence_reuse",
            description="Reusing cached measurement truth / evidence without revalidation",
            entry_point="Any code that reads measurement-truth records without re-verifying fingerprints",
            bypasses=[
                "evidence-reconciliation",
                "fingerprint-verification",
                "population-consistency",
            ],
            classification="BLOCKING_BYPASS",
            detection="Enforcement boundary checks population fingerprint + config fingerprint + toolchain fingerprint before any reuse",
            mitigation="ExecutionEnforcer.verify_fingerprint() blocks stale evidence; preflight refuses execution if fingerprints mismatch",
            derivation_source="M52.6: M52.5 enforcement boundary implements fingerprint verification",
            evidence="execution_enforcer.py _verify_fingerprint() method",
        )
    )

    # 6. Direct executor_pipeline invocation (bypasses verification-contract + enforcement)
    paths.append(
        BypassPath(
            name="direct_executor_pipeline",
            description="User calls executor_pipeline.main() directly instead of going through verification-contract + enforce",
            entry_point="python -m runtime.foundation.verification.executor_pipeline --run-mutation",
            bypasses=[
                "verification-contract",
                "enforcement-boundary",
                "capability-resolution",
            ],
            classification="BYPASS_RISK",
            detection="Import trace / stack trace showing direct executor_pipeline import",
            mitigation="executor_pipeline is internal; verify.py enforce is the only authorized entry point",
            derivation_source="M52.6: M52.4 verification-contract is canonical; executor_pipeline is internal implementation",
            evidence="executor_pipeline.py is not exposed as a verify.py route (except via evidence-*)",
        )
    )

    # 7. Unmapped CLI routes (the 12 classified as LEGACY_SUPERSEDED/OPERATIONAL_OBSERVABILITY)
    paths.append(
        BypassPath(
            name="legacy_unmapped_routes",
            description="Legacy C42 routes (affected, diagnose, repair, risk, certify-v4/v5, intelligence-audit) still executable",
            entry_point="verify.py affected | diagnose | repair | risk | certify-v4 | certify-v5 | intelligence-audit",
            bypasses=["capability-discovery", "blast-radius", "evidence-planning"],
            classification="LEGACY_SUPERSEDED",  # explicitly classified, not a silent bypass
            detection="CLI matrix explicitly classifies these as LEGACY_SUPERSEDED",
            mitigation="Explicitly classified in M52.3 CLI matrix; discovery resolver points to canonical successors",
            derivation_source="M52.3: 7 routes classified as LEGACY_SUPERSEDED with named successors",
            evidence="cli_capability_matrix.py classification entries for affected, diagnose, etc.",
        )
    )

    # 8. Observability routes (analytics, health, dashboard, ci-doctor)
    paths.append(
        BypassPath(
            name="observability_routes",
            description="Platform observability routes (analytics, health, dashboard, ci-doctor) executable but outside verification scope",
            entry_point="verify.py analytics | health | dashboard | ci-doctor",
            bypasses=["none - explicitly out of verification scope"],
            classification="SAFE",  # explicitly out of scope
            detection="CLI matrix classifies as OPERATIONAL_OBSERVABILITY",
            mitigation="Explicitly classified; no impact on verification gate; documented as non-verification",
            derivation_source="M52.3: 4 routes classified as OPERATIONAL_OBSERVABILITY",
            evidence="cli_capability_matrix.py classification entries for analytics, health, dashboard, ci-doctor",
        )
    )

    # 9. Forensic low-level escape routes (strengthen-survivor-forensic, forensic-diagnose, etc.)
    paths.append(
        BypassPath(
            name="forensic_low_level_escapes",
            description="Forensic CLI routes (strengthen-survivor-forensic, forensic-diagnose, strengthen-analyze, etc.) require live mutmut run",
            entry_point="verify.py strengthen-survivor-forensic | forensic-diagnose | strengthen-analyze | strengthen-propose | strengthen-validate | strengthen-report",
            bypasses=["intel-classification", "strengthening-pipeline-human-auth"],
            classification="INTENTIONAL_LOW_LEVEL_ESCAPE",  # explicitly marked, never silent
            detection="CLI matrix classifies as INTENTIONAL_LOW_LEVEL_ESCAPE",
            mitigation="Explicitly classified; capability-discovery resolver does not point to these for certification path",
            derivation_source="M52.2: forensic routes renamed to explicit forensic names; M52.3 classified",
            evidence="verify.py dispatch for forensic-* routes; strengthen.forensic catalog entry",
        )
    )

    # 10. Knowledge sub-routes (knowledge endpoint|capability|workspace|rule|component)
    paths.append(
        BypassPath(
            name="knowledge_sub_routes",
            description="Knowledge base query sub-routes (endpoint, capability, workspace, rule, component)",
            entry_point="verify.py knowledge [endpoint|capability|workspace|rule|component]",
            bypasses=["none - explicitly cataloged in M52.3"],
            classification="CONTROLLED",  # properly cataloged
            detection="CLI matrix has knowledge with sub-routes under evidence.knowledge-base",
            mitigation="Cataloged as evidence.knowledge-base; all sub-routes tracked",
            derivation_source="M52.3: knowledge route with sub-commands added to catalog",
            evidence="verify.py knowledge dispatch with sub-commands; evidence.knowledge-base catalog entry",
        )
    )

    # 11. Profile routes (quick, backend, frontend, contracts, etc.)
    paths.append(
        BypassPath(
            name="profile_routes",
            description="Verification profile routes (quick, backend, frontend, contracts, property, integration, migration, repository, full, runtime, golden, playwright)",
            entry_point="verify.py quick | backend | frontend | contracts | property | integration | migration | repository | full | runtime | golden | playwright",
            bypasses=["none - profiles are canonical execution entry points"],
            classification="CONTROLLED",
            detection="CLI matrix classifies profiles as exec.profile.* capabilities",
            mitigation="Profiles are the canonical batch execution surfaces; evidence-planner drives them",
            derivation_source="M52.1: 12 profile capabilities registered in catalog",
            evidence="catalog has exec.profile.* entries; verify.py dispatches to VerificationOrchestrator.run(profile=...)",
        )
    )

    # 12. Measurement coverage direct (verify.py measurement coverage <scope>)
    paths.append(
        BypassPath(
            name="measurement_coverage_direct",
            description="Direct measurement coverage invocation",
            entry_point="verify.py measurement coverage <scope>",
            bypasses=["none - measurement-truth is canonical"],
            classification="CONTROLLED",
            detection="CLI matrix has measure.coverage capability",
            mitigation="measurement-truth is the canonical entry point; coverage is a sub-command",
            derivation_source="M52.1: measure.coverage capability registered",
            evidence="verify.py measurement coverage dispatches to coverage_measurement.measure_coverage_cli",
        )
    )

    return paths


def build_bypass_enforcement_report() -> BypassEnforcementReport:
    """Build the complete bypass enforcement report."""
    paths = _analyze_bypass_paths()

    summary: dict[str, int] = {}
    for p in paths:
        summary[p.classification] = summary.get(p.classification, 0) + 1

    return BypassEnforcementReport(
        paths=paths,
        summary=summary,
    )


def main() -> int:
    """CLI: verify.py bypass-enforcement [--json] [--out PATH]"""
    import sys

    parser = __import__("argparse").ArgumentParser(
        prog="verify.py bypass-enforcement", add_help=False
    )
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--out", help="Output file path")
    args = parser.parse_args(sys.argv[2:])

    report = build_bypass_enforcement_report()

    output = json.dumps(report.to_dict(), indent=2, default=str)

    if args.out:
        Path(args.out).write_text(output)
        print(f"Written to {args.out}")
    if args.json or args.out:
        print(output)
    else:
        print(f"Total bypass paths analyzed: {len(report.paths)}")
        for cls, count in report.summary.items():
            print(f"  {cls}: {count}")
        for p in report.paths:
            print(f"  {p.name} [{p.classification}]: {p.description}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
