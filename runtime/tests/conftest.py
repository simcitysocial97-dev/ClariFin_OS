"""Shared fixtures for runtime verification tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from runtime.foundation.verification.registry import (
    VerificationRegistry,
    reset_registry,
)
from runtime.foundation.verification.planner import CrossLayerImpactPlanner


@pytest.fixture
def repo_root(tmp_path: Path) -> Path:
    """Provide an isolated synthetic repo root."""
    return tmp_path


@pytest.fixture
def fixture_dir() -> Path:
    """Return the fixtures directory."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def load_fixture(fixture_dir: Path):
    """Load a fixture scenario by name."""

    def _load(name: str) -> dict:
        base = fixture_dir / name
        expected_path = base / "expected.json"
        map_path = base / "cross-layer-map.json"
        diff_path = base / "diff.json"

        result = {
            "name": name,
            "base": base,
        }
        if expected_path.exists():
            result["expected"] = json.loads(expected_path.read_text())
        if map_path.exists():
            result["cross_layer_map"] = json.loads(map_path.read_text())
        if diff_path.exists():
            result["diff"] = json.loads(diff_path.read_text())
        return result

    return _load


@pytest.fixture
def synthetic_cross_layer_map(tmp_path: Path, repo_root: Path):
    """Create a temporary cross-layer map for isolated testing."""

    def _make_map(data: dict) -> Path:
        map_path = repo_root / "runtime" / "generated" / "cross-layer-map.json"
        map_path.parent.mkdir(parents=True, exist_ok=True)
        map_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return map_path

    return _make_map


@pytest.fixture
def planner_with_map(synthetic_cross_layer_map):
    """Create a CrossLayerImpactPlanner backed by a temporary map."""

    def _make(map_data: dict) -> CrossLayerImpactPlanner:
        map_path = synthetic_cross_layer_map(map_data)
        return CrossLayerImpactPlanner(map_path=map_path)

    return _make


@pytest.fixture
def isolated_registry(tmp_path: Path):
    """Provide a VerificationRegistry with a temporary YAML config."""
    config = {
        "version": "1.0",
        "workflows": {
            "quick": {
                "name": "Quick",
                "description": "Quick checks",
                "category": "capability",
                "scope": "quick",
                "command": "echo quick",
                "estimated_duration_seconds": 10,
                "scopes": ["quick"],
            },
            "backend": {
                "name": "Backend",
                "description": "Backend checks",
                "category": "capability",
                "scope": "backend",
                "command": "echo backend",
                "estimated_duration_seconds": 30,
                "scopes": ["backend", "contracts"],
            },
            "contracts": {
                "name": "Contracts",
                "description": "Contract checks",
                "category": "contract",
                "scope": "contracts",
                "command": "echo contracts",
                "estimated_duration_seconds": 30,
                "scopes": ["contracts"],
            },
        },
        "scripts": {
            "run_fast_checks": {
                "name": "Fast Checks",
                "path": ".github/scripts/run_fast_checks.sh",
                "description": "Fast checks",
                "category": "capability",
                "scope": "quick",
                "estimated_duration_seconds": 10,
            },
        },
        "capabilities": {
            "loan-engine": {
                "name": "Loan Engine",
                "description": "Loan calculations",
                "category": "capability",
                "scopes": ["backend", "property", "contracts", "integration", "repository"],
                "workflows": ["property", "contracts", "backend"],
                "scripts": ["run_fast_checks"],
                "modules": ["backend/src/engines/loan_engine"],
                "requirements": [
                    {
                        "id": "loan-engine-property",
                        "category": "property",
                        "severity": "critical",
                        "description": "Property tests",
                        "scope": "property",
                        "module": "backend/src/engines/loan_engine",
                        "capability": "loan-engine",
                    },
                    {
                        "id": "loan-engine-contract",
                        "category": "contract",
                        "severity": "critical",
                        "description": "Contract tests",
                        "scope": "contracts",
                        "module": "backend/src/engines/loan_engine",
                        "capability": "loan-engine",
                    },
                ],
            },
            "reconciliation": {
                "name": "Reconciliation Engine",
                "description": "Reconciliation",
                "category": "capability",
                "scopes": ["backend", "property", "contracts", "integration", "repository"],
                "workflows": ["property", "contracts", "backend"],
                "scripts": ["run_fast_checks"],
                "modules": ["backend/src/reconciliation"],
                "requirements": [],
            },
            "ledger": {
                "name": "Ledger Service",
                "description": "Ledger",
                "category": "capability",
                "scopes": ["backend", "contracts", "integration", "repository"],
                "workflows": ["contracts", "backend", "integration"],
                "scripts": ["run_fast_checks"],
                "modules": ["backend/src/ledger"],
                "requirements": [
                    {
                        "id": "ledger-invariant",
                        "category": "invariant",
                        "severity": "critical",
                        "description": "Invariant tests",
                        "scope": "contracts",
                        "module": "backend/src/ledger",
                        "capability": "ledger",
                    },
                ],
            },
            "migrations": {
                "name": "Migrations",
                "description": "Migrations",
                "category": "migration",
                "scopes": ["migration", "backend", "repository"],
                "workflows": ["migration"],
                "scripts": [],
                "modules": ["backend/src/migrations"],
                "requirements": [],
            },
        },
        "categories": {
            "capability": {"enabled": True},
            "contract": {"enabled": True},
            "property": {"enabled": True},
            "invariant": {"enabled": True},
            "integration": {"enabled": True},
            "migration": {"enabled": True},
            "architectural": {"enabled": True},
        },
        "scopes": {
            "quick": {"enabled": True},
            "backend": {"enabled": True},
            "frontend": {"enabled": True},
            "contracts": {"enabled": True},
            "property": {"enabled": True},
            "mutation": {"enabled": True},
            "integration": {"enabled": True},
            "migration": {"enabled": True},
            "repository": {"enabled": True},
            "full": {"enabled": True},
        },
        "modules": {
            "backend": {"source": "backend/src", "tests": "backend/tests", "category": "capability"},
            "frontend": {"source": "frontend/src", "tests": "frontend/tests", "category": "contract_frontend"},
        },
    }

    config_path = tmp_path / "verification.yaml"
    config_path.write_text(json.dumps(config), encoding="utf-8")

    # We need a YAML file, so let's write proper YAML
    import yaml

    config_path.write_text(yaml.dump(config), encoding="utf-8")

    registry = VerificationRegistry(config_path=config_path)
    registry.load()
    return registry


@pytest.fixture(autouse=True)
def reset_global_registry():
    """Reset global registry between tests."""
    reset_registry()
    yield
    reset_registry()
