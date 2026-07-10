# System Blueprint - ClariFinOS 2.0

*Personal Financial Intelligence Platform*

---

## Core Vision

**Question**: "How can a user completely understand and optimize their financial life using deterministic financial intelligence?"

Every feature must serve this purpose. The platform is NOT a generic budget tracker or expense manager. It is a **Financial Intelligence Platform** that provides:

1. **Complete Financial Visibility** - All money flows tracked, explained, and optimized
2. **Deterministic Calculations** - Integer paise arithmetic, no floating point errors, auditable results
3. **Actionable Intelligence** - Not just data, but insights that drive specific actions
4. **Privacy-First Architecture** - All data stays local, LLM inference is quantized and local

---

## Five Core Engines Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           USER INTERFACE LAYER                              │
│  Next.js Server Components + Client Components for interactivity               │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
┌───────────────────────────────────▼───────────────────────────────────────┐
│                      ORCHESTRATION SERVICE LAYER                             │
│  - Transaction Import Service                                                │
│  - Reconciliation Coordination                                               │
│  - Financial Intelligence Service                                          │
│  - Notification Dispatch                                                     │
└───────────────────────────────────┬───────────────────────────────────────┘
                                    │
┌───────────────────────────────────▼───────────────────────────────────────┐
│                    DETERMINISTIC FINANCE ENGINE LAYER                         │
│                                                                             │
│  ┌─────────────────┐  ┌──────────────────┐  ┌──────────────────┐          │
│  │  Account Engine │  │ Reconciliation   │  │    Loan Engine   │          │
│  │                 │  │     Engine       │  │                  │          │
│  └─────────────────┘  └──────────────────┘  └──────────────────┘          │
│                                                                             │
│  ┌─────────────────┐  ┌──────────────────┐                                │
│  │ Credit Card     │  │ Behaviour Engine │                                │
│  │ Intelligence    │  │                  │                                │
│  └─────────────────┘  └──────────────────┘                                │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
┌───────────────────────────────────▼───────────────────────────────────────┐
│                    LLM-ASSISTED EXPERIENCE LAYER                           │
│  - Phi-3 Mini (local) for explanations                                     │
│  - Qwen-VL 2B for receipt parsing                                          │
│  - Cached responses for consistency                                          │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Design Principles

### 1. Deterministic Precision
- All monetary values stored as **integer paise** (₹1.00 = 100 paise)
- All calculations use **Decimal with ROUND_HALF_UP**
- All financial formulas derived from **industry-standard sources** (banking, actuarial)
- No LLMs for numerical calculations

### 2. Immutability by Default
- Transactions cannot be UPDATED or DELETED (triggers enforce)
- Reconciliation creates metadata records, never mutates ledger
- All changes append-only with deterministic keys

### 3. Explainability
- Every score has traceable components
- Every recommendation explains the "why"
- Every match generates human-readable explanations
- No black-box decisions

### 4. India-First, Global-Ready
- Retain UPI/NEFT/RTGS detection patterns
- Multi-currency support designed but initialized for INR
- Tax formulas derived from Indian tax law (extensible)

### 5. Privacy-First
- All data in local SQLite (optionally PostgreSQL)
- LLM inference via quantized local models
- No transaction data leaves the device
- End-to-end encryption ready

---

## Core Engine Definitions

### 1. Account Intelligence Engine
**Purpose**: Understand every account's role in financial health

**Responsibilities**:
- Account lifecycle management (opening, closing, dormant detection)
- Institution metadata (bank capabilities, interest rates, fees)
- Balance history with trends
- Account health scoring
- Cross-account analytics and relationships
- Salary/Savings/Credit/Wallet/UPI categorization

**Key Metrics**:
- Account Health Score (balances, activity, fees)
- Cash Flow Rate (per account)
- Balance Trend (improving/deteriorating)

### 2. Reconciliation Engine
**Purpose**: Create a complete money flow graph across all accounts

**Responsibilities**:
- Match internal transfers (same institution)
- Match inter-bank transfers (UPI, NEFT, RTGS, IMPS)
- Match credit card payments (credit side → checking)
- Match loan payments (checking → loan)
- Handle split/merged transactions
- Maintain audit trail of all reconciliation actions
- Compute reconciliation health score

**Key Metrics**:
- Reconciliation Coverage (% of transactions matched)
- Confidence Score (per match)
- Money Flow Accuracy (input = output)

### 3. Loan Intelligence Engine
**Purpose**: Optimize debt for minimum cost and maximum flexibility

**Responsibilities**:
- EMI calculation (fixed, floating, hybrid rates)
- Amortization schedule with dynamic adjustments
- Prepayment impact analysis (recurring, lump sum)
- Refinance evaluation with break-even analysis
- Avalanche/Snowball payoff strategy
- Tax benefit calculations (80C, 24)
- Loan Health Score

**Key Metrics**:
- Debt-to-Income Ratio
- Liability Ratio
- Interest Saved
- Months Saved
- Loan Affordability Score

### 4. Credit Card Intelligence Engine
**Purpose**: Minimize interest costs and maximize rewards

**Responsibilities**:
- Billing cycle tracking
- Payment optimization (utilization vs interest)
- Reward points and cashback aggregation
- Subscription detection and management
- Credit score impact modeling
- Credit Health Score

**Key Metrics**:
- Credit Utilization Rate
- Average Utilization Trend
- Reward Points Earned/Year
- Interest Avoided

### 5. Behavioural Intelligence Engine
**Purpose**: Detect patterns and drive proactive decisions

**Responsibilities**:
- Savings consistency scoring
- Cashflow stability analysis
- Salary volatility detection
- Lifestyle inflation tracking
- Subscription creep analysis
- Early warning system
- Financial Resilience Score

**Key Metrics**:
- Savings Discipline Score
- Cashflow Stability Index
- Salary Dependence Ratio
- Subscription Burn Rate
- Financial Resilience Index

---

## Non-Functional Requirements

| Requirement | Target |
|-------------|--------|
| Performance | Single transaction query < 50ms, bulk import < 1s/1000 txns |
| Scalability | SQLite for individual, PostgreSQL for advisory firms |
| Determinism | Same inputs → same outputs, idempotent operations |
| Auditability | SHA-256 signatures, append-only logs |
| Explainability | All scores decomposed into traceable components |
| Testability | Every formula unit tested, every engine integration tested |
| Security | Parameterized queries, input validation, rate limiting |
| Maintainability | Modular engines, clear interfaces, documented formulas |
| Observability | Structured logs, health endpoints, audit reports |

---

## Current Codebase Integration

The existing codebase provides:
- ✅ Transaction immutability via triggers
- ✅ Paise-precise schema (`amount_paise INTEGER`)
- ✅ Hash signatures for tamper detection
- ✅ Basic EMI/amortization calculations
- ✅ Deterministic reconciliation matching
- ⚠️ Missing: credit cards, budgets, goals, forecasts
- ⚠️ Missing: India-specific credit card patterns
- ✗ Missing: floating rate support, subscription detection