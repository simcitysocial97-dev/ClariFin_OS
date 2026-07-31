# Workspace Architecture Audit

## Workspace Comparison Table

| Workspace            | Purpose                                      | Entry Point                     | Regions                                                                 | Toolbar | Filters                                                                 | Charts                                                                 | Tables                                                                 | Navigation                                                                 | Explainability                          | Evidence                                      | Missing Functionality                          |
|----------------------|----------------------------------------------|---------------------------------|-------------------------------------------------------------------------|----------|-------------------------------------------------------------------------|-------------------------------------------------------------------------|-------------------------------------------------------------------------|---------------------------------------------------------------------------|------------------------------------------|-----------------------------------------------|-----------------------------------------------|
| Behaviour            | Financial behavior analysis                 | `/api/v1/behaviour`             | Wellness score, spending patterns, savings rate, debt health, wellness radar | None     | Period (monthly, yearly)                                               | Wellness radar, spending patterns by category                          | None                                                                    | Deep link: `/behaviour`, cross-references: loans, cards                | Wellness score calculation evidence chain | Financial data sources, calculation steps     | Advanced behavior pattern detection       |
| Cashflow             | Cash flow analysis                           | `/api/v1/cashflow`              | Summary metrics, monthly trends, category breakdown, transaction list   | None     | Date range, categories, merchants, amount range (not implemented)       | Monthly cash flow trends, category spending                            | Transaction list                                                        | Deep link: `/cashflow`, cross-references: accounts, transactions       | Cash flow calculation evidence chain     | Transaction data sources, calculation steps   | Merchant-level analysis, recurring transactions |
| Credit Cards         | Credit card management                       | `/api/v1/credit-cards`          | Card summaries, utilization metrics, spending by category, statements   | None     | Statuses, banks                                                        | Utilization percentages, spending by category                          | Card list, statement list                                              | Deep link: `/cards`, cross-references: net worth, accounts             | Utilization calculation evidence chain   | Card data sources, calculation steps         | Interest calculation details, payment alerts  |
| Investments          | Investment portfolio tracking                | `/api/v1/investments`           | Investment summaries, performance data, asset allocation                | None     | Investment types, institutions, statuses                               | Asset allocation, performance trends                                   | Holdings table                                                          | Deep link: `/investments`, cross-references: net worth, accounts       | Investment value calculation evidence chain | Investment data sources, calculation steps   | Benchmark comparison, risk analysis        |
| Loans                | Loan management                              | `/api/v1/loans`                 | Loan summaries, amortization schedules, payment progress                | None     | Loan types, lenders, statuses                                          | Payment progress, interest analysis                                    | Loan list, amortization schedule                                       | Deep link: `/loans`, cross-references: net worth, accounts              | Outstanding balance calculation evidence chain | Loan data sources, calculation steps        | Prepayment analysis, floating rate simulation |
| Net Worth            | Net worth calculation                        | `/api/v1/net-worth`             | Net worth summary, asset/liability breakdown, trend analysis            | None     | Date range, account types, period                                      | Asset/liability composition, net worth trend                           | Asset breakdown, liability breakdown                                   | Deep link: `/net-worth`, cross-references: accounts, investments, loans | Net worth calculation evidence chain     | Account, investment, loan data sources        | Historical trend analysis, scenario comparison |
| Reconciliation       | Transaction reconciliation                  | `/api/v1/reconciliation`        | Statement summaries, status overview, discrepancies                     | None     | Status, banks                                                          | Match rate visualization                                                | Statement list, discrepancy list, audit trail                          | Deep link: `/reconciliation`, cross-references: accounts, transactions  | Match rate calculation evidence chain    | Statement data sources, reconciliation steps  | Discrepancy resolution workflow, automated matching |

## Detailed Workspace Analysis

### 1. Behaviour Workspace

**Purpose**
Financial behavior analysis and wellness scoring to help users understand their spending patterns, savings habits, and overall financial health.

**Entry Point**
- API: `/api/v1/behaviour`
- Parameters: `period` (monthly, yearly)

**Regions**
- **Wellness Score**: Overall financial wellness score (0-100)
- **Spending Patterns**: Category-based spending breakdown
- **Savings Rate**: Current savings rate and trend
- **Debt Health**: Debt health metrics and recommendations
- **Wellness Radar**: Multi-dimensional wellness visualization

**Toolbar**
- None (basic period filter only)

**Filters**
- Period: Monthly or yearly analysis

**Charts**
- **Wellness Radar**: Visualization of multiple wellness dimensions (spending discipline, saving rate, debt health, investment growth, credit utilization)
- **Spending Patterns**: Category-based spending distribution

**Tables**
- None

**Navigation**
- Deep link: `/behaviour`
- Cross-references:
  - Loans: `/loans`
  - Credit Cards: `/cards`

**Explainability**
- **Evidence Chain**: Detailed breakdown of wellness score calculation
  - Summary: Description of analysis scope
  - Evidence: Data sources with confidence scores
  - Calculation Steps: Step-by-step calculation logic
  - Source References: Data origins
  - Confidence Score: Overall confidence in the analysis

**Evidence**
- Financial data from loan and credit card repositories
- Calculation steps showing how wellness score is derived
- Confidence scores for each data source

**Missing Functionality**
- Advanced behavior pattern detection (impulse spending, subscription growth)
- Time-based spending analysis (night spending, weekend spending)
- Income source analysis
- Lifestyle inflation detection
- Customizable wellness dimensions

---

### 2. Cashflow Workspace

**Purpose**
Cash flow analysis and transaction tracking to help users understand income, expenses, and net cash flow trends.

**Entry Point**
- API: `/api/v1/cashflow`
- Parameters: `period` (monthly, yearly)

**Regions**
- **Summary Metrics**: Total income, total expenses, net cash flow, transaction count
- **Trend Analysis**: Direction, percentage change, volatility score
- **Monthly Data**: Monthly income, expenses, and net cash flow
- **Category Breakdown**: Spending by category
- **Transaction List**: Recent transactions

**Toolbar**
- None (basic filters only)

**Filters**
- Date range (not implemented)
- Categories (not implemented)
- Merchants (not implemented)
- Amount range (not implemented)

**Charts**
- **Monthly Trends**: Income, expenses, and net cash flow over time
- **Category Spending**: Spending distribution by category

**Tables**
- **Transaction List**: Recent transactions with date, description, amount, category, and merchant

**Navigation**
- Deep link: `/cashflow`
- Cross-references:
  - Accounts: `/accounts`
  - Transactions: `/transactions`

**Explainability**
- **Evidence Chain**: Detailed breakdown of cash flow calculation
  - Summary: Analysis scope and transaction count
  - Evidence: Income and expense totals with confidence scores
  - Calculation Steps: Net cash flow calculation logic
  - Source References: Transaction and category data sources
  - Confidence Score: Overall confidence in the analysis

**Evidence**
- Transaction data from cash flow service
- Calculation steps showing net cash flow derivation
- Confidence scores for data sources

**Missing Functionality**
- Merchant-level spending analysis
- Recurring transaction detection
- Cash flow forecasting
- Expense categorization customization
- Transaction tagging

---

### 3. Credit Cards Workspace

**Purpose**
Credit card management and utilization analysis to help users track card balances, utilization, and spending patterns.

**Entry Point**
- API: `/api/v1/credit-cards`
- Parameters: `statuses`, `banks` (comma-separated)

**Regions**
- **Card Summaries**: Individual card details and balances
- **Utilization Metrics**: Credit utilization percentages
- **Spending Analysis**: Spending by category
- **Statement List**: Recent credit card statements

**Toolbar**
- None

**Filters**
- Statuses: Filter by card status (active, closed, etc.)
- Banks: Filter by issuing bank

**Charts**
- **Utilization Percentages**: Visualization of credit utilization by card
- **Spending by Category**: Category-based spending distribution

**Tables**
- **Card List**: Individual card details (name, bank, last 4 digits, balance, limit, due date)
- **Statement List**: Recent statements with period, due amount, and status

**Navigation**
- Deep link: `/cards`
- Cross-references:
  - Net Worth: `/net-worth`
  - Accounts: `/accounts`

**Explainability**
- **Evidence Chain**: Detailed breakdown of utilization calculation
  - Summary: Number of active cards and total balance
  - Evidence: Card data sources with confidence scores
  - Calculation Steps: Total balance calculation logic
  - Source References: Credit card and statement data sources
  - Confidence Score: Overall confidence in the analysis

**Evidence**
- Credit card data from repository
- Statement data for utilization calculation
- Calculation steps showing balance aggregation

**Missing Functionality**
- Interest calculation details
- Payment due alerts
- Reward points tracking
- EMI conversion analysis
- Spending trend analysis

---

### 4. Investments Workspace

**Purpose**
Investment portfolio tracking and performance analysis to help users monitor investment values, returns, and asset allocation.

**Entry Point**
- API: `/api/v1/investments`
- Parameters: `investment_types`, `institutions`, `statuses` (comma-separated)

**Regions**
- **Investment Summaries**: Individual investment details
- **Performance Data**: Historical performance
- **Asset Allocation**: Investment type distribution
- **Holdings Table**: Detailed holdings information

**Toolbar**
- None

**Filters**
- Investment Types: Filter by investment type (equity, debt, etc.)
- Institutions: Filter by financial institution
- Statuses: Filter by investment status (active, closed, etc.)

**Charts**
- **Asset Allocation**: Distribution of investments by type
- **Performance Trends**: Historical value and returns (placeholder)

**Tables**
- **Holdings Table**: Detailed investment information (name, type, institution, invested amount, current value, returns)

**Navigation**
- Deep link: `/investments`
- Cross-references:
  - Net Worth: `/net-worth`
  - Accounts: `/accounts`

**Explainability**
- **Evidence Chain**: Detailed breakdown of investment value calculation
  - Summary: Number of active investments and total value
  - Evidence: Investment data sources with confidence scores
  - Calculation Steps: Total value calculation logic
  - Source References: Investment data sources
  - Confidence Score: Overall confidence in the analysis

**Evidence**
- Investment data from repository
- Calculation steps showing value aggregation
- Confidence scores for data sources

**Missing Functionality**
- Benchmark comparison
- Risk analysis
- Dividend tracking
- Investment goal tracking
- Performance attribution

---

### 5. Loans Workspace

**Purpose**
Loan management and amortization analysis to help users track loan balances, payment progress, and interest costs.

**Entry Point**
- API: `/api/v1/loans`
- Parameters: `loan_types`, `lenders`, `statuses` (comma-separated)

**Regions**
- **Loan Summaries**: Individual loan details
- **Amortization Schedules**: Monthly payment breakdown
- **Payment Progress**: Repayment progress visualization
- **Interest Analysis**: Interest rate categorization

**Toolbar**
- None

**Filters**
- Loan Types: Filter by loan type (personal, home, auto, etc.)
- Lenders: Filter by lending institution
- Statuses: Filter by loan status (active, closed, etc.)

**Charts**
- **Payment Progress**: Visualization of repayment progress
- **Interest Analysis**: Interest rate distribution by category

**Tables**
- **Loan List**: Individual loan details (name, lender, type, balance, EMI, status)
- **Amortization Schedule**: Monthly payment breakdown (placeholder)

**Navigation**
- Deep link: `/loans`
- Cross-references:
  - Net Worth: `/net-worth`
  - Accounts: `/accounts`

**Explainability**
- **Evidence Chain**: Detailed breakdown of outstanding balance calculation
  - Summary: Number of active loans and total outstanding
  - Evidence: Loan data sources with confidence scores
  - Calculation Steps: Total outstanding calculation logic
  - Source References: Loan data sources
  - Confidence Score: Overall confidence in the analysis

**Evidence**
- Loan data from repository
- Calculation steps showing balance aggregation
- Confidence scores for data sources

**Missing Functionality**
- Prepayment analysis
- Floating rate simulation
- Loan comparison tools
- Refinancing analysis
- EMI adjustment scenarios

---

### 6. Net Worth Workspace

**Purpose**
Net worth calculation and composition analysis to help users understand their overall financial position.

**Entry Point**
- API: `/api/v1/net-worth`
- Parameters: `date_range`, `account_types`, `period`

**Regions**
- **Net Worth Summary**: Total net worth, assets, and liabilities
- **Composition**: Asset and liability breakdown
- **Trend Analysis**: Net worth direction and percentage change

**Toolbar**
- None

**Filters**
- Date Range: Filter by specific date range
- Account Types: Filter by account type
- Period: Analysis period (1M, 3M, 1Y, etc.)

**Charts**
- **Asset/Liability Composition**: Visualization of asset and liability distribution
- **Net Worth Trend**: Historical net worth trend (placeholder)

**Tables**
- **Asset Breakdown**: Individual asset details (accounts, investments)
- **Liability Breakdown**: Individual liability details (loans, credit cards)

**Navigation**
- Deep link: `/net-worth`
- Cross-references:
  - Accounts: `/accounts`
  - Investments: `/investments`
  - Loans: `/loans`
  - Credit Cards: `/credit-cards`

**Explainability**
- **Evidence Chain**: Detailed breakdown of net worth calculation
  - Summary: Number of accounts, investments, and loans included
  - Evidence: Data sources with confidence scores
  - Calculation Steps: Net worth calculation logic (Assets - Liabilities)
  - Source References: Account, investment, loan, and statement data sources
  - Confidence Score: Overall confidence in the analysis

**Evidence**
- Account data from repository
- Investment data from repository
- Loan data from repository
- Credit card statement data
- Calculation steps showing net worth derivation

**Missing Functionality**
- Historical trend analysis
- Scenario comparison (what-if analysis)
- Net worth forecasting
- Goal tracking
- Asset depreciation modeling

---

### 7. Reconciliation Workspace

**Purpose**
Transaction reconciliation and discrepancy management to help users match transactions with bank statements.

**Entry Point**
- API: `/api/v1/reconciliation`
- Parameters: `status`, `banks` (comma-separated)

**Regions**
- **Statement Summaries**: Individual statement details
- **Status Overview**: Reconciliation status metrics
- **Discrepancies**: Transaction discrepancies (placeholder)
- **Audit Trail**: Reconciliation history (placeholder)

**Toolbar**
- None

**Filters**
- Status: Filter by reconciliation status
- Banks: Filter by bank

**Charts**
- **Match Rate Visualization**: Percentage of reconciled transactions

**Tables**
- **Statement List**: Individual statement details (bank, period, transaction count, reconciled count, status)
- **Discrepancy List**: Transaction discrepancies (placeholder)
- **Audit Trail**: Reconciliation history (placeholder)

**Navigation**
- Deep link: `/reconciliation`
- Cross-references:
  - Accounts: `/accounts`
  - Transactions: `/transactions`

**Explainability**
- **Evidence Chain**: Detailed breakdown of match rate calculation
  - Summary: Number of statements and total transactions
  - Evidence: Statement data sources with confidence scores
  - Calculation Steps: Match rate calculation logic
  - Source References: Statement data sources
  - Confidence Score: Overall confidence in the analysis

**Evidence**
- Statement data from reconciliation repository
- Calculation steps showing match rate derivation
- Confidence scores for data sources

**Missing Functionality**
- Discrepancy resolution workflow
- Automated transaction matching
- Manual reconciliation interface
- Discrepancy categorization
- Reconciliation history tracking