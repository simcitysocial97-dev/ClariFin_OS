"""Coverage Integrity Tests.

These tests validate that the generated artifacts are valid and all referenced
paths in capability manifests actually exist.
"""

from __future__ import annotations

import json
import pathlib

import yaml

PROJECT_ROOT = pathlib.Path(__file__).parent.parent.parent.parent
GENERATED_DIR = PROJECT_ROOT / "backend" / "tests" / "generated"
BACKEND_DIR = PROJECT_ROOT / "backend"


def test_coverage_json_exists() -> None:
    """coverage.json must exist in backend/tests/generated/."""
    assert (GENERATED_DIR / "coverage.json").exists(), "coverage.json not found - run check_coverage.py first"


def test_coverage_json_valid() -> None:
    """coverage.json must be valid JSON with expected structure."""
    with open(GENERATED_DIR / "coverage.json") as f:
        data = json.load(f)

    assert "generated_at" in data, "coverage.json missing 'generated_at'"
    assert "capabilities" in data, "coverage.json missing 'capabilities'"
    assert isinstance(data["capabilities"], list), "'capabilities' must be a list"

    for cap in data["capabilities"]:
        assert "id" in cap, "Capability missing 'id'"
        assert "name" in cap, "Capability missing 'name'"
        assert "overall_maturity" in cap, "Capability missing 'overall_maturity'"


def test_all_capability_references_exist() -> None:
    """All referenced paths in capability registry must exist."""
    errors: list[str] = []

    registry_path = GENERATED_DIR / "capability-registry.yaml"
    with open(registry_path) as f:
        registry = yaml.safe_load(f)

    capabilities = registry.get("capabilities", [])

    for manifest in capabilities:
        cap_id = manifest.get("id", "unknown")

        # Check routers
        for router in manifest.get("routers", []):
            path = BACKEND_DIR / router
            if not path.exists():
                errors.append(f"{cap_id}: router {router} NOT FOUND")

        # Check services
        for service in manifest.get("services", []):
            path = BACKEND_DIR / service
            if not path.exists():
                errors.append(f"{cap_id}: service {service} NOT FOUND")

        # Check golden datasets
        for dataset in manifest.get("golden_datasets", []):
            path = BACKEND_DIR / dataset
            if not path.exists():
                errors.append(f"{cap_id}: golden dataset {dataset} NOT FOUND")

        # Check property tests
        for test in manifest.get("property_tests", []):
            path = BACKEND_DIR / test
            alt_path = BACKEND_DIR / test.replace("tests/properties/", "tests/property/")
            if not path.exists() and not alt_path.exists():
                errors.append(f"{cap_id}: property test {test} NOT FOUND")

        # Check invariants
        for inv in manifest.get("invariants", []):
            path = BACKEND_DIR / inv
            alt_path = BACKEND_DIR / inv.replace("tests/invariants/", "tests/invariant/")
            alt_path2 = BACKEND_DIR / inv.replace("tests/domain/invariants/", "tests/invariant/")
            if not path.exists() and not alt_path.exists() and not alt_path2.exists():
                errors.append(f"{cap_id}: invariant {inv} NOT FOUND")

        # Check engines
        for engine in manifest.get("engines", []):
            path = BACKEND_DIR / engine
            found = False
            if path.exists():
                found = True
            else:
                match = re.match(r"tests/engines/test_(.+)\.py", engine)
                if match:
                    filename = match.group(1)
                    alt_path = BACKEND_DIR / f"tests/unit/engines/{filename}/test_{filename}.py"
                    if alt_path.exists():
                        found = True
            if not found:
                errors.append(f"{cap_id}: engine {engine} NOT FOUND")

        # Check repositories
        for repo in manifest.get("repositories", []):
            path = BACKEND_DIR / repo
            alt_path = BACKEND_DIR / repo.replace("tests/repositories/", "tests/unit/repositories/")
            if not path.exists() and not alt_path.exists():
                errors.append(f"{cap_id}: repository {repo} NOT FOUND")

    assert not errors, "Missing references:\n" + "\n".join(errors)


def test_coverage_report_md_exists() -> None:
    """coverage.md must exist in memory-bank/generated/."""
    assert (GENERATED_DIR / "coverage.md").exists(), "coverage.md not found - run check_coverage.py first"


def test_traceability_md_exists() -> None:
    """traceability.md must exist in memory-bank/generated/."""
    assert (GENERATED_DIR / "traceability.md").exists(), "traceability.md not found - run check_coverage.py first"


def test_change_impact_md_exists() -> None:
    """change-impact.md must exist in memory-bank/generated/."""
    assert (GENERATED_DIR / "change-impact.md").exists(), "change-impact.md not found - run check_coverage.py first"


def test_generated_files_have_content() -> None:
    """Generated files must not be empty."""
    for filename in ["coverage.md", "coverage.json", "traceability.md", "change-impact.md", "capability-registry.yaml"]:
        path = GENERATED_DIR / filename
        if path.exists():
            content = path.read_text()
            assert len(content) > 100, f"{filename} is suspiciously short ({len(content)} bytes)"
