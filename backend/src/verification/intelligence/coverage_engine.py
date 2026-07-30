"""Architectural Coverage Engine.

Moves beyond traditional code coverage to generate architectural verification coverage.
Shows which verification types are present for each capability,
helping identify verification gaps.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

from src.verification.runtime.registries import CapabilityRegistry

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
BACKEND_DIR = PROJECT_ROOT
GENERATED_DIR = BACKEND_DIR / "tests" / "generated"


VERIFICATION_TYPES = [
    "contract",
    "property",
    "mutation",
    "golden",
    "integration",
    "capability",
    "invariant",
    "architecture",
    "coverage",
]


@dataclass
class CapabilityCoverage:
    """Coverage status for a single capability."""

    capability_id: str
    capability_name: str = ""
    risk: str = "LOW"
    criticality: str = "unknown"
    coverage: dict[str, bool] = field(default_factory=dict)
    missing: list[str] = field(default_factory=list)
    present: list[str] = field(default_factory=list)
    gap_count: int = 0
    total_checks: int = 0
    coverage_percent: float = 0.0
    status: str = "GAP"

    def to_dict(self) -> dict[str, Any]:
        return {
            "capability_id": self.capability_id,
            "capability_name": self.capability_name,
            "risk": self.risk,
            "criticality": self.criticality,
            "coverage": self.coverage,
            "missing": self.missing,
            "present": self.present,
            "gap_count": self.gap_count,
            "total_checks": self.total_checks,
            "coverage_percent": self.coverage_percent,
            "status": self.status,
        }


@dataclass
class ArchitecturalCoverage:
    """Complete architectural coverage report."""

    capabilities: list[CapabilityCoverage] = field(default_factory=list)
    summary: dict[str, Any] = field(default_factory=dict)
    generated_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "capabilities": [c.to_dict() for c in self.capabilities],
            "summary": self.summary,
            "generated_at": self.generated_at,
        }


class CoverageEngine:
    """Generates architectural verification coverage."""

    def __init__(self) -> None:
        self._capability_registry: CapabilityRegistry = cast(CapabilityRegistry, {})
        self._capabilities: list[CapabilityCoverage] = []

    def generate_all(self) -> ArchitecturalCoverage:
        """Generate architectural coverage for all capabilities."""
        self._load_registry()

        capabilities: list[CapabilityCoverage] = []

        for cap in self._capability_registry.get("capabilities", []):
            cap_id = cap.get("id", "")

            coverage = self._assess_capability_coverage(cap, cap_id)

            capabilities.append(coverage)

        self._capabilities = capabilities

        summary = self._compute_summary(capabilities)

        return ArchitecturalCoverage(
            capabilities=capabilities,
            summary=summary,
            generated_at=datetime.now(UTC).isoformat(),
        )

    def _load_registry(self) -> None:
        """Load the capability registry."""
        from src.verification.runtime.registries import load_capability_registry

        self._capability_registry = load_capability_registry()

    def _assess_capability_coverage(
        self, cap: dict[str, Any], cap_id: str
    ) -> CapabilityCoverage:
        """Assess verification coverage for a single capability."""
        coverage: dict[str, bool] = {}
        missing: list[str] = []
        present: list[str] = []

        for vtype in VERIFICATION_TYPES:
            is_present = self._check_verification_type(cap, vtype)
            coverage[vtype] = is_present
            if is_present:
                present.append(vtype)
            else:
                missing.append(vtype)

        gap_count = len(missing)
        total_checks = len(VERIFICATION_TYPES)
        coverage_percent = (
            (total_checks - gap_count) / total_checks * 100 if total_checks > 0 else 0.0
        )

        if gap_count == 0:
            status = "COMPLETE"
        elif gap_count <= 2:
            status = "PARTIAL"
        else:
            status = "GAP"

        return CapabilityCoverage(
            capability_id=cap_id,
            capability_name=cap.get("name", cap_id),
            risk=cap.get("risk", "LOW"),
            criticality=cap.get("criticality", "unknown"),
            coverage=coverage,
            missing=missing,
            present=present,
            gap_count=gap_count,
            total_checks=total_checks,
            coverage_percent=coverage_percent,
            status=status,
        )

    def _check_verification_type(self, cap: dict[str, Any], vtype: str) -> bool:
        """Check if a specific verification type is present for a capability."""
        if vtype == "contract":
            return bool(cap.get("contracts"))

        if vtype == "property":
            prop_tests = cap.get("property_tests", [])
            if prop_tests:
                return True
            prop_dir = Path(BACKEND_DIR / "tests" / "properties" / cap.get("id", ""))
            return prop_dir.exists()

        if vtype == "mutation":
            mut_map_path = GENERATED_DIR / "mutation-map.json"
            if mut_map_path.exists():
                try:
                    with open(mut_map_path) as f:
                        mut_data = json.load(f)
                    entries = (
                        mut_data.get("entries", [])
                        if isinstance(mut_data, dict)
                        else []
                    )
                    return any(e.get("capability") == cap.get("id") for e in entries)
                except (json.JSONDecodeError, TypeError):
                    pass
            return False

        if vtype == "golden":
            return bool(cap.get("golden_datasets"))

        if vtype == "integration":
            int_dir = Path(BACKEND_DIR / "tests" / "integration")
            return int_dir.exists() and any(int_dir.rglob("test_*.py"))

        if vtype == "capability":
            cap_dir = Path(BACKEND_DIR / "tests" / "capability" / cap.get("id", ""))
            return cap_dir.exists() and any(cap_dir.glob("test_*.py"))

        if vtype == "invariant":
            return bool(cap.get("invariants"))

        if vtype == "architecture":
            arch_dir = Path(BACKEND_DIR / "tests" / "architecture")
            return arch_dir.exists() and any(arch_dir.glob("test_*.py"))

        if vtype == "coverage":
            coverage_path = GENERATED_DIR / "coverage.json"
            return coverage_path.exists()

        return False

    def _compute_summary(
        self, capabilities: list[CapabilityCoverage]
    ) -> dict[str, Any]:
        """Compute summary statistics."""
        total = len(capabilities)
        if total == 0:
            return {
                "total_capabilities": 0,
                "complete": 0,
                "partial": 0,
                "gap": 0,
                "average_coverage_percent": 0.0,
                "total_gaps": 0,
            }

        complete = sum(1 for c in capabilities if c.status == "COMPLETE")
        partial = sum(1 for c in capabilities if c.status == "PARTIAL")
        gap = sum(1 for c in capabilities if c.status == "GAP")
        avg_coverage = sum(c.coverage_percent for c in capabilities) / total
        total_gaps = sum(c.gap_count for c in capabilities)

        return {
            "total_capabilities": total,
            "complete": complete,
            "partial": partial,
            "gap": gap,
            "average_coverage_percent": round(avg_coverage, 1),
            "total_gaps": total_gaps,
        }

    def get_capabilities_with_gaps(self) -> list[CapabilityCoverage]:
        """Get capabilities that have verification gaps."""
        return [c for c in self._capabilities if c.status in ("PARTIAL", "GAP")]

    def get_capabilities_complete(self) -> list[CapabilityCoverage]:
        """Get capabilities with complete verification coverage."""
        return [c for c in self._capabilities if c.status == "COMPLETE"]


def generate_architectural_coverage() -> ArchitecturalCoverage:
    """Convenience function to generate architectural coverage."""
    engine = CoverageEngine()
    return engine.generate_all()


def get_coverage_report() -> dict[str, Any]:
    """Get a quick coverage report dict."""
    engine = CoverageEngine()
    coverage = engine.generate_all()
    return coverage.to_dict()
