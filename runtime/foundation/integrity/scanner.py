"""Architectural Scanner — Program 10.

Performs deterministic scans of backend Python and frontend TypeScript source
files using:

  * Python ``ast`` module        — exact import extraction for Python files
  * Text-level import analysis   — for TypeScript files (no TS AST available
                                   in the standard library)
  * Cross-layer map              — `runtime/generated/cross-layer-map.json`
  * Repository graph index       — `runtime/generated/repository/index.json`
  * Existing planner artifacts   — verification profiles, registry

Produces an immutable ``ArchitecturalGraph`` consumed by rules and the
integrity engine.

No regex-only scanning where AST is available.
"""

from __future__ import annotations

import ast
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from runtime.foundation.integrity.models import ArchitectureLayer

# ---------------------------------------------------------------------------
# Layer classification
# ---------------------------------------------------------------------------

_BACKEND_ROOT = "backend/src"
_FRONTEND_ROOT = "frontend"

_ENGINE_ROOTS_FALLBACK = frozenset({"engines"})


def _engine_paths() -> frozenset[str]:
    """Engine ownership roots, taken from the canonical architecture provider.

    Program 13.3 removed the hardcoded single-file-engine inventory. The
    provider is the only authority on what an engine is.
    """
    cached = getattr(_engine_paths, "_cache", None)
    if cached is not None:
        return cached
    try:
        from runtime.foundation.architecture import get_architecture

        arch = get_architecture()
        paths = frozenset(e.path for e in arch.engines.values()) | frozenset(
            e.entry_point for e in arch.engines.values()
        )
    except Exception:
        paths = frozenset()
    _engine_paths._cache = paths  # type: ignore[attr-defined]
    return paths


def _is_engine_path(norm: str) -> bool:
    """True when the provider says ``norm`` belongs to an engine."""
    engine_paths = _engine_paths()
    if norm in engine_paths:
        return True
    for root in engine_paths:
        if not root.endswith(".py") and norm.startswith(root.rstrip("/") + "/"):
            return True
    return False


_SERVICE_DIRS = {"services"}
_ROUTER_DIRS = {"routers"}
_DTO_DIRS = {"core/dtos", "models"}
_REPO_DIRS = {"repositories"}

_FRONTEND_API_DIRS = {"api"}
_FRONTEND_CAPABILITY_DIRS = {"capabilities"}
_FRONTEND_MAPPER_DIRS = {"mappers"}
_FRONTEND_VIEWMODEL_MARKERS = {"-view-model", "view-model"}
_FRONTEND_WORKSPACE_DIRS = {"workspace", "runtime"}
_FRONTEND_COMPONENT_ROOTS = {"components"}


def classify_layer(file_path: str) -> ArchitectureLayer:
    """Classify a file path into its canonical architectural layer."""
    norm = file_path.replace("\\", "/")

    if not norm.startswith("backend/") and not norm.startswith("frontend/"):
        return ArchitectureLayer.UNKNOWN

    if norm.startswith("backend/"):
        if norm.endswith(".py"):
            rel = (
                norm[len("backend/src/") :]
                if norm.startswith("backend/src/")
                else norm[len("backend/") :]
            )
            parts = rel.split("/")
            top = parts[0] if parts else ""
            if _is_engine_path(norm) or top in _ENGINE_ROOTS_FALLBACK:
                return ArchitectureLayer.BACKEND_ENGINE
            if top in _SERVICE_DIRS:
                return ArchitectureLayer.BACKEND_SERVICE
            if top in _ROUTER_DIRS:
                return ArchitectureLayer.BACKEND_ROUTER
            if (
                top in _DTO_DIRS
                or norm.startswith("backend/src/core/dtos/")
                or norm.startswith("backend/src/models/")
            ):
                return ArchitectureLayer.BACKEND_DTO
            if top in _REPO_DIRS:
                return ArchitectureLayer.BACKEND_REPOSITORY
            return ArchitectureLayer.UNKNOWN
        return ArchitectureLayer.UNKNOWN

    if norm.startswith("frontend/"):
        rel = norm[len("frontend/") :]
        parts = rel.split("/") if rel else []
        top = parts[0] if parts else ""
        if top == "lib" and len(parts) > 1:
            sub = parts[1]
            if sub in _FRONTEND_API_DIRS:
                return ArchitectureLayer.FRONTEND_API
            if sub in _FRONTEND_CAPABILITY_DIRS:
                return ArchitectureLayer.FRONTEND_CAPABILITY
            if sub in _FRONTEND_MAPPER_DIRS:
                return ArchitectureLayer.FRONTEND_MAPPER
            if sub in _FRONTEND_WORKSPACE_DIRS:
                return ArchitectureLayer.FRONTEND_WORKSPACE
        if top == "components":
            return ArchitectureLayer.FRONTEND_COMPONENT
        if top == "types" and any(m in norm for m in _FRONTEND_VIEWMODEL_MARKERS):
            return ArchitectureLayer.FRONTEND_VIEWMODEL
        if top == "types":
            return ArchitectureLayer.UNKNOWN
        if top == "app" and norm.endswith("page.tsx"):
            return ArchitectureLayer.FRONTEND_PAGE
        return ArchitectureLayer.UNKNOWN

    return ArchitectureLayer.UNKNOWN


# ---------------------------------------------------------------------------
# Import resolution
# ---------------------------------------------------------------------------

_TS_ALIAS_MAP = {
    "@/": "frontend/",
    "@/lib/": "frontend/lib/",
    "@/types/": "frontend/types/",
    "@/components/": "frontend/components/",
    "@/app/": "frontend/app/",
}

_BACKEND_MODULE_PREFIX = "src."


def _resolve_ts_import(import_path: str, repo_root: Path) -> str | None:
    """Resolve a TypeScript import path to a concrete file path relative to repo root."""
    if import_path.startswith("@/"):
        resolved = import_path.replace("@/", "frontend/", 1)
    elif import_path.startswith("frontend/"):
        resolved = import_path
    else:
        return None

    for ext in (".ts", ".tsx", ".js", ".jsx"):
        candidate = resolved + ext
        if (repo_root / candidate).exists():
            return candidate
    for ext in ("/index.ts", "/index.tsx", "/index.js", "/index.jsx"):
        candidate = resolved + ext
        if (repo_root / candidate).exists():
            return candidate
    return None


def _resolve_py_import(module: str, repo_root: Path) -> str | None:
    """Resolve a Python import module to a concrete file path relative to repo root."""
    if module.startswith(_BACKEND_MODULE_PREFIX):
        rel = module.replace(".", "/")
        for ext in (".py",):
            candidate = f"backend/src/{rel}{ext}"
            if (repo_root / candidate).exists():
                return candidate
        candidate = f"backend/src/{rel}/__init__.py"
        if (repo_root / candidate).exists():
            return candidate
    if module.startswith("backend.src."):
        rel = module[len("backend.src.") :].replace(".", "/")
        for ext in (".py",):
            candidate = f"backend/src/{rel}{ext}"
            if (repo_root / candidate).exists():
                return candidate
        candidate = f"backend/src/{rel}/__init__.py"
        if (repo_root / candidate).exists():
            return candidate
    return None


def _resolve_import_to_layer(
    import_path: str, file_type: str, repo_root: Path
) -> tuple[str | None, ArchitectureLayer]:
    """Resolve an import to (resolved_path, layer)."""
    if file_type == "python":
        resolved = _resolve_py_import(import_path, repo_root)
    else:
        resolved = _resolve_ts_import(import_path, repo_root)
    if resolved:
        return resolved, classify_layer(resolved)
    return None, ArchitectureLayer.UNKNOWN


# ---------------------------------------------------------------------------
# TypeScript import / call scanning
# ---------------------------------------------------------------------------

_TS_IMPORT_RE = re.compile(
    r"""^\s*import\s+
        (?:[\w*{},\s]+\s+from\s+)?
        ['"]([^'"]+)['"]""",
    re.MULTILINE | re.VERBOSE,
)

_FETCH_RE = re.compile(r"\bfetch\s*\(")

_REACT_IMPORT_RE = re.compile(r"""['"]react['"]""")

_WORKSPACE_REG_RE = re.compile(r"useWorkspaceRegistration")


def _scan_ts_imports(source: str) -> list[tuple[str, int]]:
    """Extract (module, line_number) pairs from a TypeScript source file."""
    imports: list[tuple[str, int]] = []
    for match in _TS_IMPORT_RE.finditer(source):
        module = match.group(1)
        line_no = source[: match.start()].count("\n") + 1
        imports.append((module, line_no))
    return imports


def _scan_ts_fetch_calls(source: str) -> list[int]:
    """Return 1-based line numbers of fetch() calls."""
    lines = source.split("\n")
    result: list[int] = []
    for idx, line in enumerate(lines, start=1):
        if _FETCH_RE.search(line):
            result.append(idx)
    return result


def _has_workspace_registration(source: str) -> bool:
    return bool(_WORKSPACE_REG_RE.search(source))


def _has_react_import(source: str) -> bool:
    return bool(_REACT_IMPORT_RE.search(source))


# ---------------------------------------------------------------------------
# Python AST scanning
# ---------------------------------------------------------------------------


def _scan_py_imports(tree: ast.AST) -> list[tuple[str, int]]:
    """Extract (module, line_number) pairs from a Python AST."""
    imports: list[tuple[str, int]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append((alias.name, node.lineno))
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if node.level > 0:
                module = "." * node.level + module
            imports.append((module, node.lineno))
    return imports


# ---------------------------------------------------------------------------
# File discovery
# ---------------------------------------------------------------------------

_PY_EXTS = (".py",)
_TS_EXTS = (".ts", ".tsx")

_EXCLUDE_DIRS = frozenset(
    {
        "__pycache__",
        ".venv",
        "venv",
        "node_modules",
        ".next",
        "dist",
        "build",
        ".git",
        "__tests__",
        "tests",
    }
)

_EXCLUDE_FILES = frozenset(
    {
        "__init__.py",
        "__main__.py",
        "conftest.py",
    }
)


def _should_exclude(rel_path: str) -> bool:
    parts = rel_path.replace("\\", "/").split("/")
    for part in parts:
        if part in _EXCLUDE_DIRS:
            return True
    filename = parts[-1]
    if filename.startswith("test_") or filename.startswith("conftest"):
        return True
    if filename in _EXCLUDE_FILES:
        return True
    return False


def discover_source_files(repo_root: Path) -> list[str]:
    """Discover all backend Python and frontend TypeScript source files.

    Excludes tests, caches, __init__ files, and other non-source artifacts.
    Returns paths relative to *repo_root*, sorted for determinism.
    """
    results: list[str] = []
    for root, dirs, files in os_walk(repo_root):
        # Prune excluded directories in-place
        dirs[:] = sorted(d for d in dirs if d not in _EXCLUDE_DIRS)
        for fname in sorted(files):
            if not fname.endswith(_PY_EXTS + _TS_EXTS):
                continue
            full = Path(root) / fname
            rel = str(full.relative_to(repo_root)).replace("\\", "/")
            if _should_exclude(rel):
                continue
            results.append(rel)
    return sorted(results)


def os_walk(repo_root: Path):
    """Wrapper around os.walk that only descends into backend/src and frontend/."""
    import os

    roots_to_scan = [
        repo_root / "backend" / "src",
        repo_root / "frontend",
    ]
    for base in roots_to_scan:
        if not base.exists():
            continue
        for root, dirs, files in os.walk(base, topdown=True):
            dirs[:] = sorted(d for d in dirs if d not in _EXCLUDE_DIRS)
            yield root, dirs, files


# ---------------------------------------------------------------------------
# Immutable scan result models
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class ImportRecord:
    """A single import statement extracted from a source file."""

    module: str
    line_number: int
    resolved_path: str | None
    layer: str


@dataclass(frozen=True, slots=True)
class ScannedFile:
    """A single scanned source file with all extracted metadata."""

    path: str
    layer: str
    file_type: str
    imports: tuple[ImportRecord, ...]
    fetch_call_lines: tuple[int, ...]
    has_workspace_registration: bool
    class_names: tuple[str, ...]
    function_names: tuple[str, ...]

    def imports_from_layer(self, layer: ArchitectureLayer) -> list[ImportRecord]:
        return [imp for imp in self.imports if imp.layer == layer.value]

    def has_import_from_layer(self, layer: ArchitectureLayer) -> bool:
        return any(imp.layer == layer.value for imp in self.imports)

    def has_react_import(self) -> bool:
        for imp in self.imports:
            if imp.module == "react" or imp.module.startswith("react/"):
                return True
        return False


@dataclass(frozen=True, slots=True)
class ArchitecturalGraph:
    """The complete architectural snapshot produced by the scanner.

    Immutable and deterministic for a given repository state.
    """

    files: tuple[ScannedFile, ...]
    cross_layer_map: dict[str, Any]
    graph_nodes: tuple[dict[str, Any], ...]
    graph_edges: tuple[dict[str, Any], ...]
    files_scanned: int
    repo_root: str
    scan_errors: tuple[str, ...] = ()

    def get_file(self, path: str) -> ScannedFile | None:
        for f in self.files:
            if f.path == path:
                return f
        return None

    def files_in_layer(self, layer: ArchitectureLayer) -> list[ScannedFile]:
        return [f for f in self.files if f.layer == layer.value]

    def endpoints_in_map(self) -> set[str]:
        result: set[str] = set()
        for entry in self.cross_layer_map.values():
            if not isinstance(entry, dict):
                continue
            for ep in entry.get("endpoints", []):
                result.add(ep)
        return result

    def capabilities_in_map(self) -> set[str]:
        result: set[str] = set()
        for entry in self.cross_layer_map.values():
            if not isinstance(entry, dict):
                continue
            for cap in entry.get("capabilities", []):
                result.add(cap)
        return result

    def mappers_in_map(self) -> set[str]:
        result: set[str] = set()
        for entry in self.cross_layer_map.values():
            if not isinstance(entry, dict):
                continue
            for mp in entry.get("mappers", []):
                result.add(mp)
        return result

    def view_models_in_map(self) -> set[str]:
        result: set[str] = set()
        for entry in self.cross_layer_map.values():
            if not isinstance(entry, dict):
                continue
            for vm in entry.get("viewModels", []):
                result.add(vm)
        return result

    def workspaces_in_map(self) -> set[str]:
        result: set[str] = set()
        for entry in self.cross_layer_map.values():
            if not isinstance(entry, dict):
                continue
            for ws in entry.get("workspace", []):
                result.add(ws)
        return result

    def components_in_map(self) -> set[str]:
        result: set[str] = set()
        for entry in self.cross_layer_map.values():
            if not isinstance(entry, dict):
                continue
            for comp in entry.get("components", []):
                result.add(comp)
        return result

    def graph_renderers_in_map(self) -> set[str]:
        result: set[str] = set()
        for entry in self.cross_layer_map.values():
            if not isinstance(entry, dict):
                continue
            for gr in entry.get("graphRenderers", []):
                result.add(gr)
        return result

    def tests_in_map(self) -> set[str]:
        result: set[str] = set()
        for entry in self.cross_layer_map.values():
            if not isinstance(entry, dict):
                continue
            for t in entry.get("tests", []):
                result.add(t)
        return result

    def to_dict(self) -> dict[str, Any]:
        return {
            "files_scanned": self.files_scanned,
            "cross_layer_entries": len(self.cross_layer_map),
            "graph_nodes": len(self.graph_nodes),
            "graph_edges": len(self.graph_edges),
            "scan_errors": list(self.scan_errors),
        }


# ---------------------------------------------------------------------------
# Scanner
# ---------------------------------------------------------------------------


class ArchitecturalScanner:
    """Deterministic scanner that builds an ``ArchitecturalGraph``.

    Uses Python ``ast`` for backend Python files and text-level scanning for
    frontend TypeScript files.  Loads the cross-layer map and repository graph
    from the generated artifacts.
    """

    DEFAULT_REPO_ROOT = Path(__file__).resolve().parents[3]
    DEFAULT_GRAPH_INDEX = "runtime/generated/repository/index.json"

    def __init__(
        self,
        repo_root: Path | None = None,
        cross_layer_map_path: Path | None = None,
        graph_index_path: Path | None = None,
    ) -> None:
        self.repo_root = repo_root or self.DEFAULT_REPO_ROOT
        # Program 13.3: chains come from the architecture provider. A path is
        # accepted only as an explicit test-fixture injection seam.
        self.cross_layer_map_path = cross_layer_map_path
        self.graph_index_path = (
            graph_index_path or self.repo_root / self.DEFAULT_GRAPH_INDEX
        )

    def scan(self) -> ArchitecturalGraph:
        """Run a full architectural scan and return an immutable graph."""
        errors: list[str] = []
        files: list[ScannedFile] = []

        source_files = discover_source_files(self.repo_root)

        for rel_path in source_files:
            try:
                scanned = self._scan_file(rel_path)
                if scanned is not None:
                    files.append(scanned)
            except Exception as exc:  # noqa: BLE001
                errors.append(f"{rel_path}: {exc}")

        cross_layer_map = self._load_cross_layer_map(errors)
        graph_nodes, graph_edges = self._load_graph_index(errors)

        return ArchitecturalGraph(
            files=tuple(files),
            cross_layer_map=cross_layer_map,
            graph_nodes=tuple(graph_nodes),
            graph_edges=tuple(graph_edges),
            files_scanned=len(files),
            repo_root=str(self.repo_root),
            scan_errors=tuple(errors),
        )

    def _scan_file(self, rel_path: str) -> ScannedFile | None:
        full_path = self.repo_root / rel_path
        if not full_path.exists():
            return None

        layer = classify_layer(rel_path)
        file_type = "typescript" if rel_path.endswith((".ts", ".tsx")) else "python"

        if file_type == "python":
            return self._scan_python(full_path, rel_path, layer)
        return self._scan_typescript(full_path, rel_path, layer)

    def _scan_python(
        self, full: Path, rel: str, layer: ArchitectureLayer
    ) -> ScannedFile:
        source = full.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(full))
        imports: list[ImportRecord] = []

        for module, line_no in _scan_py_imports(tree):
            resolved, target_layer = _resolve_import_to_layer(
                module, "python", self.repo_root
            )
            imports.append(
                ImportRecord(
                    module=module,
                    line_number=line_no,
                    resolved_path=resolved,
                    layer=target_layer.value,
                )
            )

        class_names: list[str] = []
        function_names: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                class_names.append(node.name)
            elif isinstance(node, ast.FunctionDef) or isinstance(
                node, ast.AsyncFunctionDef
            ):
                function_names.append(node.name)

        return ScannedFile(
            path=rel,
            layer=layer.value,
            file_type="python",
            imports=tuple(imports),
            fetch_call_lines=(),
            has_workspace_registration=False,
            class_names=tuple(class_names),
            function_names=tuple(function_names),
        )

    def _scan_typescript(
        self, full: Path, rel: str, layer: ArchitectureLayer
    ) -> ScannedFile:
        source = full.read_text(encoding="utf-8")
        imports: list[ImportRecord] = []

        for module, line_no in _scan_ts_imports(source):
            resolved, target_layer = _resolve_import_to_layer(
                module, "typescript", self.repo_root
            )
            imports.append(
                ImportRecord(
                    module=module,
                    line_number=line_no,
                    resolved_path=resolved,
                    layer=target_layer.value,
                )
            )

        fetch_lines = tuple(_scan_ts_fetch_calls(source))
        has_ws = _has_workspace_registration(source)

        return ScannedFile(
            path=rel,
            layer=layer.value,
            file_type="typescript",
            imports=tuple(imports),
            fetch_call_lines=fetch_lines,
            has_workspace_registration=has_ws,
            class_names=(),
            function_names=(),
        )

    def _load_cross_layer_map(self, errors: list[str]) -> dict[str, Any]:
        if self.cross_layer_map_path is None:
            try:
                from runtime.foundation.architecture.chains import get_chain_map

                return get_chain_map()
            except Exception as exc:  # noqa: BLE001
                errors.append(f"Architecture provider unavailable: {exc}")
                return {}
        try:
            with open(self.cross_layer_map_path, encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                return data
            errors.append(f"Cross-layer map is not a dict: {self.cross_layer_map_path}")
            return {}
        except FileNotFoundError:
            errors.append(f"Cross-layer map not found: {self.cross_layer_map_path}")
            return {}
        except (json.JSONDecodeError, OSError) as exc:
            errors.append(f"Error loading cross-layer map: {exc}")
            return {}

    def _load_graph_index(self, errors: list[str]) -> tuple[list[dict], list[dict]]:
        try:
            with open(self.graph_index_path, encoding="utf-8") as f:
                data = json.load(f)
        except FileNotFoundError:
            errors.append(f"Graph index not found: {self.graph_index_path}")
            return [], []
        except (json.JSONDecodeError, OSError) as exc:
            errors.append(f"Error loading graph index: {exc}")
            return [], []

        meta = data.get("metadata", {})
        graph_data = data.get("graph", {})
        if not graph_data:
            graph_data = data
        nodes = graph_data.get("nodes", [])
        edges = graph_data.get("edges", [])
        return list(nodes), list(edges)
