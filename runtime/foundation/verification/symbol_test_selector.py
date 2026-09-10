"""Symbol-based test selection for verification scope optimization."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Set

logger = logging.getLogger(__name__)


@dataclass
class SymbolTestSelection:
    """Result of symbol-based test selection."""

    selected_tests: Set[Path] = field(default_factory=set)
    reason: str = "unknown"
    changed_symbols: List[str] = field(default_factory=list)
    coverage_available: bool = False


class SymbolTestSelector:
    """Select tests based on changed symbols using coverage mapping."""

    def __init__(self, symbol_test_map_path: Path = None):
        self.map_path = (
            symbol_test_map_path
            or Path("runtime/generated/symbol-test-map.json")
        )
        self.symbol_to_tests = self._load_map()

    def _load_map(self) -> Dict[str, Set[Path]]:
        """Load cached symbol-to-test mapping from JSON file."""
        if not self.map_path.exists():
            logger.warning(
                f"Symbol-test map not found at {self.map_path}, "
                "coverage-based test selection will fallback to module-level"
            )
            return {}

        try:
            data = json.loads(self.map_path.read_text())
            result: Dict[str, Set[Path]] = {}
            for symbol, test_files in data.items():
                result[symbol] = {Path(t) for t in test_files}
            return result
        except (json.JSONDecodeError, OSError) as e:
            logger.warning(f"Failed to load symbol-test map: {e}")
            return {}

    def select_tests_for_symbols(
        self, changed_symbols: Dict[Path, Set]
    ) -> SymbolTestSelection:
        """Select tests that cover the given changed symbols.

        Args:
            changed_symbols: Mapping of file path to set of changed Symbol objects.

        Returns:
            SymbolTestSelection with selected tests and reason.
        """
        if not changed_symbols:
            return SymbolTestSelection(
                selected_tests=set(),
                reason="no-changed-symbols",
                coverage_available=bool(self.symbol_to_tests),
            )

        all_changed_symbol_names: Set[str] = set()
        for symbols in changed_symbols.values():
            for sym in symbols:
                all_changed_symbol_names.add(sym.name)

        if not self.symbol_to_tests:
            return SymbolTestSelection(
                selected_tests=set(),
                reason="fallback-no-coverage-map",
                changed_symbols=sorted(all_changed_symbol_names),
                coverage_available=False,
            )

        selected_tests: Set[Path] = set()
        for symbol_name in all_changed_symbol_names:
            if symbol_name in self.symbol_to_tests:
                selected_tests.update(self.symbol_to_tests[symbol_name])

        if not selected_tests:
            return SymbolTestSelection(
                selected_tests=set(),
                reason="no-tests-cover-symbols",
                changed_symbols=sorted(all_changed_symbol_names),
                coverage_available=True,
            )

        return SymbolTestSelection(
            selected_tests=selected_tests,
            reason="symbol-level",
            changed_symbols=sorted(all_changed_symbol_names),
            coverage_available=True,
        )

    def get_coverage_status(self) -> bool:
        """Check if coverage mapping is available."""
        return bool(self.symbol_to_tests)

    def rebuild_map(self, test_directory: Path) -> Dict[str, Set[Path]]:
        """Rebuild the symbol-to-test mapping by running tests with coverage.

        This is expensive — call only when map is stale or missing.
        """
        from .symbol_resolver import CoverageSymbolMapper

        mapper = CoverageSymbolMapper()
        symbol_to_tests = mapper.build_symbol_to_test_map(test_directory)
        self.symbol_to_tests = {
            k: v for k, v in symbol_to_tests.items()
        }
        self._save_map()
        return self.symbol_to_tests

    def _save_map(self):
        """Persist the symbol-to-test mapping to JSON."""
        flat_map = {}
        for symbol_name, test_files in self.symbol_to_tests.items():
            flat_map[symbol_name] = sorted(str(tf) for tf in test_files)
        self.map_path.parent.mkdir(parents=True, exist_ok=True)
        self.map_path.write_text(json.dumps(flat_map, indent=2))
        logger.info(f"Saved symbol-test map with {len(flat_map)} entries")


if __name__ == "__main__":
    selector = SymbolTestSelector()
    print(f"Coverage available: {selector.get_coverage_status()}")
    if selector.get_coverage_status():
        sample_symbols = list(selector.symbol_to_tests.keys())[:3]
        print(f"Sample symbols: {sample_symbols}")
        for sym in sample_symbols:
            tests = selector.symbol_to_tests[sym]
            print(f"  {sym}: {len(tests)} test(s)")
    else:
        print("No coverage map — run tests with --cov to build one")
