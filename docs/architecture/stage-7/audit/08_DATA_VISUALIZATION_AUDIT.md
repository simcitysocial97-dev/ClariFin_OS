# Data Visualization Audit

## Inventory of Visualizations

### CashflowChart
**Location**: `/frontend/components/dashboard/cashflow-chart.tsx`
**Purpose**: Visualize monthly cash flow trends showing income, expenses, and net cash flow
**Data Source**: `useCashflow` hook (`/api/cashflow/monthly`)
**Data Structure**:
```typescript
interface CashflowMonth {
  month_label: string;
  income_paise: number;
  expense_paise: number;
  net_paise: number;
  transaction_count: number;
}
```

**Visualization Type**: Composed bar/line chart
- **Bars**: Income (green) and expenses (red)
- **Line**: Net cash flow (blue)
- **X-axis**: Month labels
- **Y-axis**: Amount in paise (formatted as ₹K or ₹L)

**Interactivity**:
- Tooltips showing exact values on hover
- Responsive design for different screen sizes

**Limitations**:
- Fixed 6-month view by default
- No date range filtering
- No drill-down capability
- No comparative analysis
- No forecasting
- Limited customization

---

### CategorySpendChart
**Location**: `/frontend/components/dashboard/category-spend-chart.tsx`
**Purpose**: Visualize spending distribution by category
**Data Source**: `useOverview` hook (`/api/overview`)
**Data Structure**:
```typescript
interface CategoryData {
  name: string;
  value: number; // amount_paise
}
```

**Visualization Type**: Bar chart
- **Bars**: Spending by category
- **X-axis**: Category names
- **Y-axis**: Amount in paise

**Interactivity**:
- Basic hover tooltips
- Responsive design

**Limitations**:
- No time-based filtering
- No drill-down to transactions
- No comparative analysis
- No trend analysis
- Limited customization

---

### BehaviorScoreCard
**Location**: `/frontend/components/dashboard/behavior-score-card.tsx`
**Purpose**: Visualize financial health score and component breakdown
**Data Source**: `useBehaviorScore` hook (`/api/behavior/score`)
**Data Structure**:
```typescript
interface BehaviorScore {
  financial_health_score: number;
  components: {
    savings_discipline: number;
    habit_stability: number;
    impulsivity: number;
  };
  risk_flags: {
    india_specific: {
      loan_app_pattern_flag: boolean;
    };
    high_impulsivity: boolean;
    high_stress: boolean;
    low_savings: boolean;
  };
  summary: string;
}
```

**Visualization Type**: Composite visualization
- **Radial Progress**: Overall score (0-100)
- **Component Bars**: Sub-metric breakdown (savings discipline, habit stability, impulsivity)
- **Badges**: Risk flags

**Interactivity**:
- Static visualization (no interactivity)
- Responsive design

**Limitations**:
- No historical comparison
- No drill-down to evidence
- No customization
- No trend analysis
- Limited explainability

---

### Sparkline
**Location**: `/frontend/components/ui/sparkline.tsx`
**Purpose**: Compact visualization of trends in small spaces
**Data Source**: Various (passed as props)
**Data Structure**: Array of numbers

**Visualization Type**: Mini line chart
- **Line**: Trend visualization
- **Color**: Customizable

**Interactivity**:
- Basic hover effects
- Responsive design

**Limitations**:
- No tooltips
- No axis labels
- No data points
- Limited customization

---

### RecurringChargesWidget
**Location**: `/frontend/components/dashboard/recurring-charges-widget.tsx`
**Purpose**: Visualize recurring subscription patterns
**Data Source**: `useOverview` hook (`/api/overview`)
**Data Structure**: Array of recurring charge objects

**Visualization Type**: List/table visualization
- **List**: Recurring charges with description and amount
- **Sparkline**: Trend visualization

**Interactivity**:
- Basic hover effects
- Responsive design

**Limitations**:
- No time-based filtering
- No categorization
- No trend analysis
- No comparative analysis
- Limited customization

---

### TopMerchantsWidget
**Location**: `/frontend/components/dashboard/top-merchants-widget.tsx`
**Purpose**: Visualize top spending merchants
**Data Source**: `useAnalytics` hook (`/api/analytics`)
**Data Structure**: Array of merchant objects

**Visualization Type**: List/table visualization
- **List**: Merchants ranked by spending
- **Amount**: Spending amount

**Interactivity**:
- Basic hover effects
- Responsive design

**Limitations**:
- No time-based filtering
- No categorization
- No trend analysis
- No comparative analysis
- Limited customization

---

### InsightsPanel
**Location**: `/frontend/components/dashboard/insights-panel.tsx`
**Purpose**: Visualize behavioral insights with severity indicators
**Data Source**: `useOverview` hook (`/api/overview`)
**Data Structure**:
```typescript
interface Insight {
  title: string;
  description: string;
  severity: "positive" | "warning" | string;
  icon?: string;
}
```

**Visualization Type**: List visualization
- **Cards**: Insight cards with severity coloring
- **Icons**: Severity indicators
- **Expandable**: "Show more" functionality

**Interactivity**:
- Expand/collapse functionality
- Responsive design

**Limitations**:
- No filtering by severity
- No sorting options
- No historical comparison
- No evidence visualization
- Limited customization

---

### AnalyticsSummaryBar
**Location**: `/frontend/components/dashboard/analytics-summary-bar.tsx`
**Purpose**: Visualize key metrics summary
**Data Source**:
- `useOverview` hook (`/api/overview`)
- `useAnalytics` hook (`/api/analytics`)

**Data Structure**:
```typescript
interface AnalyticsSummary {
  transaction_count: number;
  unique_merchants: number;
  months_of_data: number;
  highest_month: string;
}
```

**Visualization Type**: Metric bar
- **Metrics**: Four key metrics displayed side-by-side
- **Separators**: Visual separation between metrics

**Interactivity**:
- Loading/error states
- Responsive design

**Limitations**:
- No trend visualization
- No comparative analysis
- No drill-down capability
- Limited customization

---

## Visualization Categories

### Charts
| Visualization       | Purpose                                      | Data Source               | Type               | Interactivity       | Limitations                          |
|---------------------|----------------------------------------------|---------------------------|---------------------|----------------------|---------------------------------------|
| CashflowChart       | Cash flow trend visualization                | `/api/cashflow/monthly`   | Composed bar/line   | Tooltips, hover      | Fixed time range, no drill-down       |
| CategorySpendChart  | Category spending visualization              | `/api/overview`          | Bar chart           | Tooltips             | No time filtering, no drill-down      |
| Sparkline           | Compact trend visualization                  | Various                   | Line chart          | Hover                | No tooltips, no axis labels           |

### Cards
| Visualization       | Purpose                                      | Data Source               | Type               | Interactivity       | Limitations                          |
|---------------------|----------------------------------------------|---------------------------|---------------------|----------------------|---------------------------------------|
| BehaviorScoreCard   | Financial health score visualization         | `/api/behavior/score`     | Composite           | None                 | No historical comparison, no evidence |
| KPI Cards           | Financial metric visualization               | `/api/dashboard/summary`  | Card grid           | None                 | No trend visualization                |

### Tables
| Visualization       | Purpose                                      | Data Source               | Type               | Interactivity       | Limitations                          |
|---------------------|----------------------------------------------|---------------------------|---------------------|----------------------|---------------------------------------|
| RecentTransactions  | Transaction listing                          | `/api/dashboard/summary`  | Table               | Hover, navigation    | Limited filtering, no bulk actions    |
| RecurringCharges    | Recurring subscription visualization         | `/api/overview`          | List/table          | Hover                | No time filtering, no categorization  |
| TopMerchants        | Top merchant spending visualization          | `/api/analytics`          | List/table          | Hover                | No time filtering, no categorization  |

### Panels
| Visualization       | Purpose                                      | Data Source               | Type               | Interactivity       | Limitations                          |
|---------------------|----------------------------------------------|---------------------------|---------------------|----------------------|---------------------------------------|
| InsightsPanel       | Behavioral insights visualization            | `/api/overview`          | List                | Expand/collapse      | No filtering, no evidence             |
| AnalyticsSummaryBar | Key metrics summary                          | `/api/overview`, `/api/analytics` | Metric bar      | None                 | No trend visualization                |

## Data Sources

### API Endpoints
| Endpoint                     | Purpose                                      | Data Structure                          | Used By                          |
|------------------------------|----------------------------------------------|-----------------------------------------|----------------------------------|
| `/api/cashflow/monthly`      | Monthly cash flow data                       | Array of CashflowMonth objects          | CashflowChart                    |
| `/api/overview`              | Overview metrics and insights                | Overview object with charts and insights | CategorySpendChart, InsightsPanel, AnalyticsSummaryBar, RecurringChargesWidget |
| `/api/behavior/score`        | Financial behavior score                     | BehaviorScore object                    | BehaviorScoreCard                |
| `/api/analytics`             | Analytics data                               | Analytics object                        | TopMerchantsWidget, AnalyticsSummaryBar |
| `/api/dashboard/summary`     | Dashboard summary metrics                    | DashboardSummary object                 | KPI Cards, RecentTransactions    |

### Data Transformation
1. **Paise Conversion**: All monetary values are converted from paise to rupees for display
2. **Formatting**: Values are formatted with Indian currency symbols and separators
3. **Scaling**: Large values are scaled to ₹K or ₹L for readability
4. **Color Coding**: Positive/negative values are color-coded (green/red)
5. **Severity Coding**: Insights are color-coded by severity

## Interactivity

### Implemented Interactivity
1. **Tooltips**: Hover-based tooltips showing exact values
2. **Hover Effects**: Visual feedback on hover
3. **Expand/Collapse**: "Show more" functionality in InsightsPanel
4. **Navigation**: Clickable elements that navigate to detailed views
5. **Responsive Design**: Adapts to different screen sizes

### Missing Interactivity
1. **Drill-Down**: Click to see detailed breakdown
2. **Filtering**: Interactive filtering by date, category, etc.
3. **Sorting**: Interactive sorting of data
4. **Zooming**: Zoom in/out of time periods
5. **Comparative Analysis**: Side-by-side comparison
6. **Customization**: User-defined visualization settings
7. **Annotations**: Add notes to visualizations
8. **Sharing**: Share visualizations with others
9. **Export**: Export visualization data or images
10. **Bookmarking**: Save visualization states

## Visualization Purpose

### Financial Health
| Visualization       | Purpose                                      | Key Metrics                          |
|---------------------|----------------------------------------------|--------------------------------------|
| BehaviorScoreCard   | Overall financial health                     | Wellness score, component breakdown  |
| KPI Cards           | Key financial metrics                        | Net cash flow, savings rate, EMI ratio, buffer days |

### Spending Analysis
| Visualization       | Purpose                                      | Key Metrics                          |
|---------------------|----------------------------------------------|--------------------------------------|
| CashflowChart       | Cash flow trends                             | Income, expenses, net cash flow      |
| CategorySpendChart  | Spending by category                         | Category distribution                |
| TopMerchantsWidget  | Top spending merchants                       | Merchant ranking, spending amounts   |
| RecurringCharges    | Recurring subscription patterns              | Subscription detection, amounts      |

### Transaction Analysis
| Visualization       | Purpose                                      | Key Metrics                          |
|---------------------|----------------------------------------------|--------------------------------------|
| RecentTransactions  | Recent transaction listing                   | Date, description, category, amount  |

### Insights & Recommendations
| Visualization       | Purpose                                      | Key Metrics                          |
|---------------------|----------------------------------------------|--------------------------------------|
| InsightsPanel       | Behavioral insights                          | Insight severity, recommendations    |
| AnalyticsSummaryBar | Key metrics summary                          | Transaction count, unique merchants, months of data, peak month |

## Visualization Limitations

### Technical Limitations
1. **No Real-Time Updates**: Visualizations don't update in real-time
2. **Limited Time Ranges**: Fixed or limited time range options
3. **No Comparative Analysis**: No side-by-side comparison capabilities
4. **No Forecasting**: No predictive visualization capabilities
5. **Limited Customization**: Limited user customization options
6. **No Drill-Down**: No ability to drill down to underlying data
7. **No Annotations**: No ability to add notes or annotations
8. **No Sharing**: No ability to share visualizations
9. **No Export**: No ability to export visualization data or images
10. **No Bookmarking**: No ability to save visualization states

### Data Limitations
1. **Aggregated Data**: Most visualizations show aggregated data only
2. **Limited Granularity**: Limited control over data granularity
3. **No Raw Data Access**: No access to underlying raw data
4. **Limited Historical Data**: Limited historical data availability
5. **No Benchmarking**: No industry benchmark comparison
6. **No Scenario Analysis**: No what-if scenario visualization
7. **No Goal Tracking**: No visualization of financial goals
8. **No Alert Visualization**: No visualization of financial alerts
9. **No Pattern Visualization**: No visualization of spending patterns
10. **No Evidence Visualization**: No visualization of evidence chains

### UX Limitations
1. **Limited Interactivity**: Basic hover effects only
2. **No Keyboard Navigation**: No keyboard-based interaction
3. **No Accessibility**: Limited accessibility features
4. **No Mobile Optimization**: Limited mobile-specific optimizations
5. **No Dark/Light Mode**: Limited theme support
6. **No Responsive Controls**: Controls don't adapt to screen size
7. **No Custom Layouts**: No user-defined layouts
8. **No Component Docking**: No drag-and-drop arrangement
9. **No Component Resizing**: No adjustable component sizes
10. **No Component Collapsing**: No expand/collapse functionality

## Visualization Gaps

### Critical Gaps
1. **Net Worth Visualization**: No dedicated net worth trend visualization
2. **Utilization Visualization**: No credit utilization visualization
3. **Amortization Visualization**: No loan amortization schedule visualization
4. **Pattern Visualization**: No spending pattern visualization
5. **Alert Visualization**: No financial alert visualization

### High Priority Gaps
1. **Forecast Visualization**: No financial forecast visualization
2. **Scenario Comparison**: No side-by-side scenario comparison
3. **Evidence Visualization**: No evidence chain visualization
4. **Recommendation Visualization**: No actionable recommendation visualization
5. **Goal Visualization**: No financial goal tracking visualization

### Medium Priority Gaps
1. **Benchmark Visualization**: No industry benchmark comparison
2. **Temporal Visualization**: No time-based filtering and comparison
3. **Geospatial Visualization**: No location-based spending visualization
4. **Network Visualization**: No financial relationship visualization
5. **Sankey Visualization**: No money flow visualization

### Low Priority Gaps
1. **3D Visualization**: No advanced 3D visualizations
2. **Animated Visualization**: No animated data storytelling
3. **AR/VR Visualization**: No augmented/virtual reality visualizations
4. **Voice-Activated Visualization**: No voice-controlled visualizations
5. **Haptic Visualization**: No touch-based feedback visualizations

## Visualization Architecture

### Current Architecture
1. **Frontend Framework**: Next.js with React
2. **Charting Library**: Recharts (dynamically imported)
3. **Styling**: Tailwind CSS
4. **State Management**: React Query for data fetching
5. **Component Library**: Custom UI component library
6. **Visualization Components**: Dedicated visualization components

### Data Flow
1. **API Integration**: REST API calls to backend services
2. **Data Validation**: Zod schema validation for API responses
3. **State Management**: React Query for caching and state
4. **Component Rendering**: Visualization component rendering
5. **Error Handling**: Component-level error boundaries

### Technical Components
1. **ChartContainer**: Wrapper for charts with loading/error/empty states
2. **Visualization Components**: Dedicated components for each visualization type
3. **Data Hooks**: Custom hooks for data fetching
4. **UI Components**: Reusable UI components for visualization elements
5. **Utility Functions**: Formatting and calculation utilities

## Visualization Recommendations

### Immediate Improvements
1. **Add Time Range Controls**: Enable date range filtering for all visualizations
2. **Implement Drill-Down**: Add drill-down capability to all visualizations
3. **Enhance Interactivity**: Add more interactive elements (sorting, filtering)
4. **Improve Tooltips**: Add more detailed tooltips with additional context
5. **Add Export Capability**: Enable data and image export for all visualizations

### Short-Term Improvements
1. **Implement Comparative Analysis**: Add side-by-side comparison capabilities
2. **Add Forecasting**: Implement basic forecasting visualizations
3. **Enhance Customization**: Add user-defined visualization settings
4. **Improve Accessibility**: Add accessibility features
5. **Add Mobile Optimization**: Optimize visualizations for mobile devices

### Long-Term Improvements
1. **Implement Evidence Visualization**: Add evidence chain visualization
2. **Add Pattern Visualization**: Implement spending pattern visualization
3. **Implement Alert Visualization**: Add financial alert visualization
4. **Add Goal Visualization**: Implement financial goal tracking visualization
5. **Implement Scenario Analysis**: Add what-if scenario visualization

### Strategic Improvements
1. **Implement Custom Dashboards**: Enable user-defined dashboard layouts
2. **Add Component Docking**: Implement drag-and-drop component arrangement
3. **Implement Component Resizing**: Add adjustable component sizes
4. **Add Component Collapsing**: Implement expand/collapse functionality
5. **Implement Visualization Sharing**: Enable sharing of visualizations