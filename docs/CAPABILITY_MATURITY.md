# Capability Maturity Framework — ClariFin_OS

> Four levels defining when a capability is complete enough.

---

## Maturity Levels

### L1: Correct

**Purpose:** The capability produces mathematically correct output.

**Acceptance Criteria:**
- All golden master tests pass
- Property tests cover edge cases
- Invariants hold for all inputs
- Type checking passes (mypy/ruff)

**Stopping Conditions:**
- Must NOT advance if any L1 criterion fails
- Must halt on CRITICAL risk from change_intelligence

**Typical Examples:**
- Loan EMI calculation returns correct integer paise
- Cashflow surplus = income - expense (identity preserved)
- Credit utilization ratio in [0, 1] range

**Advancement Rules:**
- 90%+ engine coverage required
- All invariants in `tests/domain/invariants/` pass
- No float usage in currency paths

---

### L2: Useful

**Purpose:** The capability solves a real user problem.

**Acceptance Criteria:**
- API endpoint exists and works
- Request/response validated against OpenAPI
- Capability smoke test passes
- No 404/500 errors in happy path

**Stopping Conditions:**
- STOP if router returns 500 errors
- STOP if endpoint not reachable from frontend

**Typical Examples:**
- `/api/transactions` returns parsed transactions
- Dashboard widget displays real data
- PDF import produces usable output

**Advancement Rules:**
- Must pass L1
- Must have API contract tests
- Must load in dashboard without errors

---

### L3: Explainable

**Purpose:** The capability reveals WHY it produced its result.

**Acceptance Criteria:**
- Output includes contributing factors
- Confidence scores in 0-10000 bps range
- LLM explanations trace to deterministic data
- Audit trail captures key decisions

**Stopping Conditions:**
- STOP if result has no derivation path
- STOP if confidence exceeds 10000 or below 0

**Typical Examples:**
- Loan health score shows: tenure, interest, prepayment impact
- Behaviour score shows: savings rate, credit dependency, impulse
- Reconciliation match shows: date window, amount difference, confidence

**Advancement Rules:**
- Must pass L1, L2
- Each metric MUST have explainable derivation (per ARCHITECTURE_CONSTRAINTS.md)

---

### L4: Delightful

**Purpose:** The capability exceeds user expectations.

**Acceptance Criteria:**
- Loading < 2 seconds for typical data
- Clear error messages for edge cases
- Recommendation/guidance provided
- Visual polish (loading states, empty states)

**Stopping Conditions:**
- STOP if frontend tests fail
- STOP if build produces console errors

**Typical Examples:**
- Suggestions adapt to user patterns
- Charts update smoothly
- Empty states guide next action

**Advancement Rules:**
- Must pass L1, L2, L3
- Must pass frontend lint/type-check/build

---

## Dogfooding Guidance

Test capabilities with **real financial data**:

1. Import own bank statements
2. Verify numbers against bank app
3. Check explanations for plausibility
4. Validate recommendations are actionable

Dogfooding = "Does this trust the user's money?"

---

## Worked Example: Transaction Exploration Capability

### L1: Correct
- ✅ Transactions parsed from PDF with integer paise
- ✅ Golden test: 100 transactions match expected hash
- ✅ Property test: amount always integer, type in [credit, debit]
- ✅ Type check: mypy clean on transaction_parser.py

### L2: Useful
- ✅ `/api/transactions` endpoint returns parsed data
- ✅ Contract test validates OpenAPI schema
- ✅ Frontend hook `useTransactions()` loads data
- ✅ No 404/500 in happy path

### L3: Explainable
- ✅ Each transaction has source: statement_id, line_number
- ✅ Category assignment includes confidence score
- ✅ Unmatched transactions flagged for review
- ✅ Rules engine documents categorization logic

### L4: Delightful
- ✅ Transactions load in < 500ms (cached)
- ✅ Category filter works without reload
- ✅ Search handles partial matches
- ✅ Empty state prompts file upload

**Current Status:** L2 — API works, needs explainability improvements.

---

*Version: 1.0 (Stage 0)*  
*Use this framework to assess any capability before advancement.*