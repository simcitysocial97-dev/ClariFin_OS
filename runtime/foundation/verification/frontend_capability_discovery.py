"""Frontend Capability Discovery — Maps frontend symbols to capability identifiers.

This module extends the existing capability model to represent frontend
responsibility without creating a parallel capability registry.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, List

from runtime.foundation.verification.typescript_symbol_resolver import TypeScriptSymbol, TypeScriptSymbolExtractor


class FrontendCapabilityKind(str, Enum):
    """Classification of frontend capabilities."""
    
    ROUTE = "frontend_route"
    PAGE = "frontend_page"
    COMPONENT = "frontend_component"
    HOOK = "frontend_hook"
    STORE = "frontend_store"
    API_CLIENT = "frontend_api_client"
    DTO_TYPE = "frontend_dto_type"
    UTILITY = "frontend_utility"
    CONFIGURATION = "frontend_config"
    TEST = "frontend_test"
    E2E = "frontend_e2e"
    GENERATED = "frontend_generated"
    LEGACY = "frontend_legacy"


PATH_TO_KIND = {
    "frontend/app/": FrontendCapabilityKind.ROUTE,
    "frontend/components/": FrontendCapabilityKind.COMPONENT,
    "frontend/lib/hooks/": FrontendCapabilityKind.HOOK,
    "frontend/lib/store/": FrontendCapabilityKind.STORE,
    "frontend/lib/api/": FrontendCapabilityKind.API_CLIENT,
    "frontend/types/": FrontendCapabilityKind.DTO_TYPE,
    "frontend/lib/utils/": FrontendCapabilityKind.UTILITY,
    "frontend/lib/formatters/": FrontendCapabilityKind.UTILITY,
    "frontend/lib/validation/": FrontendCapabilityKind.UTILITY,
    "frontend/lib/mappers/": FrontendCapabilityKind.UTILITY,
    "frontend/lib/simulation/": FrontendCapabilityKind.COMPONENT,
    "frontend/lib/renderers/": FrontendCapabilityKind.COMPONENT,
    "frontend/lib/visualization/": FrontendCapabilityKind.COMPONENT,
    "frontend/lib/graph/": FrontendCapabilityKind.COMPONENT,
    "frontend/lib/navigation/": FrontendCapabilityKind.COMPONENT,
    "frontend/lib/interaction/": FrontendCapabilityKind.COMPONENT,
    "frontend/lib/command/": FrontendCapabilityKind.COMPONENT,
    "frontend/lib/timeline/": FrontendCapabilityKind.COMPONENT,
    "frontend/lib/groups/": FrontendCapabilityKind.COMPONENT,
    "frontend/lib/sort/": FrontendCapabilityKind.COMPONENT,
    "frontend/lib/filters/": FrontendCapabilityKind.UTILITY,
    "frontend/__tests__/": FrontendCapabilityKind.TEST,
    "frontend/tests/e2e/": FrontendCapabilityKind.E2E,
    "frontend/generated/": FrontendCapabilityKind.GENERATED,
    "frontend/app/platform/": FrontendCapabilityKind.ROUTE,
}

DOMAIN_MAPPING = {
    "accounts": "frontend-accounts",
    "behaviour": "frontend-behaviour",
    "behavior": "frontend-behaviour",
    "cards": "frontend-cards",
    "cashflow": "frontend-cashflow",
    "dashboard": "frontend-dashboard",
    "forecast": "frontend-forecast",
    "investments": "frontend-investments",
    "loans": "frontend-loans",
    "net-worth": "frontend-networth",
    "networth": "frontend-networth",
    "reconciliation": "frontend-reconciliation",
    "transactions": "frontend-transactions",
    "settings": "frontend-settings",
    "platform": "frontend-platform",
    "command-center": "frontend-command-center",
}


@dataclass
class FrontendCapability:
    """A frontend capability with evidence-backed attribution."""
    
    capability_id: str
    name: str
    kind: FrontendCapabilityKind
    domain: str
    symbols: List[TypeScriptSymbol] = field(default_factory=list)
    files: List[Path] = field(default_factory=list)
    api_dependencies: List[str] = field(default_factory=list)
    backend_capabilities: List[str] = field(default_factory=list)
    test_files: List[Path] = field(default_factory=list)
    e2e_files: List[Path] = field(default_factory=list)
    confidence: float = 1.0
    attribution_status: str = "mapped"
    
    def to_dict(self) -> dict:
        return {
            "capability_id": self.capability_id,
            "name": self.name,
            "kind": self.kind.value,
            "domain": self.domain,
            "symbol_count": len(self.symbols),
            "file_count": len(self.files),
            "files": [str(f) for f in self.files],
            "api_dependencies": self.api_dependencies,
            "backend_capabilities": self.backend_capabilities,
            "test_files": [str(f) for f in self.test_files],
            "e2e_files": [str(f) for f in self.e2e_files],
            "confidence": self.confidence,
            "attribution_status": self.attribution_status,
        }


class FrontendCapabilityDiscoverer:
    """Discovers and attributes frontend capabilities from source code."""
    
    def __init__(self, repo_root: Path = None):
        self.repo_root = repo_root or Path.cwd()
        self.frontend_root = self.repo_root / "frontend"
        self.ts_extractor = TypeScriptSymbolExtractor()
        self._frontend_backend_mapper = None
    
    @property
    def frontend_backend_mapper(self):
        if self._frontend_backend_mapper is None:
            from runtime.foundation.verification.frontend_backend_map import FrontendBackendMapper
            self._frontend_backend_mapper = FrontendBackendMapper(self.repo_root)
        return self._frontend_backend_mapper
    
    def _classify_file(self, file_path: Path) -> FrontendCapabilityKind:
        """Classify a file by its path."""
        try:
            rel_path = str(file_path.relative_to(self.repo_root))
        except ValueError:
            return FrontendCapabilityKind.UTILITY
        
        for prefix, kind in PATH_TO_KIND.items():
            if rel_path.startswith(prefix):
                return kind
        
        if rel_path.endswith(".test.ts") or rel_path.endswith(".test.tsx") or "__tests__" in rel_path:
            return FrontendCapabilityKind.TEST
        if rel_path.startswith("frontend/tests/e2e/"):
            return FrontendCapabilityKind.E2E
        if "generated" in rel_path:
            return FrontendCapabilityKind.GENERATED
            
        return FrontendCapabilityKind.UTILITY
    
    def _extract_domain(self, file_path: Path) -> str:
        """Extract the domain from file path."""
        try:
            rel_path = str(file_path.relative_to(self.frontend_root))
        except ValueError:
            return "frontend-shared"
        
        parts = rel_path.split("/")
        
        if parts[0] == "app" and len(parts) > 1:
            domain = parts[1].replace("-page", "").replace("-workspace", "")
            return DOMAIN_MAPPING.get(domain, f"frontend-{domain}")
        
        if parts[0] == "components" and len(parts) > 1:
            domain = parts[1]
            return DOMAIN_MAPPING.get(domain, f"frontend-{domain}")
        
        if parts[0] == "lib" and parts[1] == "hooks" and len(parts) > 2:
            hook_name = parts[2].replace(".ts", "").replace("use-", "")
            for key, value in DOMAIN_MAPPING.items():
                if key in hook_name:
                    return value
        
        if parts[0] == "lib" and len(parts) > 1:
            domain = parts[1]
            return DOMAIN_MAPPING.get(domain, f"frontend-{domain}")
        
        return "frontend-shared"
    
    def _get_api_dependencies(self, symbols: List[TypeScriptSymbol], file_path: Path) -> List[str]:
        """Extract API dependencies from symbols and file content."""
        endpoints = set()
        
        try:
            content = file_path.read_text(encoding="utf-8")
            import re
            patterns = [
                r"""apiFetch\s*\(\s*['"`]([^'"`]+)['"`]""",
                r"""apiFetchJson\s*\(\s*['"`]([^'"`]+)['"`]""",
                r"""fetch\s*\(\s*['"`]([^'"`]+)['"`]""",
            ]
            for pattern in patterns:
                matches = re.findall(pattern, content)
                for match in matches:
                    if match.startswith("/api/") or match.startswith("/platform/"):
                        endpoints.add(match)
        except Exception:
            pass
        
        return list(endpoints)
    
    def _get_backend_capabilities(self, api_endpoints: List[str]) -> List[str]:
        """Map API endpoints to backend capabilities."""
        endpoint_to_capability = self._build_endpoint_capability_map()
        
        backend_caps = set()
        for endpoint in api_endpoints:
            normalized = endpoint
            if "${" in endpoint:
                import re
                normalized = re.sub(r"\$\{[^}]+\}", ":param", endpoint)
            normalized = normalized.replace("{id}", ":param").replace("{", ":param").replace("}", "")
            normalized = normalized.split("?")[0]
            
            for consumer_endpoint in endpoint_to_capability:
                if self._endpoints_match(normalized, consumer_endpoint):
                    cap = endpoint_to_capability[consumer_endpoint]
                    if cap != "unknown":
                        backend_caps.add(cap)
        
        return list(backend_caps)
    
    def _build_endpoint_capability_map(self) -> Dict[str, str]:
        """Build mapping from endpoint to backend capability."""
        endpoint_map = {}
        try:
            import json
            api_map_path = self.repo_root / "backend/tests/generated/api-map.json"
            if api_map_path.exists():
                api_map = json.loads(api_map_path.read_text())
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
                for endpoint_data in api_map.get("endpoints", []):
                    endpoint = endpoint_data.get("endpoint", "")
                    router = endpoint_data.get("router", "")
                    capability = router_to_capability.get(router, "unknown")
                    if endpoint and capability != "unknown":
                        endpoint_map[endpoint] = capability
        except Exception:
            pass
        return endpoint_map
    
    def _endpoints_match(self, endpoint1: str, endpoint2: str) -> bool:
        """Check if two endpoints match (handling :param wildcards and template vars)."""
        import re
        def normalize(ep: str) -> str:
            ep = re.sub(r"\$\{[^}]+\}", ":param", ep)
            ep = re.sub(r"\{[^}]+\}", ":param", ep)
            ep = ep.split("?")[0]
            return ep
        return normalize(endpoint1) == normalize(endpoint2)
    
    def _find_test_files(self, capabilities: Dict[str, FrontendCapability]) -> None:
        """Find test files for each capability."""
        test_dirs = [
            self.frontend_root / "__tests__",
            self.frontend_root / "tests" / "e2e",
        ]
        
        for test_dir in test_dirs:
            if not test_dir.exists():
                continue
            
            for test_file in test_dir.rglob("*.test.ts*"):
                rel_path = str(test_file.relative_to(self.frontend_root))
                
                for cap in capabilities.values():
                    if cap.domain.replace("frontend-", "") in rel_path:
                        if test_dir.name == "e2e":
                            cap.e2e_files.append(test_file)
                        else:
                            cap.test_files.append(test_file)
    
    def discover_capabilities(self, directory: Path = None) -> Dict[str, FrontendCapability]:
        """Discover all frontend capabilities in a directory."""
        target_dir = directory or self.frontend_root
        
        symbols_by_file = self.ts_extractor.extract_from_directory(target_dir)
        
        capabilities: Dict[str, FrontendCapability] = {}
        
        for file_path, symbols in symbols_by_file.items():
            if not symbols:
                continue
                
            kind = self._classify_file(file_path)
            domain = self._extract_domain(file_path)
            
            if kind == FrontendCapabilityKind.ROUTE:
                try:
                    rel_path = str(file_path.relative_to(self.frontend_root / "app"))
                except ValueError:
                    rel_path = file_path.stem
                route_name = rel_path.replace("/page.tsx", "").replace("/workspace-page.tsx", "").replace(".tsx", "")
                if not route_name:
                    route_name = "root"
                capability_id = f"frontend:route:{domain}:{route_name}"
            elif kind == FrontendCapabilityKind.HOOK:
                hook_name = file_path.stem.replace("use-", "")
                capability_id = f"frontend:hook:{domain}:{hook_name}"
            elif kind == FrontendCapabilityKind.COMPONENT:
                try:
                    rel_path = str(file_path.relative_to(self.frontend_root / "components"))
                    comp_name = rel_path.split("/")[0] if "/" in rel_path else file_path.stem
                except ValueError:
                    comp_name = file_path.stem
                capability_id = f"frontend:component:{domain}:{comp_name}"
            elif kind == FrontendCapabilityKind.STORE:
                capability_id = f"frontend:store:{domain}"
            elif kind == FrontendCapabilityKind.API_CLIENT:
                capability_id = f"frontend:api-client:{domain}"
            else:
                capability_id = f"frontend:{kind.value}:{domain}:{file_path.stem}"
            
            if capability_id not in capabilities:
                capabilities[capability_id] = FrontendCapability(
                    capability_id=capability_id,
                    name=f"{domain} {kind.value}",
                    kind=kind,
                    domain=domain,
                )
            
            cap = capabilities[capability_id]
            cap.symbols.extend(symbols)
            cap.files.append(file_path)
            
            if kind == FrontendCapabilityKind.HOOK:
                endpoints = self._get_api_dependencies(symbols, file_path)
                for endpoint in endpoints:
                    cap.api_dependencies.append(endpoint)
        
        for cap in capabilities.values():
            cap.api_dependencies = list(set(cap.api_dependencies))
            cap.files = list(set(cap.files))
        
        if capabilities:
            for cap in capabilities.values():
                cap.backend_capabilities = self._get_backend_capabilities(cap.api_dependencies)
        
        self._find_test_files(capabilities)
        
        return capabilities


if __name__ == "__main__":
    from pathlib import Path
    
    discoverer = FrontendCapabilityDiscoverer()
    capabilities = discoverer.discover_capabilities(Path("frontend/lib/hooks"))
    
    print(f"Discovered {len(capabilities)} frontend capabilities from hooks:")
    for cap_id, cap in sorted(capabilities.items()):
        if cap.api_dependencies:
            print(f"\n  {cap_id}")
            print(f"    Name: {cap.name}")
            print(f"    Kind: {cap.kind.value}")
            print(f"    Domain: {cap.domain}")
            print(f"    Symbols: {len(cap.symbols)}")
            print(f"    Files: {len(cap.files)}")
            print(f"    API Dependencies: {cap.api_dependencies}")
            print(f"    Backend Capabilities: {cap.backend_capabilities}")
            print(f"    Status: {cap.attribution_status}")