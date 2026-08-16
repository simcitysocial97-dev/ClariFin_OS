"""Frontend scanner — discovers TypeScript/React modules in ``frontend/``.

Discovers:
- Next.js app router routes (``frontend/app/``)
- React components (``frontend/components/``, ``frontend/app/``)
- Custom hooks (``frontend/hooks/``)
- TypeScript modules (``frontend/lib/``, ``frontend/types/``)
- API client functions and their endpoint mappings (``frontend/lib/api/client.ts``)
- Import relationships between frontend modules

Uses regex-based parsing (no TypeScript parser available in Python stdlib).
Scanners never execute repository code.
"""

from __future__ import annotations

import re

from runtime.foundation.repository.scanner.base import BaseScanner, ScanResult

# Directories to skip when walking the frontend tree
_SKIP_DIRS: frozenset[str] = frozenset(
    {
        "node_modules",
        ".next",
        "dist",
        "test-results",
        ".git",
        "__tests__",
        "tests",
    }
)

# File extensions to scan
_TS_EXTENSIONS: frozenset[str] = frozenset({".ts", ".tsx"})

# Regex patterns for TypeScript parsing
_EXPORT_FUNCTION_RE = re.compile(
    r"export\s+(?:async\s+)?function\s+(\w+)", re.MULTILINE
)
_EXPORT_CONST_RE = re.compile(r"export\s+const\s+(\w+)\s*[:=]", re.MULTILINE)
_EXPORT_DEFAULT_RE = re.compile(
    r"export\s+default\s+(?:async\s+)?function\s*(\w+)?", re.MULTILINE
)
_EXPORT_CLASS_RE = re.compile(r"export\s+class\s+(\w+)", re.MULTILINE)
_EXPORT_INTERFACE_RE = re.compile(r"export\s+interface\s+(\w+)", re.MULTILINE)
_EXPORT_TYPE_RE = re.compile(r"export\s+type\s+(\w+)", re.MULTILINE)
_IMPORT_RE = re.compile(
    r"import\s+(?:type\s+)?(?:\{[^}]+\}|\*\s+as\s+\w+|\w+)\s+from\s+['\"]([^'\"]+)['\"]",
    re.MULTILINE,
)
_HOOK_RE = re.compile(r"function\s+(use\w+)", re.MULTILINE)
# API client: find function name and URL from template literal fetch calls
_API_FUNCTION_RE = re.compile(r"export\s+(?:async\s+)?function\s+(\w+)", re.MULTILINE)
_ARROW_EXPORT_RE = re.compile(
    r"export\s+const\s+(\w+)\s*=\s*(?:async\s*)?\([^)]*\)\s*=>", re.MULTILINE
)
_EXPORT_DEFAULT_RE = re.compile(
    r"export\s+default\s+(?:async\s+)?function\s*(\w+)?", re.MULTILINE
)
_EXPORT_CLASS_RE = re.compile(r"export\s+class\s+(\w+)", re.MULTILINE)
_EXPORT_INTERFACE_RE = re.compile(r"export\s+interface\s+(\w+)", re.MULTILINE)
_EXPORT_TYPE_RE = re.compile(r"export\s+type\s+(\w+)", re.MULTILINE)
_IMPORT_RE = re.compile(
    r"import\s+(?:type\s+)?(?:\{[^}]+\}|\*\s+as\s+\w+|\w+)\s+from\s+['\"]([^'\"]+)['\"]",
    re.MULTILINE,
)
_HOOK_RE = re.compile(r"function\s+(use\w+)", re.MULTILINE)
# Match fetch calls with template literals: fetch(`${API_BASE}/api/...`)
_FETCH_TEMPLATE_RE = re.compile(r"fetch\s*\(\s*`\$\{API_BASE\}([^`]+)`", re.MULTILINE)
# Match fetch calls with string literals: fetch('/api/...')
_FETCH_STRING_RE = re.compile(r"fetch\s*\(\s*['\"](/api/[^'\"\\)]+)['\"]", re.MULTILINE)
# Match function declarations that start with fetch
_FETCH_FUNCTION_RE = re.compile(
    r"export\s+(?:async\s+)?function\s+(fetch\w+)", re.MULTILINE
)
# Match function body boundaries to associate fetch calls with functions
_FUNCTION_BOUNDARY_RE = re.compile(
    r"export\s+(?:async\s+)?function\s+(\w+)", re.MULTILINE
)


class FrontendScanner(BaseScanner):
    """Discover frontend modules, components, hooks, routes, and API usage."""

    def scan(self) -> ScanResult:
        result = ScanResult()
        if not self.frontend_dir.exists():
            return result

        # Discover routes
        self._discover_routes(result)

        # Discover components
        self._discover_components(result)

        # Discover hooks
        self._discover_hooks(result)

        # Discover modules (lib, types)
        self._discover_modules(result)

        # Discover API client functions
        self._discover_api_client(result)

        # Discover import relationships
        self._discover_imports(result)

        return result

    # -- routes --------------------------------------------------------------

    def _discover_routes(self, result: ScanResult) -> None:
        """Discover Next.js app router routes from frontend/app/."""
        app_dir = self.frontend_dir / "app"
        if not app_dir.exists():
            return

        for page_file in app_dir.rglob("page.tsx"):
            # Compute route path from directory structure
            rel_dir = page_file.parent.relative_to(app_dir)
            route_parts = list(rel_dir.parts)
            if route_parts == []:
                route_path = "/"
            else:
                route_path = "/" + "/".join(route_parts)

            rel = self.rel_path(page_file, self.frontend_dir)
            result.add_node(
                node_type="frontend_route",
                name=route_path,
                path=rel,
                source="filesystem:frontend/app",
                properties={
                    "route": route_path,
                    "is_dynamic": any(part.startswith("[") for part in route_parts),
                    "dynamic_params": [
                        part[1:-1]
                        for part in route_parts
                        if part.startswith("[") and part.endswith("]")
                    ],
                },
            )

    # -- components ----------------------------------------------------------

    def _discover_components(self, result: ScanResult) -> None:
        """Discover React components in frontend/components/ and frontend/app/."""
        for base_dir_name in ("components", "app"):
            base_dir = self.frontend_dir / base_dir_name
            if not base_dir.exists():
                continue

            for tsx_file in base_dir.rglob("*.tsx"):
                if tsx_file.name == "page.tsx" or tsx_file.name == "layout.tsx":
                    continue
                if "__tests__" in tsx_file.parts:
                    continue

                content = self.safe_read(tsx_file)
                if content is None:
                    continue

                rel = self.rel_path(tsx_file, self.frontend_dir)
                components = self._extract_components(content)

                for comp_name in components:
                    result.add_node(
                        node_type="component",
                        name=comp_name,
                        path=rel,
                        source="ast:frontend",
                        properties={
                            "file": rel,
                            "is_client_component": "'use client'" in content,
                        },
                    )

    # -- hooks ---------------------------------------------------------------

    def _discover_hooks(self, result: ScanResult) -> None:
        """Discover custom hooks in frontend/hooks/."""
        hooks_dir = self.frontend_dir / "hooks"
        if not hooks_dir.exists():
            return

        for ts_file in hooks_dir.rglob("*.ts"):
            if ts_file.name == "use-command-palette.ts":
                pass  # still process
            content = self.safe_read(ts_file)
            if content is None:
                continue

            rel = self.rel_path(ts_file, self.frontend_dir)
            hook_names = self._extract_hooks(content)

            for hook_name in hook_names:
                result.add_node(
                    node_type="hook",
                    name=hook_name,
                    path=rel,
                    source="ast:frontend/hooks",
                    properties={
                        "file": rel,
                    },
                )

    # -- modules -------------------------------------------------------------

    def _discover_modules(self, result: ScanResult) -> None:
        """Discover TypeScript modules in frontend/lib/ and frontend/types/."""
        for base_dir_name in ("lib", "types"):
            base_dir = self.frontend_dir / base_dir_name
            if not base_dir.exists():
                continue

            for ts_file in base_dir.rglob("*.ts"):
                if ts_file.name.endswith(".d.ts"):
                    continue
                if "__tests__" in ts_file.parts:
                    continue

                content = self.safe_read(ts_file)
                if content is None:
                    continue

                rel = self.rel_path(ts_file, self.frontend_dir)
                module_name = ts_file.stem

                # Extract exports
                functions = list(set(_EXPORT_FUNCTION_RE.findall(content)))
                consts = list(set(_ARROW_EXPORT_RE.findall(content)))
                interfaces = list(set(_EXPORT_INTERFACE_RE.findall(content)))
                types = list(set(_EXPORT_TYPE_RE.findall(content)))
                classes = list(set(_EXPORT_CLASS_RE.findall(content)))

                result.add_node(
                    node_type="module",
                    name=module_name,
                    path=rel,
                    source="filesystem:frontend",
                    properties={
                        "module_type": "frontend",
                        "functions": sorted(functions),
                        "consts": sorted(consts),
                        "interfaces": sorted(interfaces),
                        "types": sorted(types),
                        "classes": sorted(classes),
                    },
                )

    # -- API client ----------------------------------------------------------

    def _discover_api_client(self, result: ScanResult) -> None:
        """Parse frontend/lib/api/client.ts to map API functions to endpoints."""
        client_file = self.frontend_dir / "lib" / "api" / "client.ts"
        if not client_file.exists():
            return

        content = self.safe_read(client_file)
        if content is None:
            return

        rel = self.rel_path(client_file, self.frontend_dir)

        # Find all exported functions that start with fetch
        api_functions = list(set(_FETCH_FUNCTION_RE.findall(content)))
        # Also find arrow function exports
        api_functions.extend(_ARROW_EXPORT_RE.findall(content))

        # Find all fetch URLs from template literals and string literals
        template_urls = _FETCH_TEMPLATE_RE.findall(content)
        string_urls = _FETCH_STRING_RE.findall(content)

        # Build function-to-endpoint mapping by scanning function bodies
        function_endpoints: dict[str, list[dict[str, str]]] = {}
        for func_name in api_functions:
            function_endpoints[func_name] = []

        # Find function body boundaries to associate fetch calls with functions
        func_boundaries: list[tuple[int, str]] = []
        for match in _FUNCTION_BOUNDARY_RE.finditer(content):
            func_boundaries.append((match.start(), match.group(1)))

        # For each URL found, find which function it belongs to
        all_urls: list[tuple[str, str]] = []
        for url in template_urls:
            all_urls.append((url, "GET"))
        for url in string_urls:
            all_urls.append((url, "GET"))

        for url, method in all_urls:
            # Find the function that contains this URL by position
            url_pos = content.find(url)
            if url_pos == -1:
                continue
            # Find the closest function boundary before this URL
            containing_func: str | None = None
            for pos, fname in func_boundaries:
                if pos <= url_pos:
                    containing_func = fname
                else:
                    break
            if containing_func and containing_func in function_endpoints:
                function_endpoints[containing_func].append(
                    {"method": method, "path": url}
                )

        # Create API client function nodes
        for func_name, endpoints in function_endpoints.items():
            if not endpoints:
                continue
            result.add_node(
                node_type="module",
                name=func_name,
                path=rel,
                source="ast:frontend/api-client",
                properties={
                    "module_type": "api_client_function",
                    "function_name": func_name,
                    "endpoints": endpoints,
                },
            )

            # Create edges: api_client_function consumes endpoints
            for ep in endpoints:
                ep_id = f"endpoint:{ep['method']} {ep['path']}"
                result.add_edge(
                    source_id=f"module:{rel}",
                    target_id=ep_id,
                    relationship="consumes",
                    confidence=0.7,
                    evidence=f"api_client:{func_name}",
                )

    # -- imports -------------------------------------------------------------

    def _discover_imports(self, result: ScanResult) -> None:
        """Discover import relationships between frontend modules."""
        for ts_file in self.frontend_dir.rglob("*.ts"):
            if ts_file.name.endswith(".d.ts"):
                continue
            if any(part in _SKIP_DIRS for part in ts_file.parts):
                continue
            if "__tests__" in ts_file.parts or "/tests/" in str(ts_file):
                continue

            content = self.safe_read(ts_file)
            if content is None:
                continue

            rel = self.rel_path(ts_file, self.frontend_dir)
            source_id = f"module:{rel}"

            for match in _IMPORT_RE.finditer(content):
                import_path = match.group(1)
                if import_path.startswith("@/"):
                    target_rel = import_path[2:] + ".ts"
                    target_id = f"module:{target_rel}"
                    result.add_edge(
                        source_id=source_id,
                        target_id=target_id,
                        relationship="imports",
                        confidence=0.7,
                        evidence=f"import:{import_path}",
                    )

    # -- extraction helpers --------------------------------------------------

    def _extract_components(self, content: str) -> list[str]:
        """Extract React component names from TypeScript content."""
        components: list[str] = []

        # Named function components: export function ComponentName()
        components.extend(
            m for m in _EXPORT_FUNCTION_RE.findall(content) if m[0].isupper()
        )

        # Arrow function components: export const ComponentName = (...)
        components.extend(
            m for m in _ARROW_EXPORT_RE.findall(content) if m[0].isupper()
        )

        # Default exports
        default_match = _EXPORT_DEFAULT_RE.search(content)
        if default_match and default_match.group(1):
            components.append(default_match.group(1))

        return list(set(components))

    def _extract_hooks(self, content: str) -> list[str]:
        """Extract hook function names from TypeScript content."""
        hooks: list[str] = []
        hooks.extend(_HOOK_RE.findall(content))
        return list(set(hooks))
