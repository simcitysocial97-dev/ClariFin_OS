# Validation Strength Report

Generated: 2026-07-31T06:03:51.770197+00:00

## Strength Classification

| Capability | Criticality | Strength | Score | Evidence | Gaps |
|------------|-------------|----------|-------|----------|------|
| Account Management | high | Critical | 20 | property(2), golden(3), smoke(1), invariants(1) | No contract tests |
| Credit Cards | high | Critical | 20 | property(4), golden(3), smoke(1), invariants(1) | No contract tests |
| Debt Management | high | Critical | 20 | property(1), golden(3), smoke(1), invariants(1) | No contract tests |
| Financial Health | high | Critical | 20 | property(2), golden(3), smoke(1), invariants(1) | No contract tests |
| Household Cashflow | high | Critical | 20 | property(1), golden(4), smoke(1), invariants(1) | No contract tests |
| Reconciliation | high | Critical | 20 | property(2), golden(2), smoke(1), invariants(2) | No contract tests |
| Transaction Intelligence | high | Critical | 20 | property(1), golden(3), smoke(1), invariants(2) | No contract tests |
| Verification | high | Moderate | 7 | smoke(3) | No property tests, No golden tests, No contract tests, No invariant tests |
| Financial Events | medium | Critical | 20 | property(2), golden(2), smoke(2), invariants(1) | No contract tests |
| Forecasting | medium | Critical | 20 | property(1), golden(3), smoke(1), invariants(1) | No contract tests |
| Pattern Analysis | medium | Critical | 20 | property(1), golden(2), smoke(1), invariants(1) | No contract tests |
| Recommendations | medium | Critical | 20 | property(1), golden(3), smoke(1), invariants(1) | No contract tests |

## Scoring Legend

| Score Range | Strength | Description |
|-------------|----------|-------------|
| 12+ | Critical | Well protected against regressions |
| 8-11 | Strong | Good coverage, minor gaps |
| 4-7 | Moderate | Some coverage, notable gaps |
| 0-3 | Weak | Minimal or no validation evidence |

## Evidence Weights

| Evidence Type | Weight | Purpose |
|---------------|--------|---------|
| Property tests | 5 | Catch edge cases and invariants |
| Golden tests | 5 | Regression protection |
| Contract tests | 4 | API correctness |
| Capability Smoke | 3 | Integration verification |
| Invariants | 3 | Domain rule enforcement |
| Performance | 2 | Performance regression detection |
| Architecture | 2 | Layer boundary compliance |