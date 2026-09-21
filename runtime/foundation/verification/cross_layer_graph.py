"""Cross-Layer Dependency Graph — Extends existing frontend/backend map with
capability-level relationships, confidence scoring, and evidence tracking.

This module builds upon the existing frontend_backend_map.py and
frontend_backend_gate.py without replacing them.
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path

from runtime.foundation.verification.endpoint_normalize import (
    EndpointNormalizer,
)
from runtime.foundation.verification.frontend_backend_map import (
    FrontendBackendMapper,
)
from runtime.foundation.verification.frontend_capability_discovery import (
    FrontendCapability,
    FrontendCapabilityDiscoverer,
)
from runtime.foundation.verification.typescript_symbol_resolver import (
    TypeScriptSymbolExtractor,
)

logger = logging.getLogger(__name__)


@dataclass
class CrossLayerEdge:
    """A relationship between frontend and backend elements."""

    source_id: str
    source_type: str
    target_id: str
    target_type: str
    relationship: str
    confidence: float
    evidence: list[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)


@dataclass
class ContractDrift:
    """Represents a detected contract drift between frontend and backend."""

    frontend_endpoint: str
    backend_endpoint: str | None
    drift_type: str
    severity: str
    description: str
    frontend_file: str | None = None
    frontend_symbol: str | None = None
    backend_router: str | None = None
    # Provenance fields for normalization mismatches
    frontend_normalized: str | None = None
    backend_normalized: str | None = None
    normalization_rules: tuple = field(default_factory=tuple)


@dataclass
class CrossLayerGraph:
    """Complete cross-layer dependency graph."""

    frontend_capabilities: dict[str, FrontendCapability] = field(default_factory=dict)
    backend_capabilities: dict[str, dict] = field(default_factory=dict)
    edges: list[CrossLayerEdge] = field(default_factory=list)
    contract_drifts: list[ContractDrift] = field(default_factory=list)
    unmapped_frontend: list[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)

    def add_edge(self, edge: CrossLayerEdge) -> None:
        self.edges.append(edge)

    def get_edges_from(self, source_id: str) -> list[CrossLayerEdge]:
        return [e for e in self.edges if e.source_id == source_id]

    def get_edges_to(self, target_id: str) -> list[CrossLayerEdge]:
        return [e for e in self.edges if e.target_id == target_id]

    def get_frontend_consumers_of_backend_endpoint(self, endpoint: str) -> list[CrossLayerEdge]:
        return [e for e in self.edges if e.target_id == endpoint and e.target_type == "endpoint"]

    def get_backend_dependencies_of_frontend_capability(self, capability_id: str) -> list[CrossLayerEdge]:
        return [e for e in self.edges if e.source_id == capability_id and e.target_type in ("endpoint", "capability")]

    def to_dict(self) -> dict:
        return {
            "frontend_capabilities": {k: v.to_dict() for k, v in self.frontend_capabilities.items()},
            "backend_capabilities": self.backend_capabilities,
            "edges": [asdict(e) for e in self.edges],
            "contract_drifts": [asdict(d) for d in self.contract_drifts],
            "unmapped_frontend": self.unmapped_frontend,
            "metadata": self.metadata,
        }


class CrossLayerGraphBuilder:
    """Builds the cross-layer dependency graph from source code."""

    def __init__(self, repo_root: Path = None):
        self.repo_root = repo_root or Path(__file__).resolve().parents[3]
        self.frontend_root = self.repo_root / "frontend"
        self.backend_root = self.repo_root / "backend"

        self.ts_extractor = TypeScriptSymbolExtractor()
        self.frontend_mapper = FrontendBackendMapper(self.repo_root)
        self.capability_discoverer = FrontendCapabilityDiscoverer(self.repo_root)

        self._graph: CrossLayerGraph | None = None
        self._api_map: dict | None = None
        self._contract_registry: dict | None = None
        self._platform_endpoints: dict[str, dict] = {}  # endpoint -> {method, router, capability}
        self._normalizer = EndpointNormalizer()

    def build(self, force_rebuild: bool = False) -> CrossLayerGraph:
        """Build the complete cross-layer graph."""
        if self._graph and not force_rebuild:
            return self._graph

        self._graph = CrossLayerGraph()

        self._graph.frontend_capabilities = self.capability_discoverer.discover_capabilities()

        self._load_backend_capabilities()
        self._scan_platform_router()

        self._build_frontend_to_backend_edges()

        self._build_backend_to_frontend_edges()

        self._detect_contract_drifts()

        self._identify_unmapped_frontend()

        return self._graph

    def _load_backend_capabilities(self) -> None:
        api_map_path = self.repo_root / "backend/tests/generated/api-map.json"
        if api_map_path.exists():
            self._api_map = json.loads(api_map_path.read_text())

            router_to_capability = {
                "accounts": "account-engine",
                "behaviour": "behaviour-engine",
                "cards": "credit-card-engine",
                "cashflow": "cashflow-engine",
                "dashboard": "ledger",
                "financial_intelligence": "financial-intelligence",
                "forecast": "financial-intelligence",
                "import": "account-engine",
                "institutions": "account-engine",
                "investments": "ledger",
                "loans": "loan-engine",
                "members": "ledger",
                "networth": "cashflow-engine",
                "reconciliation": "reconciliation",
                "reconciliation_workspace": "reconciliation",
                "reconciliations": "reconciliation",
                "transactions": "ledger",
                "categories": "ledger",
                "analytics": "ledger",
                "overview": "ledger",
                "audit": "ledger",
                "banks": "account-engine",
                "statements": "credit-card-engine",
                "credit_cards": "credit-card-engine",
                "financial_events": "ledger",
                "upload": "account-engine",
                "export": "ledger",
                "platform": "runtime-verification",
            }

            for endpoint_data in self._api_map.get("endpoints", []):
                endpoint = endpoint_data.get("endpoint", "")
                router = endpoint_data.get("router", "")
                capability = router_to_capability.get(router, "unknown")

                self._graph.backend_capabilities[endpoint] = {
                    "endpoint": endpoint,
                    "method": endpoint_data.get("method", ""),
                    "router": router,
                    "capability": capability,
                    "operation_id": endpoint_data.get("operation_id", ""),
                    "request_schema": endpoint_data.get("request_schema", {}),
                    "response_schema": endpoint_data.get("response_schema", {}),
                }

        contract_registry_path = self.repo_root / "backend/tests/generated/contract-registry.json"
        if contract_registry_path.exists():
            self._contract_registry = json.loads(contract_registry_path.read_text())

    def _scan_platform_router(self) -> None:
        """Scan platform.py router directly for endpoints not in api-map.json."""
        platform_router = self.backend_root / "src" / "routers" / "platform.py"
        if not platform_router.exists():
            return

        content = platform_router.read_text()

        # Extract router prefix
        prefix_match = re.search(
            r'APIRouter\s*\(\s*prefix\s*=\s*["\']([^"\']+)["\']', content
        )
        prefix = prefix_match.group(1) if prefix_match else ""

        # Match @router.METHOD("/path")
        pattern = r'@router\.(get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)["\']'
        matches = re.findall(pattern, content)

        for method, path in matches:
            if prefix and path:
                full_path = prefix.rstrip("/") + "/" + path.lstrip("/")
            elif prefix:
                full_path = prefix
            else:
                full_path = path

            # Store with method for method-aware matching
            self._platform_endpoints[full_path] = {
                "endpoint": full_path,
                "method": method.upper(),
                "router": "platform",
                "capability": "runtime-verification",
            }

            # Also add to backend_capabilities for edge building
            self._graph.backend_capabilities[full_path] = {
                "endpoint": full_path,
                "method": method.upper(),
                "router": "platform",
                "capability": "runtime-verification",
                "operation_id": "",
                "request_schema": {},
                "response_schema": {},
            }

    def _build_frontend_to_backend_edges(self) -> None:
        for cap_id, cap in self._graph.frontend_capabilities.items():
            for ep_info in cap.api_dependencies:
                endpoint = ep_info["endpoint"]
                method = ep_info["method"]
                # Use method-aware normalization
                fe_normalized = self._normalizer.normalize(endpoint, method)
                canonical_key = fe_normalized.canonical_path

                backend_endpoint = self._find_backend_endpoint(canonical_key)

                if backend_endpoint:
                    # Get backend method for proper normalization
                    be_info = self._graph.backend_capabilities.get(backend_endpoint, {})
                    be_method = be_info.get("method", "GET")
                    be_normalized = self._normalizer.normalize(backend_endpoint, be_method)
                    backend_cap = be_info.get("capability", "unknown")

                    edge = CrossLayerEdge(
                        source_id=cap_id,
                        source_type="capability",
                        target_id=backend_endpoint,
                        target_type="endpoint",
                        relationship="calls",
                        confidence=0.9,
                        evidence=[
                            f"Frontend hook calls {endpoint}",
                            f"Matched to backend endpoint {backend_endpoint}",
                            f"Normalization: {', '.join(fe_normalized.normalization_rules)}",
                        ],
                        metadata={
                            "frontend_endpoint": endpoint,
                            "frontend_method": method,
                            "frontend_normalized": fe_normalized.canonical_path,
                            "backend_endpoint": backend_endpoint,
                            "backend_method": be_method,
                            "backend_normalized": be_normalized.canonical_path,
                            "backend_capability": backend_cap,
                            "normalization_rules": fe_normalized.normalization_rules,
                        }
                    )
                    self._graph.add_edge(edge)

                    if backend_cap != "unknown":
                        cap_edge = CrossLayerEdge(
                            source_id=cap_id,
                            source_type="capability",
                            target_id=backend_cap,
                            target_type="capability",
                            relationship="depends_on",
                            confidence=0.8,
                            evidence=[f"Frontend capability {cap_id} calls backend endpoint {backend_endpoint}"],
                            metadata={
                                "via_endpoint": backend_endpoint,
                            }
                        )
                        self._graph.add_edge(cap_edge)
                else:
                    edge = CrossLayerEdge(
                        source_id=cap_id,
                        source_type="capability",
                        target_id=canonical_key,
                        target_type="endpoint",
                        relationship="calls",
                        confidence=0.3,
                        evidence=[f"Frontend calls {endpoint} but no matching backend endpoint found"],
                        metadata={
                            "frontend_endpoint": endpoint,
                            "frontend_method": method,
                            "frontend_normalized": canonical_key,
                            "drift_suspected": True,
                        }
                    )
                    self._graph.add_edge(edge)

    def _build_backend_to_frontend_edges(self) -> None:
        consumer_map = self.frontend_mapper.build_consumer_map()

        for endpoint, consumer_info in consumer_map.items():
            for hook_file in consumer_info.hook_files:
                hook_path = Path(hook_file)
                if hook_path.exists():
                    cap_id = self._find_capability_for_file(hook_path)
                    if cap_id:
                        edge = CrossLayerEdge(
                            source_id=endpoint,
                            source_type="endpoint",
                            target_id=cap_id,
                            target_type="capability",
                            relationship="consumed_by",
                            confidence=0.95,
                            evidence=[f"Backend endpoint {endpoint} consumed by frontend hook {hook_file}"],
                            metadata={
                                "consumer_file": hook_file,
                                "consumer_type": "hook",
                            }
                        )
                        self._graph.add_edge(edge)

            for comp_file in consumer_info.component_files:
                comp_path = Path(comp_file)
                if comp_path.exists():
                    cap_id = self._find_capability_for_file(comp_path)
                    if cap_id:
                        edge = CrossLayerEdge(
                            source_id=endpoint,
                            source_type="endpoint",
                            target_id=cap_id,
                            target_type="capability",
                            relationship="consumed_by",
                            confidence=0.9,
                            evidence=[f"Backend endpoint {endpoint} consumed by frontend component {comp_file}"],
                            metadata={
                                "consumer_file": comp_file,
                                "consumer_type": "component",
                            }
                        )
                        self._graph.add_edge(edge)

    def _find_capability_for_file(self, file_path: Path) -> str | None:
        for cap_id, cap in self._graph.frontend_capabilities.items():
            if any(str(f) == str(file_path) for f in cap.files):
                return cap_id
        return None

    def _find_backend_endpoint(self, canonical_key: str) -> str | None:
        # First check api_map endpoints
        if self._api_map:
            for endpoint_data in self._api_map.get("endpoints", []):
                backend_endpoint = endpoint_data.get("endpoint", "")
                method = endpoint_data.get("method", "GET")
                be_normalized = self._normalizer.normalize(backend_endpoint, method)
                if be_normalized.canonical_path == canonical_key:
                    return backend_endpoint

        # Then check platform router endpoints
        for endpoint, info in self._platform_endpoints.items():
            method = info.get("method", "GET")
            be_normalized = self._normalizer.normalize(endpoint, method)
            if be_normalized.canonical_path == canonical_key:
                return endpoint

        return None

    def _detect_contract_drifts(self) -> None:
        if not self._api_map and not self._platform_endpoints:
            return

        # Collect all frontend endpoints with their capabilities
        frontend_endpoints = []
        for cap_id, cap in self._graph.frontend_capabilities.items():
            for ep_info in cap.api_dependencies:
                endpoint = ep_info["endpoint"]
                method = ep_info["method"]
                fe_normalized = self._normalizer.normalize(endpoint, method)
                frontend_endpoints.append({
                    "original": endpoint,
                    "method": method,
                    "normalized": fe_normalized,
                    "capability_id": cap_id,
                    "files": cap.files,
                })

        # Collect all backend endpoints
        backend_endpoints = []

        if self._api_map:
            for endpoint_data in self._api_map.get("endpoints", []):
                endpoint = endpoint_data.get("endpoint", "")
                method = endpoint_data.get("method", "GET")
                be_normalized = self._normalizer.normalize(endpoint, method)
                backend_endpoints.append({
                    "original": endpoint,
                    "method": method,
                    "normalized": be_normalized,
                    "router": endpoint_data.get("router", ""),
                })

        for endpoint, info in self._platform_endpoints.items():
            method = info.get("method", "GET")
            be_normalized = self._normalizer.normalize(endpoint, method)
            backend_endpoints.append({
                "original": endpoint,
                "method": method,
                "normalized": be_normalized,
                "router": "platform",
            })

        # Build lookup maps by canonical key
        backend_by_canonical = {be["normalized"].canonical_path: be for be in backend_endpoints}

        # Classify each frontend endpoint
        for fe in frontend_endpoints:
            canonical_key = fe["normalized"].canonical_path

            if canonical_key in backend_by_canonical:
                be = backend_by_canonical[canonical_key]
                # Semantic match - endpoints are equivalent after normalization
                # No drift created; provenance preserved in edge metadata
                # (Edge already created in _build_frontend_to_backend_edges)
                pass
            else:
                # No matching backend endpoint
                # Classify the type of mismatch
                fe_original = fe["original"]

                # Check for query parameter differences
                if "?" in fe_original:
                    drift_type = "query_parameter"
                    severity = "medium"
                    description = f"Frontend calls {fe_original} with query params but no matching backend endpoint"
                # Check for encodeURIComponent
                elif "encodeURIComponent" in fe_original:
                    drift_type = "encoding_mismatch"
                    severity = "medium"
                    description = f"Frontend uses encodeURIComponent in {fe_original} but no matching backend endpoint"
                # Check for /platform/ prefix without /v1
                elif fe_original.startswith("/platform/") and not fe_original.startswith("/platform/v1/"):
                    drift_type = "prefix_mismatch"
                    severity = "medium"
                    description = f"Frontend uses /platform/ prefix without /v1: {fe_original}"
                # Check for singular vs plural (reconciliation vs reconciliations)
                elif "/reconciliation/" in fe_original or fe_original == "/api/reconciliation":
                    drift_type = "path_mismatch"
                    severity = "high"
                    description = f"Frontend uses singular 'reconciliation' but backend uses plural 'reconciliations': {fe_original}"
                else:
                    drift_type = "missing_endpoint"
                    severity = "critical"
                    description = f"Frontend calls {fe_original} but no matching backend endpoint exists"

                drift = ContractDrift(
                    frontend_endpoint=fe_original,
                    backend_endpoint=None,
                    drift_type=drift_type,
                    severity=severity,
                    description=description,
                    frontend_file=str(fe["files"][0]) if fe["files"] else None,
                    frontend_symbol=fe["capability_id"],
                    frontend_normalized=fe["normalized"].canonical_path,
                    normalization_rules=fe["normalized"].normalization_rules,
                )
                self._graph.contract_drifts.append(drift)

        logger.info(f"Contract drifts detected: {len(self._graph.contract_drifts)}")

    def _identify_unmapped_frontend(self) -> None:
        all_ts_files = list(self.frontend_root.rglob("*.ts")) + list(self.frontend_root.rglob("*.tsx"))

        filtered_files = []
        for f in all_ts_files:
            parts = f.parts
            if not any(part in ["node_modules", ".next", "dist", "__tests__", ".git", "tests"] for part in parts):
                filtered_files.append(f)

        mapped_files = set()
        for cap in self._graph.frontend_capabilities.values():
            for f in cap.files:
                mapped_files.add(str(f))

        for f in filtered_files:
            rel_path = str(f.relative_to(self.repo_root))
            if rel_path not in mapped_files:
                self._graph.unmapped_frontend.append(rel_path)

    def save_graph(self, output_path: Path) -> None:
        if self._graph:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(json.dumps(self._graph.to_dict(), indent=2))

    def load_graph(self, input_path: Path) -> CrossLayerGraph:
        data = json.loads(input_path.read_text())
        self._graph = CrossLayerGraph()
        self._graph.frontend_capabilities = data.get("frontend_capabilities", {})
        self._graph.backend_capabilities = data.get("backend_capabilities", {})
        self._graph.edges = [CrossLayerEdge(**e) for e in data.get("edges", [])]
        self._graph.contract_drifts = [ContractDrift(**d) for d in data.get("contract_drifts", [])]
        self._graph.unmapped_frontend = data.get("unmapped_frontend", [])
        self._graph.metadata = data.get("metadata", {})
        return self._graph


def build_cross_layer_graph(repo_root: Path = None) -> CrossLayerGraph:
    builder = CrossLayerGraphBuilder(repo_root)
    return builder.build()


if __name__ == "__main__":
    from pathlib import Path

    builder = CrossLayerGraphBuilder()
    graph = builder.build()

    print(f"Frontend capabilities: {len(graph.frontend_capabilities)}")
    print(f"Backend endpoints: {len(graph.backend_capabilities)}")
    print(f"Edges: {len(graph.edges)}")
    print(f"Contract drifts: {len(graph.contract_drifts)}")
    print(f"Unmapped frontend files: {len(graph.unmapped_frontend)}")

    for drift in graph.contract_drifts:
        print(f"\nDRIFT: {drift.drift_type} - {drift.severity}")
        print(f"  Frontend: {drift.frontend_endpoint}")
        print(f"  Backend: {drift.backend_endpoint}")
        print(f"  Description: {drift.description}")

    builder.save_graph(Path("runtime/generated/cross-layer-graph.json"))
    print("\nGraph saved to runtime/generated/cross-layer-graph.json")
