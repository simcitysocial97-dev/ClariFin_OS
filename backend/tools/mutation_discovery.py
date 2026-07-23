#!/usr/bin/env python3
"""Mutation Discovery Engine - Analyzes engine functions for mutation testing readiness.

Uses AST analysis to determine purity, identifies mutation candidates, and classifies
functions by business criticality. No external mutation testing dependencies required.

Output files:
- mutation-map.json: Discovered functions with purity analysis
- mutation-readiness.json: Per-engine readiness scores
- mutation-readiness.md: Human-readable readiness report
- mutation-registry.json: Full registry with test coverage mapping
- mutation-gaps.md: Actionable report of validation gaps
"""

from __future__ import annotations

import ast
import json
import re
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

# Project root from this file's location (backend/tools → backend → project_root)
PROJECT_ROOT = Path(__file__).parent.parent.parent
BACKEND_DIR = PROJECT_ROOT / "backend"
GENERATED_DIR = PROJECT_ROOT / "memory-bank" / "generated"

# Purity classification confidence levels
CONFIDENCE_HIGH = "HIGH"
CONFIDENCE_MEDIUM = "MEDIUM"
CONFIDENCE_LOW = "LOW"

# Mutation readiness statuses
STATUS_READY = "Ready"
STATUS_PARTIAL = "Partial"
STATUS_BLOCKED = "Blocked"

# Killability estimates
KILLABILITY_HIGH = "HIGH"
KILLABILITY_MEDIUM = "MEDIUM"
KILLABILITY_LOW = "LOW"
KILLABILITY_UNKNOWN = "UNKNOWN"


@dataclass
class FunctionAnalysis:
    """Analysis result for a single function."""
    module: str
    function: str
    purity: Literal["PURE", "IMPURE", "UNKNOWN"] = "UNKNOWN"
    confidence: str = CONFIDENCE_LOW
    mutation_types: list[str] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)
    criticality: str = "medium"
    risk: str = "low"


@dataclass
class EngineReadiness:
    """Readiness analysis for an engine module."""
    module_path: str
    pure_functions: int = 0
    impure_functions: int = 0
    unknown_functions: int = 0
    readiness: str = STATUS_BLOCKED
    killability_estimate: str = KILLABILITY_UNKNOWN


# AST-based purity blockers - these indicate impure functions
PURITY_BLOCKERS = {
    # Database access
    "sqlite3", "FinanceDB", "get_db", "session", "Session",
    # Filesystem
    "open", "pathlib", "os.", "os.path", "pickle", "shutil", "tempfile",
    # Network
    "requests", "httpx", "urllib", "http.client", "socket",
    # Subprocess
    "subprocess", "multiprocessing",
    # Randomness/Non-determinism
    "random", "uuid", "secrets", "datetime.now", "time.time",
    # Environment
    "os.environ", "os.getenv", "os.putenv", "sys.argv",
    # Threading
    "threading", "asyncio.create_task", "concurrent.futures",
}


def analyze_function_ast(source_path: Path, function_name: str) -> FunctionAnalysis:
    """Analyze a function using AST to determine purity and mutation types.

    Args:
        source_path: Path to the source file
        function_name: Name of the function to analyze

    Returns:
        FunctionAnalysis with purity status, blockers, and mutation types
    """
    module_path = str(source_path.relative_to(BACKEND_DIR))

    with open(source_path) as f:
        source = f.read()

    try:
        tree = ast.parse(source)
    except SyntaxError:
        return FunctionAnalysis(
            module=module_path,
            function=function_name,
            purity="UNKNOWN",
            confidence=CONFIDENCE_LOW,
        )

    # Find the function definition
    func_node = None
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == function_name:
            func_node = node
            break

    if not func_node:
        return FunctionAnalysis(
            module=module_path,
            function=function_name,
            purity="UNKNOWN",
            confidence=CONFIDENCE_LOW,
        )

    blockers: list[str] = []
    mutation_types: list[str] = []

    # Check for purity blockers in the function
    func_source = ast.get_source_segment(source, func_node) or ""

    for blocker in PURITY_BLOCKERS:
        # Direct attribute access check
        if blocker in func_source:
            blockers.append(blocker)

    # Check imports in the module
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if any(b in alias.name for b in ["sqlite3", "requests", "httpx", "random", "pickle"]):
                    blockers.append(f"import:{alias.name}")
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                if any(b in node.module for b in ["sqlite3", "requests", "httpx", "random", "pickle", "finance_db"]):
                    blockers.append(f"import:{node.module}")

    # Determine purity
    if blockers:
        purity = "IMPURE"
        confidence = CONFIDENCE_HIGH if blockers else CONFIDENCE_LOW
    else:
        # Check for monetary operations that suggest business logic
        has_arithmetic = bool(re.search(r'\+|-|\*|/', func_source))
        has_comparison = bool(re.search(r'[<>]|=|!=|<=|>=', func_source))

        if has_arithmetic or has_comparison:
            purity = "PURE"
            confidence = CONFIDENCE_HIGH
        else:
            purity = "PURE"
            confidence = CONFIDENCE_MEDIUM

    # Identify mutation types based on AST analysis
    mutation_types = identify_mutation_types(func_source)

    return FunctionAnalysis(
        module=module_path,
        function=function_name,
        purity=purity,
        confidence=confidence,
        mutation_types=mutation_types,
        blockers=blockers,
    )


def identify_mutation_types(source: str) -> list[str]:
    """Identify potential mutation types applicable to this function.

    Categories:
    - Arithmetic: +, -, *, / operations
    - Comparison: <, >, ==, !=, <=, >=
    - Boolean: and, or, not
    - Constant: numeric literals
    - Boundary: off-by-one, range checks
    """
    types: list[str] = []

    # Arithmetic operators
    if re.search(r'\+|-|\*|/', source):
        types.append("Arithmetic")

    # Comparison operators
    if re.search(r'==|!=|<=|>=|<|>', source):
        types.append("Comparison")

    # Boolean operators
    if re.search(r'\band\b|\bor\b|\bnot\b', source):
        types.append("Boolean")

    # Constants (numeric literals)
    if re.search(r'\d+\.?\d*', source):
        types.append("Constant replacement")

    # Boundary conditions
    if re.search(r'range|len\(|for .+ in|while', source):
        types.append("Boundary conditions")

    # Off-by-one patterns
    if re.search(r'\+ 1|- 1|[-+]=[+-]?1', source):
        types.append("Off-by-one")

    # Loop patterns
    if re.search(r'\bfor\b|\bwhile\b', source):
        types.append("Loop termination")

    # Sign inversion potential
    if re.search(r'-1|negate|inverse|invert', source, re.I):
        types.append("Sign inversion")

    return types


def get_engine_functions(engine_path: Path) -> list[str]:
    """Extract top-level function names from an engine file.

    Args:
        engine_path: Path to the engine Python file

    Returns:
        List of function names defined in the file
    """
    functions: list[str] = []

    try:
        with open(engine_path) as f:
            tree = ast.parse(f.read())
    except SyntaxError:
        return functions

    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.FunctionDef) and not node.name.startswith("_"):
            functions.append(node.name)

    return functions


def discover_engine_files() -> list[Path]:
    """Find all engine Python files in the codebase.

    Returns:
        List of paths to engine files
    """
    engine_files: list[Path] = []
    engines_dir = BACKEND_DIR / "src" / "engines"

    # Top-level engine files
    if engines_dir.exists():
        for f in engines_dir.glob("*.py"):
            if f.name != "__init__.py":
                engine_files.append(f)

        # Subdirectory engines
        for subdir in engines_dir.iterdir():
            if subdir.is_dir():
                for f in subdir.glob("*.py"):
                    if f.name != "__init__.py":
                        engine_files.append(f)

    return engine_files


def load_capability_registry() -> dict[str, Any]:
    """Load the capability registry for criticality mapping."""
    import yaml
    registry_path = GENERATED_DIR / "capability-registry.yaml"
    if registry_path.exists():
        with open(registry_path) as f:
            return yaml.safe_load(f) or {"capabilities": []}
    return {"capabilities": []}


def get_capability_for_engine(engine_path: Path, registry: dict[str, Any]) -> tuple[str, str, str]:
    """Get capability info for an engine file.

    Returns:
        Tuple of (capability_id, criticality, risk)
    """
    relative_path = f"src/engines/{engine_path.relative_to(BACKEND_DIR / 'src' / 'engines')}"
    relative_path = str(relative_path).replace("//", "/")

    for cap in registry.get("capabilities", []):
        for engine in cap.get("engines", []):
            if engine in relative_path:
                return cap.get("id", "unknown"), cap.get("criticality", "medium"), cap.get("risk", "low")

    return "unknown", "medium", "low"


def compute_killability(functions: list[FunctionAnalysis], cap_info: dict[str, Any]) -> str:
    """Estimate mutation killability based on function coverage.

    Score based on:
    - HIGH: All functions have property tests + golden tests
    - MEDIUM: Mix of pure/impure with some coverage
    - LOW: Many impure functions or no coverage
    """
    if not functions:
        return KILLABILITY_UNKNOWN

    pure_count = sum(1 for f in functions if f.purity == "PURE")
    impure_count = sum(1 for f in functions if f.purity == "IMPURE")

    # Check if there are property or golden tests
    has_property = len(cap_info.get("property_tests", [])) > 0
    has_golden = len(cap_info.get("golden_datasets", [])) > 0

    # High killability if mostly pure functions with good test coverage
    if impure_count == 0 and pure_count > 0:
        has_types = any(len(f.mutation_types) > 0 for f in functions if f.purity == "PURE")
        if has_types and (has_property or has_golden):
            return KILLABILITY_HIGH
        return KILLABILITY_MEDIUM

    # Low killability if many impure functions
    if impure_count > pure_count:
        return KILLABILITY_LOW

    return KILLABILITY_MEDIUM


def analyze_engine_readiness(engine_path: Path, functions: list[FunctionAnalysis]) -> EngineReadiness:
    """Compute readiness status for an engine."""
    pure_count = sum(1 for f in functions if f.purity == "PURE")
    impure_count = sum(1 for f in functions if f.purity == "IMPURE")
    unknown_count = sum(1 for f in functions if f.purity == "UNKNOWN")

    # Determine readiness
    if impure_count == 0 and pure_count > 0:
        readiness = STATUS_READY
    elif impure_count > 0 and pure_count == 0:
        readiness = STATUS_BLOCKED
    else:
        readiness = STATUS_PARTIAL

    # Compute killability estimate (basic)
    killability = compute_killability(functions, {})

    return EngineReadiness(
        module_path=str(engine_path.relative_to(BACKEND_DIR)),
        pure_functions=pure_count,
        impure_functions=impure_count,
        unknown_functions=unknown_count,
        readiness=readiness,
        killability_estimate=killability,
    )


def generate_mutation_map(functions: list[FunctionAnalysis]) -> dict[str, Any]:
    """Generate the mutation-map.json structure."""
    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "functions": [
            {
                "module": f.module,
                "function": f.function,
                "purity": f.purity,
                "confidence": f.confidence,
                "mutation_types": f.mutation_types,
                "blockers": f.blockers,
                "criticality": f.criticality,
                "risk": f.risk,
            }
            for f in functions
        ],
    }


def generate_mutation_registry(functions: list[FunctionAnalysis], registry: dict[str, Any]) -> dict[str, Any]:
    """Generate the full mutation-registry.json with test coverage mapping."""
    entries = []

    # Group functions by module
    functions_by_module: dict[str, list[FunctionAnalysis]] = {}
    for f in functions:
        if f.module not in functions_by_module:
            functions_by_module[f.module] = []
        functions_by_module[f.module].append(f)

    for module_path, funcs in functions_by_module.items():
        # Find capability for this module
        cap_id = "unknown"
        cap_info = {}
        for cap in registry.get("capabilities", []):
            for engine in cap.get("engines", []):
                if engine in module_path:
                    cap_id = cap.get("id", "unknown")
                    cap_info = cap
                    break

        # Collect mutation types
        all_mutation_types = set()
        for f in funcs:
            all_mutation_types.update(f.mutation_types)

        entry = {
            "module": module_path,
            "function": "multiple",  # Registry entry for whole module
            "capability": cap_id,
            "risk": funcs[0].risk if funcs else "low",
            "mutation_types": list(all_mutation_types),
            "existing_tests": {
                "smoke_tests": f"tests/capabilities/{cap_id}" if cap_id != "unknown" else None,
                "property_tests": cap_info.get("property_tests", []),
                "golden_tests": cap_info.get("golden_datasets", []),
            },
            "property_tests": bool(cap_info.get("property_tests")),
            "golden_tests": bool(cap_info.get("golden_datasets")),
            "contracts": bool(cap_info.get("contracts")),
            "performance_tests": False,  # Will be enhanced later
        }

        entries.append(entry)

    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "entries": entries,
    }


def generate_readiness_report(engines: list[EngineReadiness]) -> dict[str, Any]:
    """Generate mutation-readiness.json structure."""
    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "engines": [
            {
                "module_path": e.module_path,
                "pure_functions": e.pure_functions,
                "impure_functions": e.impure_functions,
                "unknown_functions": e.unknown_functions,
                "readiness": e.readiness,
                "killability_estimate": e.killability_estimate,
            }
            for e in engines
        ],
    }


def generate_readiness_markdown(engines: list[EngineReadiness], registry: dict[str, Any]) -> str:
    """Generate mutation-readiness.md human-readable report."""
    lines = [
        "# Mutation Readiness Report",
        "",
        f"Generated: {datetime.now(UTC).isoformat()}",
        "",
        "## Engine Readiness Status",
        "",
        "| Engine | Pure Functions | Impure Functions | Readiness | Killability Estimate |",
        "|--------|----------------|------------------|-----------|---------------------|",
    ]

    for e in sorted(engines, key=lambda x: x.readiness == STATUS_BLOCKED):
        lines.append(
            f"| `{e.module_path}` | {e.pure_functions} | {e.impure_functions} | {e.readiness} | {e.killability_estimate} |"
        )

    lines.extend([
        "",
        "## Readiness Legend",
        "",
        "| Status | Description |",
        "|--------|-------------|",
        "| Ready | Pure functions with no blockers - ready for mutation testing |",
        "| Partial | Mix of pure/impure functions - limited mutation candidates |",
        "| Blocked | Impure functions prevent safe mutation testing |",
        "",
        "## Killability Estimate Legend",
        "",
        "| Estimate | Meaning |",
        "|----------|---------|",
        "| HIGH | Strong test coverage likely to catch mutations |",
        "| MEDIUM | Some coverage, may miss edge cases |",
        "| LOW | Weak coverage, mutations may survive |",
        "| UNKNOWN | Unable to determine |",
    ])

    return "\n".join(lines)


def generate_gaps_report(functions: list[FunctionAnalysis], registry: dict[str, Any]) -> str:
    """Generate mutation-gaps.md - actionable report of validation gaps."""
    lines = [
        "# Mutation Validation Gaps Report",
        "",
        f"Generated: {datetime.now(UTC).isoformat()}",
        "",
        "## Summary",
        "",
    ]

    # Group by module
    modules: dict[str, list[FunctionAnalysis]] = {}
    for f in functions:
        if f.module not in modules:
            modules[f.module] = []
        modules[f.module].append(f)

    for module_path, funcs in sorted(modules.items()):
        lines.extend([
            f"### `{module_path}`",
            "",
        ])

        # Get capability info
        cap_id = "unknown"
        for cap in registry.get("capabilities", []):
            for engine in cap.get("engines", []):
                if engine in module_path:
                    cap_id = cap.get("id", "unknown")
                    break

        # Find capability info
        cap_info = {}
        for cap in registry.get("capabilities", []):
            if cap.get("id") == cap_id:
                cap_info = cap
                break

        # Analyze coverage
        has_property = len(cap_info.get("property_tests", [])) > 0
        has_golden = len(cap_info.get("golden_datasets", [])) > 0
        has_invariants = len(cap_info.get("invariants", [])) > 0
        has_contracts = len(cap_info.get("contracts", [])) > 0

        # Pure functions check
        pure_funcs = [f for f in funcs if f.purity == "PURE"]
        impure_funcs = [f for f in funcs if f.purity == "IMPURE"]

        if pure_funcs:
            lines.append("✓ Pure functions detected")
        else:
            lines.append("✗ No pure functions - blocked for mutation testing")

        if has_property:
            lines.append("✓ Property tests available")
        else:
            lines.append("✗ No property tests")

        if has_golden:
            lines.append("✓ Golden datasets available")
        else:
            lines.append("✗ No golden datasets")

        if has_invariants:
            lines.append("✓ Invariant tests available")
        else:
            lines.append("✗ No invariant tests")

        if has_contracts:
            lines.append("✓ Contract tests available")
        else:
            lines.append("✗ No contract tests")

        if impure_funcs:
            lines.append(f"✗ Impure functions (blockers): {len(impure_funcs)}")
            for imp in impure_funcs:
                lines.append(f"  - `{imp.function}`: blocked by {imp.blockers}")

        lines.append("")

    return "\n".join(lines)


def main() -> None:
    """Run mutation discovery and generate outputs."""
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)

    # Load capability registry
    registry = load_capability_registry()

    # Discover engine files
    engine_files = discover_engine_files()

    all_functions: list[FunctionAnalysis] = []
    all_engines: list[EngineReadiness] = []

    for engine_path in engine_files:
        # Get capability context
        cap_id, criticality, risk = get_capability_for_engine(engine_path, registry)

        # Get functions in this engine
        functions = get_engine_functions(engine_path)

        # Analyze each function
        engine_functions: list[FunctionAnalysis] = []
        for func_name in functions:
            analysis = analyze_function_ast(engine_path, func_name)
            analysis.criticality = criticality
            analysis.risk = risk
            engine_functions.append(analysis)
            all_functions.append(analysis)

        # Find capability info for killability
        cap_info = {}
        for cap in registry.get("capabilities", []):
            if cap.get("id") == cap_id:
                cap_info = cap
                break

        # Analyze engine readiness
        engine_readiness = analyze_engine_readiness(engine_path, engine_functions)
        engine_readiness.killability_estimate = compute_killability(engine_functions, cap_info)
        all_engines.append(engine_readiness)

    # Generate outputs
    # 1. mutation-map.json
    mutation_map = generate_mutation_map(all_functions)
    with open(GENERATED_DIR / "mutation-map.json", "w") as f:
        json.dump(mutation_map, f, indent=2)
    print("Generated: mutation-map.json")

    # 2. mutation-readiness.json
    readiness_report = generate_readiness_report(all_engines)
    with open(GENERATED_DIR / "mutation-readiness.json", "w") as f:
        json.dump(readiness_report, f, indent=2)
    print("Generated: mutation-readiness.json")

    # 3. mutation-readiness.md
    readiness_md = generate_readiness_markdown(all_engines, registry)
    with open(GENERATED_DIR / "mutation-readiness.md", "w") as f:
        f.write(readiness_md)
    print("Generated: mutation-readiness.md")

    # 4. mutation-registry.json
    mutation_registry = generate_mutation_registry(all_functions, registry)
    with open(GENERATED_DIR / "mutation-registry.json", "w") as f:
        json.dump(mutation_registry, f, indent=2)
    print("Generated: mutation-registry.json")

    # 5. mutation-gaps.md
    gaps_report = generate_gaps_report(all_functions, registry)
    with open(GENERATED_DIR / "mutation-gaps.md", "w") as f:
        f.write(gaps_report)
    print("Generated: mutation-gaps.md")

    # Summary
    print(f"\nDiscovered {len(all_functions)} functions in {len(engine_files)} engine files")
    pure = sum(1 for f in all_functions if f.purity == "PURE")
    impure = sum(1 for f in all_functions if f.purity == "IMPURE")
    print(f"Pure: {pure}, Impure: {impure}, Unknown: {len(all_functions) - pure - impure}")


if __name__ == "__main__":
    main()
