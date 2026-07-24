# Validation Strength Report

Generated: 2026-07-24T03:15:34.121743+00:00

## Strength Classification

| Capability | Criticality | Strength | Score | Evidence | Gaps |
|------------|-------------|----------|-------|----------|------|

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