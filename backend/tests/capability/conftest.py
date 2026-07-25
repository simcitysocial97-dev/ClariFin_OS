"""Shared fixtures and configuration for capability smoke tests."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Ensure src is on path for all capability tests
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))


def pytest_configure(config: pytest.Config) -> None:
    """Register capability marker."""
    config.addinivalue_line("markers", "capability: mark test as capability smoke test")


def load_capability_manifest(capability_id: str) -> dict[str, object]:
    """Load a capability YAML manifest from memory-bank/capabilities/."""
    import yaml  # type: ignore[import-untyped]

    manifest_path = Path(__file__).parent.parent.parent.parent / "memory-bank" / "capabilities" / f"{capability_id}.yaml"
    with open(manifest_path) as f:
        return yaml.safe_load(f)  # type: ignore[no-any-return]


def validate_manifest_fields(manifest: dict[str, object], required_fields: list[str]) -> None:
    """Assert that a manifest contains all required fields."""
    missing = [field for field in required_fields if field not in manifest]
    assert not missing, f"Manifest missing required fields: {missing}"


@pytest.fixture
def capability_manifest() -> dict[str, object]:
    """Provide capability manifest from the test module's directory name."""
    import os

    capability_id = os.path.basename(str(Path(__file__).parent))
    return load_capability_manifest(capability_id)
