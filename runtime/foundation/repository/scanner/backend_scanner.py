"""Backend scanner — discovers Python modules in ``backend/src/``.

Discovers:
- Python packages and modules
- Engine modules (``src/engines/``)
- Service modules (``src/services/``)
- Repository modules (``src/repositories/``)
- Router modules (``src/routers/``) and their FastAPI endpoints
- Model modules (``src/models/``)
- Import relationships between modules (AST-based)

Scanners never execute repository code — they parse with ``ast`` only.
"""

from __future__ import annotations

import ast
from pathlib import Path

from typing import Any
from runtime.foundation.repository.scanner.base import BaseScanner, ScanResult


# Directories under src/ that map to a module type
_MODULE_TYPE_MAP: dict[str, str] = {
    "engines": "engine",
    "services": "service",
    "repositories": "repository",
    "routers": "router",
    "models": "model",
    "core": "core",
    "app": "app",
    "common": "common",
    "extraction": "extraction",
    "reports": "report",
    "structural": "structural",
    "utils": "utility",
    "verification": "verification",
    "orchestration": "orchestration",
    "audits": "audit",
}


class BackendScanner(BaseScanner):
    """Discover backend Python modules, routers, and import relationships."""

    def scan(self) -> ScanResult:
        result = ScanResult()
        if not self.src_dir.exists():
            return result

        # Discover packages and modules
        self._discover_packages(result)
        self._discover_modules(result)

        # Discover router endpoints
        self._discover_router_endpoints(result)

        # Discover import relationships
        self._discover_imports(result)

        return result

    # -- packages ------------------------------------------------------------

    def _discover_packages(self, result: ScanResult) -> None:
        """Discover Python packages (directories with __init__.py)."""
        for py_file in self.src_dir.rglob("__init__.py"):
            pkg_dir = py_file.parent
            rel = self.rel_path(pkg_dir, self.backend_dir)
            module_name = self._path_to_module(pkg_dir, self.src_dir)
            if module_name:
                module_type = self._infer_module_type(rel)
                result.add_node(
                    node_type="package",
                    name=pkg_dir.name,
                    path=rel,
                    source="filesystem:backend/src",
                    properties={
                        "module": module_name,
                        "module_type": module_type,
                    },
                )

    # -- modules -------------------------------------------------------------

    def _discover_modules(self, result: ScanResult) -> None:
        """Discover individual Python modules and classify them."""
        for py_file in self.src_dir.rglob("*.py"):
            if py_file.name == "__init__.py":
                continue

            rel = self.rel_path(py_file, self.backend_dir)
            module_name = self._path_to_module(py_file, self.src_dir)
            if not module_name:
                continue

            module_type = self._infer_module_type(rel)
            functions = self._extract_functions(py_file)
            classes = self._extract_classes(py_file)

            result.add_node(
                node_type="module",
                name=py_file.stem,
                path=rel,
                source="filesystem:backend/src",
                properties={
                    "module": module_name,
                    "module_type": module_type,
                    "functions": functions,
                    "classes": classes,
                },
            )

    # -- router endpoints ----------------------------------------------------

    def _discover_router_endpoints(self, result: ScanResult) -> None:
        """Parse router files to discover FastAPI endpoints."""
        routers_dir = self.src_dir / "routers"
        if not routers_dir.exists():
            return

        for py_file in routers_dir.glob("*.py"):
            if py_file.name == "__init__.py":
                continue

            tree = self.safe_parse_ast(py_file)
            if tree is None:
                continue

            rel = self.rel_path(py_file, self.backend_dir)
            module_name = self._path_to_module(py_file, self.src_dir)
            if not module_name:
                continue

            router_name = self._find_router_name(tree)
            prefix = self._find_router_prefix(tree)
            endpoints = self._extract_endpoints(tree, router_name, prefix)

            # Update the router module node with endpoint info
            for node in result.nodes:
                if node.id == f"module:{rel}":
                    node.properties["router_name"] = router_name
                    node.properties["prefix"] = prefix
                    node.properties["endpoints"] = endpoints
                    break

            # Create endpoint nodes
            for ep in endpoints:
                ep_id = f"endpoint:{ep['method']} {ep['path']}"
                result.add_node(
                    node_type="endpoint",
                    name=f"{ep['method']} {ep['path']}",
                    path=rel,
                    source="ast:routers",
                    properties={
                        "method": ep["method"],
                        "path": ep["path"],
                        "operation_id": ep["operation_id"],
                        "router": router_name,
                        "router_module": module_name,
                        "tags": ep["tags"],
                        "summary": ep.get("summary", ""),
                    },
                )
                # Edge: router module implements endpoint
                result.add_edge(
                    source_id=f"module:{rel}",
                    target_id=ep_id,
                    relationship="implements",
                    confidence=1.0,
                    evidence="ast:router_decorator",
                )

    # -- imports -------------------------------------------------------------

    def _discover_imports(self, result: ScanResult) -> None:
        """Discover import relationships between modules via AST."""
        for py_file in self.src_dir.rglob("*.py"):
            if py_file.name == "__init__.py":
                continue

            tree = self.safe_parse_ast(py_file)
            if tree is None:
                continue

            rel = self.rel_path(py_file, self.backend_dir)
            source_module = self._path_to_module(py_file, self.src_dir)
            if not source_module:
                continue

            source_id = f"module:{rel}"

            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom) and node.module:
                    if not node.module.startswith("src."):
                        continue

                    target_module = node.module
                    target_rel = self._module_to_path(target_module, self.src_dir)
                    if target_rel is None:
                        continue

                    self._infer_module_type(target_rel)
                    target_id = f"module:{target_rel}"

                    # Determine relationship type based on what's being imported
                    rel_type = self._infer_relationship(source_module, target_module)

                    result.add_edge(
                        source_id=source_id,
                        target_id=target_id,
                        relationship=rel_type,
                        confidence=0.8,
                        evidence=f"import_from:{target_module}",
                    )

    # -- helpers -------------------------------------------------------------

    def _path_to_module(self, py_file: Path, base_dir: Path) -> str | None:
        """Convert a file path to a dotted module name."""
        try:
            rel = py_file.relative_to(base_dir)
        except ValueError:
            return None
        if rel == Path("."):
            return ""
        parts = list(rel.with_suffix("").parts)
        if parts and parts[-1] == "__init__":
            parts = parts[:-1]
        if not parts:
            return ""
        return ".".join(parts)

    def _module_to_path(self, module: str, base_dir: Path) -> str | None:
        """Convert a dotted module name to a relative file path."""
        parts = module.split(".")
        # module starts with "src."
        if parts[0] != "src":
            return None
        parts = parts[1:]

        # Try as package (directory/__init__.py)
        pkg_path = base_dir / Path(*parts) / "__init__.py"
        if pkg_path.exists():
            return self.rel_path(pkg_path.parent, self.backend_dir)

        # Try as module (file.py)
        mod_path = base_dir / Path(*parts).with_suffix(".py")
        if mod_path.exists():
            return self.rel_path(mod_path, self.backend_dir)

        return None

    def _infer_module_type(self, rel_path: str) -> str:
        """Infer the module type from its path."""
        parts = rel_path.split("/")
        if len(parts) > 1 and parts[0] == "src":
            # parts[1] is the top-level directory under src/
                return _MODULE_TYPE_MAP.get(parts[1], "unknown")
        return "unknown"

    def _extract_functions(self, py_file: Path) -> list[str]:
        """Extract top-level function names from a Python file."""
        tree = self.safe_parse_ast(py_file)
        if tree is None:
            return []
        return [
            node.name
            for node in ast.walk(tree)
            if isinstance(node, ast.FunctionDef)
        ]

    def _extract_classes(self, py_file: Path) -> list[str]:
        """Extract top-level class names from a Python file."""
        tree = self.safe_parse_ast(py_file)
        if tree is None:
            return []
        return [
            node.name
            for node in ast.walk(tree)
            if isinstance(node, ast.ClassDef)
        ]

    def _find_router_name(self, tree: ast.Module) -> str | None:
        """Find the APIRouter variable name from source."""
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and isinstance(
                        node.value, ast.Call
                    ):
                        func = node.value.func
                        if isinstance(func, ast.Name) and func.id == "APIRouter":
                            return target.id
                        if (
                            isinstance(func, ast.Attribute)
                            and func.attr == "APIRouter"
                        ):
                            return target.id
        return None

    def _find_router_prefix(self, tree: ast.Module) -> str | None:
        """Find the router prefix from the APIRouter constructor."""
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and isinstance(
                        node.value, ast.Call
                    ):
                        func = node.value.func
                        is_router = False
                        if isinstance(func, ast.Name) and func.id == "APIRouter":
                            is_router = True
                        elif (
                            isinstance(func, ast.Attribute)
                            and func.attr == "APIRouter"
                        ):
                            is_router = True

                        if is_router:
                            for kw in node.value.keywords:
                                if kw.arg == "prefix":
                                    if isinstance(kw.value, ast.Constant):
                                        return kw.value.value
        return None

    def _extract_endpoints(
        self, tree: ast.Module, router_name: str | None, prefix: str | None
    ) -> list[dict[str, Any]]:
        """Extract endpoint definitions from router decorators."""
        endpoints: list[dict[str, Any]] = []
        if not router_name:
            return endpoints

        for node in ast.walk(tree):
            if not isinstance(node, ast.FunctionDef):
                continue

            for decorator in node.decorator_list:
                method, path = self._parse_route_decorator(decorator, router_name)
                if method and path:
                    full_path = self._join_prefix(prefix, path)
                    endpoints.append(
                        {
                            "method": method,
                            "path": full_path,
                            "operation_id": node.name,
                            "tags": [],
                            "summary": node.name,
                        }
                    )

        return endpoints

    def _parse_route_decorator(
        self, decorator: ast.expr, router_name: str
    ) -> tuple[str | None, str | None]:
        """Parse a @router.get("/path") decorator to extract method and path."""
        if not isinstance(decorator, ast.Call):
            return None, None

        func = decorator.func
        if not isinstance(func, ast.Attribute):
            return None, None

        if not isinstance(func.value, ast.Name) or func.value.id != router_name:
            return None, None

        method = func.attr.upper()
        if method not in ("GET", "POST", "PUT", "DELETE", "PATCH"):
            return None, None

        if decorator.args and isinstance(decorator.args[0], ast.Constant):
            return method, decorator.args[0].value

        return None, None

    @staticmethod
    def _join_prefix(prefix: str | None, path: str) -> str:
        """Join a router prefix with a route path."""
        if not prefix:
            return path
        if prefix.endswith("/") and path.startswith("/"):
            return prefix + path[1:]
        if not prefix.endswith("/") and not path.startswith("/"):
            return prefix + "/" + path
        return prefix + path

    @staticmethod
    def _infer_relationship(source_module: str, target_module: str) -> str:
        """Infer the relationship type from module paths."""
        # Router imports Service → calls
        if "routers" in source_module and "services" in target_module:
            return "calls"
        # Service imports Engine → calls
        if "services" in source_module and "engines" in target_module:
            return "calls"
        # Service imports Repository → depends_on
        if "services" in source_module and "repositories" in target_module:
            return "depends_on"
        # Engine imports Repository → depends_on
        if "engines" in source_module and "repositories" in target_module:
            return "depends_on"
        # Engine imports Model → depends_on
        if "engines" in source_module and "models" in target_module:
            return "depends_on"
        # Repository imports Model → depends_on
        if "repositories" in source_module and "models" in target_module:
            return "depends_on"
        # Service imports Model → depends_on
        if "services" in source_module and "models" in target_module:
            return "depends_on"
        # Default: imports
        return "imports"
