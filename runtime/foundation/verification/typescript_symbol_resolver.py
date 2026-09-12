"""TypeScript/TSX Symbol Resolver — Python wrapper for the ts-morph based extractor.

Extends the existing symbol-resolution architecture so the framework can reason
about TypeScript/TSX. Uses the existing project dependency on ts-morph via a
Node.js subprocess. Integrates with the existing SymbolExtractor caching model.
"""

from __future__ import annotations

import json
import logging
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Set

from runtime.foundation.verification.symbol_resolver import Symbol

logger = logging.getLogger(__name__)


class TypeScriptSymbol:
    """Represents a TypeScript/TSX symbol."""

    def __init__(
        self,
        name: str,
        kind: str,
        file: Path,
        start_line: int,
        end_line: int,
        parent_class: Optional[str] = None,
        exported: bool = False,
        is_default_export: bool = False,
        is_react_component: bool = False,
        is_hook: bool = False,
        is_api_client_call: bool = False,
        imported_symbols: Optional[List[str]] = None,
        exported_symbols: Optional[List[str]] = None,
    ):
        self.name = name
        self.kind = kind
        self.file = file
        self.start_line = start_line
        self.end_line = end_line
        self.parent_class = parent_class
        self.exported = exported
        self.is_default_export = is_default_export
        self.is_react_component = is_react_component
        self.is_hook = is_hook
        self.is_api_client_call = is_api_client_call
        self.imported_symbols = imported_symbols or []
        self.exported_symbols = exported_symbols or []

    def __repr__(self):
        return f"TypeScriptSymbol({self.kind} '{self.name}', {self.file.name}:{self.start_line}-{self.end_line})"

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "kind": self.kind,
            "file": str(self.file),
            "start_line": self.start_line,
            "end_line": self.end_line,
            "parent_class": self.parent_class,
            "exported": self.exported,
            "is_default_export": self.is_default_export,
            "is_react_component": self.is_react_component,
            "is_hook": self.is_hook,
            "is_api_client_call": self.is_api_client_call,
            "imported_symbols": self.imported_symbols,
            "exported_symbols": self.exported_symbols,
            "symbol_id": self.symbol_id,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "TypeScriptSymbol":
        return cls(
            name=data["name"],
            kind=data["kind"],
            file=Path(data["file"]),
            start_line=data.get("start_line") or data.get("startLine") or 0,
            end_line=data.get("end_line") or data.get("endLine") or 0,
            parent_class=data.get("parent_class") or data.get("parentClass"),
            exported=data.get("exported", False),
            is_default_export=data.get("is_default_export") or data.get("isDefaultExport") or False,
            is_react_component=data.get("is_react_component") or data.get("isReactComponent") or False,
            is_hook=data.get("is_hook") or data.get("isHook") or False,
            is_api_client_call=data.get("is_api_client_call") or data.get("isApiClientCall") or False,
            imported_symbols=data.get("imported_symbols") or data.get("importedSymbols") or [],
            exported_symbols=data.get("exported_symbols") or data.get("exportedSymbols") or [],
        )

    def to_symbol(self) -> Symbol:
        """Convert to base Symbol for compatibility with existing infrastructure."""
        return Symbol(
            name=self.name,
            kind=self.kind,
            file=self.file,
            start_line=self.start_line,
            end_line=self.end_line,
            parent_class=self.parent_class,
        )

    @property
    def symbol_id(self) -> str:
        """Deterministic frontend symbol identity.
        
        Format: frontend:<relative-path-from-repo-root>:<symbol-name>
        Example: frontend:frontend/lib/hooks/use-accounts.ts:useManagedAccounts
        """
        repo_root = Path.cwd()
        try:
            rel_path = self.file.relative_to(repo_root)
        except ValueError:
            rel_path = self.file
        return f"frontend:{rel_path}:{self.name}"


class TypeScriptSymbolExtractor:
    """Extract symbols from TypeScript/TSX source files via ts-morph."""

    def __init__(self, cache_path: Path = None, frontend_root: Path = None):
        self.frontend_root = frontend_root or Path("frontend")
        self.cache_path = cache_path or Path("runtime/generated/typescript-symbol-cache/symbol-cache.json")
        self.cache = self._load_cache()
        self._ts_resolver_script = Path("runtime/foundation/verification/typescript_symbol_resolver.ts")

    def _load_cache(self) -> dict:
        if self.cache_path.exists():
            try:
                return json.loads(self.cache_path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError) as e:
                logger.warning(f"Failed to load TypeScript symbol cache: {e}")
        return {}

    def _save_cache(self):
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        self.cache_path.write_text(json.dumps(self.cache, indent=2))

    def _run_ts_resolver(self, target_path: Path) -> dict:
        """Run the TypeScript symbol resolver script via npx tsx."""
        repo_root = Path.cwd()
        target_abs = target_path if target_path.is_absolute() else repo_root / target_path
        frontend_root = repo_root / "frontend"
        ts_resolver_script_abs = repo_root / self._ts_resolver_script

        if not ts_resolver_script_abs.exists():
            raise FileNotFoundError(f"TypeScript resolver script not found: {ts_resolver_script_abs}")

        target_rel_to_repo = target_abs.relative_to(repo_root)

        cmd = [
            "npx", "tsx",
            str(ts_resolver_script_abs),
            str(target_rel_to_repo),
            "--cache-dir", str(self.cache_path.parent),
        ]

        env = os.environ.copy()
        env["NODE_PATH"] = str(frontend_root / "node_modules")

        try:
            result = subprocess.run(
                cmd,
                cwd=str(frontend_root),
                capture_output=True,
                text=True,
                timeout=300,
                env=env,
            )
        except subprocess.TimeoutExpired:
            logger.error(f"TypeScript resolver timed out for {target_path}")
            return {"files": [], "totalFiles": 0, "totalSymbols": 0}
        except Exception as e:
            logger.error(f"Failed to run TypeScript resolver: {e}")
            return {"files": [], "totalFiles": 0, "totalSymbols": 0}

        if result.returncode != 0:
            logger.error(f"TypeScript resolver failed: {result.stderr}")
            return {"files": [], "totalFiles": 0, "totalSymbols": 0}

        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse TypeScript resolver output: {e}")
            return {"files": [], "totalFiles": 0, "totalSymbols": 0}

    def extract_from_file(self, file_path: Path) -> List[TypeScriptSymbol]:
        """Extract all symbols from a single TypeScript/TSX file."""
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
                return [TypeScriptSymbol.from_dict(s) for s in cached["symbols"]]

        result = self._run_ts_resolver(file_path)

        symbols = []
        for file_data in result.get("files", []):
            for sym_data in file_data.get("symbols", []):
                symbols.append(TypeScriptSymbol.from_dict(sym_data))

        self.cache[file_key] = {
            "mtime": file_mtime,
            "symbols": [s.to_dict() for s in symbols],
        }
        self._save_cache()
        return symbols

    def extract_from_directory(self, directory: Path) -> Dict[Path, List[TypeScriptSymbol]]:
        """Extract symbols from all TypeScript/TSX files in a directory recursively."""
        result = {}
        directory = Path(directory)
        repo_root = Path.cwd()
        
        result_data = self._run_ts_resolver(directory)

        for file_data in result_data.get("files", []):
            file_rel = Path(file_data["file"])
            file_abs = repo_root / file_rel
            symbols = [TypeScriptSymbol.from_dict(s) for s in file_data.get("symbols", [])]
            result[file_abs] = symbols

            file_key = str(file_abs.resolve())
            try:
                mtime = file_abs.stat().st_mtime
                self.cache[file_key] = {
                    "mtime": mtime,
                    "symbols": [s.to_dict() for s in symbols],
                }
            except OSError:
                pass

        self._save_cache()
        return result

    def get_symbol_at_line(self, file_path: Path, line_number: int) -> Optional[TypeScriptSymbol]:
        """Find which symbol contains the given line number."""
        symbols = self.extract_from_file(file_path)
        for symbol in symbols:
            if symbol.start_line <= line_number <= symbol.end_line:
                return symbol
        return None

    def get_react_components(self, file_path: Path) -> List[TypeScriptSymbol]:
        """Get all React components in a file."""
        symbols = self.extract_from_file(file_path)
        return [s for s in symbols if s.is_react_component]

    def get_hooks(self, file_path: Path) -> List[TypeScriptSymbol]:
        """Get all hooks in a file."""
        symbols = self.extract_from_file(file_path)
        return [s for s in symbols if s.is_hook]

    def get_api_client_calls(self, file_path: Path) -> List[TypeScriptSymbol]:
        """Get all API client calls in a file."""
        symbols = self.extract_from_file(file_path)
        return [s for s in symbols if s.is_api_client_call]

    def get_exported_symbols(self, file_path: Path) -> List[TypeScriptSymbol]:
        """Get all exported symbols in a file."""
        symbols = self.extract_from_file(file_path)
        return [s for s in symbols if s.exported]

    def invalidate_cache(self, file_path: Path = None):
        """Invalidate cache entry for a specific file or clear entire cache."""
        if file_path:
            file_key = str(Path(file_path).resolve())
            self.cache.pop(file_key, None)
            self._save_cache()
        else:
            self.cache.clear()
            self._save_cache()

    def find_symbol_by_name(self, name: str, directory: Path = None) -> List[TypeScriptSymbol]:
        """Find all symbols with a given name in a directory."""
        search_dir = directory or self.frontend_root
        all_symbols = []
        
        result_data = self._run_ts_resolver(search_dir)
        
        for file_data in result_data.get("files", []):
            for sym_data in file_data.get("symbols", []):
                if sym_data["name"] == name:
                    all_symbols.append(TypeScriptSymbol.from_dict(sym_data))
        
        return all_symbols


class TypeScriptCoverageSymbolMapper:
    """Map test coverage data to TypeScript symbols (function/component/hook)."""

    def __init__(self, coverage_file: Path = Path("frontend/coverage/coverage-final.json")):
        self.coverage_file = coverage_file
        self.extractor = TypeScriptSymbolExtractor()
        self.symbol_test_map_path = Path("runtime/generated/typescript-symbol-test-map.json")
        self.symbol_test_map = self._load_symbol_test_map()

    def _load_symbol_test_map(self) -> Dict[str, List[str]]:
        if self.symbol_test_map_path.exists():
            try:
                return json.loads(self.symbol_test_map_path.read_text())
            except (json.JSONDecodeError, OSError):
                logger.warning("Failed to load TypeScript symbol-test map cache")
        return {}

    def _save_symbol_test_map(self):
        self.symbol_test_map_path.parent.mkdir(parents=True, exist_ok=True)
        self.symbol_test_map_path.write_text(json.dumps(self.symbol_test_map, indent=2))

    def load_coverage_data(self) -> Dict[Path, Set[int]]:
        """Load Vitest coverage data: file → set of covered line numbers."""
        if not self.coverage_file.exists():
            return {}

        try:
            data = json.loads(self.coverage_file.read_text())
        except (json.JSONDecodeError, OSError) as e:
            logger.warning(f"Failed to load coverage data: {e}")
            return {}

        covered_lines = {}
        for file_path_str, file_data in data.items():
            file_path = Path(file_path_str)
            if "frontend" not in file_path_str:
                continue
            
            lines = set()
            if "s" in file_data:
                for line_str, count in file_data["s"].items():
                    if count > 0:
                        lines.add(int(line_str))
            
            if lines:
                covered_lines[file_path] = lines

        return covered_lines

    def map_coverage_to_symbols(
        self, covered_lines: Dict[Path, Set[int]]
    ) -> Dict[Path, Set[str]]:
        """Map covered lines to symbol names per source file."""
        file_to_symbols = {}

        for file_path, lines in covered_lines.items():
            symbols = self.extractor.extract_from_file(file_path)
            covered_symbols = set()

            for line in lines:
                symbol = self.extractor.get_symbol_at_line(file_path, line)
                if symbol:
                    covered_symbols.add(symbol.name)

            file_to_symbols[file_path] = covered_symbols

        return file_to_symbols

    def get_symbols_for_test(self, test_file: str) -> Set[str]:
        """Run vitest on a single test file and return covered symbol names."""
        test_path = Path(test_file)
        if not test_path.exists():
            logger.warning(f"Test file not found: {test_file}")
            return set()

        with tempfile.TemporaryDirectory() as tmpdir:
            cov_file = Path(tmpdir) / "coverage-final.json"

            cmd = [
                "npx", "vitest", "run",
                str(test_path),
                "--coverage",
                "--coverage.reporter=json",
                f"--coverage.reportsDirectory={tmpdir}",
            ]

            try:
                result = subprocess.run(
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

            mapper = TypeScriptCoverageSymbolMapper(cov_file)
            covered = mapper.load_coverage_data()
            symbols = mapper.map_coverage_to_symbols(covered)

            all_symbols = set()
            for symbol_set in symbols.values():
                all_symbols.update(symbol_set)

            return all_symbols

    def build_symbol_to_test_map(
        self, test_directory: Path, force_rebuild: bool = False
    ) -> Dict[str, Set[Path]]:
        """Build map: symbol_name → set of test files that cover it."""
        test_directory = Path(test_directory)

        if not force_rebuild and self._symbol_test_map_is_valid(test_directory):
            return self._reconstruct_symbol_to_test_map()

        test_files = sorted(test_directory.rglob("*.test.ts")) + sorted(test_directory.rglob("*.test.tsx"))
        if not test_files:
            logger.warning(f"No test files found in {test_directory}")
            return {}

        symbol_to_tests: Dict[str, Set[Path]] = {}

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

            for symbol_name, test_files in cached.items():
                for test_file in test_files:
                    tf = Path(test_file)
                    if not tf.exists():
                        return False
                    if tf.stat().st_mtime > self.symbol_test_map_path.stat().st_mtime:
                        return False

            return True
        except Exception:
            return False

    def _reconstruct_symbol_to_test_map(self) -> Dict[str, Set[Path]]:
        """Convert cached flat map back to sets."""
        result = {}
        for symbol_name, test_files in self.symbol_test_map.items():
            result[symbol_name] = {Path(tf) for tf in test_files}
        return result

    def _save_symbol_test_map_from_result(
        self, symbol_to_tests: Dict[str, Set[Path]]
    ):
        """Save symbol-to-test map as JSON-serializable dict."""
        flat_map = {}
        for symbol_name, test_files in symbol_to_tests.items():
            flat_map[symbol_name] = sorted(str(tf) for tf in test_files)
        self.symbol_test_map = flat_map
        self._save_symbol_test_map()

    def get_coverage_for_symbol(
        self, symbol_name: str
    ) -> Dict[str, Set[str]]:
        """Get which test files cover a specific symbol."""
        return self._reconstruct_symbol_to_test_map().get(symbol_name, set())

    def list_all_covered_symbols(self, covered_lines: Dict[Path, Set[int]]) -> Set[str]:
        """Return flat set of all symbol names covered by given coverage data."""
        file_to_symbols = self.map_coverage_to_symbols(covered_lines)
        all_symbols = set()
        for symbol_set in file_to_symbols.values():
            all_symbols.update(symbol_set)
        return all_symbols


if __name__ == "__main__":
    import sys

    extractor = TypeScriptSymbolExtractor()
    
    if len(sys.argv) > 1:
        test_file = Path(sys.argv[1])
    else:
        test_file = Path("frontend/lib/hooks/use-accounts.ts")

    if test_file.exists():
        symbols = extractor.extract_from_file(test_file)
        print(f"Extracted {len(symbols)} symbols from {test_file.name}")
        for s in symbols[:10]:
            tags = []
            if s.exported:
                tags.append("exported")
            if s.is_react_component:
                tags.append("react-component")
            if s.is_hook:
                tags.append("hook")
            if s.is_api_client_call:
                tags.append("api-call")
            tag_str = f" [{', '.join(tags)}]" if tags else ""
            print(f"  {s.kind} {s.name} (lines {s.start_line}-{s.end_line}){tag_str}")
        print("TypeScript symbol extraction working")
    else:
        print(f"Test file not found: {test_file}")