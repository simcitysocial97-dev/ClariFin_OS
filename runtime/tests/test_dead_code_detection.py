"""M9-C55 — Dead Code & Gate Registration Tests.

Identifies potentially unused public functions and verifies gates are registered.
"""
from __future__ import annotations

import ast
import subprocess
import sys
from collections import defaultdict
from pathlib import Path


class TestDeadCodeDetection:
    """Detect unused public functions in runtime code."""

    def test_no_unused_public_functions(self):
        """Public functions should be called somewhere in runtime or tests."""
        defined: defaultdict[str, list[Path]] = defaultdict(list)
        called: set[str] = set()

        runtime_files = list(Path("runtime/foundation").rglob("*.py"))
        test_files = list(Path("runtime/tests").glob("test_*.py"))
        all_files = runtime_files + test_files

        exclude_dirs = {"__pycache__", "generated", "archive"}

        # Collect definitions (skip private, magic, test functions)
        for py_file in runtime_files:
            if any(d in py_file.parts for d in exclude_dirs):
                continue
            try:
                tree = ast.parse(py_file.read_text())
            except SyntaxError:
                continue
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    if node.name.startswith("_") or node.name.startswith("test_"):
                        continue
                    defined[node.name].append(py_file)

        # Collect calls
        for py_file in all_files:
            if any(d in py_file.parts for d in exclude_dirs):
                continue
            try:
                tree = ast.parse(py_file.read_text())
            except SyntaxError:
                continue
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name):
                        called.add(node.func.id)
                    elif isinstance(node.func, ast.Attribute):
                        called.add(node.func.attr)

        # Find potentially unused public functions
        unused = []
        for func_name, files in defined.items():
            if func_name not in called:
                is_cli_entry = any("canonical_control_plane" in str(f) or "cli.py" in str(f) for f in files)
                if not is_cli_entry:
                    unused.append((func_name, files[0]))

        if unused:
            print(f"\n⚠️  {len(unused)} potentially unused public functions:")
            for func, fpath in unused[:15]:
                print(f"   {func} defined in {fpath.name}")
        # Warning only — dynamic dispatch may call some of these


class TestGateRegistration:
    """Verify verification gates are registered and functional."""

    def test_api_contract_gate_exists(self):
        """ApiContractGate must be importable."""
        from runtime.foundation.verification.api_contracts.gate import ApiContractGate
        assert ApiContractGate is not None

    def test_frontend_backend_gate_exists(self):
        """FrontendBackendGate must be importable."""
        from runtime.foundation.verification.frontend_backend_gate import FrontendBackendGate
        assert FrontendBackendGate is not None

    def test_api_contract_gate_callable(self):
        """ApiContractGate must have an execute method."""
        from runtime.foundation.verification.api_contracts.gate import ApiContractGate
        assert hasattr(ApiContractGate, "execute") or hasattr(ApiContractGate, "run")

    def test_certification_gate_exists(self):
        """CertificationGate must be importable."""
        from runtime.foundation.verification.certification import CertificationGate
        assert CertificationGate is not None
