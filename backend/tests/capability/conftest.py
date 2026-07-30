"""Shared fixtures and configuration for capability smoke tests."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

# Ensure src is on path for all capability tests


def pytest_configure(config: pytest.Config) -> None:
    """Register capability marker."""
    config.addinivalue_line("markers", "capability: mark test as capability smoke test")


def load_capability_manifest(capability_id: str) -> dict[str, object]:
    """Load a capability manifest from the combined capability-registry.yaml."""
    registry_path = (
        Path(__file__).parent.parent.parent / "generated" / "capability-registry.yaml"
    )
    with open(registry_path) as f:
        registry = yaml.safe_load(f)

    # Find the matching capability by ID from the combined list
    capabilities = registry.get("capabilities", [])
    for cap in capabilities:
        if cap.get("id") == capability_id:
            return cap  # type: ignore[no-any-return]

    raise ValueError(f"Capability '{capability_id}' not found in registry.")


def validate_manifest_fields(
    manifest: dict[str, object], required_fields: list[str]
) -> None:
    """Assert that a manifest contains all required fields."""
    missing = [field for field in required_fields if field not in manifest]
    assert not missing, f"Manifest missing required fields: {missing}"


@pytest.fixture
def capability_manifest() -> dict[str, object]:
    """Provide capability manifest from the test module's directory name."""
    import os

    capability_id = os.path.basename(str(Path(__file__).parent))
    return load_capability_manifest(capability_id)
