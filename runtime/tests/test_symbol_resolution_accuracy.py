"""M9-C55 — Symbol Resolution Accuracy Tests.

Validates that AST-based symbol extraction reports correct names, kinds, line
ranges, and parent classes.
"""
from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from runtime.foundation.verification.symbol_resolver import SymbolExtractor


class TestSymbolResolutionAccuracy:
    """Tests for symbol extraction correctness."""

    def test_extract_known_functions(self):
        test_file = Path("backend/src/engines/loan_engine/emi.py")
        if not test_file.exists():
            pytest.skip("emi.py not found")

        symbols = SymbolExtractor().extract_from_file(test_file)
        assert len(symbols) > 0
        names = {s.name for s in symbols}
        # emi.py defines compute_* functions, not calculate_emi
        expected_symbols = ["compute_emi_fixed", "compute_emi_floating", "compute_monthly_interest"]
        for expected in expected_symbols:
            assert expected in names, f"Expected symbol {expected} not found. Found: {names}"

    def test_line_ranges_valid(self):
        test_file = Path("backend/src/engines/loan_engine/emi.py")
        if not test_file.exists():
            pytest.skip("emi.py not found")

        for sym in SymbolExtractor().extract_from_file(test_file):
            assert sym.start_line > 0
            assert sym.end_line >= sym.start_line
            assert sym.end_line < 100000

    def test_method_vs_function_distinction(self):
        code = (
            "class TestClass:\n"
            "    def method_one(self):\n"
            "        pass\n"
            "\n"
            "    def method_two(self):\n"
            "        pass\n"
            "\n"
            "def top_level_function():\n"
            "    pass\n"
        )
        with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as f:
            f.write(code)
            tmp = Path(f.name)
        try:
            symbols = SymbolExtractor().extract_from_file(tmp)
            methods = [s for s in symbols if s.kind == "method"]
            functions = [s for s in symbols if s.kind == "function"]
            classes = [s for s in symbols if s.kind == "class"]

            assert len(methods) == 2, f"Expected 2 methods, got {len(methods)}: {[s.name for s in methods]}"
            assert len(functions) == 1, f"Expected 1 function, got {len(functions)}"
            assert len(classes) == 1, f"Expected 1 class, got {len(classes)}"

            for m in methods:
                assert m.parent_class == "TestClass", f"Method {m.name} parent_class={m.parent_class}"
        finally:
            tmp.unlink(missing_ok=True)

    def test_coverage_symbol_mapper_skips_no_data(self):
        from runtime.foundation.verification.symbol_resolver import CoverageSymbolMapper

        mapper = CoverageSymbolMapper()
        covered = mapper.load_coverage_data()
        if covered:
            mapped = mapper.map_coverage_to_symbols(covered)
            assert isinstance(mapped, dict)
