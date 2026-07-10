# Feature Gap Analysis

*Evidence-based assessment of each financial engine*

---

## LOAN MODULE

### Current Implementation (from `backend/src/engines/loan_engine.py`)

| Capability | Status | Implementation Location |
|------------|--------|-------------------------|
| ✓ Amortization schedule | ✅ Present | `compute_amortization_schedule()` |
| ✓ Dynamic amortization | ✅ Present | Same function, handles standard reducing balance |
| ✓ Recalculation after prepayment | ✅ Present | `compute_prepayment_impact()` |
| ✗ Recurring prepayments | ❌ Missing | No scheduled prepayment logic |
| ✗ One-time lump sum prepayment history | ❌ Missing | No history tracking |
| ✓ Compare repayment strategies | ✅ Partially | Two prepayment modes: reduce_tenure vs reduce_emi |
| ✓ Interest saved | ✅ Present | Returned in prepayment impact |
| ✓ Months saved | ✅ Present | Returned as `months_saved` |
| ✓ Payoff simulation | ✅ Present | `prepayment_paise` affecting remaining months |
| ✗ Refinance simulation | ❌ Missing | No rate/par rate comparison |
| ✗ Floating interest rates | ❌ Missing | Fixed annual_rate only |
| ✓ Fixed rates | ✅ Present | Standard EMI calculation |
| ✗ Hybrid loans | ❌ Missing | No step-up or teaser rate logic |
| ✓ EMI recalculation | ✅ Present | `compute_remaining_months()` |
| ✗ Tenure recalculation after changes | ❌ Missing | No partial tenure adjustment |
| ✗ Early closure | ❌ Missing | No prepayment to zero logic |
| ✗ Payment history | ❌ Missing | No payment table/link |
| ✗ Missed payment handling | ❌ Missing | No grace period or penalty logic |
| ✗ Penalties | ❌ Missing | No late fee calculations |
| ✗ Tax deduction calculations | ❌ Missing | No interest component tracking |
| ✗ Debt-to-income ratio | ❌ Missing | Only EMI ratio in behavior engine |
| ✗ Loan utilization | ❌ Missing | No sanction vs outstanding ratio |
| ✗ Liability ratio | ❌ Missing | No total liabilities/assets ratio |
| ✗ Affordability analysis | ❌ Missing | No income multiplier check |
| ✗ Credit exposure | ❌ Missing | No credit bureau integration |
| ✗ Payoff recommendation engine | ❌ Missing | No smart prepayment advice |
| ✗ Loan health score | ❌ Missing | No comprehensive scoring |
| ✗ Scenario modelling | ❌ Missing | No "what-if" analysis beyond prepayment |
| ✗ "Should I prepay?" recommendation | ❌ Missing | No decision engine |

### Why Missing Features Matter

| Missing Feature | Why It Is Critical |
|-----------------|-------------------|
| **Recurring Prepayments** | Users making regular prepayments (e.g., monthly surplus) need compound interest savings projections. Without this, they cannot plan for systematic prepayment strategies. |
| **Refinance Simulation** | Interest rate changes are fundamental. Users expect to compare current loan terms against market rates to evaluate break-even points. |
| **Floating/Hybrid Rates** | Most Indian loans (home loans) are floating rate. A fixed-rate-only engine fails to serve 70%+ of borrowers. |
| **Missed Payment Handling** | Late payments incur penalties and interest shocks. Users need to model impact and recovery paths. |
| **Tax Deductions** | In India, loan interest is tax-deductible (Section 24, 80C). Without this, cost of borrowing is overstated, misleading prepayment decisions. |
| **Debt-to-Income Ratio** | Lenders and regulators use this metric. Users need to track DTI for loan eligibility and financial health. |

---

## INVESTMENTS ENGINE

### Current Implementation (from `backend/src/repositories/investment_repository.py`)

| Capability | Status | Implementation |
|------------|--------|---------------|
| ✓ Portfolio tracking | ⚠️ Partial | CRUD only, no analytics |
| ✗ Asset allocation | ❌ Missing | No sector/stock/bond breakdown |
| ✗ SIP analysis | ❌ Missing | No systematic investment tracking |
| ✗ XIRR | ❌ Missing | No IRR engine exists |
| ✗ CAGR | ❌ Missing | No growth rate calculations |
| ✗ Time-weighted return | ❌ Missing | Requires timestamped NAV history |
| ✗ Benchmark comparison | ❌ Missing | No index comparison logic |
| ✗ Sector allocation | ❌ Missing | No sector classification |
| ✗ Risk score | ❌ Missing | No volatility/beta calculations |
| ✗ Volatility | ❌ Missing | No standard deviation metrics |
| ✗ Drawdown | ❌ Missing | No peak-to-trough analysis |
| ✗ Rebalancing suggestions | ❌ Missing | No target allocation logic |
| ✗ Goal mapping | ❌ Missing | No goal-to-investment linking |
| ✗ Tax harvesting | ❌ Missing | No profit booking logic |
| ✗ Dividend tracking | ❌ Missing | No dividend table/fields |
| ✗ Capital gains | ❌ Missing | No STCG/LTCG calculations |
| ✗ Diversification score | ❌ Missing | No correlation/sector overlap |

### Why Missing Features Matter

| Missing Feature | Why It Is Critical |
|-----------------|-------------------|
| **XIRR/CAGR** | Users cannot measure true portfolio returns. This is the cornerstone metric for investment decisions. |
| **Asset Allocation** | Over-allocation to a single sector creates unseen risk. Modern investors expect instant allocation breakdowns. |
| **Benchmark Comparison** | Without comparing to NIFTY/Sensex, users cannot assess manager performance. This is expected in all investment apps. |
| **Rebalancing Suggestions** | Portfolio drift leads to risk concentration. Automated rebalancing is a key value-add in robo-advisors. |
| **Tax Harvesting** | In India, tax-loss harvesting saves 10-20% tax. Competitors like Groww, Zerodha offer this. |

---

## RECONCILIATION ENGINE

### Current Implementation (from `backend/src/engines/reconciliation_engine.py`)

| Capability | Status | Details |
|------------|--------|---------|
| ✓ Matching algorithms | ✅ Present | Exact and window-based only |
| ✓ Duplicate detection | ✅ Present | Via deterministic_key uniqueness |
| ✗ Partial matches | ❌ Missing | No fuzzy/partial amount matching |
| ✓ Manual override | ⚠️ Partial | match_type='manual' possible but no UI tracking |
| ✓ Confidence score | ✅ Present | Deterministic weight-based 0.0-1.0 |
| ✓ Explanation | ✅ Present | Human-readable string per match |
| ✓ Multi-account reconciliation | ✅ Present | Cross-account matching |
| ✗ Split transactions | ❌ Missing | No multi-leg reconciliation |
| ✗ Audit trail | ❌ Missing | No who/when/why tracking |
| ✗ Rollback | ❌ Missing | No undo/redo support |
| ✗ Explainability | ⚠️ Partial | Explanation exists but no reasoning tree |

### Missing Capabilities Analysis

| Missing Feature | Why It Is Critical |
|-----------------|-------------------|
| **Partial Matches** | Real-world transfers often have fees/surcharges. Exact matching misses 20-30% of true transfers. |
| **Audit Trail** | Financial audit requires who confirmed what. Compliance demands full trail. |
| **Rollback** | Users make mistakes. Without undo, errors corrupt ledger integrity. |

---

## AUDIT ENGINE

### Current Implementation (from `backend/src/engines/ledger_audit_engine.py`)

| Capability | Status | Implementation |
|------------|--------|----------------|
| ✓ Immutability | ✅ Present | Triggers prevent UPDATE/DELETE |
| ✓ Tamper detection | ✅ Present | SHA-256 hash verification |
| ✗ Audit signatures | ❌ Missing | No HMAC/digital signatures |
| ✗ Chain verification | ❌ Missing | No Merkle chain |
| ✗ Timeline | ❌ Missing | No time-series of changes |
| ✗ Who changed what | ❌ Missing | No user/action tracking |
| ✗ Reason tracking | ❌ Missing | No audit log of changes |
| ✗ Version history | ❌ Missing | No historical snapshots |
| ✗ Rollback | ❌ Missing | No restore capability |
| ✗ Regulatory readiness | ⚠️ Partial | Basic checks, no formal reports |

### Why Missing Features Matter

| Missing Feature | Why It Is Critical |
|-----------------|-------------------|
| **Digital Signatures** | For enterprise compliance, SHA-256 alone is insufficient. Digital signatures provide non-repudiation. |
| **Version History** | Auditors need to see data evolution. Point-in-time recovery is essential for dispute resolution. |
| **Regulatory Reports** | Banks require SOX, PCI-DSS reports. Automated generation is mandatory for B2B adoption. |

---

## BEHAVIOR ENGINE

### Current Implementation (from `backend/src/engines/behavior_engine.py`)

| Capability | Status | Implementation |
|------------|--------|----------------|
| ✓ Spending score | ⚠️ Partial | Part of financial_health_score, not standalone |
| ✓ Saving score | ⚠️ Partial | Part of financial_health_score |
| ⚠️ Cashflow stability | ❌ Missing | No dedicated metric |
| ⚠️ Financial discipline | ❌ Missing | No dedicated score |
| ✓ Overspending detection | ⚠️ Partial | Impulsivity score > 0.7 |
| ⚠️ Subscription detection | ⚠️ Partial | Only India patterns via keywords |
| ✗ Salary dependency | ❌ Missing | No income source analysis |
| ✗ Burn rate | ❌ Missing | No runway calculations |
| ✗ Lifestyle inflation | ❌ Missing | No YoY category growth analysis |
| ✗ Income volatility | ❌ Missing | No income consistency metrics |
| ⚠️ Emergency fund score | ⚠️ Partial | Buffer days in stress index |
| ✗ Behavior trends | ❌ Missing | No trend analysis over time |
| ✗ Monthly comparisons | ❌ Missing | No period-over-period metrics |
| ✗ Recommendation engine | ❌ Missing | No action suggestions |
| ✗ Nudges | ❌ Missing | No push/email nudges |
| ✗ Personal insights | ❌ Missing | No narrative generation |

### Missing Capabilities Analysis

| Missing Feature | Why It Is Critical |
|-----------------|-------------------|
| **Burn Rate/Runway** | Users need to know how long their savings last. Essential for early-career professionals. |
| **Subscription Detection** | Multiple apps charge recurring fees. Missed subscriptions waste 5-15% of income. |
| **Lifestyle Inflation** | Category spending growth outpacing income creates long-term wealth destruction. |
| **Nudges** | Personal finance apps drive action through timely nudges (YNAB, Monarch Money). |

---

## DASHBOARD

### Current Implementation (from `backend/src/services/dashboard_service.py`)

| Capability | Status | Implementation |
|------------|--------|----------------|
| ✓ Executive summary | ✅ Present | `/dashboard/summary` endpoint |
| ⚠️ Net worth | ⚠️ Present | Current snapshot, no history |
| ⚠️ Cash flow | ⚠️ Partial | Monthly totals only |
| ✗ Income vs expense | ❌ Missing | No period breakdowns |
| ✗ Top merchants | ❌ Missing | No merchant count/amount |
| ✗ Top categories | ❌ Missing | No ranked spending |
| ✗ Budget health | ❌ Missing | No budget module exists |
| ✗ Forecast | ❌ Missing | No prediction engine |
| ✗ Alerts | ❌ Missing | No notification system |
| ✗ Loan summary | ❌ Missing | No EMI/upcoming payments |
| ✗ Investment summary | ❌ Missing | No returns/allocation |
| ✗ Behavior summary | ⚠️ Partial | Health score only |
| ✗ Reconciliation summary | ❌ Missing | No pending matches |
| ✗ Upcoming obligations | ❌ Missing | No scheduled payments |

---

## Classification Summary

| Module | Classification |
|--------|----------------|
| **Accounts** | Basic |
| **Transactions** | Good (immutability is enterprise-grade) |
| **Categories** | Basic |
| **Rules Engine** | Missing |
| **Behavior Engine** | Prototype (India-focused) |
| **Reconciliation Engine** | Good (deterministic matching) |
| **Loans** | Prototype (EMI + amortization only) |
| **Audit Engine** | Good (basic integrity, no compliance) |
| **Dashboard** | Basic |
| **Investments** | Basic (CRUD, no analytics) |
| **Budgets** | Missing |
| **Goals** | Missing |
| **Cash Flow** | Basic |
| **Income Analysis** | Basic |
| **Expenses** | Basic |
| **Reports** | Basic |
| **Import Pipeline** | Good (PDF+CSV) |
| **PDF Extraction** | Prototype |
| **Analytics** | Basic |
| **Notifications** | Missing |
| **Risk Analysis** | Prototype |
| **Forecasting** | Missing |
| **Settings** | Missing |
| **Tax Module** | Missing |