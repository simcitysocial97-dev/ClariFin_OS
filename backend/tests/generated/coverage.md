# Coverage Report

Generated automatically by `tools/development/check_coverage.py`.
System capabilities are canonical (`verification.yaml`); real evidence
is discovered from `engine-topology.json` and `backend/tests/capability/*`.

## Capability Coverage Matrix

| Capability | Status | Structural | Validation | Documentation | Overall |
|------------|--------|------------|------------|---------------|---------|
| API Contracts (`api-contracts`) | MODULE_MAPPED_NO_ENGINE | NONE | NONE | ✗ | NONE |
| End-to-End Tests (`e2e-tests`) | WORKFLOW_ONLY | NONE | NONE | ✗ | NONE |
| Golden Regression (`golden-regression`) | WORKFLOW_ONLY | NONE | NONE | ✗ | NONE |
| Ledger Service (`ledger`) | MAPPED | ✓ | NONE | ✗ | ✗ |
| Loan Engine (`loan-engine`) | MAPPED | ✓ | ✓ | ✗ | ✗ |
| Database Migrations (`migrations`) | WORKFLOW_ONLY | NONE | NONE | ✗ | NONE |
| Mutation Analysis (`mutation-analysis`) | WORKFLOW_ONLY | NONE | NONE | ✗ | NONE |
| Reconciliation Engine (`reconciliation`) | MAPPED | ✓ | ✓ | ✗ | ✗ |
| Runtime Verification (`runtime-verification`) | WORKFLOW_ONLY | NONE | NONE | ✗ | NONE |

## Status Legend

| Status | Meaning |
|--------|---------|
| MAPPED | Engine + implementation + tests discovered |
| MAPPED_NO_TESTS | Engine + implementation discovered, no tests |
| MODULE_MAPPED_NO_ENGINE | Module dir exists, no engine topology |
| WORKFLOW_ONLY | Defined by workflow, no engine mapping |
| UNMAPPED | No discoverable evidence |

## Maturity Legend

| Symbol | Meaning |
|--------|---------|
| ✓ | Complete coverage |
| PARTIAL | Partial coverage |
| ✗ | Missing coverage |
| NONE | No coverage |