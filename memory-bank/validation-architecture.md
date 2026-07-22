# Validation Architecture

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
