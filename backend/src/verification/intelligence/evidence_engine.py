"""Verification Evidence Engine.

Every verified capability exposes evidence describing why it is considered verified.
Evidence types include:
- Contract Tests
- Property Tests
- Golden Regression
- Integration Tests
- Mutation Testing
- Coverage
- Capability Tests

Evidence summaries are generated automatically.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
BACKEND_DIR = PROJECT_ROOT / "backend"
GENERATED_DIR = BACKEND_DIR / "tests" / "generated"


VALID_EVIDENCE_TYPES = [
    "contract",
    "property",
    "golden",
    "integration",
    "mutation",
    "coverage",
    "capability",
    "invariant",
    "architecture",
]

EVIDENCE_STATUS = {
    "verified": "VERIFIED",
    "partial": "PARTIAL",
    "missing": "MISSING",
    "skipped": "SKIPPED",
}


@dataclass
class EvidenceItem:
    """A single piece of verification evidence."""

    evidence_type: str
    status: str
    path: str = ""
    test_count: int = 0
    pass_count: int = 0
    fail_count: int = 0
    skip_count: int = 0
    coverage_percent: float = 0.0
    last_run: str = ""
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "evidence_type": self.evidence_type,
            "status": self.status,
            "path": self.path,
            "test_count": self.test_count,
            "pass_count": self.pass_count,
            "fail_count": self.fail_count,
            "skip_count": self.skip_count,
            "coverage_percent": self.coverage_percent,
            "last_run": self.last_run,
            "notes": self.notes,
        }


@dataclass
class CapabilityEvidence:
    """Evidence summary for a single capability."""

    capability_id: str
    capability_name: str = ""
    risk: str = "LOW"
    criticality: str = "unknown"
    evidence: list[EvidenceItem] = field(default_factory=list)
    overall_status: str = "MISSING"
    verified_count: int = 0
    total_count: int = 0
    generated_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "capability_id": self.capability_id,
            "capability_name": self.capability_name,
            "risk": self.risk,
            "criticality": self.criticality,
            "evidence": [e.to_dict() for e in self.evidence],
            "overall_status": self.overall_status,
            "verified_count": self.verified_count,
            "total_count": self.total_count,
            "generated_at": self.generated_at,
        }

    @property
    def is_fully_verified(self) -> bool:
        return self.overall_status == "VERIFIED"

    @property
    def has_gaps(self) -> bool:
        return (
            any(e.status == "MISSING" for e in self.evidence)
            or self.verified_count < self.total_count
        )


@dataclass
class EvidenceSummary:
    """Complete evidence summary for all capabilities."""

    capabilities: list[CapabilityEvidence] = field(default_factory=list)
    generated_at: str = ""
    total_capabilities: int = 0
    fully_verified: int = 0
    partial: int = 0
    missing: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "capabilities": [c.to_dict() for c in self.capabilities],
            "generated_at": self.generated_at,
            "total_capabilities": self.total_capabilities,
            "fully_verified": self.fully_verified,
            "partial": self.partial,
            "missing": self.missing,
        }


class EvidenceEngine:
    """Generates verification evidence for capabilities."""

    def __init__(self) -> None:
        self._capability_registry: dict[str, Any] = {}

    def generate_all(self) -> EvidenceSummary:
        """Generate evidence for all registered capabilities."""
        self._load_registry()

        capabilities: list[CapabilityEvidence] = []

        for cap in self._capability_registry.get("capabilities", []):
            cap_id = cap.get("id", "")
            cap_name = cap.get("name", cap_id)
            risk = cap.get("risk", "LOW")
            criticality = cap.get("criticality", "unknown")

            evidence_items = self._generate_capability_evidence(cap)

            verified = sum(1 for e in evidence_items if e.status == "VERIFIED")
            total = len(evidence_items)

            if verified == total and total > 0:
                overall = "VERIFIED"
            elif verified > 0:
                overall = "PARTIAL"
            else:
                overall = "MISSING"

            capabilities.append(
                CapabilityEvidence(
                    capability_id=cap_id,
                    capability_name=cap_name,
                    risk=risk,
                    criticality=criticality,
                    evidence=evidence_items,
                    overall_status=overall,
                    verified_count=verified,
                    total_count=total,
                    generated_at=datetime.now(UTC).isoformat(),
                )
            )

        fully_verified = sum(1 for c in capabilities if c.overall_status == "VERIFIED")
        partial = sum(1 for c in capabilities if c.overall_status == "PARTIAL")
        missing = sum(1 for c in capabilities if c.overall_status == "MISSING")

        return EvidenceSummary(
            capabilities=capabilities,
            generated_at=datetime.now(UTC).isoformat(),
            total_capabilities=len(capabilities),
            fully_verified=fully_verified,
            partial=partial,
            missing=missing,
        )

    def _load_registry(self) -> None:
        """Load the capability registry."""
        from src.verification.runtime.registries import load_capability_registry

        self._capability_registry = load_capability_registry()

    def _generate_capability_evidence(self, cap: dict[str, Any]) -> list[EvidenceItem]:
        """Generate evidence items for a single capability."""
        cap_id = cap.get("id", "")
        evidence: list[EvidenceItem] = []

        evidence.append(self._assess_contract_evidence(cap, cap_id))
        evidence.append(self._assess_property_evidence(cap, cap_id))
        evidence.append(self._assess_golden_evidence(cap, cap_id))
        evidence.append(self._assess_integration_evidence(cap, cap_id))
        evidence.append(self._assess_mutation_evidence(cap, cap_id))
        evidence.append(self._assess_coverage_evidence(cap, cap_id))
        evidence.append(self._assess_capability_test_evidence(cap, cap_id))
        evidence.append(self._assess_invariant_evidence(cap, cap_id))
        evidence.append(self._assess_architecture_evidence(cap, cap_id))

        return evidence

    def _assess_contract_evidence(
        self, cap: dict[str, Any], cap_id: str
    ) -> EvidenceItem:
        """Assess contract test evidence."""
        contracts = cap.get("contracts", [])
        if not contracts:
            return EvidenceItem(
                evidence_type="contract",
                status="SKIPPED",
                notes="No contracts registered",
            )

        contract_dir = Path(BACKEND_DIR / "tests" / "contract" / "generated")
        test_files = (
            list(contract_dir.glob("test_*.py")) if contract_dir.exists() else []
        )

        return EvidenceItem(
            evidence_type="contract",
            status="VERIFIED" if test_files else "MISSING",
            path=str(contract_dir),
            test_count=len(test_files),
            notes=f"{len(contracts)} contracts registered, {len(test_files)} test files found",
        )

    def _assess_property_evidence(
        self, cap: dict[str, Any], cap_id: str
    ) -> EvidenceItem:
        """Assess property test evidence."""
        prop_tests = cap.get("property_tests", [])
        if not prop_tests:
            return EvidenceItem(
                evidence_type="property",
                status="SKIPPED",
                notes="No property tests registered",
            )

        prop_dir = Path(BACKEND_DIR / "tests" / "properties")
        prop_files = list(prop_dir.rglob("test_*.py")) if prop_dir.exists() else []

        return EvidenceItem(
            evidence_type="property",
            status="VERIFIED" if prop_files else "MISSING",
            path=str(prop_dir),
            test_count=len(prop_files),
            notes=f"{len(prop_tests)} property test paths registered, {len(prop_files)} files found",
        )

    def _assess_golden_evidence(self, cap: dict[str, Any], cap_id: str) -> EvidenceItem:
        """Assess golden regression evidence."""
        datasets = cap.get("golden_datasets", [])
        if not datasets:
            return EvidenceItem(
                evidence_type="golden",
                status="SKIPPED",
                notes="No golden datasets registered",
            )

        dataset_dir = Path(BACKEND_DIR / "tests" / "golden" / "datasets")
        dataset_files = list(dataset_dir.glob("*.json")) if dataset_dir.exists() else []

        return EvidenceItem(
            evidence_type="golden",
            status="VERIFIED" if dataset_files else "MISSING",
            path=str(dataset_dir),
            test_count=len(dataset_files),
            notes=f"{len(datasets)} golden datasets registered, {len(dataset_files)} files found",
        )

    def _assess_integration_evidence(
        self, cap: dict[str, Any], cap_id: str
    ) -> EvidenceItem:
        """Assess integration test evidence."""
        integration_dir = Path(BACKEND_DIR / "tests" / "integration")
        test_files = (
            list(integration_dir.rglob("test_*.py")) if integration_dir.exists() else []
        )

        return EvidenceItem(
            evidence_type="integration",
            status="VERIFIED" if test_files else "MISSING",
            path=str(integration_dir),
            test_count=len(test_files),
            notes=f"{len(test_files)} integration test files found",
        )

    def _assess_mutation_evidence(
        self, cap: dict[str, Any], cap_id: str
    ) -> EvidenceItem:
        """Assess mutation testing evidence."""
        mutation_dir = Path(BACKEND_DIR / "tests" / "generated" / "mutation")
        mut_map_path = GENERATED_DIR / "mutation-map.json"

        if mut_map_path.exists():
            try:
                with open(mut_map_path) as f:
                    mut_data = json.load(f)
                entries = (
                    mut_data.get("entries", []) if isinstance(mut_data, dict) else []
                )
                cap_entries = [e for e in entries if e.get("capability") == cap_id]
                has_mutation = len(cap_entries) > 0
                return EvidenceItem(
                    evidence_type="mutation",
                    status="VERIFIED" if has_mutation else "MISSING",
                    path=str(mutation_dir),
                    test_count=len(cap_entries),
                    notes=f"{len(cap_entries)} mutation entries for capability",
                )
            except (json.JSONDecodeError, TypeError):
                pass

        return EvidenceItem(
            evidence_type="mutation",
            status="MISSING",
            path=str(mutation_dir),
            notes="No mutation data available",
        )

    def _assess_coverage_evidence(
        self, cap: dict[str, Any], cap_id: str
    ) -> EvidenceItem:
        """Assess coverage evidence."""
        coverage_path = GENERATED_DIR / "coverage.json"

        if coverage_path.exists():
            try:
                with open(coverage_path) as f:
                    coverage_data = json.load(f)

                coverage_pct = 0.0
                if isinstance(coverage_data, dict):
                    totals = coverage_data.get("totals", {})
                    coverage_pct = totals.get("percent_covered", 0.0)

                return EvidenceItem(
                    evidence_type="coverage",
                    status="VERIFIED" if coverage_pct > 0 else "MISSING",
                    path=str(coverage_path),
                    coverage_percent=coverage_pct,
                    notes=f"Overall coverage: {coverage_pct:.1f}%",
                )
            except (json.JSONDecodeError, TypeError):
                pass

        return EvidenceItem(
            evidence_type="coverage",
            status="MISSING",
            path=str(coverage_path),
            notes="No coverage data available",
        )

    def _assess_capability_test_evidence(
        self, cap: dict[str, Any], cap_id: str
    ) -> EvidenceItem:
        """Assess capability smoke test evidence."""
        cap_test_dir = Path(BACKEND_DIR / "tests" / "capability" / cap_id)
        test_files = (
            list(cap_test_dir.glob("test_*.py")) if cap_test_dir.exists() else []
        )

        return EvidenceItem(
            evidence_type="capability",
            status="VERIFIED" if test_files else "MISSING",
            path=str(cap_test_dir),
            test_count=len(test_files),
            notes=f"{len(test_files)} capability test files found",
        )

    def _assess_invariant_evidence(
        self, cap: dict[str, Any], cap_id: str
    ) -> EvidenceItem:
        """Assess invariant test evidence."""
        inv_tests = cap.get("invariants", [])
        if not inv_tests:
            return EvidenceItem(
                evidence_type="invariant",
                status="SKIPPED",
                notes="No invariants registered",
            )

        inv_dir = Path(BACKEND_DIR / "tests" / "invariants")
        inv_files = list(inv_dir.glob("test_*.py")) if inv_dir.exists() else []

        return EvidenceItem(
            evidence_type="invariant",
            status="VERIFIED" if inv_files else "MISSING",
            path=str(inv_dir),
            test_count=len(inv_files),
            notes=f"{len(inv_tests)} invariant paths registered, {len(inv_files)} files found",
        )

    def _assess_architecture_evidence(
        self, cap: dict[str, Any], cap_id: str
    ) -> EvidenceItem:
        """Assess architecture test evidence."""
        arch_dir = Path(BACKEND_DIR / "tests" / "architecture")
        test_files = list(arch_dir.glob("test_*.py")) if arch_dir.exists() else []

        return EvidenceItem(
            evidence_type="architecture",
            status="VERIFIED" if test_files else "MISSING",
            path=str(arch_dir),
            test_count=len(test_files),
            notes=f"{len(test_files)} architecture test files found",
        )


def generate_evidence_summary() -> EvidenceSummary:
    """Convenience function to generate evidence summary."""
    engine = EvidenceEngine()
    return engine.generate_all()


def get_capability_evidence(capability_id: str) -> CapabilityEvidence | None:
    """Get evidence for a specific capability."""
    engine = EvidenceEngine()
    summary = engine.generate_all()
    for cap in summary.capabilities:
        if cap.capability_id == capability_id:
            return cap
    return None
