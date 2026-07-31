"""API scanner — loads existing API metadata from canonical sources.

Reads (does NOT duplicate):
- ``backend/tests/generated/api-map.json`` — full endpoint metadata with capability mapping
- ``frontend/api-schema.json`` — OpenAPI 3.1.0 specification
- ``backend/tests/generated/contract-registry.json`` — router-level contract registry

Creates ``api`` and ``endpoint`` nodes and ``implements`` edges from
capabilities to endpoints.
"""

from __future__ import annotations


from runtime.foundation.repository.scanner.base import BaseScanner, ScanResult


class ApiScanner(BaseScanner):
    """Load API endpoints from existing canonical sources."""

    def scan(self) -> ScanResult:
        result = ScanResult()

        self._scan_api_map(result)
        self._scan_openapi(result)
        self._scan_contract_registry(result)

        return result

    def _scan_api_map(self, result: ScanResult) -> None:
        """Load api-map.json for endpoint metadata with capability mapping."""
        api_map = self.safe_read_json(self.generated_dir / "api-map.json")
        if api_map is None:
            return

        generated_at = api_map.get("generated_at", "")
        result.add_node(
            node_type="generated_artifact",
            name="api-map.json",
            path="backend/tests/generated/api-map.json",
            source="generated:api-map",
            properties={
                "generated_at": generated_at,
                "endpoint_count": len(api_map.get("endpoints", [])),
            },
        )

        for ep in api_map.get("endpoints", []):
            method = ep.get("method", "GET")
            path = ep.get("endpoint", ep.get("path", ""))
            router = ep.get("router", "")
            capability = ep.get("capability", "unknown")
            operation_id = ep.get("operation_id", "")
            summary = ep.get("summary", "")
            tags = ep.get("tags", [])

            ep_id = f"endpoint:{method} {path}"
            result.add_node(
                node_type="endpoint",
                name=f"{method} {path}",
                path=f"src/routers/{router}.py" if router else "",
                source="generated:api-map",
                properties={
                    "method": method,
                    "path": path,
                    "operation_id": operation_id,
                    "router": router,
                    "capability": capability,
                    "summary": summary,
                    "tags": tags,
                    "status_codes": ep.get("status_codes", []),
                },
            )

            # Edge: capability implements endpoint
            if capability and capability != "unknown":
                result.add_edge(
                    source_id=f"capability:{capability}",
                    target_id=ep_id,
                    relationship="implements",
                    confidence=0.9,
                    evidence="api-map.json:capability",
                )

            # Edge: router module implements endpoint
            if router:
                result.add_edge(
                    source_id=f"module:src/routers/{router}.py",
                    target_id=ep_id,
                    relationship="implements",
                    confidence=0.9,
                    evidence="api-map.json:router",
                )

    def _scan_openapi(self, result: ScanResult) -> None:
        """Load OpenAPI spec from frontend/api-schema.json."""
        spec = self.safe_read_json(self.frontend_dir / "api-schema.json")
        if spec is None:
            return

        result.add_node(
            node_type="api",
            name="Personal Finance API",
            path="frontend/api-schema.json",
            source="openapi:api-schema",
            properties={
                "openapi_version": spec.get("openapi", ""),
                "title": spec.get("info", {}).get("title", ""),
                "version": spec.get("info", {}).get("version", ""),
                "path_count": len(spec.get("paths", {})),
                "schema_count": len(spec.get("components", {}).get("schemas", {})),
            },
        )

        # Create API nodes for each path
        for path, methods in spec.get("paths", {}).items():
            for method, details in methods.items():
                if method not in ("get", "post", "put", "delete", "patch"):
                    continue
                method_upper = method.upper()
                ep_id = f"endpoint:{method_upper} {path}"
                # Only add if not already present from api-map
                existing = result.get_node(ep_id) if hasattr(result, "get_node") else None
                if existing is None:
                    result.add_node(
                        node_type="endpoint",
                        name=f"{method_upper} {path}",
                        path="frontend/api-schema.json",
                        source="openapi:api-schema",
                        properties={
                            "method": method_upper,
                            "path": path,
                            "operation_id": details.get("operationId", ""),
                            "summary": details.get("summary", ""),
                            "tags": details.get("tags", []),
                        },
                    )

    def _scan_contract_registry(self, result: ScanResult) -> None:
        """Load contract-registry.json for router-level contract metadata."""
        registry = self.safe_read_json(self.generated_dir / "contract-registry.json")
        if registry is None:
            return

        result.add_node(
            node_type="generated_artifact",
            name="contract-registry.json",
            path="backend/tests/generated/contract-registry.json",
            source="generated:contract-registry",
            properties={
                "generated_at": registry.get("generated_at", ""),
                "router_count": len(registry.get("routers", {})),
            },
        )

        for router_name, router_data in registry.get("routers", {}).items():
            for ep in router_data.get("endpoints", []):
                method = ep.get("method", "GET")
                path = ep.get("path", "")
                ep_id = f"endpoint:{method} {path}"

                # Update existing endpoint node with contract info
                for node in result.nodes:
                    if node.id == ep_id:
                        node.properties["request_schema"] = ep.get(
                            "request_schema", {}
                        )
                        node.properties["response_schema"] = ep.get(
                            "response_schema", {}
                        )
                        node.properties["status_codes"] = ep.get(
                            "status_codes", []
                        )
                        break
