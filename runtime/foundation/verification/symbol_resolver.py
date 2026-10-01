"""AST-based Python symbol extractor with caching."""

import ast
import json
import logging
import subprocess
import tempfile
from pathlib import Path

logger = logging.getLogger(__name__)


class Symbol:
    """Represents a Python symbol (function, method, or class)."""

    def __init__(
        self,
        name: str,
        kind: str,
        file: Path,
        start_line: int,
        end_line: int,
        parent_class: str = None,
    ):
        self.name = name
        self.kind = kind
        self.file = file
        self.start_line = start_line
        self.end_line = end_line
        self.parent_class = parent_class

    def __repr__(self):
        return f"Symbol({self.kind} '{self.name}', {self.file.name}:{self.start_line}-{self.end_line})"

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "kind": self.kind,
            "file": str(self.file),
            "start_line": self.start_line,
            "end_line": self.end_line,
            "parent_class": self.parent_class,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Symbol":
        return cls(
            name=data["name"],
            kind=data["kind"],
            file=Path(data["file"]),
            start_line=data["start_line"],
            end_line=data["end_line"],
            parent_class=data.get("parent_class"),
        )


class SymbolExtractor:
    """Extract symbols from Python source files via AST parsing.

    Results are cached on disk keyed by resolved absolute path and validated by
    file mtime. The cache is deliberately bounded and self-pruning — see
    ``_is_cacheable`` and ``_prune_cache`` for why that is a correctness
    requirement rather than a housekeeping nicety.
    """

    def __init__(self, cache_path: Path = None):
        self.cache_path = cache_path or Path("runtime/generated/symbol-cache.json")
        self.cache = self._load_cache()
        # Only rewrite the file when something actually changed. Rewriting it
        # unconditionally serialised the entire cache on every extraction, so
        # the cost of touching one small file was the cost of the whole cache.
        self._dirty = False

    def _load_cache(self) -> dict:
        if self.cache_path.exists():
            try:
                cache = json.loads(self.cache_path.read_text())
            except (json.JSONDecodeError, OSError):
                logger.warning("Failed to load symbol cache, starting fresh")
                return {}
            return self._prune_cache(cache)
        return {}

    def _prune_cache(self, cache: dict) -> dict:
        """Drop entries that can never be served again.

        Two classes of entry are dead weight:

        * paths under the system temp directory, whose files are deleted when
          the process ends — a later run will never find them, so their parsed
          symbols can never be reused;
        * any path that no longer exists, whose mtime can never be matched
          again.

        Without this the cache grew without bound: one full test-suite run left
        51 of 52 entries pointing at ephemeral ``/tmp/tmpXXXX.py`` fixtures,
        12.5 MB of payload on disk in a single run. Because every extraction
        re-serialised the whole cache, the extractor grew slower with every run
        until it exceeded the per-test time budget, which presented as a suite
        that failed intermittently depending on how much history had piled up.
        The cache is an optimisation; letting it grow past the point where it
        costs more than it saves is how it became a correctness problem.
        """
        if not cache:
            return cache
        temp_dir = Path(tempfile.gettempdir()).resolve()
        keep: dict = {}
        dropped_temp = 0
        dropped_missing = 0
        for key, entry in cache.items():
            try:
                path = Path(key)
            except (TypeError, ValueError):
                dropped_missing += 1
                continue
            try:
                if path.is_relative_to(temp_dir):
                    dropped_temp += 1
                    continue
            except (OSError, ValueError):
                pass
            try:
                if not path.exists():
                    dropped_missing += 1
                    continue
            except OSError:
                dropped_missing += 1
                continue
            keep[key] = entry
        if dropped_temp or dropped_missing:
            logger.debug(
                "Pruned symbol cache: %d ephemeral temp entries, %d missing-path entries",
                dropped_temp,
                dropped_missing,
            )
        return keep

    def _is_cacheable(self, resolved: Path) -> bool:
        """Whether a resolved path belongs in the persistent cache.

        Files under the system temp directory are excluded. Their parsed
        symbols have no reuse value across processes — the file is gone before
        the next run — so persisting them is pure cost: disk, serialisation
        time, and a growing file that every later run must read and rewrite.
        """
        try:
            return not resolved.is_relative_to(Path(tempfile.gettempdir()).resolve())
        except (OSError, ValueError):
            return True

    def _save_cache(self):
        if not self._dirty:
            return
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        self.cache_path.write_text(json.dumps(self.cache, indent=2))
        self._dirty = False

    def extract_from_file(self, file_path: Path) -> list[Symbol]:
        """Extract all symbols from a single Python file.

        Uses mtime-based cache invalidation. Handles malformed files gracefully.
        """
        file_path = Path(file_path)

        try:
            file_mtime = file_path.stat().st_mtime
        except FileNotFoundError:
            logger.warning(f"File not found: {file_path}")
            return []

        file_key = str(file_path.resolve())

        if file_key in self.cache:
            cached = self.cache[file_key]
            if cached.get("mtime") == file_mtime:
                return [Symbol.from_dict(s) for s in cached["symbols"]]

        symbols = []
        try:
            source = file_path.read_text(encoding="utf-8")
            tree = ast.parse(source, filename=str(file_path))

            class Visitor(ast.NodeVisitor):
                def __init__(self):
                    self.class_stack = []

                def visit_ClassDef(self, node):
                    symbols.append(
                        Symbol(
                            name=node.name,
                            kind="class",
                            file=file_path,
                            start_line=node.lineno,
                            end_line=node.end_lineno or node.lineno,
                        )
                    )
                    self.class_stack.append(node.name)
                    self.generic_visit(node)
                    self.class_stack.pop()

                def visit_FunctionDef(self, node):
                    self._function(node)

                def visit_AsyncFunctionDef(self, node):
                    self._function(node)

                def _function(self, node):
                    parent = self.class_stack[-1] if self.class_stack else None
                    symbols.append(
                        Symbol(
                            name=node.name,
                            kind="method" if parent else "function",
                            file=file_path,
                            start_line=node.lineno,
                            end_line=node.end_lineno or node.lineno,
                            parent_class=parent,
                        )
                    )
                    self.generic_visit(node)

            Visitor().visit(tree)

        except SyntaxError as e:
            logger.warning(f"Syntax error in {file_path}: {e}")
        except Exception as e:
            logger.warning(f"Failed to parse {file_path}: {e}")

        # Persist only files whose parsed symbols can actually be reused. A file
        # under the system temp directory is deleted when the process exits, so
        # caching it costs a permanent, ever-growing entry that no later run can
        # ever hit — and because the whole cache is re-serialised on write, that
        # cost is paid again on every subsequent extraction of any file.
        if self._is_cacheable(Path(file_key)):
            self.cache[file_key] = {
                "mtime": file_mtime,
                "symbols": [s.to_dict() for s in symbols],
            }
            self._dirty = True
        else:
            self.cache.pop(file_key, None)
        self._save_cache()
        return symbols

    def extract_from_directory(self, directory: Path) -> dict[Path, list[Symbol]]:
        """Extract symbols from all Python files in a directory recursively."""
        result = {}
        directory = Path(directory)
        for py_file in sorted(directory.rglob("*.py")):
            symbols = self.extract_from_file(py_file)
            result[py_file] = symbols
        return result

    def get_symbol_at_line(self, file_path: Path, line_number: int) -> Symbol:
        """Find which symbol contains the given line number."""
        symbols = self.extract_from_file(file_path)
        for symbol in symbols:
            if symbol.start_line <= line_number <= symbol.end_line:
                return symbol
        return None

    def invalidate_cache(self, file_path: Path = None):
        """Invalidate cache entry for a specific file or clear entire cache."""
        if file_path:
            file_key = str(Path(file_path).resolve())
            self.cache.pop(file_key, None)
            self._save_cache()
        else:
            self.cache.clear()
            self._save_cache()


class CoverageSymbolMapper:
    """Map test coverage data to symbols (function/method/class)."""

    def __init__(self, coverage_file: Path = Path(".coverage")):
        self.coverage_file = coverage_file
        self.extractor = SymbolExtractor()
        self.symbol_test_map_path = Path("runtime/generated/symbol-test-map.json")
        self.symbol_test_map = self._load_symbol_test_map()

    def _load_symbol_test_map(self) -> dict[str, list[str]]:
        if self.symbol_test_map_path.exists():
            try:
                return json.loads(self.symbol_test_map_path.read_text())
            except (json.JSONDecodeError, OSError):
                logger.warning("Failed to load symbol-test map cache")
        return {}

    def _save_symbol_test_map(self):
        self.symbol_test_map_path.parent.mkdir(parents=True, exist_ok=True)
        self.symbol_test_map_path.write_text(json.dumps(self.symbol_test_map, indent=2))

    def load_coverage_data(self) -> dict[Path, set[int]]:
        """Load coverage data: file → set of covered line numbers."""
        if not self.coverage_file.exists():
            return {}

        try:
            import coverage as cov_module
        except ImportError:
            logger.warning("coverage.py not installed, returning empty coverage data")
            return {}

        try:
            cov = cov_module.Coverage(data_file=str(self.coverage_file))
            cov.load()

            covered_lines = {}
            for filename in cov.get_data().measured_files():
                file_path = Path(filename)
                analysis = cov.analysis(filename)
                covered_lines[file_path] = set(analysis[1])  # Line numbers executed

            return covered_lines
        except Exception as e:
            logger.warning(f"Failed to load coverage data: {e}")
            return {}

    def map_coverage_to_symbols(
        self, covered_lines: dict[Path, set[int]]
    ) -> dict[Path, set[str]]:
        """Map covered lines to symbol names per source file."""
        file_to_symbols = {}

        for file_path, lines in covered_lines.items():
            covered_symbols = set()

            for line in lines:
                symbol = self.extractor.get_symbol_at_line(file_path, line)
                if symbol:
                    covered_symbols.add(symbol.name)

            file_to_symbols[file_path] = covered_symbols

        return file_to_symbols

    def get_symbols_for_test(self, test_file: str) -> set[str]:
        """Run pytest on a single test file and return covered symbol names."""
        test_path = Path(test_file)
        if not test_path.exists():
            logger.warning(f"Test file not found: {test_file}")
            return set()

        with tempfile.TemporaryDirectory() as tmpdir:
            cov_file = Path(tmpdir) / ".coverage"

            cmd = [
                "python",
                "-m",
                "pytest",
                str(test_path),
                "--cov=backend/src",
                "--cov-report=",
                "--cov-config=.coveragerc",
                f"--cov-file={cov_file}",
                "-q",
            ]

            try:
                subprocess.run(
                    cmd,
                    cwd=Path.cwd(),
                    capture_output=True,
                    text=True,
                    timeout=300,
                )
            except subprocess.TimeoutExpired:
                logger.warning(f"Test timed out: {test_file}")
                return set()
            except Exception as e:
                logger.warning(f"Failed to run test {test_file}: {e}")
                return set()

            if not cov_file.exists():
                return set()

            mapper = CoverageSymbolMapper(cov_file)
            covered = mapper.load_coverage_data()
            symbols = mapper.map_coverage_to_symbols(covered)

            all_symbols = set()
            for symbol_set in symbols.values():
                all_symbols.update(symbol_set)

            return all_symbols

    def build_symbol_to_test_map(
        self, test_directory: Path, force_rebuild: bool = False
    ) -> dict[str, set[Path]]:
        """Build map: symbol_name → set of test files that cover it.

        Uses cached results unless force_rebuild=True or cache is stale.
        """
        test_directory = Path(test_directory)

        if not force_rebuild and self._symbol_test_map_is_valid(test_directory):
            return self._reconstruct_symbol_to_test_map()

        test_files = sorted(test_directory.rglob("test_*.py"))
        if not test_files:
            logger.warning(f"No test files found in {test_directory}")
            return {}

        symbol_to_tests: dict[str, set[Path]] = {}

        for test_file in test_files:
            covered_symbols = self.get_symbols_for_test(str(test_file))

            for symbol_name in covered_symbols:
                if symbol_name not in symbol_to_tests:
                    symbol_to_tests[symbol_name] = set()
                symbol_to_tests[symbol_name].add(test_file)

        self._save_symbol_test_map_from_result(symbol_to_tests)
        return symbol_to_tests

    def _symbol_test_map_is_valid(self, test_directory: Path) -> bool:
        """Check if cached symbol-test map is up to date."""
        if not self.symbol_test_map_path.exists():
            return False

        try:
            cached = json.loads(self.symbol_test_map_path.read_text())
            if not cached:
                return False

            # Check mtime of all test files referenced
            for _symbol_name, test_files in cached.items():
                for test_file in test_files:
                    tf = Path(test_file)
                    if not tf.exists():
                        return False
                    # If any referenced test file is newer than cache, rebuild
                    if tf.stat().st_mtime > self.symbol_test_map_path.stat().st_mtime:
                        return False

            return True
        except Exception:
            return False

    def _reconstruct_symbol_to_test_map(self) -> dict[str, set[Path]]:
        """Convert cached flat map back to sets."""
        result = {}
        for symbol_name, test_files in self.symbol_test_map.items():
            result[symbol_name] = {Path(tf) for tf in test_files}
        return result

    def _save_symbol_test_map_from_result(self, symbol_to_tests: dict[str, set[Path]]):
        """Save symbol-to-test map as JSON-serializable dict."""
        flat_map = {}
        for symbol_name, test_files in symbol_to_tests.items():
            flat_map[symbol_name] = sorted(str(tf) for tf in test_files)
        self.symbol_test_map = flat_map
        self._save_symbol_test_map()

    def get_coverage_for_symbol(self, symbol_name: str) -> dict[str, set[str]]:
        """Get which test files cover a specific symbol."""
        return self._reconstruct_symbol_to_test_map().get(symbol_name, set())

    def list_all_covered_symbols(self, covered_lines: dict[Path, set[int]]) -> set[str]:
        """Return flat set of all symbol names covered by given coverage data."""
        file_to_symbols = self.map_coverage_to_symbols(covered_lines)
        all_symbols = set()
        for symbol_set in file_to_symbols.values():
            all_symbols.update(symbol_set)
        return all_symbols


if __name__ == "__main__":

    extractor = SymbolExtractor()
    test_file = Path("backend/src/engines/loan_engine/emi.py")

    if test_file.exists():
        symbols = extractor.extract_from_file(test_file)
        print(f"Extracted {len(symbols)} symbols from {test_file.name}")
        for s in symbols[:5]:
            print(f"  {s.kind} {s.name} (lines {s.start_line}-{s.end_line})")
        if len(symbols) > 0:
            print("Symbol extraction working")
    else:
        print(f"Test file not found: {test_file}")
