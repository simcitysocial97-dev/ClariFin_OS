# Implementation Roadmap - ClariFinOS 2.0

*Milestone-based development plan*

---

## Milestone 1: Foundation (Weeks 1-4)

### Objectives
- Extend database schema for ClariFinOS 2.0
- Implement core deterministic models
- Set up LLM infrastructure

### Files Affected
- `backend/src/db.py` - Add new tables/columns
- `backend/src/engines/loan_engine.py` - Extended EMI functions
- `backend/src/engines/behaviour_engine.py` - New scoring functions
- `docs/clarifin2/` - Documentation complete

### Database Changes
- Add `account_balances_history` table
- Extend `accounts` with types and metadata
- Extend `loans` with floating rate support
- Create `institutions` reference table

### Repositories
- `AccountRepository` extended
- `LoanRepository` extended
- New: `InstitutionRepository`

### Services
- `AccountHealthService` - Health score calculation
- `LoanHealthService` - Loan scoring

### Tests
- Schema migration tests
- Extended loan calculation tests
- Health score tests

### Documentation
- Verify all blueprint docs complete
- API contract ready

### Migration Strategy
Non-breaking: All new columns nullable, backward compatible

### Estimated Effort
- 4 weeks, 1 engineer

### Dependencies
None

### Risk Level
LOW - Schema extensions only

### Acceptance Criteria
- [ ] All new tables created
- [ ] Migrations run without error
- [ ] Backward compatibility maintained
- [ ] Health score endpoint works

---

## Milestone 2: Account Intelligence (Weeks 5-8)

### Objectives
- Complete account lifecycle management
- Implement health scoring
- Add cross-account analytics

### Files Affected
- `backend/src/services/account_service.py` (new)
- `backend/src/services/account_health_service.py` (new)
- `backend/src/routers/accounts.py` - Extended endpoints
- `backend/tests/` - Account tests

### Database Changes
- Activate NOT NULL constraints where ready
- Add indexes for performance

### Repositories
- `AccountBalanceHistoryRepository` (new)
- `AccountRepository` extended with balance history

### Services
- `AccountService` - Lifecycle methods
- `AccountHealthService` - Scoring logic

### Tests
- Account creation/retrieval tests
- Balance history tests
- Health score unit tests
- Integration tests for lifecycle

### Estimated Effort
- 4 weeks, 1 engineer

### Dependencies
Milestone 1 complete

### Risk Level
MEDIUM - Balance calculations critical

### Acceptance Criteria
- [ ] All account types supported
- [ ] Health score accurate (compared to benchmarks)
- [ ] Balance history maintained
- [ ] Cross-account linking works

---

## Milestone 3: Reconciliation Flagship (Weeks 9-12)

### Objectives
- Implement complete reconciliation workflows
- Add audit trail and rollback
- Build money flow graph

### Files Affected
- `backend/src/engines/reconciliation_engine.py` - Extended
- `backend/src/services/reconciliation_service.py` (new)
- `backend/src/routers/reconciliation.py` - Extended
- `backend/tests/test_reconciliation.py` - Extended

### Database Changes
- `reconciliations` extended with audit fields
- `reconciliation_audit_log` (new table)
- `reconciliation_stats` (new table)

### Repositories
- `ReconciliationRepository` extended
- `ReconciliationAuditRepository` (new)

### Services
- `ReconciliationService` - Full workflow
- `ReconciliationHealthService` - Stats calculation

### Tests
- Match algorithm tests
- Split/undo workflow tests
- Audit trail tests
- Integration: full scan accuracy > 95%

### Estimated Effort
- 4 weeks, 1 engineer

### Dependencies
Milestone 1 complete

### Risk Level
HIGH - Core differentiator

### Acceptance Criteria
- [ ] 95%+ match detection rate
- [ ] Undo works correctly
- [ ] Audit trail complete
- [ ] Health score accurate

---

## Milestone 4: Loan Intelligence (Weeks 13-16)

### Objectives
- Floating rate support
- Prepayment and refinance analysis
- Avalanche/snowball strategies

### Files Affected
- `backend/src/engines/loan_engine.py` - Extended
- `backend/src/services/loan_service.py` - Extended
- `backend/src/routers/loans.py` - Extended
- `backend/tests/` - Loan tests

### Database Changes
- `loan_payments` (new)
- `loan_scenarios` (new)
- Index on `loans.next_emi_date`

### Repositories
- `LoanPaymentRepository` (new)
- `LoanScenarioRepository` (new)

### Services
- `LoanService` - Extended with payment/scenario methods
- `LoanStrategyService` - Avalanche/snowball logic

### Tests
- Floating rate EMI tests
- Prepayment impact tests
- Refinance break-even tests
- Strategy recommendation tests

### Estimated Effort
- 4 weeks, 1 engineer

### Dependencies
Milestone 1 complete

### Risk Level
MEDIUM - Complex calculations

### Acceptance Criteria
- [ ] Floating rates work
- [ ] Prepayment simulation accurate
- [ ] Refinance analysis correct
- [ ] Strategies recommended

---

## Milestone 5: Credit Cards (Weeks 17-20)

### Objectives
- Credit card lifecycle
- Utilization optimization
- Subscription detection

### Files Affected
- `backend/src/services/credit_card_service.py` (new)
- `backend/src/routers/cards_statements.py` - Credit card endpoints
- `backend/tests/` - Credit card tests

### Database Changes
- `credit_cards` (new)
- `credit_card_statements` (new)
- `credit_card_subscriptions` (new)

### Repositories
- `CreditCardRepository` (new)
- `CreditCardStatementRepository` (new)
- `CreditCardSubscriptionRepository` (new)

### Services
- `CreditCardService` - Core logic
- `RewardOptimizationService` - Category allocation

### Tests
- Utilization tests
- Interest calculation tests
- Subscription detection tests
- Payment optimization tests

### Estimated Effort
- 4 weeks, 1 engineer

### Dependencies
Milestone 2 complete

### Risk Level
MEDIUM - Credit scoring accuracy

### Acceptance Criteria
- [ ] Utilization tracked correctly
- [ ] Payment optimization works
- [ ] Subscriptions detected
- [ ] Credit health score accurate

---

## Milestone 6: Behaviour Engine (Weeks 21-24)

### Objectives
- Complete behavioural scoring
- Early warning system
- Recommendations engine

### Files Affected
- `backend/src/engines/behaviour_engine.py` - Extended
- `backend/src/services/behaviour_service.py` - Extended
- `backend/src/routers/behaviour.py` - Extended
- `backend/tests/test_behavior_engine.py` - Extended

### Database Changes
- `behaviour_snapshots` (new)
- `behaviour_patterns` (new)
- `recommendations` (new)

### Repositories
- `BehaviourSnapshotRepository` (new)
- `RecommendationRepository` (new)

### Services
- `BehaviourService` - Extended scoring
- `AlertService` - Warning generation

### Tests
- All metric tests
- Alert trigger tests
- Recommendation logic tests
- Integration: wellness score

### Estimated Effort
- 4 weeks, 1 engineer

### Dependencies
All previous milestones

### Risk Level
MEDIUM - Scoring accuracy

### Acceptance Criteria
- [ ] Wellness score accurate
- [ ] Alerts trigger correctly
- [ ] Recommendations actionable
- [ ] Patterns detected

---

## Milestone 7: AI Assistant (Weeks 25-28)

### Objectives
- LLM integration
- Explanations and Q&A
- Receipt parsing

### Files Affected
- `backend/src/services/llm_service.py` (new)
- All engines - Explanation endpoints
- `backend/tests/test_llm_mock.py` - Mock tests

### Database Changes
- `llm_cache` (new)

### Services
- `LLMService` - Local inference wrapper
- `ExplanationService` - Prompt formatting

### Tests
- Mock tests (no LLM required)
- Cache functionality tests
- Prompt formatting tests

### Estimated Effort
- 4 weeks, 0.5 engineer (part-time)

### Dependencies
Milestone 3-6 complete

### Risk Level
LOW - Enhancement layer

### Acceptance Criteria
- [ ] Explanations generated
- [ ] Cache works
- [ ] Graceful fallback

---

## Timeline Summary

| Milestone | Weeks | Focus | Team |
|-----------|-------|-------|------|
| 1. Foundation | 1-4 | Schema + Core | 1 BE |
| 2. Accounts | 5-8 | Account Intelligence | 1 BE |
| 3. Reconciliation | 9-12 | Money Flow Graph | 1 BE |
| 4. Loans | 13-16 | Loan Analytics | 1 BE |
| 5. Credit Cards | 17-20 | Credit Optimization | 1 BE |
| 6. Behaviour | 21-24 | Behavioural Intelligence | 0.5 BE |
| 7. AI | 25-28 | LLM Assistant | 0.5 BE |

**Total: 28 weeks (~7 months)**

---

## Parallel Work Streams

### Stream A: Core Engines (BE Team)
- Account Engine
- Loan Engine  
- Credit Card Engine

### Stream B: Intelligence Layer (BE Team)
- Reconciliation
- Behaviour Engine
- LLM Integration

### Stream C: Infrastructure (Shared)
- Database migrations
- API endpoints
- Tests

---

## Success Metrics

| Milestone | Target |
|-----------|--------|
| Test Coverage | > 85% at each milestone |
| API Response | < 100ms for 95% of requests |
| Reconciliation | > 95% match detection |
| Calculations | Match Excel/bank calculators |
| Wellness Score | Correlates with manual assessment |