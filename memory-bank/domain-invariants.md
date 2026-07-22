# Domain Invariants

## Monetary Invariants (QEA-5)

| Invariant | Rule | Test Location |
|-----------|------|---------------|
| Integer paise | All amounts are integers representing paise (₹1 = 100 paise) | `tests/domain/invariants/money.py` |
| No floats | Never use float for currency | `tests/domain/invariants/money.py` |
| Negative valid | Negative paise represents debits/expenses | `tests/domain/invariants/money.py` |

## Confidence Invariants (QEA-6)

| Invariant | Rule | Test Location |
|-----------|------|---------------|
| Integer bps | All confidence values are integers | `tests/domain/invariants/forecast.py` |
| Range 0-10000 | Confidence in basis points, 0-10000 (0-100%) | `tests/domain/invariants/forecast.py` |

## Financial Invariants

| Invariant | Rule | Test Location |
|-----------|------|---------------|
| Surplus | income - expense = surplus (mathematical identity) | `tests/domain/invariants/cashflow.py` |
| Loan principal | Principal monotonically decreases during repayment | `tests/domain/invariants/loan.py` |
| Loan balance | Final balance >= 0 (cannot be negative in healthy loan) | `tests/domain/invariants/loan.py` |
| Forecast confidence | Remains valid (0-10000 bps) | `tests/domain/invariants/forecast.py` |

## ADF Framework Structure

### Directory Layout
```
backend/tests/domain/
├── invariants/          # Pure assertion modules (no pytest imports)
│   ├── __init__.py
│   ├── money.py         # QEA-5: assert_money_invariants()
│   ├── cashflow.py      # INVARIANT 2: income - expense = surplus
│   ├── loan.py          # INVARIANT 3-5: principal decreases, balances valid
│   ├── forecast.py      # INVARIANT 6: confidence in bps range
│   ├── credit.py        # Utilization, EMI validations
│   └── statement.py     # Statement integrity checks
├── generators/          # Plain Python primitive generators
│   ├── __init__.py
│   └── primitives.py    # paise(), confidence_bps(), iso_date()
└── builders/            # Plain Python builders (Hypothesis-agnostic)
    ├── __init__.py
    ├── household.py
    ├── account.py
    ├── transaction.py
    ├── loan.py
    └── statement.py
```

### Hypothesis Profiles
- **fast**: 20 examples (developer iteration)
- **normal**: 150 examples (CI)
- **deep**: 1000 examples (nightly)

Control via `HYPOTHESIS_PROFILE` environment variable.

## Implementation Notes

- All invariant functions use `dict[str, Any]` type hints
- Property tests use Hypothesis `@given` decorator
- Builders are plain Python - can be used with or without Hypothesis
- Runtime assertion validation, not static type checking