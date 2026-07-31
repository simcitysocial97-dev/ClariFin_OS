"""Contract Test Evidence Collector."""

from __future__ import annotations

from typing import List

from .base import EvidenceCollector, EvidenceArtifact


class ContractTestCollector(EvidenceCollector):
    """Collects contract testing evidence from API contract tests."""

    @property
    def artifact_type(self) -> str:
        return "contract_test"

    @property
    def name(self) -> str:
        return "Contract Test Results"

    def collect(self) -> List[EvidenceArtifact]:
        artifacts = []

        contract_dir = self.workspace_root / "backend" / "tests" / "generated"
        if not contract_dir.exists():
            return artifacts

        # Contract registry
        contract_registry = contract_dir / "contract-registry.json"
        if contract_registry.exists():
            data = self._read_json(contract_registry)
            if data:
                artifacts.append(
                    self._artifact(
                        name="Contract Registry",
                        path=contract_registry,
                        metadata={
                            "contracts_count": len(data.get("contracts", [])),
                        },
                    )
                )

        # Contract coverage
        contract_coverage = contract_dir / "contract-coverage.json"
        if contract_coverage.exists():
            data = self._read_json(contract_coverage)
            if data:
                artifacts.append(
                    self._artifact(
                        name="Contract Coverage",
                        path=contract_coverage,
                        metadata={
                            "endpoints_tested": data.get("endpoints_tested", 0),
                            "endpoints_total": data.get("endpoints_total", 0),
                            "coverage_percentage": data.get("coverage_percentage", 0.0),
                        },
                    )
                )

        # OpenAPI sync result
        openapi_current = contract_dir / "openapi-current.json"
        if openapi_current.exists():
            data = self._read_json(openapi_current)
            if data:
                artifacts.append(
                    self._artifact(
                        name="OpenAPI Schema (Current)",
                        path=openapi_current,
                        metadata={
                            "endpoints": len(data.get("paths", {})),
                        },
                    )
                )

        return artifacts
