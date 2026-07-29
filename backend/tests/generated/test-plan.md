# Recommended Verification Plan

Generated: 2026-07-28T03:59:18.187956+00:00

## Stage 1: Lint & Type Check

```bash
scripts/verify-fast.sh
```

## Stage 2: Architecture Tests

```bash
pytest tests/architecture -q --tb=short
```

## Stage 3: Capability Smoke Tests (Affected)

- ✓ pytest tests/capability/account_management -q
- ✓ pytest tests/capability/debt_management -q
- ✓ pytest tests/capability/household_cashflow -q
- ✓ pytest tests/capability/pattern_analysis -q
- ✓ pytest tests/capability/reconciliation -q
- ✓ pytest tests/capability/transaction_intelligence -q

## Stage 4: Property Tests (Affected)

- ✓ tests/properties/cashflow
- ✓ tests/properties/lending
- ✓ tests/properties/reconciliation

## Stage 5: Golden Tests (Affected)

```bash
pytest tests/golden -k 'family_household,high_debt_household,multiple_loans,normal_household,salary_only' -q --tb=short
```
