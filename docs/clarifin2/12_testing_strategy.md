# Testing Strategy - ClariFinOS 2.0

*Comprehensive test approach for all engines*

---

## Testing Philosophy

### Determinism First
Every test must be repeatable with same inputs. Tests run in parallel with no shared state.

### Financial Accuracy
All monetary calculations must be validated against known formulas and edge cases.

### Integration Coverage
Each engine must integrate correctly with:
- Transaction repository
- Other engines
- API layer
- External services (LLM)

---

## Test Categories

### Unit Tests (60% of tests)
Pure function testing for all financial models.

### Integration Tests (30% of tests)
Cross-engine workflows and database operations.

### End-to-End Tests (10% of tests)
Full user flows from import to dashboard.

---

## Account Engine Tests

### Unit Tests
```
test_health_score_activity() - Test activity scoring formula
test_health_score_balance() - Test balance scoring tiers
test_cash_flow_calculation() - Test net flow and velocity
test_dormant_detection() - Test 12-month threshold
test_account_types() - Test all supported types
```

### Integration Tests
```
test_account_creation_flow() - Create account, verify schema
test_balance_history_insertion() - Insert 90 days, query correctly
test_link_account_relationships() - Link 2 accounts, verify flow
test_institution_metadata() - Create institution, link accounts
```

---

## Reconciliation Engine Tests

### Unit Tests
```
test_exact_match_confidence() - Same amount, same date = 1.0
test_window_match_confidence() - Date diff affects score
test_description_similarity() - UPI keywords trigger bonus
test_confidence_capping() - Never exceeds 1.0
test_deterministic_key() - Same inputs = same key
```

### Integration Tests
```
test_full_scan_accuracy() - 100 transactions, verify matches
test_inter_bank_matching() - HDFC to ICICI transfer
test_credit_card_payment_match() - Bank to card payment
test_loan_payment_match() - Checking to loan payment
test_split_transaction_workflow() - Multi-leg reconciliation
```

---

## Loan Engine Tests

### Unit Tests
```
test_emi_fixed_rate() - Standard EMI calculation
test_emi_zero_rate() - Zero interest edge case
test_amortization_schedule() - Month-by-month breakdown
test_prepayment_reduce_tenure() - Tenure reduction impact
test_prepayment_reduce_emi() - EMI reduction impact
test_refinance_break_even() - Cost vs savings calculation
test_floating_rate_reset() - Rate change affects EMI
```

### Integration Tests
```
test_loan_lifecycle() - Create, add payment, verify schedule
test_multiple_loans_dti() - Combined DTI calculation
test_prepayment_scenario_save() - Create and retrieve scenario
test_loan_health_components() - All factors aggregated
```

---

## Credit Card Engine Tests

### Unit Tests
```
test_utilization_calculation() - Credit limit vs outstanding
test_interest_daily() - Daily rate applied correctly
test_payment_optimization_full() - Payment covers outstanding
test_payment_optimization_min() - Minimum payment path
test_subscription_detection_monthly() - Recurring pattern identified
test_reward_calculation_point() - Points earned per spend
```

### Integration Tests
```
test_credit_card_monthly_cycle() - Statement generation
test_multi_card_utilization() - Combined utilization
test_payment_matching() - Bank payment to credit card
test_subscription_annual_cost() - Total yearly subscription spend
```

---

## Behaviour Engine Tests

### Unit Tests
```
test_savings_discipline_formula() - Surplus ratio calculation
test_cashflow_stability_index() - Income variance scoring
test_impulse_detection_time() - Night hours flagged
test_impulse_detection_day() - Weekend spending flagged
test_lifestyle_inflation_yoy() - Year over year growth
test_resilience_index() - Buffer months calculation
```

### Integration Tests
```
test_monthly_score_trend() - Scores change appropriately
test_alert_trigger_thresholds() - Warnings fire at limits
test_recommendation_generation() - Rules produce advice
test_wellness_score_aggregation() - All factors combined
```

---

## Financial Model Tests

### Golden Master Tests
```
EMI_Golden_Test_Cases:
- ₹10L @ 8.5% for 20 years = ₹87,996/month
- ₹50L @ 9.0% for 15 years = ₹497,000/month
- ₹5L @ 0% for 5 years = ₹83,333/month

Verify against:
- bank calculators
- Excel functions
- Industry standards
```

### Edge Case Tests
```
test_negative_amortization() - Higher interest than principal
test_rounding_errors() - Paise precision maintained
test_large_numbers() - 100M+ values handled
test_small_values() - Sub-rupee precision
```

---

## LLM Layer Tests

### Mock Tests (No Real LLM)
```
test_explanation_prompt_format() - Prompt correctly structured
test_cache_key_generation() - Hash consistent
test_response_formatting() - JSON parsing
test_fallback_on_llm_error() - Graceful degradation
```

### Integration Tests (With Local LLM)
```
test_explanation_generation() - Real LLM produces text
test_receipt_parsing() - Image to structured data
test_qa_accuracy() - Answers match data
```

---

## Database Tests

### Migration Tests
```
test_schema_migration_safety() - Backward compatible
test_new_columns_nullable() - Existing data not broken
test_fk_constraints_active() - Relationships enforced
```

### Performance Tests
```
test_query_1000_transactions() - < 50ms
test_insert_performance() - 1000 rows < 1s
test_concurrent_access() - No deadlocks
```

---

## Test Data Strategy

### Synthetic Dataset Generator
```python
def generate_test_data():
    """
    Generates realistic test data:
    - 2 years transactions
    - 5 accounts (salary, savings, checking, credit, wallet)
    - 3 loans (home, personal, vehicle)
    - 2 credit cards
    - Known reconciliation matches
    """
```

### Fixtures
- `test_accounts.json` - Sample account data
- `test_loans.json` - Sample loan with EMIs
- `test_transactions.csv` - Import-ready transactions
- `test_credit_statements.csv` - Card statement data

---

## Test Execution Matrix

| Test Type | Tools | Frequency |
|-----------|-------|-----------|
| Unit Tests | pytest | Every commit |
| Integration | pytest | Every PR |
| E2E Tests | Playwright | Nightly |
| LLM Tests | Local model | Weekly |
| Performance | pytest-benchmark | Weekly |

---

## Coverage Targets

| Component | Target |
|-----------|--------|
| Engines | 90%+ |
| Models | 95%+ |
| API Layer | 80%+ |
| Database | 85%+ |
| LLM Layer | 60%+ |

---

## Acceptance Testing

### User Story Tests
```
As a user, I want to understand my loans:
- [ ] Can view amortization schedule
- [ ] Can simulate prepayment
- [ ] Receive refinance recommendation
- [ ] Get health score breakdown
```

### Regression Tests
- Every bug fix gets a test
- Every formula change gets golden master verification
- Every API change gets integration test