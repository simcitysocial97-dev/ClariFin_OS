# Traceability Matrix

Generated automatically. Shows the discovered dependency chain for each canonical capability.

## API Contracts (`api-contracts`)

**Status:** MODULE_MAPPED_NO_ENGINE
**Owning engines:** none
**Test count:** 0

### Dependency Chain

| Layer | Artifact | Status |
|-------|----------|--------|

## End-to-End Tests (`e2e-tests`)

**Status:** WORKFLOW_ONLY
**Owning engines:** none
**Test count:** 0

### Dependency Chain

| Layer | Artifact | Status |
|-------|----------|--------|

## Golden Regression (`golden-regression`)

**Status:** WORKFLOW_ONLY
**Owning engines:** none
**Test count:** 0

### Dependency Chain

| Layer | Artifact | Status |
|-------|----------|--------|

## Ledger Service (`ledger`)

**Status:** MAPPED
**Owning engines:** ledger_audit_engine
**Test count:** 1

### Dependency Chain

| Layer | Artifact | Status |
|-------|----------|--------|
| Router | `src/routers/audit.py` | ✓ |
| Service | `src/services/audit_service.py` | ✓ |
| Engine | `src/engines/ledger_audit_engine.py` | ✓ |

## Loan Engine (`loan-engine`)

**Status:** MAPPED
**Owning engines:** loan_engine
**Test count:** 9

### Dependency Chain

| Layer | Artifact | Status |
|-------|----------|--------|
| Router | `src/routers/loans.py` | ✓ |
| Service | `src/services/loan_analysis_service.py` | ✓ |
| Service | `src/services/loan_service.py` | ✓ |
| Service | `src/services/loan_simulation_service.py` | ✓ |
| Service | `src/services/transaction_intelligence_service.py` | ✓ |
| Engine | `src/engines/loan_engine/amortization.py` | ✓ |
| Engine | `src/engines/loan_engine/emi.py` | ✓ |
| Engine | `src/engines/loan_engine/floating_rate.py` | ✓ |
| Engine | `src/engines/loan_engine/foreclosure.py` | ✓ |
| Engine | `src/engines/loan_engine/metrics.py` | ✓ |
| Engine | `src/engines/loan_engine/models.py` | ✓ |
| Engine | `src/engines/loan_engine/prepayment.py` | ✓ |
| Engine | `src/engines/loan_engine/utils.py` | ✓ |
| Repository | `src/repositories/account_repository.py` | ✓ |
| Repository | `src/repositories/credit_card_repository.py` | ✓ |
| Repository | `src/repositories/financial_event_repository.py` | ✓ |
| Repository | `src/repositories/liquidity_pattern_repository.py` | ✓ |
| Repository | `src/repositories/loan_payment_repository.py` | ✓ |
| Repository | `src/repositories/loan_repository.py` | ✓ |
| Repository | `src/repositories/statement_repository.py` | ✓ |
| Repository | `src/repositories/transaction_classification_repository.py` | ✓ |
| Repository | `src/repositories/transaction_repository.py` | ✓ |
| Property Test | `tests/properties/lending/test_engine_properties.py` | ✓ |
| Property Test | `tests/properties/loan_engine/test_amortization_properties.py` | ✓ |
| Property Test | `tests/properties/loan_engine/test_emi_properties.py` | ✓ |
| Property Test | `tests/properties/loan_engine/test_floating_rate_properties.py` | ✓ |
| Property Test | `tests/properties/loan_engine/test_foreclosure_properties.py` | ✓ |
| Property Test | `tests/properties/loan_engine/test_metrics_properties.py` | ✓ |
| Property Test | `tests/properties/loan_engine/test_prepayment_properties.py` | ✓ |

## Database Migrations (`migrations`)

**Status:** WORKFLOW_ONLY
**Owning engines:** none
**Test count:** 0

### Dependency Chain

| Layer | Artifact | Status |
|-------|----------|--------|

## Mutation Analysis (`mutation-analysis`)

**Status:** WORKFLOW_ONLY
**Owning engines:** none
**Test count:** 0

### Dependency Chain

| Layer | Artifact | Status |
|-------|----------|--------|

## Reconciliation Engine (`reconciliation`)

**Status:** MAPPED
**Owning engines:** reconciliation_engine
**Test count:** 4

### Dependency Chain

| Layer | Artifact | Status |
|-------|----------|--------|
| Router | `src/routers/reconciliation.py` | ✓ |
| Service | `src/services/reconciliation_service.py` | ✓ |
| Engine | `src/engines/reconciliation_engine.py` | ✓ |
| Repository | `src/repositories/reconciliation_repository.py` | ✓ |
| Property Test | `tests/properties/reconciliation/test_engine_properties.py` | ✓ |
| Invariant | `tests/invariants/test_reconciliation_determinism.py` | ✓ |
| Invariant | `tests/invariants/test_reconciliation_properties.py` | ✓ |

## Runtime Verification (`runtime-verification`)

**Status:** WORKFLOW_ONLY
**Owning engines:** none
**Test count:** 0

### Dependency Chain

| Layer | Artifact | Status |
|-------|----------|--------|
