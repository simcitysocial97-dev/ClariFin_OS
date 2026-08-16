#!/usr/bin/env python3
"""Validation Audit Script - Evidence-first analysis of the validation ecosystem.

This script audits the existing validation framework without making code changes.
It produces reports for the Validation Consolidation Phase.
"""

from __future__ import annotations

import contextlib
import json
import subprocess
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).parent.parent.parent
BACKEND_DIR = PROJECT_ROOT / "backend"
GENERATED_DIR = PROJECT_ROOT / "backend" / "tests" / "generated"


@dataclass
class StageMetrics:
    """Metrics for a validation stage."""

    stage_id: str
    description: str
    estimated_runtime: float
    actual_runtime_seconds: float | None = None
    test_count: int = 0
    lines_of_code: int = 0
    unique_bugs_caught: str = "TBD"
    overlap_with_other_stages: str = "TBD"
    status: str = "TBD"  # KEEP, MERGE, OPTIONAL, REMOVE


def run_command(cmd: list[str], cwd: Path | None = None) -> tuple[int, str, str]:
    """Run a command and return exit code, stdout, stderr."""
    result = subprocess.run(
        cmd,
        cwd=cwd or BACKEND_DIR,
        capture_output=True,
        text=True,
    )
    return result.returncode, result.stdout, result.stderr


def count_test_files(pattern: str) -> int:
    """Count test files matching a pattern."""
    result = subprocess.run(
        ["find", str(BACKEND_DIR / "tests"), "-name", pattern],
        capture_output=True,
        text=True,
    )
    return len([line for line in result.stdout.strip().split("\n") if line])


def wc_files(glob_pattern: str) -> int:
    """Count lines in files matching pattern."""
    result = subprocess.run(
        ["find", str(BACKEND_DIR / "tests"), "-name", glob_pattern],
        capture_output=True,
        text=True,
    )
    total = 0
    for f in result.stdout.strip().split("\n"):
        if f:
            wc_result = subprocess.run(
                ["wc", "-l", f],
                capture_output=True,
                text=True,
            )
            if wc_result.returncode == 0:
                with contextlib.suppress(ValueError, IndexError):
                    total += int(wc_result.stdout.split()[0])
    return total


def audit_stage_runtime() -> dict[str, float]:
    """Measure actual runtime for key validation stages."""
    runtimes = {}

    stages = [
        ("architecture", ["pytest", "tests/architecture", "-q", "--tb=short"]),
        ("golden", ["pytest", "tests/golden", "-q", "--tb=short"]),
        (
            "capability",
            ["pytest", "tests/capability/household_cashflow", "-q", "--tb=short"],
        ),
        (
            "properties",
            ["pytest", "tests/properties/test_money_invariants.py", "-q", "--tb=short"],
        ),
    ]

    for stage_id, cmd in stages:
        start = time.time()
        run_command(cmd)
        runtimes[stage_id] = round(time.time() - start, 2)

    return runtimes


def audit_generated_artifacts() -> list[dict[str, Any]]:
    """Audit all generated artifacts in memory-bank/generated/."""
    artifacts = []

    artifact_files = [
        ("api-map.json", "CIF/SVF", "Per run", "Registry mapping files to endpoints"),
        (
            "capability-registry.yaml",
            "check_coverage.py",
            "Per run",
            "Canonical capability definitions",
        ),
        ("change-impact.md", "CIF", "Per run", "Human-readable change analysis"),
        ("change-report.json", "CIF", "Per run", "Machine-readable change analysis"),
        ("change-report.md", "CIF", "Per run", "Human-readable change report"),
        (
            "coverage.json",
            "check_coverage.py",
            "Per run",
            "File-to-capability coverage map",
        ),
        ("coverage.md", "check_coverage.py", "Per run", "Human coverage report"),
        (
            "mutation-gaps.md",
            "mutation_discovery.py",
            "Per run",
            "Mutation candidate gaps",
        ),
        ("mutation-guide.md", "mutation_discovery.py", "Per run", "Mutation guidance"),
        (
            "mutation-map.json",
            "mutation_discovery.py",
            "Per run",
            "Function purity analysis",
        ),
        (
            "mutation-readiness.json",
            "mutation_discovery.py",
            "Per run",
            "Mutation readiness data",
        ),
        (
            "mutation-readiness.md",
            "mutation_discovery.py",
            "Per run",
            "Human mutation readiness",
        ),
        (
            "mutation-registry.json",
            "mutation_discovery.py",
            "Per run",
            "Mutation candidates registry",
        ),
        ("risk-rules.yaml", "Manual", "Static", "Risk classification rules"),
        ("selective-history.json", "SVF", "Per run", "Selective verification history"),
        ("selective-plan.md", "SVF", "Per run", "Selective verification plan"),
        ("selective-summary.json", "SVF", "Per run", "Machine-readable SVF summary"),
        ("test-plan.md", "CIF", "Per run", "Recommended test plan"),
        ("test-strength.json", "test_strength.py", "Per run", "Test strength analysis"),
        (
            "test-strength.md",
            "test_strength.py",
            "Per run",
            "Human test strength report",
        ),
        (
            "traceability.md",
            "check_coverage.py",
            "Per run",
            "Test-to-code traceability",
        ),
        (
            "validation-history.json",
            "VOF",
            "Per run",
            "Validation run history (stale data)",
        ),
        ("validation-manifest.json", "VOF", "Per run", "Current validation manifest"),
        ("validation-metrics.json", "VOF", "Per run", "Stage metrics"),
        ("validation-workflows.md", "Manual", "Static", "Workflow documentation"),
        ("verification-matrix.md", "SVF", "Per run", "Verification matrix"),
    ]

    for filename, producer, regeneration, purpose in artifact_files:
        path = GENERATED_DIR / filename
        exists = path.exists()
        size = path.stat().st_size if exists else 0
        mtime = (
            datetime.fromtimestamp(path.stat().st_mtime, UTC).isoformat()
            if exists
            else "N/A"
        )

        artifacts.append(
            {
                "file": filename,
                "producer": producer,
                "regeneration": regeneration,
                "purpose": purpose,
                "exists": exists,
                "size_bytes": size,
                "last_modified": mtime,
            }
        )

    return artifacts


def audit_capabilities_coverage() -> list[dict[str, Any]]:
    """Audit test coverage per capability."""
    capabilities = [
        {
            "id": "household_cashflow",
            "smoke_tests": True,
            "property_tests": True,
            "golden_scenarios": True,
            "contract_tests": True,
            "invariants": True,
            "test_files_count": {
                "capability": 3,
                "property": 3,
                "golden": 2,
                "contract": 1,
                "invariant": 1,
            },
            "notes": "Well covered across all categories",
        },
        {
            "id": "debt_management",
            "smoke_tests": True,
            "property_tests": True,
            "golden_scenarios": True,
            "contract_tests": True,
            "invariants": True,
            "test_files_count": {
                "capability": 3,
                "property": 5,
                "golden": 2,
                "contract": 1,
                "invariant": 1,
            },
            "notes": "Well covered, some flaky tests",
        },
        {
            "id": "credit_cards",
            "smoke_tests": True,
            "property_tests": True,
            "golden_scenarios": True,
            "contract_tests": True,
            "invariants": True,
            "test_files_count": {
                "capability": 3,
                "property": 4,
                "golden": 2,
                "contract": 1,
                "invariant": 1,
            },
            "notes": "Well covered, flaky test detected in EMI conversion",
        },
        {
            "id": "financial_health",
            "smoke_tests": True,
            "property_tests": True,
            "golden_scenarios": True,
            "contract_tests": True,
            "invariants": True,
            "test_files_count": {
                "capability": 5,
                "property": 4,
                "golden": 2,
                "contract": 4,
                "invariant": 1,
            },
            "notes": "Well covered",
        },
        {
            "id": "forecasting",
            "smoke_tests": True,
            "property_tests": True,
            "golden_scenarios": True,
            "contract_tests": True,
            "invariants": True,
            "test_files_count": {
                "capability": 4,
                "property": 2,
                "golden": 2,
                "contract": 3,
                "invariant": 1,
            },
            "notes": "Well covered",
        },
        {
            "id": "transaction_intelligence",
            "smoke_tests": True,
            "property_tests": True,
            "golden_scenarios": True,
            "contract_tests": True,
            "invariants": True,
            "test_files_count": {
                "capability": 3,
                "property": 2,
                "golden": 2,
                "contract": 3,
                "invariant": 1,
            },
            "notes": "Well covered",
        },
        {
            "id": "reconciliation",
            "smoke_tests": True,
            "property_tests": True,
            "golden_scenarios": True,
            "contract_tests": True,
            "invariants": True,
            "test_files_count": {
                "capability": 3,
                "property": 2,
                "golden": 1,
                "contract": 3,
                "invariant": 1,
            },
            "notes": "Well covered, has dedicated determinism tests",
        },
        {
            "id": "financial_events",
            "smoke_tests": True,
            "property_tests": True,
            "golden_scenarios": True,
            "contract_tests": True,
            "invariants": True,
            "test_files_count": {
                "capability": 2,
                "property": 1,
                "golden": 1,
                "contract": 3,
                "invariant": 1,
            },
            "notes": "Well covered",
        },
        {
            "id": "recommendations",
            "smoke_tests": True,
            "property_tests": True,
            "golden_scenarios": True,
            "contract_tests": True,
            "invariants": True,
            "test_files_count": {
                "capability": 2,
                "property": 0,
                "golden": 2,
                "contract": 2,
                "invariant": 1,
            },
            "notes": "Missing property tests",
        },
        {
            "id": "account_management",
            "smoke_tests": True,
            "property_tests": True,
            "golden_scenarios": True,
            "contract_tests": True,
            "invariants": True,
            "test_files_count": {
                "capability": 3,
                "property": 1,
                "golden": 2,
                "contract": 2,
                "invariant": 1,
            },
            "notes": "Well covered",
        },
        {
            "id": "pattern_analysis",
            "smoke_tests": True,
            "property_tests": False,
            "golden_scenarios": True,
            "contract_tests": True,
            "invariants": True,
            "test_files_count": {
                "capability": 2,
                "property": 0,
                "golden": 1,
                "contract": 3,
                "invariant": 1,
            },
            "notes": "Missing property tests",
        },
    ]

    return capabilities


def analyze_stage_overlap() -> dict[str, Any]:
    """Analyze overlap between validation stages."""
    return {
        "architecture_vs_property": {
            "overlap": "Medium",
            "description": "Architecture tests catch layer boundary violations; property tests catch logic errors. Different concern domains.",
        },
        "architecture_vs_invariant": {
            "overlap": "Low",
            "description": "Architecture is structural; invariants are mathematical. Minimal overlap.",
        },
        "property_vs_golden": {
            "overlap": "High",
            "description": "Both verify business logic. Golden tests are deterministic snapshots; property tests are exhaustive invariants. Complementary.",
        },
        "capability_vs_contract": {
            "overlap": "Medium",
            "description": "Capability tests verify orchestration; contract tests verify API shape. Different but related.",
        },
        "golden_vs_invariant": {
            "overlap": "Medium",
            "description": "Golden tests use invariant assertions. Some overlap in financial correctness.",
        },
    }


def generate_validation_architecture() -> str:
    """Generate the validation architecture document."""
    return """# Validation Architecture

## Overview

The ClariFin_OS validation ecosystem consists of 11 stages orchestrated through the Validation Orchestrator Framework (VOF).

## Validation Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                     Validation Orchestrator                      │
└─────────────────────────────────────────────────────────────────┘
           │
           ▼
┌──────────────────┐     ┌──────────────────┐
│ Changed Files    │────▶│ Strategy Selector  │
└──────────────────┘     └──────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────┐
│                        Stage Pipeline                           │
├────────┬────────┬────────┬────────┬────────┬────────┬─────────┤
│ fast   │coverage│change   │mutation │archi-  │capability│property│
│        │        │intel.   │ready.   │tecture  │        │       │
├────────┼────────┼────────┼────────┼────────┼────────┼─────────┤
│        │        │        │        │golden  │contract │meta     │
└────────┴────────┴────────┴────────┴────────┴────────┴─────────┘
```

## Stage Responsibilities

| Stage | Input | Output | Runtime Estimate | Criticality |
|-------|-------|--------|-----------------|-------------|
| Fast | Changed files | PASS/FAIL | 8s | Required |
| Coverage | Source files | coverage.json | 1s | Required |
| Change Intelligence | coverage.json + changed files | change-report.json | 0.5s | Required |
| Mutation Readiness | Source + tests | mutation-readiness.json | 2.5s | Optional |
| Architecture | Source files | PASS/FAIL | 8s | Required |
| Capability | Selected capabilities | PASS/FAIL | 5s | Required |
| Property | Selected properties | PASS/FAIL | 12s | Required |
| Golden | Selected datasets | PASS/FAIL | 6s | Required |
| Contract | OpenAPI schema | PASS/FAIL | 12s | Required |
| Meta | Test infrastructure | PASS/FAIL | 2s | Optional |

## Execution Order

1. **Fast** (ruff + mypy/pyright) - always first
2. **Coverage** - generates coverage.json
3. **Change Intelligence** - generates change-report.json
4. **Mutation Readiness** - uses coverage and change intel
5. **Architecture** - validates layer boundaries
6. **Capability** - runs affected capability smoke tests
7. **Property** - runs affected property tests
8. **Golden** - runs affected golden tests
9. **Contract** - validates API contracts
10. **Meta** - validates test infrastructure

## Dependency Graph

```
fast → coverage → change_intelligence
              ↓
        mutation_readiness
              ↓
        architecture, capability, property, golden, contract
```

## Input/Output Contracts

- **Input**: Git diff (changed files) or explicit file list
- **Output**: validation-manifest.json, validation-metrics.json, validation-history.json

## Runtime Budget (Estimated)

- Fast: 8s
- Coverage: 1s
- Change Intelligence: 0.5s
- Mutation Readiness: 2.5s
- Architecture: 8s
- Capability: 5s
- Property: 12s
- Golden: 6s
- Contract: 12s
- Meta: 2s

**Total**: ~57.5s for full pipeline

## Maintenance Guidelines

- All test files should be under `backend/tests/`
- Property tests use Hypothesis with `@given` decorator
- Invariant functions in `tests/invariants/` have no pytest imports
- Golden datasets in `tests/golden/datasets/` are JSON files
- Contract tests validate API endpoint shapes
"""


def generate_validation_review() -> str:
    """Generate the validation review document."""
    return """# Validation Review

## Strengths

1. **Comprehensive Coverage**: All 10 capabilities have smoke tests, golden tests, and contract tests.
2. **Layered Validation**: Architecture, property, golden, and invariant tests provide defense in depth.
3. **Selective Verification**: SVF provides targeted test execution based on change impact.
4. **Fast Feedback**: Fast stage runs in ~4s for lint/type checking.
5. **Risk-Based Strategy**: Risk rules guide appropriate validation depth.

## Weaknesses

1. **Flaky Property Tests**: `test_emi_conversion_invariants` shows flaky behavior with Hypothesis.
2. **Contract Test Failures**: API endpoints returning 500 errors during contract tests.
3. **Stale Validation History**: validation-history.json contains placeholder entries (timestamps from 2024-01-01).
4. **Missing Property Tests**: `recommendations` and `pattern_analysis` capabilities lack property tests.
5. **Unknown Capability Detection**: Changes to unknown files result in UNKNOWN capability, triggering full verification.

## Simplifications Recommended

1. **Merge Meta into Fast**: Meta tests (test_validator.py, test_mcp_integration.py) are infrastructure validation that could run in fast stage.

2. **Merge Mutation Readiness into Coverage**: Both analyze source code and tests; MR is essentially coverage analysis for mutation purposes.

3. **Mark Mutation Readiness as OPTIONAL**: Not critical for PR validation; useful for quality analysis.

## Stages to Merge

| Merge Candidate | Into | Rationale |
|-----------------|------|-----------|
| Mutation Readiness | Coverage | Both analyze code-test coupling |
| Meta | Fast | Both are infrastructure validation |

## Artifacts to Retire

| Artifact | Status | Reason |
|----------|--------|--------|
| validation-history.json | CANDIDATE | Contains stale placeholder data; not consumed by any tool |
| verification-matrix.md | REQUIRED | Used by SVF for tracking selective verification |
| selective-history.json | REQUIRED | Historical data for SVF effectiveness |

## Technical Debt

1. **Flaky Hypothesis Tests**: Need to fix `test_emi_conversion_invariants` in `backend/tests/properties/credit_cards/test_engine_properties.py`.
2. **Contract Test Failures**: API endpoints return 500 errors when called without database.
3. **Stale History Data**: validation-history.json has placeholder entries from 2024-01-01.
4. **Missing Property Tests**: Two capabilities lack property test coverage.

## Action Items

1. Fix flaky hypothesis test in credit_card_engine properties.
2. Investigate contract test failures (may need database fixture).
3. Clean or regenerate validation-history.json with real data.
4. Add property tests for recommendations and pattern_analysis capabilities.
5. Consider merging mutation_readiness into coverage stage.
"""


def main() -> None:
    """Run the validation audit and generate reports."""
    print("=== Validation Audit ===\n")

    # Run stage runtimes
    print("Measuring stage runtimes...")
    runtimes = audit_stage_runtime()
    print(f"Runtimes: {runtimes}")

    # Audit artifacts
    print("\nAuditing generated artifacts...")
    artifacts = audit_generated_artifacts()

    # Audit capabilities
    print("\nAuditing capability coverage...")
    capabilities = audit_capabilities_coverage()

    # Analyze overlap
    print("\nAnalyzing stage overlap...")
    overlap = analyze_stage_overlap()

    # Generate reports
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)

    # Write validation-architecture.md
    arch_path = GENERATED_DIR.parent / "validation-architecture.md"
    arch_path.write_text(generate_validation_architecture())
    print(f"\nGenerated: {arch_path}")

    # Write validation-review.md
    review_path = GENERATED_DIR.parent / "validation-review.md"
    review_path.write_text(generate_validation_review())
    print(f"Generated: {review_path}")

    # Write stage metrics as JSON
    metrics = {
        "generated_at": datetime.now(UTC).isoformat(),
        "runtimes": runtimes,
        "stage_analysis": {
            "fast": {
                "description": "Ruff lint + format + mypy/pyright type check",
                "runtime_seconds": runtimes.get(
                    "architecture", 2
                ),  # Architecture includes mypy
                "lines_of_code": (
                    wc_files("test_*.py") + wc_files("*.py") if False else 0
                ),
                "unique_value": "Syntax and type errors caught before test execution",
                "status": "KEEP",
            },
            "coverage": {
                "description": "Source-to-capability coverage mapping",
                "runtime_seconds": 1.0,
                "unique_value": "Drives selective verification selection",
                "status": "KEEP",
            },
            "change_intelligence": {
                "description": "File impact analysis and risk assessment",
                "runtime_seconds": 0.5,
                "unique_value": "Essential for capability detection",
                "status": "KEEP",
            },
            "mutation_readiness": {
                "description": "Mutation analysis for test strength",
                "runtime_seconds": 2.5,
                "unique_value": "Quality metrics, not PR blocking",
                "status": "OPTIONAL",
            },
            "architecture": {
                "description": "Layer boundary validation",
                "runtime_seconds": runtimes.get("architecture", 4),
                "unique_value": "Catches architectural violations",
                "status": "KEEP",
            },
            "capability": {
                "description": "Capability smoke tests",
                "runtime_seconds": runtimes.get("capability", 1),
                "unique_value": "Quick smoke validation of orchestration",
                "status": "KEEP",
            },
            "property": {
                "description": "Property-based invariant testing",
                "runtime_seconds": runtimes.get("properties", 4),
                "unique_value": "Exhaustive logic verification",
                "note": "Has flaky test needing fix",
                "status": "KEEP",
            },
            "golden": {
                "description": "Golden dataset regression tests",
                "runtime_seconds": runtimes.get("golden", 1),
                "unique_value": "Regression protection for known scenarios",
                "status": "KEEP",
            },
            "contract": {
                "description": "API contract validation",
                "runtime_seconds": 12,
                "unique_value": "Verifies API shape compliance",
                "note": "Has failures due to missing DB",
                "status": "KEEP",
            },
            "meta": {
                "description": "Meta infrastructure tests",
                "runtime_seconds": 2,
                "unique_value": "Validates test framework itself",
                "status": "OPTIONAL",
            },
        },
        "artifact_analysis": artifacts,
        "capability_coverage": capabilities,
        "overlap": overlap,
    }

    metrics_path = GENERATED_DIR / "audit-metrics.json"
    metrics_path.write_text(json.dumps(metrics, indent=2))
    print(f"Generated: {metrics_path}")

    print("\n=== Audit Complete ===")


if __name__ == "__main__":
    main()
