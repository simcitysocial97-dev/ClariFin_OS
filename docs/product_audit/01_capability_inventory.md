# Financial Capability Inventory

*Generated via complete backend schema and engine trace*

---

## Accounts

### Current Functionality
- **Account CRUD**: Full create, read, update, delete operations via `AccountRepository`
- **Account Listing**: `get_all_accounts()` returns list of accounts
- **Balance Query**: Two endpoints `/accounts/{account_id}/balance` and `/accounts/{account_id}/running-balance`
- **Account Types**: Supports `'savings'` type with extensibility

### Missing Functionality
- No account hierarchy (sub-accounts, joint accounts)
- No automatic balance reconciliation from statements
- No linked account relationships (primary/secondary)
- No account metadata (opening date, interest rates, minimum balances)
- No multi-currency support

---

## Transactions

### Current Functionality
- **Core Schema**: Full transaction table with `amount_paise`, `debit`, `credit`, `hash_signature`, `date_iso`, `account_id`
- **Categorization**: Basic category field, bulk update support
- **Immutability**: Database triggers prevent UPDATE/DELETE on transactions
- **Hash Signatures**: SHA-256 computed on insert for tamper detection
- **Transfer Detection**: `is_transfer` and `counterparty` fields
- **CSV Import**: `insert_csv_transactions()` in repository
- **Monthly Summary**: Aggregation by month and category
- **Uncategorized Pattern Detection**: `get_uncategorized_patterns()` for merchant tracking

### Missing Functionality
- No recurring transaction detection/matching
- No split transaction support (single transaction → multiple categories)
- No scheduled transaction templates
- No tag/label system
- No attachment support (receipts, notes)
- No payee/merchant database with normalization
- No tax categorization codes
- No geolocation metadata

---

## Categories

### Current Functionality
- **Basic Categories**: String field on transactions
- **Subcategories**: Supported via `subcategory` field
- **Monthly Category Totals**: Aggregation endpoint exists

### Missing Functionality
- No category hierarchy tree
- No category rules (merchant → category mapping)
- No icon/color customization
- No category budgets
- No category spending insights/trends
- No category re-allocation history

---

## Rules Engine

### Current Functionality
- **None**: No rules engine exists

### Missing Functionality
- No automatic categorization rules
- No transaction transformation rules
- No merchant normalization rules
- No amount-based triggers
- No description pattern matching
- No rule versioning/history

---

## Behavior Engine

### Current Functionality
- **Financial Health Score**: Composite score (0-100) computed from 7 behavioral indices
- **Temporal Patterns**: Trend, seasonality, volatility, weekly pattern detection
- **Loss Aversion Index**: Detects erratic transaction behavior
- **Impulsivity Score**: Identifies spontaneous spending patterns
- **Habit Stability**: Measures consistency of spending patterns
- **Financial Stress Index**: Computes burn rate, buffer days, emergency fund adequacy
- **Savings Discipline**: Tracks savings consistency and adequacy
- **India-Specific Risk Patterns**:
  - UPI micro-spend clustering (>10 transactions/day <₹200)
  - Gambling/gaming transaction detection (Dream11, MPL, Rummy keywords)
  - NBFC loan app deposit detection
  - EMI burden ratio calculation

### Missing Functionality
- No salary volatility detection
- No subscription detection beyond India patterns
- No lifestyle inflation tracking
- No spending score (separate from health score)
- No saving score (dedicated metric)
- No cashflow stability score
- No financial discipline score
- No burnout/salary dependency analysis
- No real-time nudges/push notifications
- No personalized insights engine
- No comparison to peer groups
- No credit score integration

---

## Reconciliation Engine

### Current Functionality
- **Exact Match**: Same amount, same date, opposite sign, different accounts
- **Window Match**: Same amount, date within 3 days, opposite sign
- **Confidence Scoring**: Deterministic weight-based (0.0-1.0)
  - Same date: +0.4
  - Within 1 day: +0.3
  - Amount exact: +0.4
  - Description similarity > 0.7: +0.2
- **Explainability**: Human-readable explanations for each match
- **Idempotency**: Deterministic key ensures no duplicate matches
- **Multi-account Support**: Cross-account matching

### Missing Functionality
- No fuzzy/partial amount matching
- No manual override tracking
- No split transaction reconciliation
- No rollback mechanism
- No audit trail of reconciliation actions
- No auto-apply for high-confidence matches
- No reconciliation history/versioning

---

## Loans Module

### Current Functionality
- **EMI Calculation**: Reducing balance formula implementation
- **Amortization Schedule**: Full schedule generation with principal/interest breakdown
- **Prepayment Simulation**: Two modes:
  - `reduce_tenure`: Same EMI, reduces months
  - `reduce_emi`: Same tenure, reduces EMI
- **Gold Loan Interest**: Simple and compound interest calculations
- **EMI to Income Ratio**: For India-specific risk detection
- **Loan CRUD**: Full repository support

### Missing Functionality
- No recurring prepayment support
- No one-time lump sum prepayment history
- No refinance simulation
- No floating interest rate support
- No hybrid loan calculations
- No EMI recalculation after missed payments
- No tenure recalculation
- No early closure penalty calculations
- No payment history tracking
- No missed payment handling
- No penalty/interest recalculation
- No tax deduction calculations (interest component)
- No debt-to-income ratio (overall, not just EMIs)
- No loan utilization metrics
- No liability ratio calculations
- No affordability analysis
- No credit exposure metrics
- No loan payoff recommendation engine
- No loan health score
- No "Should I prepay?" recommendation algorithm

---

## Audit Engine

### Current Functionality
- **Ledger Integrity Validation**: Checks 6 invariants
  - NULL_ACCOUNT_ID
  - NEGATIVE_DEBIT
  - NEGATIVE_CREDIT
  - DUAL_ENTRY (debit AND credit > 0)
  - NULL_HASH
  - DUPLICATE_HASH
- **Hash Signature Verification**: Recomputes SHA-256 and compares
- **Tamper Detection**: Identifies modified transactions via hash mismatch
- **Read-Only Operations**: No ledger mutations

### Missing Functionality
- No immutability beyond triggers
- No tamper evidence chain (Merkle tree)
- No audit signatures (digital signatures)
- No chain verification
- No timeline/history tracking
- No "who changed what" attribution
- No reason/purpose tracking for changes
- No version history
- No rollback capability
- No regulatory readiness (SOX, PCI-DSS)
- No audit log of API access/changes

---

## Dashboard

### Current Functionality
- **Executive Summary**: Single endpoint `/dashboard/summary`
- **Net Worth Calculation**: Aggregated from accounts, investments, loans
- **Running Balance**: Per account computation
- **Behavior Summary**: Health score and indices

### Missing Functionality
- No income vs expense breakdown
- No top merchants/categories view
- No budget health indicator
- No forecast projections
- No alerts/notifications
- No loan summary (total EMI, upcoming payments)
- No investment summary (returns, allocation)
- No reconciliation summary (pending matches)
- No upcoming obligations list
- No cash flow visualization

---

## Investments

### Current Functionality
- **Basic CRUD**: Create, read, update, delete operations
- **Value Tracking**: `invested_paise`, `current_value_paise`
- **Platform Support**: Optional `platform` field
- **Units Tracking**: Optional `units` for mutual funds/stocks
- **Net Worth Integration**: Included in networth calculations

### Missing Functionality
- No portfolio tracking beyond individual assets
- No asset allocation analysis
- No SIP (Systematic Investment Plan) analysis
- No XIRR (Extended Internal Rate of Return) calculations
- No CAGR (Compound Annual Growth Rate)
- No time-weighted return calculations
- No benchmark comparison
- No sector allocation breakdown
- No risk score for portfolio
- No volatility metrics
- No drawdown analysis
- No rebalancing suggestions
- No goal mapping (retirement, house, education)
- No tax harvesting opportunities
- No dividend tracking
- No capital gains calculations
- No asset diversification score
- No portfolio performance history

---

## Budgets

### Current Functionality
- **None**: No dedicated budget module exists

### Missing Functionality
- No budget creation/scheduling
- No budget vs actual comparison
- No rollover support
- No budget categories
- No envelope budgeting
- No zero-based budgeting support

---

## Goals

### Current Functionality
- **None**: No dedicated goals module exists

### Missing Functionality
- No goal tracking
- No target amount/savings
- No timeline projections
- No progress visualization
- No goal-based investment suggestions

---

## Cash Flow

### Current Functionality
- **Monthly Cash Flow**: Endpoint `/cashflow/monthly` returns aggregated flow
- **Income/Expense Separation**: Basic credit/debit distinction

### Missing Functionality
- No cash flow prediction
- No cash flow anomaly detection
- No recurring income/spending forecasting
- No cash flow waterfalls
- No seasonality adjustment
- No trend projection

---

## Income Analysis

### Current Functionality
- **Basic Detection**: Credits identified via transaction type
- **Monthly Aggregation**: Part of cashflow endpoint

### Missing Functionality
- No income categorization (salary, business, passive)
- No income volatility analysis
- No salary prediction/timing forecasts
- No side-income detection
- No income source diversification score

---

## Expenses

### Current Functionality
- **Basic Detection**: Debits identified via transaction type
- **Category Aggregation**: Monthly totals by category

### Missing Functionality
- No expense forecasting
- No expense budgeting
- No essential vs discretionary breakdown
- No expense trend analysis
- No wasteful spending detection
- No tax-deductible expense tagging
- No recurring expense prediction

---

## Reports

### Current Functionality
- **Audit Report**: `/audit/report` endpoint
- **CSV Export**: `/export/csv` endpoint

### Missing Functionality
- No customizable report templates
- No scheduling/delivery
- No tax reports
- No investment performance reports
- No loan paydown reports
- No net worth history
- No cash flow reports
- No budget variance reports

---

## Import Pipeline

### Current Functionality
- **PDF Statement Ingestion**: Full pipeline with extraction
- **CSV Import**: Column mapping, detection, execution
- **Metadata Extraction**: Bank, period, credit limit extraction
- **Duplicate Detection**: File-level and hash-based
- **Validation**: Statement balance validation against computed totals

### Missing Functionality
- No bank API integration (Plaid, Yodlee, FinBox style)
- No automatic categorization on import
- No merchant normalization on import
- No receipt attachment during import
- No import scheduling/automation
- No OFX/QFX support
- No automatic retry on failed extractions

---

## PDF Statement Parsing

### Current Functionality
- **Bank Statement Extraction**: `statement_extractor.py`, `table_extractor.py`
- **Card Statement Support**: `/cards` endpoint exists
- **Metadata Extraction**: `metadata_extractor.py`
- **Multi-table Support**: Hybrid extraction

### Missing Functionality
- No OCR fallback for scanned PDFs
- No multi-language support
- No custom bank template training
- No statement normalization across banks

---

## Analytics

### Current Functionality
- **Basic Analytics Endpoint**: `/transactions/analytics`
- **Monthly Summary**: Credit/debit totals
- **Category Summary**: Spend by category
- **Category Totals by Month**: Time-series aggregation

### Missing Functionality
- No predictive analytics
- No anomaly detection
- No cohort analysis
- No lifetime value calculations
- No customer segmentation
- No behavioral clustering
- No spending attribution

---

## Notifications

### Current Functionality
- **None**: No notification system exists

### Missing Functionality
- No push notifications
- No email alerts
- No in-app notification center
- No alert rules (budget, balance, upcoming)
- No subscription renewal reminders

---

## Risk Analysis

### Current Functionality
- **India-Specific Microspend Risk**: UPI clustering detection
- **Gambling Risk**: Keyword detection in descriptions
- **NBFC Loan Risk**: Multiple small credit deposits
- **EMI Ratio**: Total EMIs / income ratio

### Missing Functionality
- No credit score simulation
- No default risk modeling
- No debt sustainability analysis
- No insurance coverage gaps
- No investment risk tolerance
- No portfolio risk score

---

## Forecasting

### Current Functionality
- **None**: No forecasting engine exists

### Missing Functionality
- No expense forecasting
- No income forecasting
- No loan payoff projections
- No investment growth projections
- No net worth projections
- No tax liability forecasts
- No emergency fund sufficiency

---

## Settings

### Current Functionality
- **None**: No dedicated settings module

### Missing Functionality
- No user preferences
- No theme customization
- No notification preferences
- No currency/localization
- No account linking preferences

---

## Tax Module

### Current Functionality
- **None**: No tax-specific functionality

### Missing Functionality
- No tax categorization
- No tax deduction tracking
- No tax liability estimation
- No tax report generation
- No capital gains calculator
- No tax harvesting suggestions

---

## Net Worth

### Current Functionality
- **Endpoint**: `/networth` exists
- **Components**: Accounts + Investments + Loans (with sign flip for liabilities)

### Missing Functionality
- No net worth history tracking
- No net worth trends
- No net worth comparison
- No asset/liability ratio over time
- No net worth projection

---

## Assets

### Current Functionality
- Part of net worth calculation

### Missing Functionality
- No asset appreciation tracking
- No asset depreciation handling
- No depreciation formulas (for vehicles, property)
- No asset maintenance costs

---

## Liabilities

### Current Functionality
- Loans included in net worth with negative sign

### Missing Functionality
- No credit card liability tracking
- No liability interest calculations
- No liability payoff priority ranking

---

## Summary Table

| Domain | Current Status | Missing Critical Features |
|--------|----------------|--------------------------|
| Accounts | Basic CRUD + Balance | Hierarchy, metadata, multi-currency |
| Transactions | Full schema + Immutability | Recurring, split, tags, merchant db |
| Categories | String field | Hierarchy, rules, budgets |
| Rules | None | All functionality missing |
| Behavior | Prototype (India-focused) | Salary volatility, subscriptions, nudges |
| Reconciliation | Deterministic matching | Fuzzy matching, rollback, history |
| Loans | EMI + Amortization + Prepayment | Floating rates, penalties, tax deductions |
| Audit | Integrity + Hash verification | Digital signatures, timeline, versioning |
| Dashboard | Summary endpoint | Forecast, alerts, breakdowns |
| Investments | Basic CRUD | XIRR, benchmarks, risk, rebalancing |
| Budgets | None | All functionality missing |
| Goals | None | All functionality missing |
| Cash Flow | Monthly aggregation | Prediction, forecasting |
| Income Analysis | Basic credits | Volatility, prediction |
| Expenses | Basic debits | Forecasting, categorization |
| Reports | Audit + CSV Export | Custom, scheduled, tax |
| Import | PDF + CSV | Bank API, automatic categorization |
| Analytics | Basic aggregations | Predictive, anomaly detection |
| Notifications | None | All functionality missing |
| Risk Analysis | India patterns only | Portfolio, credit, insurance |
| Forecasting | None | All functionality missing |
| Settings | None | All functionality missing |
| Tax | None | All functionality missing |
| Net Worth | Current snapshot | History, trends, projection |
| Assets | Part of net worth | Appreciation/depreciation |
| Liabilities | Part of net worth | Detailed tracking |