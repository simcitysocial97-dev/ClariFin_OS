"""
M9-C49 — Shared-Module Impact Analysis.

Closes the C48 "capability resolution incomplete for shared modules" gap for
shared infrastructure changes. When a shared module (e.g.
``backend/src/common/calculations.py``) changes, the CrossLayerImpactPlanner
path-patterns match no engine, so no capabilities are reported through that
path. This module resolves the *exact* capability set that depends on a
changed repository module using deterministic AST import analysis over the
live tree — no maintained prose, no heuristics, no second registry.

The index is a pure function of the source tree: same tree → same dependency
set → same plan (reproducibility requirement).
"""

from __future__ import annotations

import ast
from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent


# ---------------------------------------------------------------------------
# Module name ↔ path helpers (backend import domain)
# ---------------------------------------------------------------------------


def module_to_repo_path(dotted: str) -> str | None:
    """``backend.src.common.calculations`` → ``backend/src/common/calculations.py``.

    Only ``backend``-rooted modules participate; third-party and frontend
    imports are out of scope for backend capability resolution. Returns the
    path whether the module is a file or a package.
    """
    if not dotted or not (dotted.startswith("backend.") or dotted.startswith("src.")):
        return None
    # Normalise bare ``src.*`` to ``backend.src.*`` so the path logic below
    # works unchanged — all backend source lives under the ``backend/`` root.
    if dotted.startswith("src."):
        dotted = "backend." + dotted
    rel = dotted.replace(".", "/")
    candidate = f"{rel}.py"
    if (REPO_ROOT / candidate).exists():
        return candidate
    package_init = f"{rel}/__init__.py"
    if (REPO_ROOT / package_init).exists():
        return package_init
    return None


def path_to_module(rel_path: str) -> str | None:
    """``backend/src/common/calculations.py`` → ``backend.src.common.calculations``."""
    p = Path(rel_path).as_posix()
    if not p.startswith("backend/") or not p.endswith(".py"):
        return None
    dotted = p[: -len(".py")].replace("/", ".")
    if dotted.endswith(".__init__"):
        dotted = dotted[: -len(".__init__")]
    return dotted


def _iter_py_files(root: Path):
    for f in sorted(root.rglob("*.py")):
        if any(part.startswith(".") for part in f.parts):
            continue
        yield f


def _extract_imports(source: str, file_rel: str) -> set[str]:
    """Return the set of ``backend.*`` module names a file imports."""
    try:
        tree = ast.parse(source)
    except (SyntaxError, ValueError):
        return set()
    imported: set[str] = set()
    parts = file_rel.split("/")
    base_pkg: str | None = None
    if parts[0] == "backend" and len(parts) >= 3:
        # Package of the file itself (relative imports resolve against it),
        # rooted at the ``backend.`` dotted prefix.
        base_pkg = (
            ".".join(parts[:-1]) if parts[-1] != "__init__.py" else ".".join(parts[:-2])
        )

    def _add(name: str) -> None:
        if name.startswith("backend.") or name.startswith("src."):
            imported.add(name)

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                _add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.level and node.level > 0:
                if base_pkg is None:
                    continue
                full = f"{base_pkg}.{node.module}" if node.module else base_pkg
                for _ in range(node.level - 1):
                    if "." not in full:
                        break
                    full = full.rsplit(".", 1)[0]
                _add(full)
                for alias in node.names:
                    if alias.name != "*":
                        _add(f"{full}.{alias.name}")
            elif node.module:
                _add(node.module)
    return imported


# ---------------------------------------------------------------------------
# Index
# ---------------------------------------------------------------------------


@dataclass
class SharedDependencyIndex:
    """Deterministic capability → imported-module map for the live tree.

    * ``file_imports[path]`` — backend module names each file imports.
    * ``capability_modules[cap]`` — repo-relative ``.py`` paths belonging to
      the capability's declared modules.
    * ``module_dependents[mod]`` — capabilities (other or same) whose code
      transitively depends on repository module ``mod``.
    """

    file_imports: dict[str, set[str]] = field(default_factory=dict)
    capability_modules: dict[str, set[str]] = field(default_factory=dict)
    module_dependents: dict[str, set[str]] = field(default_factory=dict)

    @classmethod
    def build(cls, contract_registry) -> SharedDependencyIndex:
        idx = cls()

        # 1. Import map over all backend source files.
        backend_src = REPO_ROOT / "backend" / "src"
        if backend_src.exists():
            for f in _iter_py_files(backend_src):
                rel = f.relative_to(REPO_ROOT).as_posix()
                try:
                    source = f.read_text(encoding="utf-8")
                except OSError:
                    continue
                idx.file_imports[rel] = _extract_imports(source, rel)

        # 2. Capability module membership.
        for contract in contract_registry.get_all_contracts():
            modules: set[str] = set()
            for cap_module in contract.affected_by_paths:
                if not cap_module:
                    continue
                p = REPO_ROOT / cap_module
                if p.is_file() and p.suffix == ".py":
                    modules.add(p.relative_to(REPO_ROOT).as_posix())
                elif p.is_dir():
                    for f in _iter_py_files(p):
                        modules.add(f.relative_to(REPO_ROOT).as_posix())
            idx.capability_modules[contract.id] = modules

        # 3. File-level import DAG: file → files it imports.
        file_edges: dict[str, set[str]] = {}
        for f, imps in idx.file_imports.items():
            targets: set[str] = set()
            for imp in imps:
                target = module_to_repo_path(imp)
                if target is not None:
                    targets.add(target)
            file_edges[f] = targets

        # Transitive closure per file (deterministic fixpoint, sorted order).
        transitive: dict[str, set[str]] = {}
        changed = True
        for f in sorted(file_edges):
            transitive[f] = set(file_edges[f])
        while changed:
            changed = False
            for f in sorted(file_edges):
                current = transitive[f]
                for target in sorted(set(current) & set(file_edges)):
                    if not transitive[target].issubset(current):
                        current |= transitive[target]
                        changed = True
                transitive[f] = current

        # 4. Inverse index: module M is depended on by capability C when
        #    some file of C transitively imports M, or C owns M directly.
        for cap, files in idx.capability_modules.items():
            for f in files:
                # ownership
                idx.module_dependents.setdefault(f, set()).add(cap)
                # imported (transitively)
                for target in transitive.get(f, ()):
                    idx.module_dependents.setdefault(target, set()).add(cap)

        # 5. Reverse-lookup index: for every backend file, record which
        #    capabilities it transitively depends on (needed so that a
        #    change to a service like loan_service.py surfaces the
        #    downstream capability it invokes).
        all_files = set(file_edges.keys())
        for cap_files in idx.capability_modules.values():
            all_files |= cap_files
        for cap, cap_files in idx.capability_modules.items():
            for f in all_files:
                if f in cap_files:
                    continue  # already recorded as ownership above
                if any(cf in transitive.get(f, set()) for cf in cap_files):
                    idx.module_dependents.setdefault(f, set()).add(cap)

        return idx

    def capabilities_for_module(self, changed_path: str) -> list[str]:
        """Capabilities that depend on the given changed repo-relative path."""
        p = Path(changed_path).as_posix()
        candidates = {p}
        if p.endswith("/__init__.py"):
            candidates.add(p[: -len("/__init__.py")])
        elif p.endswith(".py"):
            candidates.add(p[: -len(".py")] + "/__init__.py")
        caps: set[str] = set()
        for cand in candidates:
            caps.update(self.module_dependents.get(cand, set()))
        return sorted(caps)


# ---------------------------------------------------------------------------
# Cache
# ---------------------------------------------------------------------------

_INDEX: SharedDependencyIndex | None = None


def get_shared_dependency_index(contract_registry=None) -> SharedDependencyIndex:
    global _INDEX
    if _INDEX is None:
        if contract_registry is None:
            from runtime.foundation.verification.capability_contract import (
                get_capability_contract_registry,
            )

            contract_registry = get_capability_contract_registry()
        _INDEX = SharedDependencyIndex.build(contract_registry)
    return _INDEX


def reset_shared_dependency_index() -> None:
    global _INDEX
    _INDEX = None
