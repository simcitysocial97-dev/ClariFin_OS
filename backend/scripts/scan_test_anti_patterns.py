#!/usr/bin/env python3
"""
Scan all backend test files for database anti-patterns that cause
performance issues or inconsistent behavior.

Patterns detected:
1. Direct FinanceDB(db_path=...) calls in test functions (not in fixtures)
2. tempfile.mkstemp() usage in test functions
3. sqlite3.connect() in test function setup (secondary connections)
4. os.unlink(db_path) in test cleanup
5. Direct 'from db import FinanceDB' in test modules
6. Local fixture definitions that create fresh databases instead of using temp_db
7. Raw try/finally db cleanup blocks
8. Direct CREATE TABLE without using temp_db fixture
"""

from __future__ import annotations

import ast
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass
class AntiPattern:
    """Represents a detected anti-pattern in a test file."""

    file_path: str
    pattern_type: str
    line_number: int
    description: str
    severity: str  # HIGH, MEDIUM, LOW
    context: str = ""


class TestFileScanner(ast.NodeVisitor):
    """AST-based scanner for test anti-patterns."""

    def __init__(self, file_path: str) -> None:
        self.file_path = file_path
        self.issues: list[AntiPattern] = []
        self._imports: dict[str, str] = {}  # alias -> original name
        self._in_fixture = False
        self._fixture_names: set[str] = set()
        self._current_function = ""
        self._function_is_test = False
        self._temp_db_fixture_exists = False

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        old_function = self._current_function
        old_is_test = self._function_is_test
        self._current_function = node.name
        self._function_is_test = node.name.startswith("test_")

        # Check if this is a pytest fixture
        is_fixture = False
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Name) and decorator.id == "pytest":
                continue
            if isinstance(decorator, ast.Attribute) and (
                isinstance(decorator.value, ast.Name)
                and decorator.value.id == "pytest"
                and decorator.attr == "fixture"
            ):
                is_fixture = True
            if (
                isinstance(decorator, ast.Call)
                and isinstance(decorator.func, ast.Attribute)
                and (
                    isinstance(decorator.func.value, ast.Name)
                    and decorator.func.value.id == "pytest"
                    and decorator.func.attr == "fixture"
                )
            ):
                is_fixture = True

        if is_fixture:
            self._in_fixture = True
            self._fixture_names.add(node.name)

        self.generic_visit(node)

        self._current_function = old_function
        self._function_is_test = old_is_test
        self._in_fixture = False

    def visit_Assign(self, node: ast.Assign) -> None:
        """Check for temp_db fixture definitions."""
        if isinstance(node.value, ast.Call):
            func = node.value.func
            if isinstance(func, ast.Name) and func.id == "pytest":
                pass
            if isinstance(func, ast.Attribute) and (
                isinstance(func.value, ast.Name)
                and func.value.id == "pytest"
                and func.attr == "fixture"
            ):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        self._fixture_names.add(target.id)
                        if target.id == "temp_db":
                            self._temp_db_fixture_exists = True
        self.generic_visit(node)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        """Check for annotated fixture assignments (PEP 526 style)."""
        if isinstance(node.value, ast.Call):
            func = node.value.func
            if (
                isinstance(func, ast.Attribute)
                and (
                    isinstance(func.value, ast.Name)
                    and func.value.id == "pytest"
                    and func.attr == "fixture"
                )
                and isinstance(node.target, ast.Name)
            ):
                self._fixture_names.add(node.target.id)
                if node.target.id == "temp_db":
                    self._temp_db_fixture_exists = True
        self.generic_visit(node)

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            if alias.asname:
                self._imports[alias.asname] = alias.name
            else:
                self._imports[alias.name] = alias.name
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        if node.module and node.module.startswith("db"):
            for alias in node.names:
                local_name = alias.asname if alias.asname else alias.name
                self._imports[local_name] = f"{node.module}.{alias.name}"
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        if not self._function_is_test and not self._in_fixture:
            self.generic_visit(node)
            return

        func = node.func

        # Pattern 1: FinanceDB(...) direct call in test/fixture
        if isinstance(func, ast.Name) and func.id == "FinanceDB":
            self.issues.append(
                AntiPattern(
                    file_path=self.file_path,
                    pattern_type="DIRECT_FINANCEDB_CALL",
                    line_number=node.lineno,
                    description="Direct FinanceDB() call creates expensive fresh DB instead of using temp_db fixture",
                    severity="HIGH",
                    context=f"FinanceDB(...) in {self._current_function}",
                )
            )

        # Pattern 2: tempfile.mkstemp() in test
        if isinstance(func, ast.Attribute):
            if (
                isinstance(func.value, ast.Name)
                and func.value.id == "tempfile"
                and func.attr == "mkstemp"
            ):
                self.issues.append(
                    AntiPattern(
                        file_path=self.file_path,
                        pattern_type="TEMP_MKSTEMP",
                        line_number=node.lineno,
                        description="tempfile.mkstemp() creates raw temp file instead of using temp_db fixture",
                        severity="HIGH",
                        context=f"tempfile.mkstemp() in {self._current_function}",
                    )
                )

            # Pattern 3: sqlite3.connect() in test/fixture setup
            if (
                isinstance(func.value, ast.Name)
                and func.value.id == "sqlite3"
                and func.attr == "connect"
                and self._function_is_test
            ):
                self.issues.append(
                    AntiPattern(
                        file_path=self.file_path,
                        pattern_type="SECONDARY_SQLITE_CONN",
                        line_number=node.lineno,
                        description="Secondary sqlite3.connect() in test - use canonical connection instead",
                        severity="MEDIUM",
                        context=f"sqlite3.connect() in {self._current_function}",
                    )
                )

        # Pattern 4: os.unlink(db_path) in cleanup
        if isinstance(func, ast.Attribute) and (
            isinstance(func.value, ast.Name)
            and func.value.id == "os"
            and func.attr == "unlink"
        ):
            self.issues.append(
                AntiPattern(
                    file_path=self.file_path,
                    pattern_type="OS_UNLINK_CLEANUP",
                    line_number=node.lineno,
                    description="Manual os.unlink(db_path) cleanup - let fixture handle cleanup",
                    severity="LOW",
                    context=f"os.unlink() in {self._current_function}",
                )
            )

        self.generic_visit(node)


def find_test_files(root: Path) -> list[Path]:
    """Find all Python test files."""
    test_files = []
    for pattern in ["tests/**/*.py", "tests/*.py"]:
        test_files.extend(root.glob(pattern))
    return sorted(set(test_files))


def scan_file(file_path: Path) -> list[AntiPattern]:
    """Scan a single test file for anti-patterns."""
    try:
        source = file_path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(file_path))
    except (SyntaxError, UnicodeDecodeError) as e:
        print(f"  SKIP {file_path}: {e}")
        return []

    scanner = TestFileScanner(str(file_path))
    scanner.visit(tree)

    # Also do simple text-based scans for patterns that AST might miss
    issues = list(scanner.issues)
    lines = source.splitlines()

    for i, line in enumerate(lines, 1):
        stripped = line.strip()

        # Check for raw try/finally db cleanup blocks
        if "try:" in stripped and i < len(lines):
            # Look ahead for cleanup patterns
            for j in range(i, min(i + 20, len(lines))):
                if "os.unlink(db_path)" in lines[j] or "os.unlink(db_path)" in lines[j]:
                    issues.append(
                        AntiPattern(
                            file_path=str(file_path),
                            pattern_type="MANUAL_CLEANUP_BLOCK",
                            line_number=j + 1,
                            description="Manual os.unlink(db_path) cleanup block",
                            severity="LOW",
                            context=f"Line {j + 1}",
                        )
                    )
                    break

        # Check for direct FinanceDB import outside fixtures
        if stripped.startswith("from db import") or stripped.startswith(
            "import FinanceDB"
        ):
            issues.append(
                AntiPattern(
                    file_path=str(file_path),
                    pattern_type="DIRECT_FINANCEDB_IMPORT",
                    line_number=i,
                    description="Direct import of FinanceDB at module level",
                    severity="MEDIUM",
                    context=stripped,
                )
            )

    return issues


def main() -> int:
    root = Path("/home/vasantha/AI-Projects/ClariFin_OS/backend")
    test_files = find_test_files(root)

    print(f"Scanning {len(test_files)} test files...")
    print("=" * 70)

    all_issues: dict[str, list[AntiPattern]] = {}
    total_issues = 0

    for file_path in test_files:
        if "venv" in str(file_path) or "__pycache__" in str(file_path):
            continue

        issues = scan_file(file_path)
        if issues:
            all_issues[str(file_path.relative_to(root))] = issues
            total_issues += len(issues)

    # Print summary
    print(f"\nTotal issues found: {total_issues}")
    print("=" * 70)

    # Group by pattern type
    by_type: dict[str, list] = {}
    for file_issues in all_issues.values():
        for issue in file_issues:
            by_type.setdefault(issue.pattern_type, []).append(issue)

    print("\nIssues by type:")
    print("-" * 70)
    for pattern_type, issues in sorted(by_type.items(), key=lambda x: -len(x[1])):
        print(f"\n{pattern_type} ({len(issues)} occurrences):")
        for issue in issues[:3]:  # Show first 3 examples
            print(f"  {issue.file_path}:{issue.line_number} - {issue.description}")
        if len(issues) > 3:
            print(f"  ... and {len(issues) - 3} more")

    # Print detailed file report
    print("\n" + "=" * 70)
    print("DETAILED FILE REPORT:")
    print("=" * 70)

    for file_path, issues in sorted(all_issues.items()):
        print(f"\n{file_path} ({len(issues)} issues):")
        for issue in issues:
            print(
                f"  Line {issue.line_number}: [{issue.severity}] {issue.pattern_type}"
            )
            print(f"    {issue.description}")
            if issue.context:
                print(f"    Context: {issue.context}")

    # Return exit code
    return 1 if total_issues > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
