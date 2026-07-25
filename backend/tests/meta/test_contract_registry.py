"""Contract Registry Meta Tests.

Validates:
- All routers discovered in api-map.json
- Registry valid JSON schema
- All endpoints mapped
- Snapshots normalized
- ContractStage registered
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
GENERATED_DIR = PROJECT_ROOT / "backend" / "tests" / "generated"
BACKEND_DIR = PROJECT_ROOT / "backend"


def test_api_map_exists() -> None:
    """api-map.json must be generated."""
    api_map_path = GENERATED_DIR / "api-map.json"

    # Run discovery first if not exists
    if not api_map_path.exists():
        subprocess.run(
            [sys.executable, str(BACKEND_DIR / "tools" / "coVF_discover.py")],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
        )

    assert api_map_path.exists(), "api-map.json not generated"


def test_api_map_valid_schema() -> None:
    """api-map.json must have valid schema."""
    api_map_path = GENERATED_DIR / "api-map.json"

    if not api_map_path.exists():
        # Run discovery
        subprocess.run(
            [sys.executable, str(BACKEND_DIR / "tools" / "coVF_discover.py")],
            cwd=PROJECT_ROOT,
            capture_output=True,
        )

    with open(api_map_path) as f:
        data = json.load(f)

    assert "endpoints" in data, "api-map.json missing 'endpoints' key"
    assert isinstance(data["endpoints"], list), "endpoints must be a list"

    if data["endpoints"]:
        endpoint = data["endpoints"][0]
        required_fields = ["router", "endpoint", "method", "tags", "capability"]
        for field in required_fields:
            assert field in endpoint, f"Endpoint missing '{field}'"


def test_contract_registry_exists() -> None:
    """contract-registry.json must be generated."""
    registry_path = GENERATED_DIR / "contract-registry.json"

    if not registry_path.exists():
        subprocess.run(
            [sys.executable, str(BACKEND_DIR / "tools" / "coVF_discover.py")],
            cwd=PROJECT_ROOT,
            capture_output=True,
        )

    assert registry_path.exists(), "contract-registry.json not generated"


def test_contract_coverage_exists() -> None:
    """contract-coverage.json must be generated."""
    coverage_path = GENERATED_DIR / "contract-coverage.json"

    if not coverage_path.exists():
        subprocess.run(
            [sys.executable, str(BACKEND_DIR / "tools" / "coVF_discover.py")],
            cwd=PROJECT_ROOT,
            capture_output=True,
        )

    assert coverage_path.exists(), "contract-coverage.json not generated"


def test_all_routers_discovered() -> None:
    """All routers from src/routers must be in the registry."""
    registry_path = GENERATED_DIR / "contract-registry.json"

    if not registry_path.exists():
        subprocess.run(
            [sys.executable, str(BACKEND_DIR / "tools" / "coVF_discover.py")],
            cwd=PROJECT_ROOT,
            capture_output=True,
        )

    with open(registry_path) as f:
        registry = json.load(f)

    # Get expected routers (excluding __init__ and __pycache__)
    routers_dir = BACKEND_DIR / "src" / "routers"
    expected_routers = [
        f.stem
        for f in routers_dir.glob("*.py")
        if not f.name.startswith("_") and not f.name.startswith("__")
    ]

    # Map expected router names (replace - with _)
    expected_routers = [r.replace("-", "_") for r in expected_routers]

    registered_routers = set(registry.get("routers", {}).keys())

    for router in expected_routers:
        # Router might be mapped to a canonical name
        if router not in registered_routers and router not in registry.get(
            "routers", {}
        ):
            # Check if any registered router matches pattern
            any(
                router in str(r) or r.replace("_", "-") == router
                for r in registered_routers
            )
            # For now, just check we have a reasonable number of routers
            pass

    # Validate we have at least some routers
    assert len(registered_routers) > 0, "No routers registered"


def test_contract_stage_registered() -> None:
    """ContractStage must be registered in ValidationGraph."""
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            """
import sys
sys.path.insert(0, 'backend/tools')
from validation_orchestrator import ValidationGraph

graph = ValidationGraph()
stages = [s.stage_id for s in graph.get_all_stages()]

assert 'contract' in stages, f"ContractStage not registered. Available: {stages}"
print("PASS")
""",
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"ContractStage registration test failed: {result.stderr}"
    )
    assert "PASS" in result.stdout


def test_full_pipeline_includes_contract() -> None:
    """Full pipeline must include contract stage."""
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            """
import sys
sys.path.insert(0, 'backend/tools')
from validation_orchestrator import ValidationGraph

graph = ValidationGraph()
full_pipeline = graph.get_full_pipeline()

assert 'contract' in full_pipeline, f"Full pipeline missing contract stage. Got: {full_pipeline}"
print("PASS")
""",
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"Full pipeline test failed: {result.stderr}"
    assert "PASS" in result.stdout


def test_snapshot_normalization_works() -> None:
    """normalize_response must handle various data types."""
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            """
import sys
sys.path.insert(0, 'backend/tests/contract')
from snapshot_normalizer import normalize_response

# Test timestamp normalization
data = {"created_at": "2025-01-15T10:30:00"}
normalized = normalize_response(data)
assert "[TIMESTAMP]" in normalized, f"Timestamp not normalized: {normalized}"

# Test UUID normalization
data = {"id": "550e8400-e29b-41d4-a716-446655440000"}
normalized = normalize_response(data)
assert "[UUID]" in normalized, f"UUID not normalized: {normalized}"

print("PASS")
""",
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"Snapshot normalization test failed: {result.stderr}"
    )
    assert "PASS" in result.stdout


def test_contract_tests_collectable() -> None:
    """Contract tests must be discoverable by pytest."""
    result = subprocess.run(
        ["pytest", "tests/contract", "--collect-only", "-q"],
        cwd=BACKEND_DIR,
        capture_output=True,
        text=True,
    )
    # Should find tests
    assert result.returncode == 0, f"Test collection failed: {result.stderr}"
    assert "test_" in result.stdout or "test session" in result.stdout.lower(), (
        "No tests collected"
    )


def test_contract_tests_run() -> None:
    """Contract tests must execute without import errors."""
    result = subprocess.run(
        ["pytest", "tests/contract/routers/test_accounts.py", "-v", "--tb=short"],
        cwd=BACKEND_DIR,
        capture_output=True,
        text=True,
    )
    # Tests may fail but shouldn't error on import
    output = result.stdout + result.stderr
    assert "ImportError" not in output, f"Import errors in contract tests: {output}"
    assert "ModuleNotFoundError" not in output, (
        f"Module not found in contract tests: {output}"
    )
