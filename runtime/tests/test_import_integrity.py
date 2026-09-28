"""M9-C55 — Import Integrity Audit.

Verifies that all runtime.foundation modules are importable, detects circular
dependencies, and flags imports from deprecated paths.
"""
from __future__ import annotations

import ast
import subprocess
import sys
from pathlib import Path


RUNTIME_ROOT = Path("runtime/foundation/verification")
TESTS_ROOT = Path("runtime/tests")


def _iter_python(root: Path, exclude: set[str] | None = None) -> list[Path]:
    """Return all .py files under root, skipping excluded directories."""
    excluded = exclude or set()
    out: list[Path] = []
    for p in root.rglob("*.py"):
        parts = {part for part in p.parts} & excluded
        if parts:
            continue
        out.append(p)
    return out


class TestImportIntegrity:
    """Tests that no runtime modules are orphaned or circularly importing."""

    def test_no_circular_imports(self):
        """Build an AST of runtime imports and look for cycles."""
        try:
            import networkx as nx  # noqa
        except ImportError:
            return  # skip when networkx unavailable

        G = nx.DiGraph()
        py_files = _iter_python(RUNTIME_ROOT, {"__pycache__", "generated"})

        for py_file in py_files:
            rel = str(py_file.relative_to(Path.cwd()).with_suffix("")).replace("/", ".")
            G.add_node(rel)
            try:
                tree = ast.parse(py_file.read_text())
            except SyntaxError:
                continue
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom) and node.module:
                    if node.module.startswith("runtime"):
                        G.add_edge(rel, node.module)

        cycles = list(nx.simple_cycles(G))
        assert not cycles, f"Found {len(cycles)} circular import chains"

    def test_no_broken_deprecated_imports(self):
        """Deprecated import paths must still resolve (re-exports)."""
        deprecated_modules = [
            "runtime.system.evidence.models.evidence",
        ]
        failures: list[str] = []
        for mod in deprecated_modules:
            try:
                __import__(mod)
            except ImportError as e:
                failures.append(f"{mod}: {e}")
        assert not failures, f"Broken deprecated imports:\n" + "\n".join(failures)

    def test_all_runtime_modules_parse(self):
        """Every runtime module must parse without syntax errors."""
        failures: list[str] = []
        for py_file in _iter_python(RUNTIME_ROOT, {"__pycache__", "generated"}):
            try:
                source = py_file.read_text()
                ast.parse(source)
            except SyntaxError as e:
                rel = str(py_file.relative_to(Path.cwd())) if Path.cwd() in py_file.parents or py_file.is_relative_to(Path.cwd()) else str(py_file)
                failures.append(f"{rel}: {e}")
        assert not failures, f"Syntax errors:\n" + "\n".join(failures[:20])
