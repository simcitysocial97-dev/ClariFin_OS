#!/usr/bin/env python3
"""Contract Validation Framework (CoVF) Discovery Tool.

Discovers API endpoints from live FastAPI application and generates:
- api-map.json: All endpoints with metadata
- contract-registry.json: Request/response schemas
- contract-coverage.json: Test coverage metrics per router
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any, cast

BACKEND_DIR = Path(__file__).parent.parent  # backend/
PROJECT_ROOT = BACKEND_DIR.parent  # project root
GENERATED_DIR = PROJECT_ROOT / "backend" / "tests" / "generated"

sys.path.insert(0, str(BACKEND_DIR))
from src.api import app  # noqa: E402


def discover_endpoints() -> list[dict[str, Any]]:
    """Discover all endpoints from FastAPI app using OpenAPI schema."""
    openapi_schema = app.openapi()

    endpoints = []

    paths = openapi_schema.get("paths", {})
    for path, methods in paths.items():
        for method, spec in methods.items():
            if method in ("get", "post", "put", "delete", "patch"):
                tags = spec.get("tags", [])
                endpoint = {
                    "router": extract_router_from_path(path, tags),
                    "endpoint": path,
                    "method": method.upper(),
                    "tags": tags,
                    "summary": spec.get("summary", ""),
                    "operation_id": spec.get("operationId", ""),
                    "request_schema": extract_request_schema(spec, method),
                    "response_schema": extract_response_schema(spec),
                    "status_codes": extract_status_codes(spec),
                    "parameters": extract_parameters(spec, method),
                }
                endpoints.append(endpoint)

    return endpoints


def extract_router_from_path(path: str, tags: list[str] | None = None) -> str:
    """Extract router name from path or tags.

    FastAPI OpenAPI tags usually contain the router name.
    Paths are like /api/v1/accounts, /api/cashflow/monthly, etc.
    """
    # Prefer tags for router identification
    if tags and len(tags) > 0:
        tag = tags[0].lower().replace("-", "_")
        if tag:
            return tag

    # Remove leading/trailing slashes and split
    segments = [s for s in path.split("/") if s and not s.startswith("v")]

    if not segments:
        return "root"

    # Map segments to router names
    first = segments[0].lower()

    # Handle common prefixes
    if first in ("accounts", "account"):
        return "accounts"
    if first in ("credit-cards", "cc"):
        return "credit_cards"
    if first in ("loans", "loan"):
        return "loans"
    if first in ("cashflow", "cash"):
        return "cashflow"
    if first in ("transactions", "txn"):
        return "transactions"
    # Handle financial-intelligence paths
    if first in ("financial-intelligence", "financial_intelligence"):
        return "financial_intelligence"

    return first.replace("-", "_")


def extract_request_schema(spec: dict[str, Any], method: str) -> dict[str, Any]:
    """Extract request schema from OpenAPI operation spec."""
    request_body = spec.get("requestBody", {})

    if not request_body:
        return {}

    content = request_body.get("content", {})
    json_content = content.get("application/json", {})
    schema = json_content.get("schema", {})

    return cast(dict[str, Any], schema)


def extract_response_schema(spec: dict[str, Any]) -> dict[str, Any]:
    """Extract response schema from OpenAPI operation spec."""
    responses = spec.get("responses", {})

    # Get schema for first successful response (200, 201, etc.)
    for code in ("200", "201", "204"):
        if code in responses:
            content = responses[code].get("content", {})
            json_content = content.get("application/json", {})
            schema = json_content.get("schema", {})
            if schema:
                return cast(dict[str, Any], schema)

    # Fallback: get any response with schema
    for _code, response in responses.items():
        content = response.get("content", {})
        json_content = content.get("application/json", {})
        schema = json_content.get("schema", {})
        if schema:
            return cast(dict[str, Any], schema)

    return {}


def extract_status_codes(spec: dict[str, Any]) -> list[str]:
    """Extract all status codes from operation spec."""
    responses = spec.get("responses", {})
    return list(responses.keys())


def extract_parameters(spec: dict[str, Any], method: str) -> list[dict[str, Any]]:
    """Extract path/query parameters from operation spec."""
    parameters = spec.get("parameters", [])

    if method.lower() == "get":
        # Also check for query parameters in requestBody (some FastAPI patterns)
        pass

    return cast(list[dict[str, Any]], parameters)


def map_endpoints_to_capabilities(
    endpoints: list[dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    """Group endpoints by capability using router-to-capability mapping."""
    # Load capability manifests
    capability_dir = PROJECT_ROOT / "memory-bank" / "capabilities"
    capability_map: dict[str, str] = {}

    for manifest_file in capability_dir.glob("*.yaml"):
        import yaml

        with open(manifest_file) as f:
            manifest = yaml.safe_load(f)
            for router in manifest.get("routers", []):
                router_name = Path(router).stem.replace("-", "_")
                capability_map[router_name] = manifest.get("id", "")

    # Group endpoints by capability
    by_capability: dict[str, list[dict[str, Any]]] = {}
    for ep in endpoints:
        router = ep["router"]
        capability = capability_map.get(router, "unknown")

        if capability not in by_capability:
            by_capability[capability] = []
        by_capability[capability].append(ep)
        ep["capability"] = capability

    return by_capability


def generate_coverage_metrics(
    endpoints: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    """Generate coverage metrics per router."""
    coverage: dict[str, dict[str, Any]] = {}

    for ep in endpoints:
        router = ep["router"]

        if router not in coverage:
            coverage[router] = {
                "endpoints": 0,
                "contract_published": False,
                "capabilities": set(),
            }

        coverage[router]["endpoints"] += 1
        coverage[router]["capabilities"].add(ep.get("capability", "unknown"))

    # Convert sets to lists for JSON serialization
    for router in coverage:
        coverage[router]["capabilities"] = sorted(coverage[router]["capabilities"])
        coverage[router]["tested"] = 0  # Will be updated by test runs
        coverage[router]["snapshots"] = 0
        coverage[router]["coverage"] = "0%"

    return coverage


def save_artifacts(
    endpoints: list[dict[str, Any]], coverage: dict[str, dict[str, Any]]
) -> None:
    """Save all generated artifacts."""
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)

    # Deterministic content hash instead of mtime timestamp
    content_hash = hashlib.sha256(
        json.dumps(endpoints, sort_keys=True).encode()
    ).hexdigest()[:16]

    # api-map.json - all endpoints with full metadata
    with open(GENERATED_DIR / "api-map.json", "w") as f:
        json.dump(
            {
                "endpoints": endpoints,
                "generated_at": content_hash,
            },
            f,
            indent=2,
        )

    # contract-registry.json - simplified registry for tests
    registry: dict[str, Any] = {
        "routers": {},
        "generated_at": content_hash,
    }

    for ep in endpoints:
        router = ep["router"]
        if router not in registry["routers"]:
            registry["routers"][router] = {
                "endpoints": [],
                "capability": ep.get("capability", "unknown"),
            }

        registry["routers"][router]["endpoints"].append(
            {
                "method": ep["method"],
                "path": ep["endpoint"],
                "request_schema": ep["request_schema"],
                "response_schema": ep["response_schema"],
                "status_codes": ep["status_codes"],
            }
        )

    with open(GENERATED_DIR / "contract-registry.json", "w") as f:
        json.dump(registry, f, indent=2)

    # contract-coverage.json - coverage metrics
    with open(GENERATED_DIR / "contract-coverage.json", "w") as f:
        json.dump(coverage, f, indent=2)


def main() -> None:
    """Main discovery entry point."""
    print("Discovering API endpoints from FastAPI...")
    endpoints = discover_endpoints()
    print(f"Found {len(endpoints)} endpoints")

    print("Mapping to capabilities...")
    by_capability = map_endpoints_to_capabilities(endpoints)

    print("Generating coverage metrics...")
    for router, eps in by_capability.items():
        print(f"  {router}: {len(eps)} endpoints")

    coverage = generate_coverage_metrics(endpoints)

    print("Saving artifacts...")
    save_artifacts(endpoints, coverage)

    print("Done!")


if __name__ == "__main__":
    main()
