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
from typing import Dict, List, Optional, Set, Tuple

from runtime.foundation.verification.frontend_backend_map import (
    ConsumerInfo,
    FrontendBackendMapper,
)
from runtime.foundation.verification.frontend_capability_discovery import (
    FrontendCapability,
    FrontendCapabilityDiscoverer,
    FrontendCapabilityKind,
)
from runtime.foundation.verification.typescript_symbol_resolver import (
    TypeScriptSymbol,
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
    evidence: List[str] = field(default_factory=list)
    metadata: Dict = field(default_factory=dict)


@dataclass
class ContractDrift:
    """Represents a detected contract drift between frontend and backend."""
    
    frontend_endpoint: str
    backend_endpoint: Optional[str]
    drift_type: str
    severity: str
    description: str
    frontend_file: Optional[str] = None
    frontend_symbol: Optional[str] = None
    backend_router: Optional[str] = None


@dataclass
class CrossLayerGraph:
    """Complete cross-layer dependency graph."""
    
    frontend_capabilities: Dict[str, FrontendCapability] = field(default_factory=dict)
    backend_capabilities: Dict[str, dict] = field(default_factory=dict)
    edges: List[CrossLayerEdge] = field(default_factory=list)
    contract_drifts: List[ContractDrift] = field(default_factory=list)
    unmapped_frontend: List[str] = field(default_factory=list)
    metadata: Dict = field(default_factory=dict)
    
    def add_edge(self, edge: CrossLayerEdge) -> None:
        self.edges.append(edge)
    
    def get_edges_from(self, source_id: str) -> List[CrossLayerEdge]:
        return [e for e in self.edges if e.source_id == source_id]
    
    def get_edges_to(self, target_id: str) -> List[CrossLayerEdge]:
        return [e for e in self.edges if e.target_id == target_id]
    
    def get_frontend_consumers_of_backend_endpoint(self, endpoint: str) -> List[CrossLayerEdge]:
        return [e for e in self.edges if e.target_id == endpoint and e.target_type == "endpoint"]
    
    def get_backend_dependencies_of_frontend_capability(self, capability_id: str) -> List[CrossLayerEdge]:
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
        self.repo_root = repo_root or Path.cwd()
        self.frontend_root = self.repo_root / "frontend"
        self.backend_root = self.repo_root / "backend"
        
        self.ts_extractor = TypeScriptSymbolExtractor()
        self.frontend_mapper = FrontendBackendMapper(self.repo_root)
        self.capability_discoverer = FrontendCapabilityDiscoverer(self.repo_root)
        
        self._graph: Optional[CrossLayerGraph] = None
        self._api_map: Optional[dict] = None
        self._contract_registry: Optional[dict] = None
    
    def build(self, force_rebuild: bool = False) -> CrossLayerGraph:
        """Build the complete cross-layer graph."""
        if self._graph and not force_rebuild:
            return self._graph
        
        self._graph = CrossLayerGraph()
        
        self._graph.frontend_capabilities = self.capability_discoverer.discover_capabilities()
        
        self._load_backend_capabilities()
        
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
    
    def _build_frontend_to_backend_edges(self) -> None:
        for cap_id, cap in self._graph.frontend_capabilities.items():
            for endpoint in cap.api_dependencies:
                normalized_endpoint = self._normalize_endpoint(endpoint)
                
                backend_endpoint = self._find_backend_endpoint(normalized_endpoint)
                
                if backend_endpoint:
                    backend_cap = self._graph.backend_capabilities.get(backend_endpoint, {}).get("capability", "unknown")
                    
                    edge = CrossLayerEdge(
                        source_id=cap_id,
                        source_type="capability",
                        target_id=backend_endpoint,
                        target_type="endpoint",
                        relationship="calls",
                        confidence=0.9,
                        evidence=[f"Frontend hook calls {endpoint}", f"Matched to backend endpoint {backend_endpoint}"],
                        metadata={
                            "frontend_endpoint": endpoint,
                            "backend_endpoint": backend_endpoint,
                            "backend_capability": backend_cap,
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
                        target_id=normalized_endpoint,
                        target_type="endpoint",
                        relationship="calls",
                        confidence=0.3,
                        evidence=[f"Frontend calls {endpoint} but no matching backend endpoint found"],
                        metadata={
                            "frontend_endpoint": endpoint,
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
    
    def _find_capability_for_file(self, file_path: Path) -> Optional[str]:
        for cap_id, cap in self._graph.frontend_capabilities.items():
            if any(str(f) == str(file_path) for f in cap.files):
                return cap_id
        return None
    
    def _normalize_endpoint(self, endpoint: str) -> str:
        endpoint = re.sub(r"\$\{[^}]+\}", ":param", endpoint)
        endpoint = re.sub(r"\{[^}]+\}", ":param", endpoint)
        endpoint = endpoint.split("?")[0]
        return endpoint
    
    def _find_backend_endpoint(self, normalized_frontend_endpoint: str) -> Optional[str]:
        if not self._api_map:
            return None
        
        for endpoint_data in self._api_map.get("endpoints", []):
            backend_endpoint = endpoint_data.get("endpoint", "")
            normalized_backend = self._normalize_endpoint(backend_endpoint)
            if normalized_backend == normalized_frontend_endpoint:
                return backend_endpoint
        
        return None
    
    def _detect_contract_drifts(self) -> None:
        if not self._api_map or not self._contract_registry:
            return
        
        frontend_endpoints = set()
        for cap in self._graph.frontend_capabilities.values():
            for endpoint in cap.api_dependencies:
                frontend_endpoints.add(self._normalize_endpoint(endpoint))
        
        backend_endpoints = set()
        for endpoint_data in self._api_map.get("endpoints", []):
            backend_endpoints.add(self._normalize_endpoint(endpoint_data.get("endpoint", "")))
        
        for fe_endpoint in frontend_endpoints:
            if fe_endpoint not in backend_endpoints:
                for cap_id, cap in self._graph.frontend_capabilities.items():
                    for endpoint in cap.api_dependencies:
                        if self._normalize_endpoint(endpoint) == fe_endpoint:
                            drift = ContractDrift(
                                frontend_endpoint=endpoint,
                                backend_endpoint=None,
                                drift_type="missing_endpoint",
                                severity="critical",
                                description=f"Frontend calls {endpoint} but no matching backend endpoint exists",
                                frontend_file=str(cap.files[0]) if cap.files else None,
                                frontend_symbol=cap_id,
                            )
                            self._graph.contract_drifts.append(drift)
                            break
        
        logger.info("Schema mismatch detection available but requires schema comparison implementation")
    
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