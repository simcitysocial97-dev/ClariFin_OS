# Platform Capabilities Audit

## Runtime Architecture

### Core Runtimes

**Backend Runtime Engines**
- **Behaviour Engine**: Financial behavior analysis and wellness scoring
- **Credit Card Engine**: Credit card metrics, interest calculation, and billing
- **Loan Engine**: Loan amortization, prepayment analysis, and foreclosure calculation
- **Recommendation Engine**: Financial behavior recommendations based on metrics

**Frontend Runtime Engines**
- **Intelligence Runtime**: Manages enabled engines and intelligence capabilities
- **Simulation Runtime**: Financial scenario simulation capabilities

### Shared Runtimes
- **Money Runtime**: Core monetary handling with explicit paise-based arithmetic (₹1.00 = 100 paise)
- **DTO Runtime**: Data Transfer Object system defining API contracts between frontend and backend
- **Mapper Runtime**: Domain-to-DTO transformation layer

## Public API

### Core API Endpoints
The platform exposes a comprehensive REST API via FastAPI with the following router domains:

- **Accounts**: Account management and balance tracking
- **Transactions**: Transaction listing and categorization
- **Dashboard**: Overview metrics and summary data
- **Cashflow**: Cash flow analysis and monthly breakdowns
- **Credit Cards**: Credit card statements and utilization metrics
- **Loans**: Loan management and amortization schedules
- **Investments**: Investment portfolio tracking
- **Net Worth**: Net worth calculation and historical tracking
- **Reconciliation**: Transaction reconciliation and discrepancy management
- **Behavior**: Financial behavior analysis and wellness scoring
- **Forecast**: Financial forecasting and scenario analysis
- **Audit**: Financial audit trails and evidence chains
- **Banks**: Institution reference data
- **Members**: Household member management
- **Export**: Data export capabilities
- **Import**: Data import and ingestion

### API Contracts (DTOs)
The platform defines comprehensive Data Transfer Objects that serve as the public API contract:

**Core DTOs**
- `AccountDTO`: Account information with balance and metadata
- `TransactionDTO`: Transaction details with amount, category, and merchant
- `DashboardSummaryDTO`: Key financial metrics and summary data
- `OverviewDTO`: Spending trends and category breakdowns

**Financial Intelligence DTOs**
- `BehaviourScoreDTO`: Financial behavior scores in basis points (0-10000)
- `SpendingPatternDTO`: Spending patterns by category with trends
- `SavingsRateDTO`: Savings rate analysis with income/expense breakdown
- `DebtHealthDTO`: Debt health metrics and ratios
- `WellnessRadarDTO`: Financial wellness dimensions and scores
- `BehaviourInsightDTO`: Insight messages with severity and actions

**Domain-Specific DTOs**
- `CashflowSummaryDTO`: Cash flow summary and monthly breakdown
- `CreditCardsDTO`: Credit card statements and utilization metrics
- `LoanSummaryDTO`: Loan information and amortization details
- `NetWorthDTO`: Net worth composition and historical trends
- `ReconciliationDTO`: Reconciliation status and discrepancies
- `InvestmentSummaryDTO`: Investment portfolio performance
- `ForecastDTO`: Financial forecast scenarios and projections

## Capability Hooks

### Financial Intelligence Hooks
- **Behaviour Analysis**: `compute_wellness_score()`, `compute_resilience_index()`, `compute_true_savings_rate()`
- **Debt Analysis**: `compute_debt_cycle_score()`, `compute_foir()`, `compute_credit_revolver_ratio()`
- **Cashflow Analysis**: `compute_income_stability()`, `compute_cashflow_stability_index()`
- **Savings Analysis**: `compute_borrowed_lifestyle_ratio()`, `compute_monthly_surplus()`
- **Recommendation Engine**: `check_debt_dependency()`, `check_foir()`, `check_liquidity()`

### Credit Card Capabilities
- **Interest Calculation**: `compute_daily_interest()`, `compute_monthly_interest_charge()`
- **Billing Calculation**: `compute_due_date()`, `compute_next_statement_date()`, `compute_minimum_due()`
- **Metrics Calculation**: `compute_utilization()`, `compute_available_credit()`, `compute_financial_metrics()`
- **EMI Conversion**: `compute_emi_conversion()` (delegates to loan engine)

### Loan Capabilities
- **Amortization**: `generate_schedule()`, `total_interest_paise()`, `validate_schedule()`
- **EMI Calculation**: `compute_emi_fixed()`, `compute_monthly_interest()`
- **Prepayment Analysis**: `apply_prepayment()`, `apply_multiple_prepayments()`
- **Floating Rate**: `apply_floating_rate_change()`, `simulate_floating_rate_schedule()`
- **Foreclosure**: `compute_foreclosure_amount()`, `compute_prepayment_breakup()`

## Graph Capabilities

### Node Types
- **Financial Entities**: Accounts, Transactions, Statements, Loans, Credit Cards
- **Temporal Nodes**: Daily balances, Monthly snapshots, Billing cycles
- **Behavioral Nodes**: Spending patterns, Income sources, Debt cycles
- **Metric Nodes**: Utilization, FOIR, Savings rate, Wellness score

### Edge Types
- **Temporal Relationships**: "has_daily_balance", "has_monthly_snapshot", "in_billing_cycle"
- **Financial Relationships**: "funds_transaction", "pays_interest", "amortizes_loan"
- **Behavioral Relationships**: "exhibits_pattern", "has_income_source", "in_debt_cycle"
- **Metric Relationships**: "has_utilization", "has_foir", "has_savings_rate"

### Traversal Capabilities
- **Daily Balance Traversal**: Traverse credit card daily balances for interest calculation
- **Amortization Schedule Traversal**: Traverse loan payment schedules for prepayment analysis
- **Transaction Pattern Traversal**: Traverse spending patterns by merchant, category, and time
- **Financial Metric Traversal**: Traverse financial metrics across time periods

### Selection Capabilities
- **Date Range Selection**: Select financial data within specific date ranges
- **Category Selection**: Filter transactions and patterns by category
- **Merchant Selection**: Filter spending patterns by merchant
- **Account Selection**: Filter financial data by account
- **Metric Threshold Selection**: Filter based on metric thresholds (e.g., utilization > 70%)

### Metrics Capabilities
- **Utilization Metrics**: Credit utilization in basis points (0-10000)
- **Debt Metrics**: Debt-to-income ratios, FOIR, debt cycle scores
- **Savings Metrics**: Savings rate, liquidity months, emergency buffer
- **Wellness Metrics**: Composite wellness score (0-100), resilience index
- **Interest Metrics**: Daily/monthly interest, total interest paid, interest saved

## Intelligence Capabilities

### Health Intelligence
- **Wellness Scoring**: Composite financial wellness score (0-100) based on multiple dimensions
- **Resilience Index**: Ability to weather financial shocks (0-1)
- **Liquidity Analysis**: Months of essential expenses covered by liquid assets
- **Wellness Classification**: "Excellent", "Healthy", "Developing", "Risk", "Critical"

### Behavior Intelligence
- **Spending Patterns**: Category-based spending trends and anomalies
- **Income Stability**: Income source analysis and stability metrics
- **Lifestyle Inflation**: Detection of lifestyle inflation trends
- **Subscription Burn**: Subscription spending analysis and growth detection
- **Time-Based Patterns**: Night spending, weekend spending, impulse purchases

### Risk Intelligence
- **Debt Cycle Detection**: Credit advances and revolving behavior scoring
- **Credit Dependency**: Ratio of credit-funded expenses to total expenses
- **FOIR Analysis**: Fixed Obligation to Income Ratio with health bands
- **Credit Revolver Ratio**: Ratio of revolving credit usage
- **Debt Health Scoring**: Composite debt health assessment

### Debt Intelligence
- **Debt Cycle Score**: Composite score for debt cycle behavior (0-100)
- **Credit Dependency Ratio**: Ratio of credit-funded lifestyle expenses
- **FOIR Calculation**: Fixed Obligation to Income Ratio with severity bands
- **Credit Revolver Ratio**: Ratio of revolving credit usage to total credit

### Cashflow Intelligence
- **Income Stability**: Monthly income stability metrics
- **Expense Stability**: Monthly expense stability metrics
- **Cashflow Stability Index**: Composite cash flow stability score (0-1)
- **Savings Rate**: True savings rate calculation
- **Monthly Surplus**: Monthly income minus expenses and fees

### Opportunity Intelligence
- **Recommendation Engine**: Rule-based financial recommendations
  - Debt dependency alerts
  - High FOIR warnings
  - Low liquidity alerts
  - Subscription growth detection
- **Severity Levels**: LOW, MEDIUM, HIGH, CRITICAL
- **Actionable Insights**: Specific suggestions for financial improvement

### Alert Intelligence
- **Alert Types**: LOW_BALANCE, HIGH_UTILIZATION, MISSED_INCOME, etc.
- **Alert Severity**: HIGH, MEDIUM, LOW
- **Alert Lifecycle**: Creation, acknowledgment, resolution
- **Evidence Chains**: Supporting evidence for alerts and insights

## Reusable Engines

### Behaviour Engine
- **Purpose**: Financial behavior analysis and wellness scoring
- **Capabilities**:
  - Wellness scoring (0-100)
  - Resilience index calculation
  - Savings rate analysis
  - Debt cycle scoring
  - Income stability metrics
  - Lifestyle inflation detection
  - Recommendation generation
- **Inputs**: Transaction data, account balances, financial metrics
- **Outputs**: Wellness scores, behavior patterns, recommendations, alerts

### Credit Card Engine
- **Purpose**: Credit card financial metrics and calculations
- **Capabilities**:
  - Daily/monthly interest calculation
  - Statement date and due date generation
  - Minimum due calculation
  - Utilization metrics
  - Available credit calculation
  - EMI conversion (delegates to loan engine)
- **Inputs**: Credit card balances, transaction data, interest rates
- **Outputs**: Interest charges, billing dates, utilization metrics, EMI details

### Loan Engine
- **Purpose**: Loan amortization and prepayment analysis
- **Capabilities**:
  - Amortization schedule generation
  - EMI calculation
  - Prepayment analysis (reduce tenure or EMI)
  - Floating rate simulation
  - Foreclosure calculation
  - Loan metrics calculation
- **Inputs**: Loan principal, interest rate, tenure, prepayment details
- **Outputs**: Amortization schedules, EMI amounts, interest savings, foreclosure costs

### Recommendation Engine
- **Purpose**: Financial behavior recommendations
- **Capabilities**:
  - Debt dependency detection
  - FOIR threshold checking
  - Liquidity assessment
  - Subscription growth detection
  - Recommendation generation
- **Inputs**: Financial metrics, behavior patterns, thresholds
- **Outputs**: Recommendations with severity, title, reason, and suggested actions

## Shared Runtime Capabilities

### Money Runtime
- **Purpose**: Core monetary handling with explicit units
- **Capabilities**:
  - Paise-based arithmetic (₹1.00 = 100 paise)
  - Type-safe money operations
  - Currency conversion
  - Rounding with banker's rounding (ROUND_HALF_EVEN)
- **Key Features**:
  - Explicit paise representation prevents floating-point errors
  - Basis points for interest rates (10000 bps = 100%)
  - Decimal precision for financial calculations

### DTO Runtime
- **Purpose**: API contract definition and validation
- **Capabilities**:
  - Pydantic-based validation
  - Schema documentation
  - Backward compatibility handling
  - Example values for API documentation
- **Key Features**:
  - All monetary fields use `_paise` suffix for explicit units
  - Temporary `_rupees` fields for backward compatibility
  - Comprehensive field descriptions

### Mapper Runtime
- **Purpose**: Domain-to-DTO transformation
- **Capabilities**:
  - Domain object to DTO conversion
  - Backward compatibility field handling
  - Monetary unit conversion
  - List response formatting
- **Key Features**:
  - Single responsibility for API response construction
  - Consistent transformation logic
  - Backward compatibility management