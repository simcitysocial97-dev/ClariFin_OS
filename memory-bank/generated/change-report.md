# Change Impact Report

Generated: 2026-07-15T14:08:32.011634+00:00

## Summary

| File | Risk | Capabilities | Confidence |
|------|------|--------------|------------|
| `backend/src/engines/cashflow_engine.py` | CRITICAL | household_cashflow | HIGH |

## Detailed Analysis

### Changed: `backend/src/engines/cashflow_engine.py`

**Risk:** CRITICAL

**Confidence:** HIGH

**Affected Capabilities:**

- `household_cashflow`

**Affected Tests:**

  - Capability Smoke Tests:
    - `tests/capabilities/household_cashflow`
  - Property Tests:
    - `tests/properties`
    - `tests/properties/cashflow`
  - Golden Datasets:
    - `family_household`
    - `normal_household`
    - `salary_only`
    - `salary_plus_loan`
  - Invariants:
    - `tests/invariants/test_cashflow.py`

**Recommended Verification:**
```bash
pytest tests/capabilities/household_cashflow -q
pytest tests/properties -q
pytest tests/properties/cashflow -q
pytest tests/golden -k 'family_household,normal_household,salary_only' -q
```

## Overall Assessment

**Risk Level:** CRITICAL

**Risk Score:** 8
