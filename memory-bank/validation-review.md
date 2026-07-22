# Validation Review

## Strengths

1. **Comprehensive Coverage**: All 10 capabilities have smoke tests, golden tests, and contract tests.
2. **Layered Validation**: Architecture, property, golden, and invariant tests provide defense in depth.
3. **Selective Verification**: SVF provides targeted test execution based on change impact.
4. **Fast Feedback**: Fast stage runs in ~4s for lint/type checking.
5. **Risk-Based Strategy**: Risk rules guide appropriate validation depth.

## Weaknesses

1. **Flaky Property Tests**: `test_emi_conversion_invariants` shows flaky behavior with Hypothesis.
2. **Contract Test Failures**: API endpoints returning 500 errors during contract tests.
3. **Stale Validation History**: validation-history.json contains placeholder entries (timestamps from 2024-01-01).
4. **Missing Property Tests**: `recommendations` and `pattern_analysis` capabilities lack property tests.
5. **Unknown Capability Detection**: Changes to unknown files result in UNKNOWN capability, triggering full verification.

## Simplifications Recommended

1. **Merge Meta into Fast**: Meta tests (test_validator.py, test_mcp_integration.py) are infrastructure validation that could run in fast stage.

2. **Merge Mutation Readiness into Coverage**: Both analyze source code and tests; MR is essentially coverage analysis for mutation purposes.

3. **Mark Mutation Readiness as OPTIONAL**: Not critical for PR validation; useful for quality analysis.

## Stages to Merge

| Merge Candidate | Into | Rationale |
|-----------------|------|-----------|
| Mutation Readiness | Coverage | Both analyze code-test coupling |
| Meta | Fast | Both are infrastructure validation |

## Artifacts to Retire

| Artifact | Status | Reason |
|----------|--------|--------|
| validation-history.json | CANDIDATE | Contains stale placeholder data; not consumed by any tool |
| verification-matrix.md | REQUIRED | Used by SVF for tracking selective verification |
| selective-history.json | REQUIRED | Historical data for SVF effectiveness |

## Technical Debt

1. **Flaky Hypothesis Tests**: Need to fix `test_emi_conversion_invariants` in `backend/tests/properties/credit_cards/test_engine_properties.py`.
2. **Contract Test Failures**: API endpoints return 500 errors when called without database.
3. **Stale History Data**: validation-history.json has placeholder entries from 2024-01-01.
4. **Missing Property Tests**: Two capabilities lack property test coverage.

## Action Items

1. Fix flaky hypothesis test in credit_card_engine properties.
2. Investigate contract test failures (may need database fixture).
3. Clean or regenerate validation-history.json with real data.
4. Add property tests for recommendations and pattern_analysis capabilities.
5. Consider merging mutation_readiness into coverage stage.
