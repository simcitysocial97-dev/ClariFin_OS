# Recommended Verification Plan

Generated: 2026-07-25T11:24:13.859845+00:00

## Stage 1: Lint & Type Check

```bash
scripts/verify-fast.sh
```

## Stage 2: Architecture Tests

```bash
pytest tests/architecture -q --tb=short
```

## Stage 3: Capability Smoke Tests (Affected)

- ✓ pytest tests/capabilities/household_cashflow -q

## Stage 4: Property Tests (Affected)

- ✓ tests/properties/cashflow

## Stage 5: Golden Tests (Affected)

```bash
pytest tests/golden -k 'family_household,normal_household,salary_only,salary_plus_loan' -q --tb=short
```
