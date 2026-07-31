#!/usr/bin/env python3
"""Test Strength Analyzer - Computes validation strength scores for capabilities.

Uses weighted scoring to assess how well capabilities are protected against
incorrect implementations. Weighted evidence approach:

Evidence Type          Weight
-------------------    ------
Property tests         5
Golden tests           5
Contract tests         4
Capability Smoke       3
Invariants             3
Performance tests      2
Architecture tests     2
Meta tests             1

Generated files:
- test-strength.json: Machine-readable strength scores
- test-strength.md: Human-readable report
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

# Project root
PROJECT_ROOT = Path(__file__).parent.parent.parent
BACKEND_DIR = PROJECT_ROOT / "backend"
GENERATED_DIR = PROJECT_ROOT / "backend" / "tests" / "generated"

# Test type weights
WEIGHTS = {
    "property": 5,
    "golden": 5,
    "contract": 4,
    "capability_smoke": 3,
    "invariants": 3,
    "performance": 2,
    "architecture": 2,
    "meta": 1,
}

# Strength levels
STRENGTH_WEAK = "Weak"
STRENGTH_MODERATE = "Moderate"
STRENGTH_STRONG = "Strong"
STRENGTH_CRITICAL = "Critical"


@dataclass
class CapabilityStrength:
    """Validation strength for a capability."""

    id: str
    name: str
    criticality: str
    structural_maturity: str = "✗"
    # Evidence counts
    smoke_tests: int = 0
    property_tests: int = 0
    golden_tests: int = 0
    contract_tests: int = 0
    performance_tests: int = 0
    invariants: int = 0
    architecture_tests: int = 0
    meta_tests: int = 0
    invariant_count: int = 0
    # Computed scores
    weighted_score: int = 0
    strength: str = STRENGTH_WEAK
    gaps: list[str] = field(default_factory=list)


def load_capability_registry() -> dict[str, Any]:
    """Load capability registry from generated directory."""
    registry_path = GENERATED_DIR / "capability-registry.yaml"
    if registry_path.exists():
        with open(registry_path) as f:
            return yaml.safe_load(f) or {"capabilities": []}
    return {"capabilities": []}


def check_path_exists(path_str: str) -> bool:
    """Check if a path exists relative to backend directory."""
    return (BACKEND_DIR / path_str).exists()


def count_test_files(test_dir_pattern: str) -> int:
    """Count test files matching a pattern."""
    count = 0
    for f in BACKEND_DIR.glob(test_dir_pattern):
        if f.is_file() and f.suffix == ".py" and f.name.startswith("test_"):
            count += 1
    return count


def analyze_capability_strength(cap: dict[str, Any]) -> CapabilityStrength:
    """Analyze validation strength for a single capability."""
    cap_id = cap.get("id", "unknown")
    cap_name = cap.get("name", "Unknown")
    criticality = cap.get("criticality", "medium")

    strength = CapabilityStrength(
        id=cap_id,
        name=cap_name,
        criticality=criticality,
    )

    # Count smoke tests (capability test files)
    cap_test_path = f"tests/capability/{cap_id}"
    if (BACKEND_DIR / cap_test_path).exists():
        for _f in (BACKEND_DIR / cap_test_path).glob("test_*.py"):
            strength.smoke_tests += 1

    # Count property tests
    for test in cap.get("property_tests", []):
        if check_path_exists(test):
            strength.property_tests += 1

    # Count golden tests (dataset files)
    for dataset in cap.get("golden_datasets", []):
        if check_path_exists(dataset):
            strength.golden_tests += 1

    # Check contract tests (registry has contract endpoints)
    contract_endpoints = cap.get("contracts", [])
    if contract_endpoints:
        # Check if there are contract test files
        contract_dir = BACKEND_DIR / "tests" / "contracts"
        if contract_dir.exists():
            for f in contract_dir.glob("*.py"):
                if f.name.startswith("test_"):
                    strength.contract_tests += 1

    # Count invariant tests
    for inv in cap.get("invariants", []):
        if check_path_exists(inv):
            strength.invariants += 1

    # Check architecture tests
    arch_tests = cap.get("architecture_tests", [])
    if arch_tests and (BACKEND_DIR / "tests" / "architecture").exists():
        strength.architecture_tests = count_test_files("tests/architecture/**/*.py")

    # Check for performance tests (look for pytest-benchmark patterns)
    perf_test_patterns = [
        "tests/performance",
        "tests/**/*perf*.py",
        "tests/**/*benchmark*.py",
    ]
    for pattern in perf_test_patterns:
        strength.performance_tests += count_test_files(pattern)

    # Compute invariant count (distinct invariant assertions)
    inv_path = f"tests/invariants/{cap_id}.py"
    if check_path_exists(inv_path):
        try:
            with open(BACKEND_DIR / inv_path) as fh:
                content = fh.read()
                strength.invariant_count = content.count("assert ")
        except Exception:
            pass

    # Structural maturity check
    engines_exist = all(check_path_exists(e) for e in cap.get("engines", []))
    services_exist = all(check_path_exists(s) for s in cap.get("services", []))
    strength.structural_maturity = "✓" if engines_exist and services_exist else "✗"

    return strength


def compute_weighted_score(strength: CapabilityStrength) -> int:
    """Compute weighted score for a capability."""
    score = 0

    if strength.property_tests > 0:
        score += WEIGHTS["property"]
    if strength.golden_tests > 0:
        score += WEIGHTS["golden"]
    if strength.contract_tests > 0:
        score += WEIGHTS["contract"]
    if strength.smoke_tests > 0:
        score += WEIGHTS["capability_smoke"]
    if strength.invariants > 0:
        score += WEIGHTS["invariants"]
    if strength.performance_tests > 0:
        score += WEIGHTS["performance"]
    if strength.architecture_tests > 0:
        score += WEIGHTS["architecture"]

    return score


def classify_strength(score: int) -> str:
    """Classify strength based on weighted score."""
    if score >= 12:  # 3+ strong evidence types
        return STRENGTH_CRITICAL
    if score >= 8:  # 2 strong or 1 strong + 2 medium
        return STRENGTH_STRONG
    if score >= 4:  # At least one medium evidence
        return STRENGTH_MODERATE
    return STRENGTH_WEAK


def compute_gaps(strength: CapabilityStrength) -> list[str]:
    """Identify validation gaps for a capability."""
    gaps = []

    if strength.property_tests == 0:
        gaps.append("No property tests")
    if strength.golden_tests == 0:
        gaps.append("No golden tests")
    if strength.contract_tests == 0:
        gaps.append("No contract tests")
    if strength.invariants == 0:
        gaps.append("No invariant tests")
    if strength.performance_tests == 0:
        gaps.append("No performance baseline")

    return gaps


def generate_json_report(capabilities: list[CapabilityStrength]) -> dict[str, Any]:
    """Generate machine-readable test-strength.json."""
    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "capabilities": [
            {
                "id": c.id,
                "name": c.name,
                "criticality": c.criticality,
                "structural_maturity": c.structural_maturity,
                "evidence": {
                    "smoke_tests": c.smoke_tests,
                    "property_tests": c.property_tests,
                    "golden_tests": c.golden_tests,
                    "contract_tests": c.contract_tests,
                    "performance_tests": c.performance_tests,
                    "invariants": c.invariants,
                    "architecture_tests": c.architecture_tests,
                },
                "weighted_score": c.weighted_score,
                "strength": c.strength,
                "gaps": c.gaps,
                "invariant_count": c.invariant_count,
            }
            for c in capabilities
        ],
    }


def generate_markdown_report(capabilities: list[CapabilityStrength]) -> str:
    """Generate human-readable test-strength.md."""
    lines = [
        "# Validation Strength Report",
        "",
        f"Generated: {datetime.now(UTC).isoformat()}",
        "",
        "## Strength Classification",
        "",
        "| Capability | Criticality | Strength | Score | Evidence | Gaps |",
        "|------------|-------------|----------|-------|----------|------|",
    ]

    for c in sorted(capabilities, key=lambda x: x.criticality == "high", reverse=True):
        evidence_parts = []
        if c.property_tests > 0:
            evidence_parts.append(f"property({c.property_tests})")
        if c.golden_tests > 0:
            evidence_parts.append(f"golden({c.golden_tests})")
        if c.contract_tests > 0:
            evidence_parts.append(f"contract({c.contract_tests})")
        if c.smoke_tests > 0:
            evidence_parts.append(f"smoke({c.smoke_tests})")
        if c.invariants > 0:
            evidence_parts.append(f"invariants({c.invariants})")

        evidence_str = ", ".join(evidence_parts) if evidence_parts else "none"
        gaps_str = ", ".join(c.gaps) if c.gaps else "none"

        lines.append(
            f"| {c.name} | {c.criticality} | {c.strength} | {c.weighted_score} | {evidence_str} | {gaps_str} |"
        )

    # Legend section
    lines.extend(
        [
            "",
            "## Scoring Legend",
            "",
            "| Score Range | Strength | Description |",
            "|-------------|----------|-------------|",
            "| 12+ | Critical | Well protected against regressions |",
            "| 8-11 | Strong | Good coverage, minor gaps |",
            "| 4-7 | Moderate | Some coverage, notable gaps |",
            "| 0-3 | Weak | Minimal or no validation evidence |",
            "",
            "## Evidence Weights",
            "",
            "| Evidence Type | Weight | Purpose |",
            "|---------------|--------|---------|",
            "| Property tests | 5 | Catch edge cases and invariants |",
            "| Golden tests | 5 | Regression protection |",
            "| Contract tests | 4 | API correctness |",
            "| Capability Smoke | 3 | Integration verification |",
            "| Invariants | 3 | Domain rule enforcement |",
            "| Performance | 2 | Performance regression detection |",
            "| Architecture | 2 | Layer boundary compliance |",
        ]
    )

    return "\n".join(lines)


def main() -> None:
    """Run test strength analysis and generate reports."""
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)

    registry = load_capability_registry()

    capabilities: list[CapabilityStrength] = []

    for cap in registry.get("capabilities", []):
        strength = analyze_capability_strength(cap)
        strength.weighted_score = compute_weighted_score(strength)
        strength.strength = classify_strength(strength.weighted_score)
        strength.gaps = compute_gaps(strength)
        capabilities.append(strength)

    # JSON output
    json_report = generate_json_report(capabilities)
    with open(GENERATED_DIR / "test-strength.json", "w") as f:
        json.dump(json_report, f, indent=2)
    print("Generated: test-strength.json")

    # Markdown output
    md_report = generate_markdown_report(capabilities)
    with open(GENERATED_DIR / "test-strength.md", "w") as f:
        f.write(md_report)
    print("Generated: test-strength.md")

    # Summary
    print(f"\nAnalyzed {len(capabilities)} capabilities")
    critical = sum(1 for c in capabilities if c.strength == STRENGTH_CRITICAL)
    strong = sum(1 for c in capabilities if c.strength == STRENGTH_STRONG)
    moderate = sum(1 for c in capabilities if c.strength == STRENGTH_MODERATE)
    weak = sum(1 for c in capabilities if c.strength == STRENGTH_WEAK)
    print(f"Critical: {critical}, Strong: {strong}, Moderate: {moderate}, Weak: {weak}")


if __name__ == "__main__":
    main()
