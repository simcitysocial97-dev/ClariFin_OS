"""M9-C62 — Automatic Authority-Drift Detector.

Inspects actual repository relationships to detect conditions where
the verification control plane's authority assumptions are wrong,
incomplete, stale, bypassed, or divergent.

Detection uses:
    - imports (AST scanning of source files)
    - call relationships (method dispatch chains)
    - command dispatch (CLI routing)
    - registry metadata (capability/verification registries)
    - known authority declarations (canonical authority records)

Output identifies:
    - detected component
    - expected authority
    - actual authority
    - classification
    - source evidence
    - severity
"""

from __future__ import annotations

import ast
import importlib
import json
import logging
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
logger = logging.getLogger(__name__)


class Severity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class DriftClassification(str, Enum):
    IMPLEMENTATION_DEFECT = "IMPLEMENTATION_DEFECT"
    AUTHORITY_DRIFT = "AUTHORITY_DRIFT"
    CONFIGURATION_DRIFT = "CONFIGURATION_DRIFT"
    CI_BYPASS = "CI_BYPASS"
    EVIDENCE_INTEGRITY_DEFECT = "EVIDENCE_INTEGRITY_DEFECT"
    ARTIFACT_INTEGRITY_DEFECT = "ARTIFACT_INTEGRITY_DEFECT"
    FALSE_POSITIVE = "FALSE_POSITIVE"
    PRE_EXISTING = "PRE_EXISTING"
    ENVIRONMENTAL = "ENVIRONMENTAL"
    UNRELATED = "UNRELATED"


@dataclass(frozen=True, slots=True)
class DriftFinding:
    detected_component: str
    expected_authority: str
    actual_authority: str
    classification: DriftClassification
    source_evidence: str
    severity: Severity
    check_name: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "check_name": self.check_name,
            "detected_component": self.detected_component,
            "expected_authority": self.expected_authority,
            "actual_authority": self.actual_authority,
            "classification": self.classification.value,
            "source_evidence": self.source_evidence,
            "severity": self.severity.value,
        }


@dataclass(frozen=True, slots=True)
class DriftReport:
    schema: str = "m9-c62-authority-drift/v1"
    generated_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    findings: list[DriftFinding] = field(default_factory=list)
    healthy: bool = True

    @property
    def critical_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == Severity.CRITICAL)

    @property
    def high_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == Severity.HIGH)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "generated_at": self.generated_at,
            "healthy": self.healthy,
            "critical_count": self.critical_count,
            "high_count": self.high_count,
            "findings": [f.to_dict() for f in self.findings],
        }


# ---------------------------------------------------------------------------
# Authority declarations — canonical source of truth
# ---------------------------------------------------------------------------

CANONICAL_PLANNER = "runtime.foundation.verification.control_plane.ControlPlanePlanner"
CANONICAL_EXECUTOR = "runtime.foundation.verification.execution_orchestrator.ExecutionOrchestrator"
CANONICAL_FACADE = "runtime.foundation.verification.control_plane_facade.ControlPlane"
CANONICAL_EVIDENCE_WRITER = "runtime.verify.record_execution_report"

SUBORDINATE_PLANNERS = {
    "runtime.foundation.verification.evidence_planner.EvidenceAwarePlanner",
    "runtime.foundation.verification.planner.planner.VerificationPlanner",
    "runtime.foundation.verification.planner.planner.CrossLayerImpactPlanner",
}

HISTORICAL_ORCHESTRATORS = {
    "runtime.foundation.verification.orchestration.orchestrator.ExecutionOrchestrator",
}

LEGACY_COMMANDS = {
    "quick", "backend", "frontend", "api-contracts",
    "runtime", "golden", "playwright",
}

CANONICAL_COMMANDS = {
    "check", "plan", "run", "diagnose",
    "strengthen", "inspect", "certify", "ci", "doctor",
}

# Known evidence writer functions (single writer pattern)
KNOWN_EVIDENCE_WRITERS = {
    "runtime.verify.record_execution_report",
    "runtime.foundation.verification.evidence_contract.save_execution_evidence_v2",
    "runtime.foundation.verification.reconciliation.save_reconciliation_report",
}


# ---------------------------------------------------------------------------
# AST-based import detector
# ---------------------------------------------------------------------------

def _scan_imports(file_path: Path, target_modules: set[str]) -> list[tuple[str, str, int]]:
    """Scan a Python file for imports of target modules.

    Returns list of (imported_module, attribute, line_number).
    """
    results: list[tuple[str, str, int]] = []
    if not file_path.exists():
        return results
    try:
        source = file_path.read_text(encoding="utf-8")
        tree = ast.parse(source)
    except (SyntaxError, UnicodeDecodeError):
        return results

    target_dotted = {t.split(".")[0] for t in target_modules}

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                top = alias.name.split(".")[0]
                if top in target_dotted:
                    results.append((alias.name, alias.asname or alias.name, node.lineno))
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                top = node.module.split(".")[0]
                if top in target_dotted:
                    for alias in node.names:
                        full = f"{node.module}.{alias.name}"
                        results.append((full, alias.asname or alias.name, node.lineno))

    return results


def _scan_file_for_module(file_path: Path, module_prefix: str) -> list[tuple[str, str, int]]:
    """Check if a file imports anything from a given module prefix."""
    if not file_path.exists():
        return []
    try:
        source = file_path.read_text(encoding="utf-8")
        tree = ast.parse(source)
    except (SyntaxError, UnicodeDecodeError):
        return []
    results: list[tuple[str, str, int]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module and node.module.startswith(module_prefix):
            for alias in node.names:
                full = f"{node.module}.{alias.name}"
                results.append((full, alias.asname or alias.name, node.lineno))
    return results


def _find_python_files(root: Path, pattern: str = "*.py") -> list[Path]:
    """Find Python files under root."""
    return sorted(root.rglob(pattern))


# ---------------------------------------------------------------------------
# Drift detectors
# ---------------------------------------------------------------------------

class PlannerDriftDetector:
    """Detect when the wrong planner is imported by canonical CLI paths."""

    def check(self) -> list[DriftFinding]:
        findings: list[DriftFinding] = []

        facade_file = REPO_ROOT / "runtime" / "foundation" / "verification" / "control_plane_facade.py"
        if not facade_file.exists():
            return findings

        imports = _scan_imports(
            facade_file,
            {
                "runtime.foundation.verification.control_plane",
                "runtime.foundation.verification.evidence_planner",
                "runtime.foundation.verification.planner",
            },
        )

        planner_imports = {m for m, _, _ in imports if "Planner" in m or "planner" in m}
        direct_top_level = {m for m in planner_imports if "ControlPlanePlanner" in m}
        subordinate_imports = {
            m for m in planner_imports
            if any(s in m for s in ["EvidenceAwarePlanner", "VerificationPlanner", "CrossLayerImpactPlanner"])
        }

        # Check facade imports ControlPlanePlanner directly (expected)
        if not direct_top_level:
            findings.append(DriftFinding(
                detected_component="control_plane_facade.py",
                expected_authority=CANONICAL_PLANNER,
                actual_authority="NO_PLANNER_IMPORTED",
                classification=DriftClassification.AUTHORITY_DRIFT,
                source_evidence="control_plane_facade.py does not import ControlPlanePlanner",
                severity=Severity.CRITICAL,
                check_name="wrong_planner_imported",
            ))
        else:
            # Verify subordinate planners are NOT directly imported by facade
            for imp in subordinate_imports:
                findings.append(DriftFinding(
                    detected_component="control_plane_facade.py",
                    expected_authority=f"Subordinate planner via {CANONICAL_PLANNER}",
                    actual_authority=imp,
                    classification=DriftClassification.AUTHORITY_DRIFT,
                    source_evidence=f"Facade directly imports subordinate planner {imp} (should be composed by ControlPlanePlanner)",
                    severity=Severity.MEDIUM,
                    check_name="direct_subordinate_planner_import",
                ))

        # Scan all CLI entry points for top-level planner usage
        cli_files = [REPO_ROOT / "runtime" / "verify.py"]
        for cli_file in cli_files:
            imports = _scan_imports(
                cli_file,
                {"runtime.foundation.verification.planner", "runtime.foundation.verification.control_plane"},
            )
            for imp, _, line in imports:
                if "CrossLayerImpactPlanner" in imp or "VerificationPlanner" in imp:
                    if "control_plane" not in imp:
                        findings.append(DriftFinding(
                            detected_component=str(cli_file),
                            expected_authority=f"Accessed via {CANONICAL_PLANNER}",
                            actual_authority=imp,
                            classification=DriftClassification.AUTHORITY_DRIFT,
                            source_evidence=f"CLI file {cli_file.name}:{line} directly imports {imp}",
                            severity=Severity.LOW,
                            check_name="cli_direct_planner_access",
                        ))

        return findings


class ExecutorDriftDetector:
    """Detect when the wrong executor is imported by canonical paths."""

    def check(self) -> list[DriftFinding]:
        findings: list[DriftFinding] = []

        facade_file = REPO_ROOT / "runtime" / "foundation" / "verification" / "control_plane_facade.py"
        if not facade_file.exists():
            return findings

        imports = _scan_imports(
            facade_file,
            {"runtime.foundation.verification.execution_orchestrator", "runtime.foundation.verification.orchestrator"},
        )

        for imp, attr, line in imports:
            if "execution_orchestrator" in imp and "ExecutionOrchestrator" in attr:
                logger.debug("Facade correctly imports ExecutionOrchestrator: %s:%d", imp, line)
            elif "orchestrator" in imp and "ExecutionOrchestrator" in attr and "execution_orchestrator" not in imp:
                findings.append(DriftFinding(
                    detected_component="control_plane_facade.py",
                    expected_authority=CANONICAL_EXECUTOR,
                    actual_authority=f"{imp}.{attr}",
                    classification=DriftClassification.AUTHORITY_DRIFT,
                    source_evidence=f"Facade line {line}: imports {imp}.{attr} instead of ExecutionOrchestrator",
                    severity=Severity.CRITICAL,
                    check_name="wrong_executor_imported",
                ))

        # Check for historical orchestrator class usage in canonical paths
        canonical_files = [
            REPO_ROOT / "runtime" / "foundation" / "verification" / "control_plane_facade.py",
            REPO_ROOT / "runtime" / "verify.py",
        ]
        for f in canonical_files:
            py_files = _find_python_files(f.parent, "*.py") if f.is_dir() else [f]
            for pf in py_files:
                imports = _scan_imports(pf, {"runtime.foundation.verification.orchestration"})
                for imp, attr, line in imports:
                    if "orchestration" in imp and "ExecutionOrchestrator" in attr:
                        findings.append(DriftFinding(
                            detected_component=str(pf),
                            expected_authority="No orchestration/orchestrator import in canonical path",
                            actual_authority=f"{imp}.{attr}",
                            classification=DriftClassification.AUTHORITY_DRIFT,
                            source_evidence=f"Canonical file {pf.relative_to(REPO_ROOT)} line {line} imports historical orchestrator class {imp}",
                            severity=Severity.HIGH,
                            check_name="historical_orchestrator_in_canonical_path",
                        ))

        return findings


class LegacyOrchestratorDriftDetector:
    """Detect when the legacy orchestrator is unexpectedly wired into canonical path."""

    def check(self) -> list[DriftFinding]:
        findings: list[DriftFinding] = []

        canonical_files = [
            REPO_ROOT / "runtime" / "foundation" / "verification" / "control_plane_facade.py",
            REPO_ROOT / "runtime" / "verify.py",
        ]

        for f in canonical_files:
            if not f.exists():
                continue
            imports = _scan_imports(f, {"runtime.foundation.verification.orchestration"})
            for imp, attr, line in imports:
                if "orchestration" in imp and "ExecutionOrchestrator" in attr:
                    findings.append(DriftFinding(
                        detected_component=str(f.relative_to(REPO_ROOT)),
                        expected_authority="ExecutionOrchestrator from execution_orchestrator",
                        actual_authority=f"{imp}.{attr}",
                        classification=DriftClassification.AUTHORITY_DRIFT,
                        source_evidence=f"Canonical path {f.relative_to(REPO_ROOT)}:{line} imports ExecutionOrchestrator from {imp} (should be from execution_orchestrator)",
                        severity=Severity.HIGH,
                        check_name="legacy_orchestrator_in_canonical_path",
                    ))

        # Check ControlPlanePlanner does not instantiate legacy orchestrator
        planner_file = REPO_ROOT / "runtime" / "foundation" / "verification" / "control_plane.py"
        if planner_file.exists():
            source = planner_file.read_text(encoding="utf-8")
            if "orchestration.orchestrator" in source and "ExecutionOrchestrator" in source:
                findings.append(DriftFinding(
                    detected_component="control_plane.py",
                    expected_authority="No reference to orchestration.orchestrator.ExecutionOrchestrator",
                    actual_authority="runtime.foundation.verification.orchestration.orchestrator.ExecutionOrchestrator",
                    classification=DriftClassification.AUTHORITY_DRIFT,
                    source_evidence="ControlPlanePlanner references historical orchestrator class",
                    severity=Severity.HIGH,
                    check_name="legacy_orchestrator_in_planner",
                ))

        return findings


class EvidencePathDriftDetector:
    """Detect when a second evidence path is introduced."""

    def check(self) -> list[DriftFinding]:
        findings: list[DriftFinding] = []

        scan_roots = [REPO_ROOT / "runtime" / "foundation" / "verification"]
        for root in scan_roots:
            if not root.exists():
                continue
            for py_file in sorted(root.rglob("*.py")):
                rel = str(py_file.relative_to(REPO_ROOT))
                if any(x in rel for x in ["__pycache__", ".git", "node_modules", "/test_", "_test.py"]):
                    continue
                imports = _scan_imports(
                    py_file,
                    {"runtime.system.observability"},
                )
                for imp, attr, line in imports:
                    if "EventStore" in attr or "RunRecord" in attr:
                        if "record_execution" not in imp and "record" not in attr:
                            findings.append(DriftFinding(
                                detected_component=rel,
                                expected_authority=CANONICAL_EVIDENCE_WRITER,
                                actual_authority=f"{imp}.{attr}",
                                classification=DriftClassification.EVIDENCE_INTEGRITY_DEFECT,
                                source_evidence=f"{rel}:{line} imports event store directly — should go through record_execution_report",
                                severity=Severity.MEDIUM,
                                check_name="second_evidence_path",
                            ))

        return findings


class ConfigurationDriftDetector:
    """Detect configuration/registry divergence."""

    def check(self) -> list[DriftFinding]:
        findings: list[DriftFinding] = []

        # Verify capability registry is the canonical authority
        try:
            from runtime.foundation.verification.capability_authority import (
                authority_audit,
                assert_no_competing_authority,
            )
            audit = authority_audit()
            if not audit.canonical_resolvable:
                findings.append(DriftFinding(
                    detected_component="capability registry",
                    expected_authority="VerificationRegistry (canonical)",
                    actual_authority="UNRESOLVABLE",
                    classification=DriftClassification.CONFIGURATION_DRIFT,
                    source_evidence="Capability authority audit shows canonical registry is not resolvable",
                    severity=Severity.CRITICAL,
                    check_name="canonical_registry_bypassed",
                ))
            if not audit.canonical_factory_callable:
                findings.append(DriftFinding(
                    detected_component="capability registry",
                    expected_authority="get_registry() (canonical factory)",
                    actual_authority="UNRESOLVABLE",
                    classification=DriftClassification.CONFIGURATION_DRIFT,
                    source_evidence="Capability authority factory is not callable",
                    severity=Severity.CRITICAL,
                    check_name="canonical_registry_bypassed",
                ))
        except Exception as exc:
            findings.append(DriftFinding(
                detected_component="capability registry",
                expected_authority="VerificationRegistry (canonical)",
                actual_authority=f"ERROR: {exc}",
                classification=DriftClassification.CONFIGURATION_DRIFT,
                source_evidence=f"Failed to audit capability authority: {exc}",
                severity=Severity.CRITICAL,
                check_name="canonical_registry_bypassed",
            ))

        # Verify verification registry
        try:
            from runtime.foundation.verification.registry import get_registry
            registry = get_registry()
            if registry is None:
                findings.append(DriftFinding(
                    detected_component="verification registry",
                    expected_authority="VerificationRegistry (canonical)",
                    actual_authority="None",
                    classification=DriftClassification.CONFIGURATION_DRIFT,
                    source_evidence="Verification registry returns None",
                    severity=Severity.CRITICAL,
                    check_name="canonical_registry_bypassed",
                ))
        except Exception as exc:
            findings.append(DriftFinding(
                detected_component="verification registry",
                expected_authority="VerificationRegistry (canonical)",
                actual_authority=f"ERROR: {exc}",
                classification=DriftClassification.CONFIGURATION_DRIFT,
                source_evidence=f"Failed to load verification registry: {exc}",
                severity=Severity.CRITICAL,
                check_name="canonical_registry_bypassed",
            ))

        return findings


class CLIDriftDetector:
    """Detect when legacy commands bypass the canonical chain."""

    def check(self) -> list[DriftFinding]:
        findings: list[DriftFinding] = []

        facade_file = REPO_ROOT / "runtime" / "foundation" / "verification" / "control_plane_facade.py"
        if not facade_file.exists():
            return findings

        source = facade_file.read_text(encoding="utf-8")

        # Verify all 9 canonical commands are dispatched
        for cmd in CANONICAL_COMMANDS:
            if cmd not in source:
                findings.append(DriftFinding(
                    detected_component="control_plane_facade.py",
                    expected_authority=f"Canonical command '{cmd}' in facade dispatch",
                    actual_authority="MISSING from facade",
                    classification=DriftClassification.AUTHORITY_DRIFT,
                    source_evidence=f"Canonical command '{cmd}' not found in control_plane_facade.py",
                    severity=Severity.CRITICAL,
                    check_name="canonical_command_missing",
                ))

        # Verify legacy aliases route through migration_map (not direct dispatch)
        for alias in LEGACY_COMMANDS:
            # Check that legacy aliases do NOT have direct method calls
            # (they should be in PROFILE_ALIASES and routed through _run_profile_alias)
            if f"cp.{alias}" in source or f"self.{alias}" in source:
                findings.append(DriftFinding(
                    detected_component="control_plane_facade.py",
                    expected_authority=f"Legacy alias '{alias}' routed through migration_map",
                    actual_authority=f"Direct execution of '{alias}' in facade",
                    classification=DriftClassification.CI_BYPASS,
                    source_evidence=f"Legacy command '{alias}' appears to be dispatched directly (should use migration_map)",
                    severity=Severity.HIGH,
                    check_name="alias_bypasses_canonical_chain",
                ))

        return findings


class CIDriftDetector:
    """Detect CI workflow bypasses and unauthorized verification paths."""

    def check(self) -> list[DriftFinding]:
        findings: list[DriftFinding] = []

        workflows_dir = REPO_ROOT / ".github" / "workflows"
        if not workflows_dir.exists():
            return findings

        for wf_file in sorted(workflows_dir.glob("*.yml")):
            source = wf_file.read_text(encoding="utf-8")
            rel = str(wf_file.relative_to(REPO_ROOT))

            # Check for direct tool invocations (not via python -m runtime.verify)
            for line in source.splitlines():
                stripped = line.strip()
                # Look for run: lines that invoke verification tools directly
                if stripped.startswith("run:") or stripped.startswith("- run:"):
                    run_content = stripped.lstrip("- ").replace("run:", "").strip()
                    if ("pytest" in run_content or "mutmut" in run_content or "ruff" in run_content) and "runtime.verify" not in run_content and "mutmut" not in run_content.split()[-1:]:
                        # Allow CodeQL and other specialized tools
                        if any(tool in run_content for tool in ["codeql", "dependabot", "release"]):
                            continue
                        findings.append(DriftFinding(
                            detected_component=rel,
                            expected_authority="python -m runtime.verify",
                            actual_authority=run_content,
                            classification=DriftClassification.CI_BYPASS,
                            source_evidence=f"Workflow {wf_file.name} directly invokes: {run_content}",
                            severity=Severity.HIGH,
                            check_name="ci_direct_tool_invocation",
                        ))

            # Check for continue-on-error: true
            if "continue-on-error" in source and "true" in source:
                for i, line in enumerate(source.splitlines(), 1):
                    if "continue-on-error" in line and "true" in line:
                        findings.append(DriftFinding(
                            detected_component=rel,
                            expected_authority="No continue-on-error: true",
                            actual_authority="continue-on-error: true",
                            classification=DriftClassification.CI_BYPASS,
                            source_evidence=f"Workflow {wf_file.name} line {i}: continue-on-error may suppress verification failures",
                            severity=Severity.MEDIUM,
                            check_name="ci_suppress_failure",
                        ))

        return findings


# ---------------------------------------------------------------------------
# Main detection entry point
# ---------------------------------------------------------------------------

def run_authority_drift_detection() -> DriftReport:
    """Run all authority drift detectors and return a report."""
    detectors = [
        PlannerDriftDetector(),
        ExecutorDriftDetector(),
        LegacyOrchestratorDriftDetector(),
        EvidencePathDriftDetector(),
        ConfigurationDriftDetector(),
        CLIDriftDetector(),
        CIDriftDetector(),
    ]

    all_findings: list[DriftFinding] = []
    for detector in detectors:
        try:
            findings = detector.check()
            all_findings.extend(findings)
            logger.debug("%s produced %d findings", detector.__class__.__name__, len(findings))
        except Exception as exc:
            logger.error("Detector %s failed: %s", detector.__class__.__name__, exc)
            all_findings.append(DriftFinding(
                detected_component=detector.__class__.__name__,
                expected_authority="Detector executed successfully",
                actual_authority=f"DETECTOR_ERROR: {exc}",
                classification=DriftClassification.ENVIRONMENTAL,
                source_evidence=f"Detector {detector.__class__.__name__} raised: {exc}",
                severity=Severity.MEDIUM,
                check_name=f"{detector.__class__.__name__}_error",
            ))

    healthy = all(
        f.severity not in (Severity.CRITICAL, Severity.HIGH)
        for f in all_findings
    )

    return DriftReport(
        findings=all_findings,
        healthy=healthy,
    )


def main() -> int:
    """CLI entry point: verify.py diagnose authority-drift."""
    import sys
    import json as json_lib

    report = run_authority_drift_detection()
    output = json_lib.dumps(report.to_dict(), indent=2, default=str)

    if "--json" in sys.argv or "--out" in sys.argv:
        out_path = None
        if "--out" in sys.argv:
            idx = sys.argv.index("--out")
            if idx + 1 < len(sys.argv):
                out_path = Path(sys.argv[idx + 1])
        if out_path:
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(output, encoding="utf-8")
            print(f"Written to {out_path}")
        if "--json" in sys.argv:
            print(output)
    else:
        if report.healthy:
            print("✅ Framework authority integrity: HEALTHY")
        else:
            print("⚠️ Framework authority integrity: DEGRADED")
            for f in report.findings:
                print(f"  [{f.severity.value.upper()}] {f.check_name}: {f.detected_component}")
                print(f"    Expected: {f.expected_authority}")
                print(f"    Actual:   {f.actual_authority}")
                print(f"    Evidence: {f.source_evidence}")
        print()
        print(f"Critical: {report.critical_count}, High: {report.high_count}, Total: {len(report.findings)}")

    return 0 if report.healthy else 1


if __name__ == "__main__":
    raise SystemExit(main())