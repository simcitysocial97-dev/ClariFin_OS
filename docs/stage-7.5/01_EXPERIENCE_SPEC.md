# Experience Specification - Stage 7.5

## Overview

ClariFin_OS is a Personal Financial Operating System that transforms raw bank statement data into actionable financial intelligence. The experience is built around **deterministic computation**, **ledger integrity**, and **evidence-based insights**.

---

## Core Experience Principles

### 1. Deterministic Financial Computation
- All monetary values are stored and computed in **paise** (₹1.00 = 100 paise) to avoid floating-point precision errors
- All scores are in **basis points** (0-10000 for 0-100%) for consistent precision
- Every calculation is reproducible: same input → same output, always

### 2. Evidence-First Design
- Every insight, alert, and recommendation includes an **evidence chain**
- Evidence includes: source references, calculation steps, confidence scores
- Users can trace any number back to its source transaction(s)

### 3. Privacy-First Architecture
- Local SQLite deployment (no cloud dependency)
- User retains full data ownership
- All processing happens client-side or on local server

---

## Runtime Architecture

### Financial Graph Runtime (`frontend/lib/graph/runtime.ts`)
**Purpose**: Build and query a unified graph of all financial entities.

**Capabilities**:
- `build(viewModels)` - Construct graph from all workspace ViewModels
- `traceMoney(from, to)` - Trace money flow between nodes
- `related(nodeId, depth)` - Find related nodes with context
- `focus(nodeId, depth)` - Focus on specific node with surroundings
- `metrics()` - Compute graph density, connectivity, value totals
- `explain(nodeId)` - Get explainability payload for any node
- `selection()` - Manage node selection state

**Node Types** (from `types.ts`):
- `transaction`, `account`, `cashflow_month`, `cashflow_category`
- `loan`, `amortization_entry`, `credit_card`, `credit_card_statement`
- `investment`, `holding`, `behaviour_score`, `spending_pattern`
- `reconciliation_statement`, `discrepancy`, `forecast_projection`
- `forecast_scenario`, `net_worth_snapshot`, `net_worth_breakdown`
- `merchant`, `category`, `institution`

**Edge Types**:
- `belongs_to`, `categorized_as`, `from_merchant`, `at_institution`
- `composes`, `affects_cashflow`, `amortizes`, `has_statement`
- `has_holding`, `impacts_score`, `reconciles`, `projects`
- `scenario_of`, `traces_to`, `references`, `derived_from`

### Intelligence Runtime (`frontend/lib/intelligence/runtime.ts`)
**Purpose**: Generate deterministic financial intelligence from the graph.

**Engines** (configurable):
- `health` - Overall financial health scoring
- `spending` - Spending pattern analysis
- `cashflow` - Cashflow insights and trends
- `debt` - Debt risk and optimization
- `investment` - Investment opportunity analysis
- `behaviour` - Behavioral pattern detection
- `goal` - Goal tracking and progress
- `risk` - Risk score computation
- `opportunity` - Opportunity identification
- `recommendation` - Actionable recommendations
- `alert` - Real-time alerts
- `anomaly` - Anomaly detection

**Output Types**:
- `Insight` - Observations with evidence, priority, related nodes
- `Alert` - Time-sensitive notifications requiring attention
- `Recommendation` - Suggested actions with rationale
- `RiskScore` - Quantified risk by category
- `OpportunityScore` - Quantified opportunities
- `Goal` - Tracked financial goals with progress
- `HealthScore` - Overall financial health with dimensions

### Simulation Runtime (`frontend/lib/simulation/runtime.ts`)
**Purpose**: Project future financial states based on historical patterns.

**Engines**:
- `CashflowSimulator` - Future cashflow projections
- `NetWorthSimulator` - Net worth trajectory
- `BudgetSimulator` - Budget scenario modeling
- `LoanSimulator` - Loan payoff projections
- `InvestmentSimulator` - Investment growth projections
- `RetirementSimulator` - Retirement corpus projections
- `GoalSimulator` - Goal achievement predictions
- `EmergencyFundSimulator` - Emergency fund adequacy

**Configuration**:
- `horizon_months` - Projection timeframe (default: 12)
- `inflation_rate_bps` - Inflation assumption (default: 300 = 3%)
- `investment_return_rate_bps` - Return assumption (default: 800 = 8%)

### Command Center Runtime (`frontend/lib/command-center/runtime.ts`)
**Purpose**: Composition layer orchestrating graph, intelligence, and simulation.

**Capabilities**:
- Workspace registration and management
- Graph building from multiple ViewModels
- Intelligence computation from current graph
- Simulation execution from graph data
- Selection management across panels
- Layout persistence (localStorage)

**Panels**:
- `graph` - Interactive money graph visualization
- `timeline` - Temporal view of financial events
- `insights` - Intelligence feed
- `search` - Global search across all entities
- `preview` - Workspace previews
- `context` - Context panel for selected nodes

---

## Workspace Architecture

### Dashboard (`/dashboard`)
**Purpose**: Financial health snapshot and overview.

**Layout**:
- Header Row - Title, data timeframe, last updated
- KPI Row (4 cards) - Net Cash Flow, Savings Rate, EMI Ratio, Buffer Days
- Analytics Summary Bar - Quick metrics summary
- Main Content (2-column) - Cashflow Trend + Category Spend (left), Behavior Score + Insights (right)
- Secondary Row (3-column) - Recurring Charges, Top Merchants, Recent Transactions
- Footer - Financial Health Score

**Data Sources**:
- `useDashboardMetrics()` - Core metrics hook
- `useOverview()` - Data summary hook

### Transactions (`/transactions`)
**Purpose**: Transaction intelligence workspace with filtering and evidence.

**Layout**:
- Toolbar Region - Search, filter toggle, group/sort controls
- Filter Panel Region - Advanced filtering UI
- Transaction Table Region - Paginated, sortable table
- Pagination Controls - Page navigation
- Selection Summary - When items selected
- Insight Panel - Transaction insights
- Action Drawer - Bulk actions
- Evidence Drawer - Transaction evidence on row click

**Capabilities**:
- `useTransactionCapability()` - State management
- Keyboard shortcuts: Ctrl+F (search), Ctrl+G (group), Ctrl+R (refresh), Ctrl+A (select all), Delete (clear)
- Scroll position persistence

### Accounts (`/accounts`)
**Purpose**: Bank account management (computed + managed).

**Layout**:
- Header - Title, Add Account button
- Total Balance Card - Combined computed + managed balance
- Section 1: Detected Accounts - From imported statements
- Section 2: Saved Accounts - Persistent managed accounts

**Capabilities**:
- Computed accounts from `/api/accounts` (derived from statements)
- Managed accounts via `/api/accounts/manage` (CRUD operations)
- Account types: savings, current, salary, fd, nre, nro

### Credit Cards (`/cards`)
**Purpose**: Credit card portfolio management.

**Layout**:
- Header - Title, Add Card button
- Card Portfolio Header - Summary statistics
- Credit Card Grid - Individual card tiles
- Statement History Drawer - On card click

**Capabilities**:
- `useCards()` - Card data hook
- `useStatementsQuery()` - Statement data hook
- Validation and statement viewing per card

### Loans (`/loans`)
**Purpose**: Loan tracking and amortization.

**Layout**:
- Header - Title, Add Loan button
- Summary Cards (3) - Total Outstanding, Total Monthly EMI, Active Loans
- Loans Grid - Individual loan cards
- Amortization Schedule Drawer - Payment schedule view
- Prepayment Simulator - What-if analysis

**Capabilities**:
- `useLoans()` - Loan data hook
- `useLoanSchedule()` - Amortization computation
- `usePrepaymentSimulation()` - Prepayment impact analysis

### Investments (`/investments`)
**Purpose**: Investment portfolio tracking.

**Layout**:
- Header - Title, Add Investment button
- Summary Cards (3) - Total Invested, Current Value, P&L
- Investments Grid - Individual investment cards
- Allocation Chart - Portfolio distribution

**Capabilities**:
- `useInvestments()` - Investment data hook
- Types: mutual_fund, stock, fd, gold_etf, ppf, nps, bonds, crypto

### Net Worth (`/net-worth`)
**Purpose**: Net worth analysis and trends.

**Layout**:
- Toolbar - Refresh, export, date range, period controls
- Net Worth Summary - Current net worth
- Composition Chart - Asset breakdown
- Trend Chart - Historical trajectory
- Account Breakdown - Detailed view
- Insights Panel - Net worth insights

**Capabilities**:
- `useNetWorthCapability()` - State management
- Period options: monthly, quarterly, yearly

### Cashflow (`/cashflow`)
**Purpose**: Cashflow truth analysis.

**Layout**:
- Toolbar - Refresh, export, share, evidence controls
- Cashflow Summary - Current period summary
- Monthly Trend Chart - Income vs expenses over time
- Category Breakdown - Spending by category
- Transaction List - Detailed transactions
- Insights Panel - Cashflow insights

**Capabilities**:
- `useCashflowCapability()` - State management
- Evidence drawer for calculation transparency

### Behaviour (`/behaviour`)
**Purpose**: Behavioral financial intelligence.

**Layout**:
- Toolbar - Refresh, period controls
- Behaviour Score - Overall wellness score
- Spending Patterns - Category and temporal patterns
- Wellness Radar - Multi-dimensional view
- Savings Rate - Savings discipline metrics
- Debt Health - Debt-related metrics
- Insights Panel - Behaviour insights

**Capabilities**:
- `useBehaviourCapability()` - State management
- Based on backend `behavior_engine.py`
- Indices: Loss Aversion, Impulsivity, Habit Stability, Financial Stress, Savings Discipline
- India-specific risk detection: UPI micro-spend, gambling, loan app patterns, EMI ratio

### Forecast (`/forecast`)
**Purpose**: Future financial projections.

**Layout**:
- Toolbar - Refresh, horizon, scenario controls
- Forecast Summary - Projection summary
- Net Worth Projection - Future net worth chart
- Cashflow Projection - Future cashflow chart
- Scenario Comparison - What-if scenarios
- Insights Panel - Forecast insights

**Capabilities**:
- `useForecastCapability()` - State management
- Integrated with Simulation Runtime

### Reconciliation (`/reconciliation`)
**Purpose**: Cross-account transaction matching.

**Layout**:
- Header - Title
- Reconciliation Summary Bar - Match statistics
- Match Grid - Pending reconciliation matches

**Capabilities**:
- `usePendingReconciliations()` - Match data hook
- Based on backend `reconciliation_engine.py`
- Match types: exact, window, fuzzy, manual

### Settings (`/settings`)
**Purpose**: App preferences and data management.

**Layout**:
- Appearance Card - Dark mode toggle
- Data Management Card - Export, import, clear data
- About Card - App version and info

---

## Navigation Model

### Primary Navigation (Sidebar)
**Sections**:
1. **Overview**
   - Dashboard - `/dashboard`

2. **Manage**
   - Transactions - `/transactions`
   - Accounts - `/accounts`
   - Credit Cards - `/cards`

### Route Redirects
- `/import` → `/transactions?tab=import`
- `/reconciliation` → `/transactions?tab=reconcile`
- `/networth` → `/dashboard?view=networth`
- `/cashflow` → `/dashboard?view=cashflow`
- `/analytics` → `/dashboard?view=analytics`

---

## Interaction Patterns

### Data Flow
```
Backend (FastAPI) → API Endpoints → DTOs → Mappers → ViewModels → Capabilities → Components → Pages
```

### State Management
- **React Query** - Server state (API data)
- **Zustand** (`use-app-store`) - Client state (UI preferences, selections)
- **Capability Hooks** - Workspace-specific state

### Error Handling
- Component-level error boundaries (isolated failures)
- Loading skeletons for each workspace
- Empty states with actionable guidance
- Error states with retry options

### Evidence Pattern
Every insight/alert includes:
1. Evidence items (type, summary, source, confidence)
2. Calculation steps (inputs, outputs, description)
3. Source references (id, type, label, timestamp)
4. Related graph node IDs
5. Deep link to source workspace

---

## Financial Correctness Guardrails

### Currency Convention
- **Paise** is the canonical unit (integer)
- All amounts stored as `amount_paise: number` (integer)
- Display formatting via `formatINR()` utility

### Score Convention
- **Basis points** (0-10000) for all scores
- Display formatting via `formatPercentage()` utility

### Determinism
- No `as any` or `@ts-ignore` in TypeScript
- No ML/LLM for predictions (deterministic algorithms only)
- Hash signatures for transaction immutability
- SQL triggers prevent transaction modification

---

## Component Reuse Matrix

| Component | Used In Workspaces |
|-----------|-------------------|
| `EvidenceDrawer` | transactions, cashflow, net-worth, behaviour, forecast |
| `WorkspaceToolbar` | transactions, forecast, behaviour, net-worth, cashflow |
| `LoadingSkeleton` | dashboard, accounts, cards, loans, investments |
| `EmptyState` | transactions, forecast, cashflow, investments, loans |
| `ErrorState` | forecast, cashflow, behaviour |
| `InsightsPanel` | dashboard, transactions, forecast, behaviour, net-worth, cashflow |

---

## Backend Integration Points

### Core Services
- `DashboardService` - Dashboard orchestration
- `AccountService` - Account balance computation
- `BehaviorService` - Behavioral analysis
- `ReconciliationService` - Cross-account matching

### Engines
- `balance_engine.py` - Running balance computation
- `behavior_engine.py` - Behavioral intelligence
- `reconciliation_engine.py` - Transaction matching
- `ledger_audit_engine.py` - Immutability verification
- `nudge_engine.py` - Behavioral nudges
- `insight_generator.py` - Insight generation

### Repositories
- `TransactionRepository` - Transaction queries
- `AccountRepository` - Account CRUD
- `ReconciliationRepository` - Reconciliation queries
- All repositories in `src/repositories/`