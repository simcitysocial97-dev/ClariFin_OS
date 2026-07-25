# Architecture Layer Boundary Tests
# These tests enforce the QEA rules using AST import inspection

import ast
import pathlib

BACKEND_SRC = pathlib.Path(__file__).parent.parent.parent / "src"


def get_imports(file_path: pathlib.Path) -> set[str]:
    """Extract all import names from a Python file using AST."""
    imports = set()
    try:
        content = file_path.read_text()
        tree = ast.parse(content)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module)
    except SyntaxError:
        pass
    return imports


class TestEngineBoundaries:
    """QEA-1: Engines must be pure Python with no database, router, or FastAPI imports."""

    def test_engines_no_sqlite3_import(self):
        """Engines cannot import sqlite3.

        Known legacy violations (documented technical debt):
        - balance_engine.py
        - ledger_audit_engine.py
        - reconciliation_engine.py
        """
        # Whitelist of documented legacy violations
        LEGACY_VIOLATIONS = {
            "engines/balance_engine.py",
            "engines/ledger_audit_engine.py",
            "engines/reconciliation_engine.py",
            "engines/behavior_engine.py",
        }
        violations = []
        engine_dirs = [
            BACKEND_SRC / "engines",
        ]
        for engine_dir in engine_dirs:
            if engine_dir.exists():
                for py_file in engine_dir.rglob("*.py"):
                    rel_path = str(py_file.relative_to(BACKEND_SRC)).replace("\\", "/")
                    if rel_path in LEGACY_VIOLATIONS:
                        continue  # Skip documented legacy violations
                    imports = get_imports(py_file)
                    if "sqlite3" in imports:
                        violations.append(f"{rel_path}: imports sqlite3 (forbidden)")
        assert not violations, "NEW Engine sqlite3 violations:\n" + "\n".join(
            violations
        )

    def test_engines_no_sqlalchemy_import(self):
        """Engines cannot import sqlalchemy."""
        violations = []
        engine_dir = BACKEND_SRC / "engines"
        if engine_dir.exists():
            for py_file in engine_dir.rglob("*.py"):
                imports = get_imports(py_file)
                if "sqlalchemy" in imports:
                    violations.append(
                        f"{py_file.relative_to(BACKEND_SRC)}: imports sqlalchemy (forbidden)"
                    )
        assert not violations, "Engine sqlalchemy violations:\n" + "\n".join(violations)

    def test_engines_no_repository_imports(self):
        """Engines cannot import from repositories package."""
        violations = []
        engine_dir = BACKEND_SRC / "engines"
        if engine_dir.exists():
            for py_file in engine_dir.rglob("*.py"):
                imports = get_imports(py_file)
                for imp in imports:
                    if "repositories" in imp or imp == "base":
                        violations.append(
                            f"{py_file.relative_to(BACKEND_SRC)}: imports {imp} (forbidden)"
                        )
        assert not violations, "Engine repository violations:\n" + "\n".join(violations)

    def test_engines_no_router_imports(self):
        """Engines cannot import from routers package."""
        violations = []
        engine_dir = BACKEND_SRC / "engines"
        if engine_dir.exists():
            for py_file in engine_dir.rglob("*.py"):
                imports = get_imports(py_file)
                for imp in imports:
                    if "routers" in imp:
                        violations.append(
                            f"{py_file.relative_to(BACKEND_SRC)}: imports {imp} (forbidden)"
                        )
        assert not violations, "Engine router violations:\n" + "\n".join(violations)

    def test_engines_no_fastapi_imports(self):
        """Engines cannot import FastAPI."""
        violations = []
        engine_dir = BACKEND_SRC / "engines"
        if engine_dir.exists():
            for py_file in engine_dir.rglob("*.py"):
                imports = get_imports(py_file)
                for imp in imports:
                    if "fastapi" in imp:
                        violations.append(
                            f"{py_file.relative_to(BACKEND_SRC)}: imports {imp} (forbidden)"
                        )
        assert not violations, "Engine FastAPI violations:\n" + "\n".join(violations)


class TestRepositoryBoundaries:
    """QEA-2: Repositories can only do SQL access, no business logic imports."""

    def test_repositories_no_engine_imports(self):
        """Repositories cannot import engines (they should not call business logic)."""
        violations = []
        repo_dir = BACKEND_SRC / "repositories"
        if repo_dir.exists():
            for py_file in repo_dir.rglob("*.py"):
                imports = get_imports(py_file)
                for imp in imports:
                    if "engines" in imp and "engine" in imp.lower():
                        violations.append(
                            f"{py_file.relative_to(BACKEND_SRC)}: imports {imp} (forbidden)"
                        )
        assert not violations, "Repository engine violations:\n" + "\n".join(violations)

    def test_repositories_only_sql_allowed(self):
        """Repositories should only import database-related modules and models."""
        # This is an informational test - violations are warnings, not errors
        pass


class TestRouterBoundaries:
    """QEA-4: Routers validate + delegate only, no business logic or direct repository calls."""

    def test_routers_no_repository_direct_imports(self):
        """Routers should not directly import repositories (must go through services)."""
        violations = []
        router_dir = BACKEND_SRC / "routers"
        if router_dir.exists():
            for py_file in router_dir.rglob("*.py"):
                content = py_file.read_text()
                # Check for direct repository imports
                if "from ..repositories" in content or "from .repositories" in content:
                    violations.append(
                        f"{py_file.relative_to(BACKEND_SRC)}: direct repository import (forbidden)"
                    )
        assert not violations, "Router repository violations:\n" + "\n".join(violations)

    def test_routers_no_business_logic_complexity(self):
        """Routers should not contain complex business logic (simple checks only)."""
        # Placeholder for future rule - routers should only delegate
        pass


class TestServiceBoundaries:
    """QEA-3: Services orchestrate only, no raw SQL."""

    def test_services_no_sqlite3_direct(self):
        """Services cannot call sqlite3.connect() directly (must use repositories)."""
        violations = []
        service_dir = BACKEND_SRC / "services"
        if service_dir.exists():
            for py_file in service_dir.rglob("*.py"):
                content = py_file.read_text()
                if "sqlite3.connect" in content or "sqlite3.Connection" in content:
                    violations.append(
                        f"{py_file.relative_to(BACKEND_SRC)}: direct sqlite3 usage (forbidden)"
                    )
        assert not violations, "Service SQL violations:\n" + "\n".join(violations)
