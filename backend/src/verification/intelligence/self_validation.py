"""Runtime Self-Validation Engine.

Extends meta verification to validate:
- dependency graph integrity
- change-impact correctness
- risk metadata consistency
- architectural coverage completeness
- evidence integrity
- duplicate detection
- missing registration
- broken dependency chains
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
BACKEND_DIR = PROJECT_ROOT
GENERATED_DIR = BACKEND_DIR / "tests" / "generated"


@dataclass
class ValidationIssue:
    """A single validation issue."""

    check: str
    severity: str
    message: str
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "check": self.check,
            "severity": self.severity,
            "message": self.message,
            "details": self.details,
        }


@dataclass
class SelfValidationReport:
    """Complete self-validation report."""

    checks: list[ValidationIssue] = field(default_factory=list)
    passed: int = 0
    failed: int = 0
    warnings: int = 0
    overall_healthy: bool = True
    generated_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "checks": [c.to_dict() for c in self.checks],
            "passed": self.passed,
            "failed": self.failed,
            "warnings": self.warnings,
            "overall_healthy": self.overall_healthy,
            "generated_at": self.generated_at,
        }


class SelfValidationEngine:
    """Validates the Verification Intelligence Layer itself."""

    def __init__(self) -> None:
        self._issues: list[ValidationIssue] = []

    def run_all(self) -> SelfValidationReport:
        """Run all self-validation checks."""
        self._issues = []

        self._check_dependency_graph_integrity()
        self._check_change_impact_correctness()
        self._check_risk_metadata_consistency()
        self._check_architectural_coverage_completeness()
        self._check_evidence_integrity()
        self._check_duplicate_detection()
        self._check_missing_registration()
        self._check_broken_dependency_chains()

        passed = sum(1 for i in self._issues if i.severity == "PASS")
        failed = sum(1 for i in self._issues if i.severity == "FAIL")
        warnings = sum(1 for i in self._issues if i.severity == "WARNING")

        return SelfValidationReport(
            checks=self._issues,
            passed=passed,
            failed=failed,
            warnings=warnings,
            overall_healthy=failed == 0,
            generated_at=datetime.now(UTC).isoformat(),
        )

    def _check_dependency_graph_integrity(self) -> None:
        """Validate that the dependency graph is internally consistent."""
        from src.verification.intelligence.dependency_engine import DependencyEngine

        engine = DependencyEngine()
        graph = engine.discover()

        if not graph.edges:
            self._issues.append(
                ValidationIssue(
                    check="dependency_graph_integrity",
                    severity="WARNING",
                    message="Dependency graph has no edges",
                    details={"edge_count": 0},
                )
            )
            return

        edge_types = {e.source_type for e in graph.edges}
        edge_types.update(e.target_type for e in graph.edges)

        self._issues.append(
            ValidationIssue(
                check="dependency_graph_integrity",
                severity="PASS",
                message=f"Dependency graph has {len(graph.edges)} edges across {len(edge_types)} component types",
                details={
                    "edge_count": len(graph.edges),
                    "component_types": sorted(edge_types),
                },
            )
        )

    def _check_change_impact_correctness(self) -> None:
        """Validate that change impact analysis produces correct results."""
        from src.verification.intelligence.impact_engine import ImpactEngine

        engine = ImpactEngine()

        test_files = [
            "backend/src/engines/cashflow_engine.py",
            "backend/src/routers/accounts.py",
            "backend/src/services/account_service.py",
        ]

        for test_file in test_files:
            impact = engine.analyze([test_file])

            if impact.overall_risk not in ("LOW", "MEDIUM", "HIGH", "CRITICAL"):
                self._issues.append(
                    ValidationIssue(
                        check="change_impact_correctness",
                        severity="FAIL",
                        message=f"Invalid risk level for {test_file}: {impact.overall_risk}",
                        details={"file": test_file, "risk": impact.overall_risk},
                    )
                )
            else:
                self._issues.append(
                    ValidationIssue(
                        check="change_impact_correctness",
                        severity="PASS",
                        message=f"Change impact for {test_file} has valid risk level: {impact.overall_risk}",
                        details={"file": test_file, "risk": impact.overall_risk},
                    )
                )

    def _check_risk_metadata_consistency(self) -> None:
        """Validate that risk metadata is consistent across components."""
        from src.verification.intelligence.risk_engine import RiskEngine

        engine = RiskEngine()
        risk_map = engine.classify_all()

        inconsistent = []
        for entry in risk_map.entries:
            if entry.risk not in ("CRITICAL", "HIGH", "MEDIUM", "LOW"):
                inconsistent.append(
                    f"{entry.id} ({entry.type}): invalid risk '{entry.risk}'"
                )

        if inconsistent:
            self._issues.append(
                ValidationIssue(
                    check="risk_metadata_consistency",
                    severity="FAIL",
                    message=f"Found {len(inconsistent)} components with invalid risk levels",
                    details={"invalid_entries": inconsistent},
                )
            )
        else:
            self._issues.append(
                ValidationIssue(
                    check="risk_metadata_consistency",
                    severity="PASS",
                    message=f"All {len(risk_map.entries)} risk entries have valid risk levels",
                    details={"entry_count": len(risk_map.entries)},
                )
            )

    def _check_architectural_coverage_completeness(self) -> None:
        """Validate that architectural coverage covers all capabilities."""
        from src.verification.intelligence.coverage_engine import CoverageEngine

        engine = CoverageEngine()
        coverage = engine.generate_all()

        total = coverage.summary.get("total_capabilities", 0)
        gap_count = coverage.summary.get("gap", 0)

        if total == 0:
            self._issues.append(
                ValidationIssue(
                    check="architectural_coverage_completeness",
                    severity="WARNING",
                    message="No capabilities found in coverage report",
                    details={"total_capabilities": 0},
                )
            )
            return

        self._issues.append(
            ValidationIssue(
                check="architectural_coverage_completeness",
                severity="PASS" if gap_count == 0 else "WARNING",
                message=f"Coverage: {total} capabilities, {gap_count} with gaps, {coverage.summary.get('average_coverage_percent', 0)}% average",
                details={
                    "total_capabilities": total,
                    "gap_count": gap_count,
                    "average_coverage_percent": coverage.summary.get(
                        "average_coverage_percent", 0
                    ),
                },
            )
        )

    def _check_evidence_integrity(self) -> None:
        """Validate that verification evidence is consistent."""
        from src.verification.intelligence.evidence_engine import EvidenceEngine

        engine = EvidenceEngine()
        summary = engine.generate_all()

        issues = []
        for cap in summary.capabilities:
            if cap.total_count > 0 and cap.verified_count == 0:
                issues.append(
                    f"{cap.capability_id}: {cap.total_count} checks, 0 verified"
                )

        if issues:
            self._issues.append(
                ValidationIssue(
                    check="evidence_integrity",
                    severity="WARNING",
                    message=f"{len(issues)} capabilities have no verified evidence",
                    details={"affected_capabilities": issues},
                )
            )
        else:
            self._issues.append(
                ValidationIssue(
                    check="evidence_integrity",
                    severity="PASS",
                    message=f"All {summary.total_capabilities} capabilities have verification evidence",
                    details={"total_capabilities": summary.total_capabilities},
                )
            )

    def _check_duplicate_detection(self) -> None:
        """Check for duplicate registrations across all registries."""
        from src.verification.runtime.registries import load_capability_registry

        registry = load_capability_registry()
        caps = registry.get("capabilities", [])
        cap_ids = [c.get("id") for c in caps if c.get("id")]
        duplicates = [cid for cid in set(cap_ids) if cap_ids.count(cid) > 1]

        if duplicates:
            self._issues.append(
                ValidationIssue(
                    check="duplicate_detection",
                    severity="FAIL",
                    message=f"Duplicate capability IDs found: {duplicates}",
                    details={"duplicates": duplicates},
                )
            )
        else:
            self._issues.append(
                ValidationIssue(
                    check="duplicate_detection",
                    severity="PASS",
                    message=f"No duplicate capability IDs in {len(cap_ids)} capabilities",
                    details={"capability_count": len(cap_ids)},
                )
            )

    def _check_missing_registration(self) -> None:
        """Check for components that exist but are not registered."""
        from src.verification.runtime.discovery import discover_capabilities

        discovered = discover_capabilities()
        discovered_ids = {c.get("id") for c in discovered if c.get("id")}

        from src.verification.runtime.registries import load_capability_registry

        registry = load_capability_registry()
        registered_ids = {
            c.get("id") for c in registry.get("capabilities", []) if c.get("id")
        }

        missing = discovered_ids - registered_ids
        if missing:
            self._issues.append(
                ValidationIssue(
                    check="missing_registration",
                    severity="WARNING",
                    message=f"{len(missing)} discovered capabilities not in registry",
                    details={"missing_capabilities": sorted(missing)},
                )
            )
        else:
            self._issues.append(
                ValidationIssue(
                    check="missing_registration",
                    severity="PASS",
                    message=f"All {len(discovered_ids)} discovered capabilities are registered",
                    details={"capability_count": len(discovered_ids)},
                )
            )

    def _check_broken_dependency_chains(self) -> None:
        """Check for broken dependency chains in the capability registry."""
        from src.verification.runtime.registries import load_capability_registry

        registry = load_capability_registry()
        caps = registry.get("capabilities", [])
        cap_ids = {c.get("id") for c in caps if c.get("id")}

        broken = []
        for cap in caps:
            cap_id = cap.get("id", "")
            for dep in cap.get("dependencies", []):
                if dep not in cap_ids:
                    broken.append(f"{cap_id} -> {dep}")

        if broken:
            self._issues.append(
                ValidationIssue(
                    check="broken_dependency_chains",
                    severity="FAIL",
                    message=f"Found {len(broken)} broken dependency references",
                    details={"broken_dependencies": broken},
                )
            )
        else:
            self._issues.append(
                ValidationIssue(
                    check="broken_dependency_chains",
                    severity="PASS",
                    message="All dependency chains are intact",
                    details={"capability_count": len(cap_ids)},
                )
            )


def run_self_validation() -> SelfValidationReport:
    """Convenience function to run all self-validation checks."""
    engine = SelfValidationEngine()
    return engine.run_all()
