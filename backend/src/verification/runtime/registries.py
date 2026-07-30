"""Runtime registries for verification intelligence.

Loads generated artifacts (capability-registry.yaml, contract-registry.json,
mutation-registry.json, api-map.json) from the generated artifacts directory.

This is the production version used by the Verification Intelligence Layer.
The tests/runtime/registries.py version is the test-time equivalent.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, TypedDict, cast

# Generated artifacts directory: backend/tests/generated/
BACKEND_DIR = Path(__file__).parent.parent.parent.parent  # project root / backend
GENERATED_DIR = BACKEND_DIR / "tests" / "generated"


class CapabilityRegistry(TypedDict):
    capabilities: list[dict[str, Any]]


class ContractRegistry(TypedDict):
    routers: dict[str, Any]
    generated_at: str | None


class ApiMap(TypedDict):
    endpoints: list[dict[str, Any]]
    generated_at: str | None


class MutationRegistry(TypedDict):
    generated_at: str | None
    entries: list[dict[str, Any]]


class ValidationManifest(TypedDict, total=False):
    pass


class RiskRules(TypedDict):
    rules: list[dict[str, Any]]


def load_capability_registry() -> CapabilityRegistry:
    """Load capability-registry.yaml.

    Returns dict with 'capabilities' list.
    Each capability has: id, name, description, criticality, risk,
    routers, services, engines, repositories, tables, golden_datasets,
    property_tests, invariants, architecture_tests, contracts, dependencies, failure_impact.
    """
    import yaml  # type: ignore[import-untyped]

    path = GENERATED_DIR / "capability-registry.yaml"
    if not path.exists():
        return {"capabilities": []}
    with open(path) as f:
        data = yaml.safe_load(f) or {"capabilities": []}
    return cast(CapabilityRegistry, data)


def load_contract_registry() -> ContractRegistry:
    """Load contract-registry.json.

    Returns dict with 'routers' and 'generated_at'.
    Each router has: endpoints list with method, path, request_schema, response_schema, status_codes.
    """
    path = GENERATED_DIR / "contract-registry.json"
    if not path.exists():
        return {"routers": {}, "generated_at": None}
    with open(path) as f:
        return cast(ContractRegistry, json.load(f))


def load_api_map() -> ApiMap:
    """Load api-map.json with full endpoint metadata.

    Returns dict with 'endpoints' list and 'generated_at'.
    Each endpoint has: router, endpoint, method, tags, capability, request_schema, response_schema, status_codes, parameters.
    """
    path = GENERATED_DIR / "api-map.json"
    if not path.exists():
        return {"endpoints": [], "generated_at": None}
    with open(path) as f:
        return cast(ApiMap, json.load(f))


def load_mutation_registry() -> MutationRegistry:
    """Load mutation-registry.json.

    Returns dict with 'generated_at' and 'entries' list.
    Each entry has: module, function, capability, risk, mutation_types, existing_tests, property_tests, golden_tests, contracts, performance_tests.
    """
    path = GENERATED_DIR / "mutation-registry.json"
    if not path.exists():
        return {"generated_at": None, "entries": []}
    with open(path) as f:
        return cast(MutationRegistry, json.load(f))


def load_validation_manifest() -> ValidationManifest | None:
    """Load validation-manifest.json from last run.

    Returns dict or None if not present.
    """
    path = GENERATED_DIR / "validation-manifest.json"
    if not path.exists():
        return None
    with open(path) as f:
        return cast(ValidationManifest, json.load(f))


def load_risk_rules() -> RiskRules:
    """Load risk-rules.yaml.

    Returns dict with 'rules' list.
    Each rule has: pattern, strategy, risk, reason.
    """
    import yaml

    path = GENERATED_DIR / "risk-rules.yaml"
    if not path.exists():
        return {"rules": []}
    with open(path) as f:
        return cast(RiskRules, yaml.safe_load(f) or {"rules": []})


def get_all_capability_ids() -> list[str]:
    """Get all registered capability IDs."""
    registry = load_capability_registry()
    return [
        cap.get("id", "") for cap in registry.get("capabilities", []) if cap.get("id")
    ]


def get_capability_by_id(capability_id: str) -> dict[str, Any] | None:
    """Get a single capability by ID."""
    registry = load_capability_registry()
    for cap in registry.get("capabilities", []):
        if cap.get("id") == capability_id:
            return cap
    return None


def get_endpoints_by_capability(capability_id: str) -> list[dict[str, Any]]:
    """Get all API endpoints belonging to a capability."""
    api_map = load_api_map()
    return [
        ep
        for ep in api_map.get("endpoints", [])
        if ep.get("capability") == capability_id
    ]


def get_mutation_entries_by_capability(capability_id: str) -> list[dict[str, Any]]:
    """Get all mutation entries for a capability."""
    registry = load_mutation_registry()
    return [
        entry
        for entry in registry.get("entries", [])
        if entry.get("capability") == capability_id
    ]
