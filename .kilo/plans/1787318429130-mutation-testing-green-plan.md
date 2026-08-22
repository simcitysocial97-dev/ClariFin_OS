# Mutation Testing Green Plan

## Problem
Mutation testing workflow fails because mutation score is below 80% threshold. The CI correctly detects gaps in test effectiveness.

## Root Cause Analysis Needed
1. Run mutation testing locally to identify surviving mutants
2. Map surviving mutants to specific engine modules
3. Add targeted tests to kill mutants

## Plan Steps

### 1. Local Mutation Analysis
```bash
cd backend && python3 -m mutmut run --paths-to-mutate=src/engines/
python3 -m mutmut results
python3 -m mutmut show
```
- Identify which mutants survive
- Group by engine module
- Categorize by mutation type (conditionals, arithmetic, etc.)

### 2. Test Coverage Gap Analysis
For each surviving mutant:
- Locate the mutated code
- Identify missing test scenarios
- Add tests in `tests/unit/engines/<engine>/` or `tests/properties/`

### 3. Common Mutation Patterns to Address
- **Condition boundary mutations**: Add tests for edge cases (0, 1, negative, empty)
- **Arithmetic mutations**: Test with boundary values, overflow scenarios
- **Return value mutations**: Verify actual return values, not just side effects
- **Exception mutations**: Test error paths and exception handling

### 4. Engine-Specific Focus Areas
Based on mutmut config (`source_paths = ["src/engines/"]`), prioritize:
- `loan_engine/` - likely complex interest calculations
- `credit_card_engine/` - fee/interest logic
- `cashflow_engine.py` - balance projections
- `financial_intelligence/` - scoring algorithms
- `reconciliation_engine.py` - matching logic

### 5. Implementation Strategy
- Add tests incrementally, re-run mutation after each batch
- Focus on highest-impact surviving mutants first
- Use property-based tests for mathematical invariants

### 6. Validation
```bash
cd backend && python3 -m mutmut run
python3 -m mutmut results  # Should show score >= 80%
```

## Out of Scope
- Lowering threshold (enterprise standard: 80%)
- Modifying mutmut config to reduce scope
- Skipping mutation testing in CI