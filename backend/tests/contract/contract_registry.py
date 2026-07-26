"""Contract registry loader and writer."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
GENERATED_DIR = PROJECT_ROOT / "backend" / "tests" / "generated"


def load_registry() -> dict[str, Any]:
    """Load contract registry from generated artifacts."""
    registry_path = GENERATED_DIR / "contract-registry.json"

    if registry_path.exists():
        with open(registry_path) as f:
            return json.load(f)

    return {"routers": {}, "generated_at": None}


def load_api_map() -> dict[str, Any]:
    """Load API map with full endpoint metadata."""
    api_map_path = GENERATED_DIR / "api-map.json"

    if api_map_path.exists():
        with open(api_map_path) as f:
            return json.load(f)

    return {"endpoints": [], "generated_at": None}


def load_coverage() -> dict[str, Any]:
    """Load contract coverage metrics."""
    coverage_path = GENERATED_DIR / "contract-coverage.json"

    if coverage_path.exists():
        with open(coverage_path) as f:
            return json.load(f)

    return {}


def get_router_endpoints(router_name: str) -> list[dict[str, Any]]:
    """Get all endpoints for a specific router."""
    registry = load_registry()
    return registry.get("routers", {}).get(router_name, {}).get("endpoints", [])


def get_endpoint_schema(router_name: str, method: str, path: str) -> dict[str, Any]:
    """Get full schema for an endpoint."""
    api_map = load_api_map()

    for endpoint in api_map.get("endpoints", []):
        if (
            endpoint["router"] == router_name
            and endpoint["method"] == method.upper()
            and endpoint["endpoint"] == path
        ):
            return {
                "request_schema": endpoint.get("request_schema", {}),
                "response_schema": endpoint.get("response_schema", {}),
                "status_codes": endpoint.get("status_codes", []),
            }

    return {}