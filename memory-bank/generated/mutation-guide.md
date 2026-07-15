# Mutation Testing Guide

This guide documents the Reliability & Mutation Validation Framework (RMVF) and how to interpret its outputs.

## Overview

The RMVF provides analysis and readiness assessment for mutation testing without executing actual mutations. It produces actionable reports that indicate:

- Which functions are pure and safe for mutation testing
- Which engines have strong test coverage to catch mutations
- Which capabilities have validation gaps

## Supported Mutation Types

These are the mutation categories the framework analyzes:

| Category | Description | Example Patterns |
|----------|-------------|----------------|
| Arithmetic | Mathematical operations | `+`, `-`, `*`, `/` |
| Comparison | Equality and ordering | `==`, `!=`, `<`, `>`, `<=`, `>=` |
| Boolean | Logical operators | `and`, `or`, `not` |
| Constant replacement | Numeric literals | `0`, `1`, `42` → `_`, `_+1`, `_-1` |
| Boundary conditions | Loop and range checks | `range()`, `len()`, bounds |
| Off-by-one | Increment/decrement errors | `i+1`, `i-1`, `i+=1` |
| Loop termination | For/while loop mutations | Loop exit conditions |
| Sign inversion | Negation errors | `-1`, `negate`, `inverse` |

## Excluded Mutation Types (Future)

These types are recognized but not yet implemented:

| Category | Reason for Exclusion |
|----------|---------------------|
| Dead code elimination | Requires full mutation execution |
| Exception raising | Side effects make detection complex |
| Decorator mutation | Property testing needed for coverage |
| Import mutation | Pure AST analysis insufficient |

## Readiness Scores

### Engine Readiness Status

- **Ready**: All functions are pure with no blockers. Safe for mutation testing.
- **Partial**: Mix of pure and impure functions. Limited mutation candidates.
- **Blocked**: Impure functions prevent safe mutation testing.

### Killability Estimates

| Level | Meaning |
|-------|---------|
| HIGH | Strong test coverage (property + golden tests) likely to catch mutations |
| MEDIUM | Some coverage, may miss edge cases |
| LOW | Weak coverage, mutations may survive |
| UNKNOWN | Unable to determine (no functions or analysis incomplete) |

### Test Strength Scores

Weighted scoring based on evidence types:

| Evidence Type | Weight | Purpose |
|---------------|--------|---------|
| Property tests | 5 | Catch edge cases and invariants |
| Golden tests | 5 | Regression protection |
| Contract tests | 4 | API correctness |
| Capability Smoke | 3 | Integration verification |
| Invariants | 3 | Domain rule enforcement |
| Performance | 2 | Performance regression detection |
| Architecture | 2 | Layer boundary compliance |

| Score Range | Strength | Description |
|-------------|----------|-------------|
| 12+ | Critical | Well protected against regressions |
| 8-11 | Strong | Good coverage, minor gaps |
| 4-7 | Moderate | Some coverage, notable gaps |
| 0-3 | Weak | Minimal or no validation evidence |

## Integration with Mutation Engines

The framework is designed for future integration with real mutation testing tools:

### Mutmut Adapter (Future)

```python
# Future adapter pattern
class MutmutAdapter(MutationProvider):
    def discover(self) -> list[FunctionAnalysis]:
        # Use RMVF's existing discovery
        return discovery.get_all_functions()

    def analyze(self, functions: list[FunctionAnalysis]) -> list[KilledMutation]:
        # Run mutmut on pure functions
        pass
```

### Cosmic-Ray Adapter (Future)

```python
class CosmicRayAdapter(MutationProvider):
    def discover(self) -> list[FunctionAnalysis]:
        # Use RMVF's existing discovery
        pass

    def report(self) -> str:
        # Generate cosmic-ray style report
        pass
```

### Mutatest Adapter (Future)

Similar adapter pattern for mutatest.

## Interpreting Reports

### mutation-registry.json

JSON registry containing:
- Module paths
- Capability associations
- Mutation type classifications
- Existing test references (smoke, property, golden)

### mutation-readiness.json

Machine-readable engine readiness:
- Pure/impure function counts
- Per-engine readiness status
- Killability estimates

### mutation-readiness.md

Human-readable summary with tables.

### mutation-gaps.md

Actionable report showing:
- Missing test types per engine
- Impure function blockers
- Capability coverage gaps

### test-strength.json / test-strength.md

Capability-level validation strength:
- Weighted scores
- Evidence breakdown
- Gap identification

## Running the Framework

```bash
# Generate all mutation analysis reports
python backend/tools/mutation_discovery.py

# Generate test strength reports
python backend/tools/test_strength.py

# Run as validation stage (full pipeline)
python backend/tools/validation_orchestrator.py --plan

# Full execution with all stages including mutation readiness
python backend/tools/validation_orchestrator.py --full
```

## Architecture Decisions

### Purity Determined by AST Analysis

Not docstrings. Functions are classified as impure if they:
- Import sqlite3, requests, httpx (database/network)
- Use random, uuid, datetime.now (non-determinism)
- Use filesystem operations (open, pathlib, os)
- Use subprocess, threading (external control)

This ensures objectivity and prevents false positives.

### Reports Only, No Mutations

The framework intentionally generates reports only:
- No source code mutation
- No test execution modification
- No risk to production code

This makes it safe to run during CI/CD.

## Adding New Capabilities

1. Add capability manifest in `memory-bank/capabilities/`
2. Run `check_coverage.py` to generate registry
3. Run `mutation_discovery.py` to analyze purity
4. Review `mutation-gaps.md` for action items
5. Add property tests to improve killability