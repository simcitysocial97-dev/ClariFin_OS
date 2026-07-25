#!/usr/bin/env python3
"""Change Intelligence Framework (CIF).

Analyzes changed files and determines impact on capabilities, tests, and risk levels.
Uses structured artifacts from CTF instead of parsing markdown.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

# Project root from this file's location (backend/tools → backend → project_root)
PROJECT_ROOT = Path(__file__).parent.parent.parent
BACKEND_DIR = PROJECT_ROOT / "backend"
GENERATED_DIR = PROJECT_ROOT / "backend" / "tests" / "generated"

# Risk levels and weights
RISK_LOW = "LOW"
RISK_MEDIUM = "MEDIUM"
RISK_HIGH = "HIGH"
RISK_CRITICAL = "CRITICAL"

RISK_WEIGHTS = {
    RISK_LOW: 1,
    RISK_MEDIUM: 2,
    RISK_HIGH: 4,
    RISK_CRITICAL: 8,
}

# Confidence levels
CONF_LOW = "LOW"
CONF_MEDIUM = "MEDIUM"
CONF_HIGH = "HIGH"


@dataclass
class ChangeImpact:
    """Impact analysis for a single changed file."""

    file: str
    risk: str = RISK_LOW
    confidence: str = CONF_HIGH
    capabilities: list[str] = field(default_factory=list)
    affected: dict[str, list[str]] = field(
        default_factory=lambda: {
            "services": [],
            "engines": [],
            "repositories": [],
            "property_tests": [],
            "golden_tests": [],
            "invariants": [],
            "capability_tests": [],
        }
    )
    recommended_commands: list[str] = field(default_factory=list)


def load_capability_registry() -> dict[str, Any]:
    """Load the capability registry YAML."""
    registry_path = GENERATED_DIR / "capability-registry.yaml"
    if not registry_path.exists():
        raise FileNotFoundError(
            "capability-registry.yaml not found - run check_coverage.py first"
        )
    with open(registry_path) as f:
        data: dict[str, Any] | None = yaml.safe_load(f)
        return data if data else {"capabilities": []}


def load_coverage() -> dict[str, Any]:
    """Load the coverage JSON."""
    coverage_path = GENERATED_DIR / "coverage.json"
    if not coverage_path.exists():
        raise FileNotFoundError("coverage.json not found - run check_coverage.py first")
    with open(coverage_path) as f:
        data: dict[str, Any] = json.load(f)
        return data


def build_file_graph(registry: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Build in-memory graph mapping files to their capabilities and tests.

    Returns a dict: file_path -> {capabilities: [...], property_tests: [...], ...}
    """
    graph: dict[str, dict[str, Any]] = {}

    for cap in registry.get("capabilities", []):
        cap_id = cap.get("id", "")

        # Map routers
        for router in cap.get("routers", []):
            path = router.lstrip("/")
            if path not in graph:
                graph[path] = {
                    "capabilities": set(),
                    "property_tests": set(),
                    "golden_tests": set(),
                    "invariants": set(),
                    "capability_tests": [],
                }
            graph[path]["capabilities"].add(cap_id)
            graph[path]["property_tests"].add(
                f"tests/properties/{cap_id.replace('_', '')}"
            )
            graph[path]["capability_tests"].append(f"tests/capabilities/{cap_id}")

        # Map services
        for service in cap.get("services", []):
            path = service.lstrip("/")
            if path not in graph:
                graph[path] = {
                    "capabilities": set(),
                    "property_tests": set(),
                    "golden_tests": set(),
                    "invariants": set(),
                    "capability_tests": [],
                }
            graph[path]["capabilities"].add(cap_id)
            graph[path]["capability_tests"].append(f"tests/capabilities/{cap_id}")

        # Map engines
        for engine in cap.get("engines", []):
            path = engine.lstrip("/")
            if path not in graph:
                graph[path] = {
                    "capabilities": set(),
                    "property_tests": set(),
                    "golden_tests": set(),
                    "invariants": set(),
                    "capability_tests": [],
                }
            graph[path]["capabilities"].add(cap_id)

            # Add property tests from capability
            for test in cap.get("property_tests", []):
                if test.startswith("tests/properties/"):
                    graph[path]["property_tests"].add(test.rsplit("/", 1)[0])

            # Add golden test names
            for dataset in cap.get("golden_datasets", []):
                if dataset.startswith("tests/golden/datasets/"):
                    dataset_name = dataset.replace(
                        "tests/golden/datasets/", ""
                    ).replace(".json", "")
                    graph[path]["golden_tests"].add(dataset_name)

            # Add invariants
            for inv in cap.get("invariants", []):
                graph[path]["invariants"].add(inv)

            graph[path]["capability_tests"].append(f"tests/capabilities/{cap_id}")

        # Map repositories
        for repo in cap.get("repositories", []):
            path = repo.lstrip("/")
            if path not in graph:
                graph[path] = {
                    "capabilities": set(),
                    "property_tests": set(),
                    "golden_tests": set(),
                    "invariants": set(),
                    "capability_tests": [],
                }
            graph[path]["capabilities"].add(cap_id)
            graph[path]["capability_tests"].append(f"tests/capabilities/{cap_id}")

    # Convert sets to sorted lists
    for path in graph:
        graph[path]["capabilities"] = sorted(graph[path]["capabilities"])
        graph[path]["property_tests"] = sorted(graph[path]["property_tests"])
        graph[path]["golden_tests"] = sorted(graph[path]["golden_tests"])
        graph[path]["invariants"] = sorted(graph[path]["invariants"])

    return graph


def classify_risk(file_path: str) -> tuple[str, str]:
    """Classify risk level for a file based on path patterns.

    Returns (risk_level, confidence) tuple.
    """
    file_lower = file_path.lower()

    # Documentation - LOW risk
    if any(ext in file_lower for ext in [".md", ".txt", ".rst", "readme", "changelog"]):
        return RISK_LOW, CONF_HIGH

    # Routers - MEDIUM risk
    if "/routers/" in file_path:
        return RISK_MEDIUM, CONF_HIGH

    # Services - MEDIUM risk
    if "/services/" in file_path:
        return RISK_MEDIUM, CONF_HIGH

    # Repositories - HIGH risk
    if "/repositories/" in file_path:
        return RISK_HIGH, CONF_HIGH

    # Engines - CRITICAL risk (financial logic)
    if "/engines/" in file_path:
        # Double-check for financial calculation keywords
        engine_path = (
            file_path.split("/engines/")[-1] if "/engines/" in file_path else ""
        )
        if any(
            kw in engine_path
            for kw in [
                "cashflow",
                "loan",
                "forecast",
                "interest",
                "amortization",
                "behaviour",
                "behavior",
                "credit_card",
            ]
        ):
            return RISK_CRITICAL, CONF_HIGH
        return RISK_HIGH, CONF_MEDIUM  # Engine but not obviously financial

    # Schema/migrations - HIGH risk
    if any(kw in file_lower for kw in ["schema", "migration", ".sql"]):
        return RISK_HIGH, CONF_HIGH

    # Unknown files - LOW risk but LOW confidence
    return RISK_LOW, CONF_LOW


def get_git_changed_files() -> list[str]:
    """Get changed files from git diff. Returns empty list if git unavailable."""
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", "HEAD"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            return []
        files = [f.strip() for f in result.stdout.strip().split("\n") if f.strip()]
        return files
    except FileNotFoundError:
        # git not available
        return []


def build_dependency_graph(registry: dict[str, Any]) -> dict[str, Any]:
    """Build mapping of capability dependencies for transitive analysis."""
    deps: dict[str, list[str]] = {}
    for cap in registry.get("capabilities", []):
        cap_id = cap.get("id", "")
        deps[cap_id] = cap.get("dependencies", [])
    return deps


def get_transitive_capabilities(cap_id: str, graph: dict[str, list[str]]) -> set[str]:
    """Get all capabilities that depend on this capability (transitively)."""
    result: set[str] = {cap_id}
    for other_cap, other_deps in graph.items():
        if cap_id in other_deps:
            result.add(other_cap)
    return result


def analyze_change(
    file_path: str, file_graph: dict[str, Any], registry: dict[str, Any]
) -> ChangeImpact:
    """Analyze a single changed file."""
    impact = ChangeImpact(file=file_path)

    # Classify risk
    risk, confidence = classify_risk(file_path)
    impact.risk = risk
    impact.confidence = confidence

    # Look up in file graph
    # Normalize path - remove backend/ prefix if present
    lookup_path = file_path.replace("backend/", "").replace("src/", "src/")

    graph_entry = file_graph.get(lookup_path) or file_graph.get(file_path)

    if graph_entry:
        impact.capabilities = graph_entry["capabilities"]
        # Remove duplicates from capability_tests
        impact.affected["capability_tests"] = sorted(
            set(graph_entry["capability_tests"])
        )
        impact.affected["property_tests"] = graph_entry["property_tests"]
        impact.affected["golden_tests"] = graph_entry["golden_tests"]
        impact.affected["invariants"] = graph_entry["invariants"]

        # Build recommended commands grouped by capability
        for cap_id in impact.capabilities:
            impact.recommended_commands.append(f"pytest tests/capabilities/{cap_id} -q")

        for prop_test in impact.affected["property_tests"]:
            impact.recommended_commands.append(f"pytest {prop_test} -q")

        if impact.affected["golden_tests"]:
            golden_keywords = ",".join(
                impact.affected["golden_tests"][:3]
            )  # Limit to avoid huge commands
            impact.recommended_commands.append(
                f"pytest tests/golden -k '{golden_keywords}' -q"
            )
    else:
        # File not in graph - unknown impact
        impact.confidence = CONF_LOW
        # Try to find capability by path pattern
        for cap in registry.get("capabilities", []):
            for router in cap.get("routers", []):
                if router in file_path:
                    impact.capabilities.append(cap["id"])
            for service in cap.get("services", []):
                if service in file_path:
                    impact.capabilities.append(cap["id"])
            for engine in cap.get("engines", []):
                if engine in file_path:
                    impact.capabilities.append(cap["id"])
            for repo in cap.get("repositories", []):
                if repo in file_path:
                    impact.capabilities.append(cap["id"])

        if not impact.capabilities:
            impact.capabilities = ["UNKNOWN"]

    return impact


def compute_overall_risk(impacts: list[ChangeImpact]) -> tuple[str, int]:
    """Compute overall risk score using weighted sum."""
    total_score = sum(RISK_WEIGHTS.get(i.risk, 1) for i in impacts)

    if total_score >= 8:
        return RISK_CRITICAL, total_score
    if total_score >= 4:
        return RISK_HIGH, total_score
    if total_score >= 2:
        return RISK_MEDIUM, total_score
    return RISK_LOW, total_score


def generate_markdown_report(impacts: list[ChangeImpact]) -> str:
    """Generate human-readable markdown report."""
    lines = [
        "# Change Impact Report",
        "",
        f"Generated: {datetime.now(UTC).isoformat()}",
        "",
        "## Summary",
        "",
    ]

    if not impacts:
        lines.extend(
            [
                "No changes detected.",
                "",
            ]
        )
        return "\n".join(lines)

    # Summary table
    lines.extend(
        [
            "| File | Risk | Capabilities | Confidence |",
            "|------|------|--------------|------------|",
        ]
    )
    for i in impacts:
        caps = ", ".join(i.capabilities) if i.capabilities else "UNKNOWN"
        lines.append(f"| `{i.file}` | {i.risk} | {caps} | {i.confidence} |")

    lines.extend(["", "## Detailed Analysis", ""])

    for i in impacts:
        lines.extend(
            [
                f"### Changed: `{i.file}`",
                "",
                f"**Risk:** {i.risk}",
                "",
                f"**Confidence:** {i.confidence}",
                "",
            ]
        )

        if i.capabilities and "UNKNOWN" not in i.capabilities:
            lines.append("**Affected Capabilities:**")
            lines.append("")
            for cap_id in i.capabilities:
                lines.append(f"- `{cap_id}`")
            lines.append("")

        if any(i.affected.values()):
            lines.append("**Affected Tests:**")
            lines.append("")

            if i.affected["capability_tests"]:
                lines.append("  - Capability Smoke Tests:")
                for t in i.affected["capability_tests"]:
                    lines.append(f"    - `{t}`")

            if i.affected["property_tests"]:
                lines.append("  - Property Tests:")
                for t in i.affected["property_tests"]:
                    lines.append(f"    - `{t}`")

            if i.affected["golden_tests"]:
                lines.append("  - Golden Datasets:")
                for t in i.affected["golden_tests"]:
                    lines.append(f"    - `{t}`")

            if i.affected["invariants"]:
                lines.append("  - Invariants:")
                for t in i.affected["invariants"]:
                    lines.append(f"    - `{t}`")
            lines.append("")

        if i.recommended_commands:
            lines.append("**Recommended Verification:**")
            lines.append("```bash")
            for cmd in i.recommended_commands:
                lines.append(cmd)
            lines.append("```")

        lines.append("")

    # Overall risk
    overall_risk, score = compute_overall_risk(impacts)
    lines.extend(
        [
            "## Overall Assessment",
            "",
            f"**Risk Level:** {overall_risk}",
            "",
            f"**Risk Score:** {score}",
            "",
        ]
    )

    return "\n".join(lines)


def generate_test_plan(impacts: list[ChangeImpact]) -> str:
    """Generate actionable test plan."""
    lines = [
        "# Recommended Verification Plan",
        "",
        f"Generated: {datetime.now(UTC).isoformat()}",
        "",
    ]

    if not impacts:
        lines.extend(
            [
                "No changes detected - no targeted verification needed.",
                "",
            ]
        )
        return "\n".join(lines)

    # Collect unique capabilities
    all_capabilities: set[str] = set()
    all_property_tests: set[str] = set()
    all_golden_keywords: set[str] = set()

    for i in impacts:
        # Exclude UNKNOWN capabilities from test plan
        if "UNKNOWN" not in i.capabilities:
            all_capabilities.update(i.capabilities)
        all_property_tests.update(i.affected["property_tests"])
        all_golden_keywords.update(i.affected["golden_tests"])

    # Stage 1: Verify-fast
    lines.extend(
        [
            "## Stage 1: Lint & Type Check",
            "",
            "```bash",
            "scripts/verify-fast.sh",
            "```",
            "",
        ]
    )

    # Stage 2: Architecture
    if all_capabilities:
        lines.extend(
            [
                "## Stage 2: Architecture Tests",
                "",
                "```bash",
                "pytest tests/architecture -q --tb=short",
                "```",
                "",
            ]
        )

    # Stage 3: Affected Capabilities
    if all_capabilities:
        lines.append("## Stage 3: Capability Smoke Tests (Affected)")
        lines.append("")
        for cap_id in sorted(all_capabilities):
            lines.append(f"- ✓ pytest tests/capabilities/{cap_id} -q")
        lines.append("")

    # Stage 4: Property Tests
    if all_property_tests:
        lines.extend(
            [
                "## Stage 4: Property Tests (Affected)",
                "",
            ]
        )
        for prop in sorted(all_property_tests):
            lines.append(f"- ✓ {prop}")
        lines.append("")

    # Stage 5: Golden Tests
    if all_golden_keywords:
        lines.extend(
            [
                "## Stage 5: Golden Tests (Affected)",
                "",
                "```bash",
                f"pytest tests/golden -k '{','.join(sorted(all_golden_keywords)[:5])}' -q --tb=short",
                "```",
                "",
            ]
        )

    return "\n".join(lines)


def main() -> None:
    """Run CIF analysis and generate reports."""
    parser = argparse.ArgumentParser(description="Change Intelligence Framework")
    parser.add_argument("files", nargs="*", help="Files to analyze (default: git diff)")
    args = parser.parse_args()

    # Get changed files
    if args.files:
        changed_files = args.files
    else:
        changed_files = get_git_changed_files()
        if not changed_files:
            print("No files provided and git diff unavailable or no changes detected.")
            # Generate empty reports
            GENERATED_DIR.mkdir(parents=True, exist_ok=True)

            empty_md = generate_markdown_report([])
            with open(GENERATED_DIR / "change-report.md", "w") as f:
                f.write(empty_md)
            print("Generated: change-report.md")

            empty_json: dict[str, Any] = {
                "generated_at": datetime.now(UTC).isoformat(),
                "git_sha": os.popen("git rev-parse HEAD 2>/dev/null || echo 'unknown'")
                .read()
                .strip()
                or "unknown",
                "changes": [],
                "overall": {"risk": RISK_LOW, "score": 0},
            }
            with open(GENERATED_DIR / "change-report.json", "w") as f:
                json.dump(empty_json, f, indent=2)
            print("Generated: change-report.json")

            empty_plan = generate_test_plan([])
            with open(GENERATED_DIR / "test-plan.md", "w") as f:
                f.write(empty_plan)
            print("Generated: test-plan.md")
            return

    # Load structured artifacts
    registry = load_capability_registry()
    load_coverage()

    # Build file graph
    file_graph = build_file_graph(registry)

    # Analyze each changed file
    impacts: list[ChangeImpact] = []
    for file_path in changed_files:
        impact = analyze_change(file_path, file_graph, registry)
        impacts.append(impact)

    # Load mutation artifacts for enhanced reporting
    mutation_map: dict[str, Any] = {}
    test_strength: dict[str, Any] = {}

    mutation_map_path = GENERATED_DIR / "mutation-map.json"
    if mutation_map_path.exists():
        with open(mutation_map_path) as f:
            mutation_map = json.load(f)

    mutation_readiness_path = GENERATED_DIR / "mutation-readiness.json"
    if mutation_readiness_path.exists():
        with open(mutation_readiness_path) as f:
            json.load(f)

    test_strength_path = GENERATED_DIR / "test-strength.json"
    if test_strength_path.exists():
        with open(test_strength_path) as f:
            test_strength = json.load(f)

    # Collect affected mutation candidates per file
    affected_mutation_candidates: dict[str, list[str]] = {}
    for file_path in changed_files:
        lookup_path = file_path.replace("backend/", "")
        for func in mutation_map.get("functions", []):
            if func.get("module") == lookup_path or lookup_path.endswith(
                func.get("module", "")
            ):
                if func.get("purity") == "PURE":
                    candidate_name = (
                        f"{func.get('module', '')}:{func.get('function', '')}"
                    )
                    affected_mutation_candidates.setdefault(file_path, []).append(
                        candidate_name
                    )

    # Build mutation readiness per capability
    mutation_readiness_by_cap: dict[str, str] = {}
    for cap in test_strength.get("capabilities", []):
        cap_id = cap.get("id")
        cap_strength = cap.get("strength", "Weak")
        if cap_id:
            mutation_readiness_by_cap[cap_id] = cap_strength

    # Generate reports
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)

    # Markdown report
    md_report = generate_markdown_report(impacts)
    with open(GENERATED_DIR / "change-report.md", "w") as f:
        f.write(md_report)
    print("Generated: change-report.md")

    # JSON report with mutation data
    json_report: dict[str, Any] = {
        "generated_at": datetime.now(UTC).isoformat(),
        "git_sha": os.popen("git rev-parse HEAD 2>/dev/null || echo 'unknown'")
        .read()
        .strip()
        or "unknown",
        "changes": [
            {
                "file": i.file,
                "risk": i.risk,
                "confidence": i.confidence,
                "capabilities": i.capabilities,
                "affected": i.affected,
                "recommended_commands": i.recommended_commands,
            }
            for i in impacts
        ],
        "overall": {
            "risk": compute_overall_risk(impacts)[0],
            "score": compute_overall_risk(impacts)[1],
        },
        "mutation_readiness": mutation_readiness_by_cap,
        "affected_mutation_candidates": affected_mutation_candidates,
        "test_strength": {
            cap.get("id"): cap.get("strength", "Weak")
            for cap in test_strength.get("capabilities", [])
        },
    }
    with open(GENERATED_DIR / "change-report.json", "w") as f:
        json.dump(json_report, f, indent=2)
    print("Generated: change-report.json")

    # Test plan
    test_plan = generate_test_plan(impacts)
    with open(GENERATED_DIR / "test-plan.md", "w") as f:
        f.write(test_plan)
    print("Generated: test-plan.md")

    # Summary output
    print("\n=== Change Summary ===")
    for i in impacts:
        caps = ", ".join(i.capabilities) if i.capabilities else "UNKNOWN"
        print(f"  {i.file}: {i.risk} risk, affects: {caps}")

    overall_risk, score = compute_overall_risk(impacts)
    print(f"\nOverall Risk: {overall_risk} (score: {score})")


if __name__ == "__main__":
    main()
