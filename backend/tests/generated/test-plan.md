# Recommended Verification Plan

Generated: 2026-07-29T17:42:18.309528+00:00

## Stage 1: Lint & Type Check

```bash
scripts/verify-fast.sh
```

## Stage 2: Architecture Tests

```bash
pytest tests/architecture -q --tb=short
```

## Stage 3: Capability Smoke Tests (Affected)

- ✓ pytest tests/capability/credit_cards -q
- ✓ pytest tests/capability/debt_management -q
- ✓ pytest tests/capability/financial_events -q
- ✓ pytest tests/capability/pattern_analysis -q
- ✓ pytest tests/capability/transaction_intelligence -q

## Stage 4: Property Tests (Affected)

- ✓ tests/properties/credit_card_engine
- ✓ tests/properties/credit_cards
- ✓ tests/properties/lending

## Stage 5: Golden Tests (Affected)

```bash
pytest tests/golden -k 'cash_advance,cc_statement_scenario,credit_card_revolver,high_debt_household,multiple_loans' -q --tb=short
```
