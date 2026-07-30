"""Test scanner — discovers test suites and maps them to capabilities.

Discovers:
- Backend test directories and files (``backend/tests/``)
- Frontend test files (``frontend/__tests__/, frontend/tests/``)
- Test suite types: unit, invariant, property, golden, contract, capability,
  architecture, mutation, integration, domain, runtime, meta

Creates ``test_suite`` nodes and ``tests`` edges from capabilities to their
test files (using the capability registry as the canonical source).
"""

from __future__ import annotations

from pathlib import Path

from repo_intelligence.scanner.base import BaseScanner, ScanResult

# Backend test subdirectories and their type classification
_BACKEND_TEST_TYPES: dict[str, str] = {
    "unit": "unit",
    "invariants": "invariant",
    "properties": "property",
    "golden": "golden",
    "contract": "contract",
    "capability": "capability",
    "architecture": "architecture",
    "mutation": "mutation",
    "integration": "integration",
    "domain": "domain",
    "runtime": "runtime",
    "meta": "meta",
    "generated": "generated",
}

# Frontend test directories
_FRONTEND_TEST_DIRS: list[str] = ["__tests__", "tests"]


class TestScanner(BaseScanner):
    """Discover test suites and map them to capabilities."""

    def scan(self) -> ScanResult:
        result = ScanResult()

        self._scan_backend_tests(result)
        self._scan_frontend_tests(result)
        self._scan_capability_test_mapping(result)

        return result

    def _scan_backend_tests(self, result: ScanResult) -> None:
        """Discover backend test directories and files."""
        if not self.tests_dir.exists():
            return

        for test_dir in sorted(self.tests_dir.iterdir()):
            if not test_dir.is_dir():
                continue
            if test_dir.name.startswith("__"):
                continue

            test_type = _BACKEND_TEST_TYPES.get(test_dir.name, "other")

            # Create a test_suite node for the directory
            rel_dir = self.rel_path(test_dir, self.backend_dir)
            result.add_node(
                node_type="test_suite",
                name=test_dir.name,
                path=rel_dir,
                source="filesystem:backend/tests",
                properties={
                    "test_type": test_type,
                    "test_count": self._count_test_files(test_dir),
                    "subdirectories": [
                        d.name
                        for d in test_dir.iterdir()
                        if d.is_dir() and not d.name.startswith("__")
                    ],
                },
            )

            # Discover individual test files
            for py_file in test_dir.rglob("test_*.py"):
                rel_file = self.rel_path(py_file, self.backend_dir)
                result.add_node(
                    node_type="module",
                    name=py_file.stem,
                    path=rel_file,
                    source="filesystem:backend/tests",
                    properties={
                        "module_type": "test",
                        "test_type": test_type,
                    },
                )

    def _scan_frontend_tests(self, result: ScanResult) -> None:
        """Discover frontend test files."""
        for test_dir_name in _FRONTEND_TEST_DIRS:
            test_dir = self.frontend_dir / test_dir_name
            if not test_dir.exists():
                continue

            for test_file in test_dir.rglob("*.ts"):
                if test_file.name.startswith("test-"):
                    continue
                rel = self.rel_path(test_file, self.frontend_dir)
                result.add_node(
                    node_type="module",
                    name=test_file.stem,
                    path=rel,
                    source="filesystem:frontend/tests",
                    properties={
                        "module_type": "test",
                        "test_type": "frontend",
                    },
                )

    def _scan_capability_test_mapping(self, result: ScanResult) -> None:
        """Map capabilities to their test files using the registry."""
        registry = self.safe_read_yaml(
            self.generated_dir / "capability-registry.yaml"
        )
        if registry is None:
            return

        for cap in registry.get("capabilities", []):
            cap_id = cap.get("id", "")
            if not cap_id:
                continue

            cap_node_id = f"capability:{cap_id}"

            # Property tests
            for test_path in cap.get("property_tests", []):
                result.add_edge(
                    source_id=cap_node_id,
                    target_id=f"module:{test_path}",
                    relationship="tests",
                    confidence=0.9,
                    evidence="capability_registry.property_tests",
                )

            # Invariants
            for test_path in cap.get("invariants", []):
                result.add_edge(
                    source_id=cap_node_id,
                    target_id=f"module:{test_path}",
                    relationship="tests",
                    confidence=0.9,
                    evidence="capability_registry.invariants",
                )

            # Golden datasets
            for dataset_path in cap.get("golden_datasets", []):
                result.add_edge(
                    source_id=cap_node_id,
                    target_id=f"generated_artifact:{dataset_path}",
                    relationship="tests",
                    confidence=0.9,
                    evidence="capability_registry.golden_datasets",
                )

            # Architecture tests
            for arch_path in cap.get("architecture_tests", []):
                result.add_edge(
                    source_id=cap_node_id,
                    target_id=f"module:{arch_path}",
                    relationship="tests",
                    confidence=0.8,
                    evidence="capability_registry.architecture_tests",
                )

            # Contracts
            for contract in cap.get("contracts", []):
                # contract is "METHOD /api/path"
                parts = contract.split(" ", 1)
                if len(parts) == 2:
                    ep_id = f"endpoint:{parts[0]} {parts[1]}"
                    result.add_edge(
                        source_id=cap_node_id,
                        target_id=ep_id,
                        relationship="verifies",
                        confidence=0.8,
                        evidence="capability_registry.contracts",
                    )

    @staticmethod
    def _count_test_files(directory: Path) -> int:
        """Count test files in a directory tree."""
        count = 0
        for py_file in directory.rglob("test_*.py"):
            count += 1
        return count
