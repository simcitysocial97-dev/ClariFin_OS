# Validation Strength Report

Generated: 2026-07-26T14:24:05.131914+00:00

## Strength Classification

| Capability | Criticality | Strength | Score | Evidence | Gaps |
|------------|-------------|----------|-------|----------|------|
| Account Management | high | Critical | 18 | property(2), golden(3), smoke(1), invariants(1) | No contract tests, No performance baseline |
| Credit Cards | high | Critical | 18 | property(1), golden(3), smoke(1), invariants(1) | No contract tests, No performance baseline |
| Debt Management | high | Critical | 18 | property(1), golden(3), smoke(1), invariants(1) | No contract tests, No performance baseline |
| Financial Health | high | Critical | 18 | property(1), golden(3), smoke(1), invariants(1) | No contract tests, No performance baseline |
| Household Cashflow | high | Critical | 18 | property(1), golden(4), smoke(1), invariants(1) | No contract tests, No performance baseline |
| Reconciliation | high | Critical | 18 | property(2), golden(2), smoke(1), invariants(1) | No contract tests, No performance baseline |
| Transaction Intelligence | high | Critical | 18 | property(1), golden(3), smoke(1), invariants(2) | No contract tests, No performance baseline |
| Financial Events | medium | Critical | 13 | golden(2), smoke(1), invariants(1) | No property tests, No contract tests, No performance baseline |
| Forecasting | medium | Critical | 18 | property(1), golden(3), smoke(1), invariants(1) | No contract tests, No performance baseline |
| Pattern Analysis | medium | Critical | 18 | property(1), golden(2), smoke(1), invariants(1) | No contract tests, No performance baseline |
| Recommendations | medium | Critical | 18 | property(1), golden(3), smoke(1), invariants(1) | No contract tests, No performance baseline |

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