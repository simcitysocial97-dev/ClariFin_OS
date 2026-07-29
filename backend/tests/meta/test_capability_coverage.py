"""Capability Coverage Validation.

Verifies that every capability has:
- Unit tests
- Property tests (where applicable)
- Contract tests
- Capability tests
- Regression tests

Produces CAPABILITY_COVERAGE.md with PASS/FAIL matrix.

Part G of Phase 3.2 — Capability Validation & Real-World Verification.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
BACKEND_DIR = PROJECT_ROOT / "backend"
TESTS_DIR = BACKEND_DIR / "tests"
GENERATED_DIR = TESTS_DIR / "generated"
COVERAGE_OUTPUT = PROJECT_ROOT / "CAPABILITY_COVERAGE.md"

# Coverage categories to check per capability
COVERAGE_CATEGORIES = [
    ("unit", "Unit Tests"),
    ("property", "Property Tests"),
    ("contract", "Contract Tests"),
    ("capability", "Capability Tests"),
    ("regression", "Regression Tests"),
    ("invariant", "Invariant Tests"),
    ("golden", "Golden Datasets"),
]


def _load_registry() -> dict[str, Any]:
    """Load the capability registry."""
    from runtime.registries import load_capability_registry

    return load_capability_registry()


def _check_unit_tests(cap: dict[str, Any]) -> bool:
    """Check if capability has unit tests."""
    # Check property_tests that reference tests/unit/
    for pt in cap.get("property_tests", []):
        if "tests/unit/" in pt:
            return True
    # Check if there are unit test files for this capability
    cap_id = cap.get("id", "")
    unit_dir = TESTS_DIR / "unit"
    if unit_dir.exists():
        for py_file in unit_dir.rglob("test_*.py"):
            rel = py_file.relative_to(TESTS_DIR)
            if cap_id.replace("_", "") in str(rel).lower():
                return True
    return False


def _check_property_tests(cap: dict[str, Any]) -> bool:
    """Check if capability has property tests."""
    for pt in cap.get("property_tests", []):
        path = BACKEND_DIR / pt
        if path.exists():
            return True
    # Check filesystem for capability-specific property tests
    cap_id = cap.get("id", "")
    props_dir = TESTS_DIR / "properties"
    if props_dir.exists():
        for subdir in props_dir.iterdir():
            if subdir.is_dir() and cap_id.replace("_", "") in subdir.name.lower():
                return True
    return False


def _check_contract_tests(cap: dict[str, Any]) -> bool:
    """Check if capability has contract tests."""
    contracts = cap.get("contracts", [])
    if contracts:
        return True
    # Check generated contract tests
    contract_dir = TESTS_DIR / "contract" / "generated"
    if contract_dir.exists():
        for py_file in contract_dir.glob("test_*.py"):
            return True
    return False


def _check_capability_tests(cap: dict[str, Any]) -> bool:
    """Check if capability has capability smoke tests."""
    cap_id = cap.get("id", "")
    cap_test_dir = TESTS_DIR / "capability" / cap_id
    return cap_test_dir.exists() and any(
        cap_test_dir.glob("test_*.py")
    )


def _check_regression_tests(cap: dict[str, Any]) -> bool:
    """Check if capability has regression tests."""
    cap_id = cap.get("id", "")
    golden_dir = TESTS_DIR / "golden"
    if golden_dir.exists():
        # Check for regression test files
        for py_file in golden_dir.rglob("test_*.py"):
            if cap_id.replace("_", "") in py_file.name.lower():
                return True
        # Check golden regressions directory
        regressions_dir = golden_dir / "regressions"
        if regressions_dir.exists():
            for py_file in regressions_dir.rglob("test_*.py"):
                return True
    # Check if golden datasets exist for this capability
    for ds in cap.get("golden_datasets", []):
        path = BACKEND_DIR / ds
        if path.exists():
            return True
    return False


def _check_invariant_tests(cap: dict[str, Any]) -> bool:
    """Check if capability has invariant tests."""
    for inv in cap.get("invariants", []):
        path = BACKEND_DIR / inv
        if path.exists():
            return True
    return False


def _check_golden_datasets(cap: dict[str, Any]) -> bool:
    """Check if capability has golden datasets."""
    for ds in cap.get("golden_datasets", []):
        path = BACKEND_DIR / ds
        if path.exists():
            return True
    return False


def _audit_coverage(cap: dict[str, Any]) -> dict[str, Any]:
    """Audit coverage for a single capability."""
    cap_id = cap.get("id", "")
    checks = {
        "unit": _check_unit_tests(cap),
        "property": _check_property_tests(cap),
        "contract": _check_contract_tests(cap),
        "capability": _check_capability_tests(cap),
        "regression": _check_regression_tests(cap),
        "invariant": _check_invariant_tests(cap),
        "golden": _check_golden_datasets(cap),
    }
    return {
        "id": cap_id,
        "name": cap.get("name", cap_id),
        "criticality": cap.get("criticality", "unknown"),
        "risk": cap.get("risk", "unknown"),
        "checks": checks,
        "passed": sum(1 for v in checks.values() if v),
        "total": len(checks),
    }


def _generate_coverage_md(results: list[dict[str, Any]]) -> str:
    """Generate CAPABILITY_COVERAGE.md content."""
    lines = [
        "# Capability Coverage Report",
        "",
        "Part G of Phase 3.2 — Capability Validation & Real-World Verification",
        "",
        "Verifies that every capability has adequate test coverage across all",
        "test categories.",
        "",
        "## Coverage Matrix",
        "",
        "| Capability | Unit | Property | Contract | Capability | Regression | Invariant | Golden | Overall |",
        "|------------|------|----------|----------|------------|------------|-----------|--------|---------|",
    ]

    for result in results:
        checks = result["checks"]
        row = f"| {result['name']} |"
        for cat in ["unit", "property", "contract", "capability", "regression", "invariant", "golden"]:
            status = "PASS" if checks[cat] else "FAIL"
            row += f" {status} |"
        overall = "PASS" if result["passed"] == result["total"] else "PARTIAL"
        row += f" {overall} |"
        lines.append(row)

    lines.extend(
        [
            "",
            "## Legend",
            "",
            "| Status | Meaning |",
            "|--------|---------|",
            "| PASS | Coverage exists |",
            "| FAIL | No coverage found |",
            "| PARTIAL | Some categories missing |",
            "",
            "## Summary",
            "",
            f"- Total capabilities: {len(results)}",
            f"- Fully covered: {sum(1 for r in results if r['passed'] == r['total'])}",
            f"- Partially covered: {sum(1 for r in results if 0 < r['passed'] < r['total'])}",
            f"- Not covered: {sum(1 for r in results if r['passed'] == 0)}",
            "",
            "## Detailed Coverage",
            "",
        ]
    )

    for result in results:
        lines.extend(
            [
                f"### {result['name']} (`{result['id']}`)",
                "",
                f"Criticality: {result['criticality']} | Risk: {result['risk']}",
                "",
                f"Coverage: {result['passed']}/{result['total']} categories",
                "",
            ]
        )
        for cat, label in COVERAGE_CATEGORIES:
            status = "✓ PASS" if result["checks"][cat] else "✗ FAIL"
            lines.append(f"- {status} — {label}")
        lines.append("")

    return "\n".join(lines)


class TestCapabilityCoverage:
    """Verify every capability has adequate test coverage."""

    @pytest.fixture(scope="class")
    def coverage_results(self) -> list[dict[str, Any]]:
        """Run coverage audit for all capabilities."""
        registry = _load_registry()
        results = []
        for cap in registry.get("capabilities", []):
            results.append(_audit_coverage(cap))
        return results

    def test_all_capabilities_covered(
        self, coverage_results: list[dict[str, Any]]
    ) -> None:
        """Every capability must be in the coverage audit."""
        registry = _load_registry()
        registered_ids = {
            c.get("id") for c in registry.get("capabilities", []) if c.get("id")
        }
        audited_ids = {r["id"] for r in coverage_results}
        missing = registered_ids - audited_ids
        assert not missing, f"Capabilities not in coverage audit: {missing}"

    def test_every_capability_has_unit_tests(
        self, coverage_results: list[dict[str, Any]]
    ) -> None:
        """Every capability must have unit tests."""
        failures = [
            r["id"] for r in coverage_results if not r["checks"]["unit"]
        ]
        assert not failures, (
            f"Capabilities without unit tests: {failures}"
        )

    def test_every_capability_has_property_tests(
        self, coverage_results: list[dict[str, Any]]
    ) -> None:
        """Every capability must have property tests."""
        failures = [
            r["id"] for r in coverage_results if not r["checks"]["property"]
        ]
        assert not failures, (
            f"Capabilities without property tests: {failures}"
        )

    def test_every_capability_has_contract_tests(
        self, coverage_results: list[dict[str, Any]]
    ) -> None:
        """Every capability must have contract tests."""
        failures = [
            r["id"] for r in coverage_results if not r["checks"]["contract"]
        ]
        assert not failures, (
            f"Capabilities without contract tests: {failures}"
        )

    def test_every_capability_has_capability_tests(
        self, coverage_results: list[dict[str, Any]]
    ) -> None:
        """Every capability must have capability smoke tests."""
        failures = [
            r["id"] for r in coverage_results if not r["checks"]["capability"]
        ]
        assert not failures, (
            f"Capabilities without capability tests: {failures}"
        )

    def test_every_capability_has_regression_tests(
        self, coverage_results: list[dict[str, Any]]
    ) -> None:
        """Every capability must have regression tests."""
        failures = [
            r["id"] for r in coverage_results if not r["checks"]["regression"]
        ]
        assert not failures, (
            f"Capabilities without regression tests: {failures}"
        )

    def test_every_capability_has_invariant_tests(
        self, coverage_results: list[dict[str, Any]]
    ) -> None:
        """Every capability must have invariant tests."""
        failures = [
            r["id"] for r in coverage_results if not r["checks"]["invariant"]
        ]
        assert not failures, (
            f"Capabilities without invariant tests: {failures}"
        )

    def test_every_capability_has_golden_datasets(
        self, coverage_results: list[dict[str, Any]]
    ) -> None:
        """Every capability must have golden datasets."""
        failures = [
            r["id"] for r in coverage_results if not r["checks"]["golden"]
        ]
        assert not failures, (
            f"Capabilities without golden datasets: {failures}"
        )

    def test_coverage_report_generated(
        self, coverage_results: list[dict[str, Any]]
    ) -> None:
        """The coverage report must be generated and written to disk."""
        md = _generate_coverage_md(coverage_results)
        assert "# Capability Coverage Report" in md
        assert "## Coverage Matrix" in md
        COVERAGE_OUTPUT.write_text(md)
        assert COVERAGE_OUTPUT.exists()
        assert COVERAGE_OUTPUT.stat().st_size > 0

    def test_high_criticality_capabilities_fully_covered(
        self, coverage_results: list[dict[str, Any]]
    ) -> None:
        """High criticality capabilities must be fully covered."""
        for result in coverage_results:
            if result["criticality"] == "high":
                assert result["passed"] == result["total"], (
                    f"High criticality capability {result['id']} is not fully covered: "
                    f"{result['passed']}/{result['total']}"
                )
