# ClariFin Loan Engine - Active Context

## Summary of Recent Changes (2026-11-07)

### Refactor: Loan Engine Pure Calculation Library
- Removed out-of-scope modules from `src/engines/loan_engine/`:
  - `health_scorer.py` - removed (out of scope)
  - `tax_calculator.py` - removed (out of scope)
  - `refinance_evaluator.py` - removed (out of scope)
  - `comparison_engine.py` - removed (out of scope)
  - `payoff_strategies.py` - removed (out of scope)
- Deleted legacy files:
  - `emi_calculator.py` → consolidated into `emi.py`
  - `amortization_builder.py` → consolidated into `amortization.py`
  - `dynamic_prepayment_engine.py` → merged into `prepayment.py`
  - `prepayment_analyzer.py` → merged into `prepayment.py`
- Updated `loan_service.py` to remove `evaluate_refinance` and `compute_health_score` methods
- Updated `loans.py` router to remove `/api/loans/{loan_id}/health` endpoint
- Updated `__init__.py` to import only from `models.py` (not `types.py`)
- Updated test file to only test in-scope functionality (prepayment, amortization, floating rate)
- All 15 tests pass

### Core Modules Retained (Pure Calculation)
- `emi.py` - EMI calculations
- `amortization.py` - Schedule generation
- `prepayment.py` - Prepayment simulation (merged dynamic + analyzer logic)
- `floating_rate.py` - Floating rate adjustments
- `foreclosure.py` - Foreclosure calculations
- `metrics.py` - Loan metrics
- `models.py` - Core data types (AmortizationRow, PrepaymentResult, etc.)
- `types.py` - Kept for backward compatibility (marked deprecated)

## Next Immediate Steps
1. Frontend build verification: `cd frontend && npm run type-check && npm run lint`
2. Run full backend test suite for regression check

## Financial Invariants Maintained
- All monetary values in paise (integer)
- All interest rates in basis points (integer)
- Banker's rounding (ROUND_HALF_EVEN)
- Immutable schedules (never modified in-place)
- ISO 8601 date format