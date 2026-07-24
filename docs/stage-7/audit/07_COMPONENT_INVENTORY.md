# Component Inventory

## Cards

### Card
**Location**: `/frontend/components/ui/card.tsx`
**Purpose**: Basic container component for content grouping
**Features**:
- Styled container with border and padding
- Header, title, content, and footer sections
- Responsive design
- Dark/light mode support

**Usage**:
```tsx
<Card>
  <CardHeader>
    <CardTitle>Title</CardTitle>
  </CardHeader>
  <CardContent>
    Content
  </CardContent>
</Card>
```

**Dependencies**: None
**Props**:
- `className`: Optional CSS classes

---

### BehaviorScoreCard
**Location**: `/frontend/components/dashboard/behavior-score-card.tsx`
**Purpose**: Financial health score visualization with component breakdown
**Features**:
- Radial progress indicator for overall score
- Component bars for sub-metrics
- Risk flag badges
- Score classification
- Responsive design

**Usage**:
```tsx
<BehaviorScoreCard />
```

**Dependencies**:
- `useBehaviorScore` hook
- `ChartContainer`
- `Badge`

**Props**: None

---

## Charts

### ChartContainer
**Location**: `/frontend/components/ui/chart-container.tsx`
**Purpose**: Wrapper component for charts with loading/error/empty states
**Features**:
- Loading state with skeleton
- Error state with retry option
- Empty state with message
- Title display
- Responsive container

**Usage**:
```tsx
<ChartContainer
  isLoading={loading}
  isError={error}
  isEmpty={empty}
  onRetry={retryFunction}
  title="Chart Title"
>
  <ActualChartComponent />
</ChartContainer>
```

**Dependencies**:
- `Skeleton`
- `BarChart3` icon

**Props**:
- `isLoading`: Loading state
- `isError`: Error state
- `isEmpty`: Empty state
- `emptyMessage`: Custom empty message
- `onRetry`: Retry function
- `children`: Chart content
- `title`: Chart title

---

### CashflowChart
**Location**: `/frontend/components/dashboard/cashflow-chart.tsx`
**Purpose**: Cash flow trend visualization showing income, expenses, and net cash flow
**Features**:
- Composed bar/line chart
- Income/expense bars
- Net cash flow line
- Tooltips with formatted values
- Responsive design
- Dynamic imports for SSR compatibility

**Usage**:
```tsx
<CashflowChart months={6} />
```

**Dependencies**:
- `recharts` (dynamic import)
- `useCashflow` hook
- `ChartContainer`
- `ExplainButton`

**Props**:
- `months`: Number of months to display

---

### CategorySpendChart
**Location**: `/frontend/components/dashboard/category-spend-chart.tsx`
**Purpose**: Category-based spending visualization
**Features**:
- Bar chart for category spending
- Responsive design
- Dynamic imports for SSR compatibility

**Usage**:
```tsx
<CategorySpendChart />
```

**Dependencies**:
- `recharts` (dynamic import)
- `useOverview` hook
- `ChartContainer`
- `ExplainButton`

**Props**: None

---

### Sparkline
**Location**: `/frontend/components/ui/sparkline.tsx`
**Purpose**: Mini line charts for compact data visualization
**Features**:
- Compact line chart
- Customizable colors
- Responsive design

**Usage**:
```tsx
<Sparkline data={[1, 2, 3, 4, 5]} color="green" />
```

**Dependencies**: None
**Props**:
- `data`: Array of values
- `color`: Line color
- `className`: Optional CSS classes

---

## Tables

### Table
**Location**: `/frontend/components/ui/table.tsx`
**Purpose**: Basic table component with styled elements
**Features**:
- Styled table, header, body, row, cell components
- Responsive design
- Dark/light mode support

**Usage**:
```tsx
<Table>
  <TableHeader>
    <TableRow>
      <TableHead>Column 1</TableHead>
    </TableRow>
  </TableHeader>
  <TableBody>
    <TableRow>
      <TableCell>Data</TableCell>
    </TableRow>
  </TableBody>
</Table>
```

**Dependencies**: None
**Props**: Standard HTML table props

---

### RecentTransactions
**Location**: `/frontend/components/dashboard/recent-transactions.tsx`
**Purpose**: Transaction table with categorization and formatting
**Features**:
- Transaction listing with date, description, category, amount
- Category badges with color coding
- Amount formatting with color coding (debit/credit)
- "View all" link
- Loading/error/empty states

**Usage**:
```tsx
<RecentTransactions
  transactions={transactions}
  isLoading={loading}
  isError={error}
  onRetry={retryFunction}
/>
```

**Dependencies**:
- `Table` components
- `Badge`
- `DataStateWrapper`
- `Button`
- `ArrowRight` icon

**Props**:
- `transactions`: Array of transaction objects
- `isLoading`: Loading state
- `isError`: Error state
- `onRetry`: Retry function

---

## Panels

### InsightsPanel
**Location**: `/frontend/components/dashboard/insights-panel.tsx`
**Purpose**: Behavioral insights display with severity indicators
**Features**:
- Severity-coded insight cards
- Expandable list with "show more" functionality
- Icon indicators for insight types
- Responsive design

**Usage**:
```tsx
<InsightsPanel />
```

**Dependencies**:
- `useOverview` hook
- `ChartContainer`
- Various icons

**Props**: None

---

### AnalyticsSummaryBar
**Location**: `/frontend/components/dashboard/analytics-summary-bar.tsx`
**Purpose**: Key metrics summary bar
**Features**:
- Four metric display areas
- Vertical separators
- Loading/error states

**Usage**:
```tsx
<AnalyticsSummaryBar />
```

**Dependencies**:
- `useOverview` hook
- `useAnalytics` hook
- `Separator`
- `DataStateWrapper`

**Props**: None

---

## Dialogs

### Dialog
**Location**: `/frontend/components/ui/dialog.tsx`
**Purpose**: Modal dialog component
**Features**:
- Trigger button
- Dialog content with header, title, description
- Open/close state management
- Responsive design

**Usage**:
```tsx
<Dialog>
  <DialogTrigger>Open</DialogTrigger>
  <DialogContent>
    <DialogHeader>
      <DialogTitle>Title</DialogTitle>
      <DialogDescription>Description</DialogDescription>
    </DialogHeader>
    Content
  </DialogContent>
</Dialog>
```

**Dependencies**: Radix UI dialog primitives
**Props**: Standard dialog props

---

### ExplainButton
**Location**: `/frontend/components/ui/explain-button.tsx`
**Purpose**: Explanation dialog trigger for metrics and visualizations
**Features**:
- Help icon button
- Dialog with title and explanation
- Compact design
- Accessible

**Usage**:
```tsx
<ExplainButton
  title="Metric Name"
  explanation="Detailed explanation of the metric and how it's calculated."
/>
```

**Dependencies**:
- `Dialog` components
- `Button`
- `HelpCircle` icon

**Props**:
- `title`: Explanation title
- `explanation`: Explanation content

---

## Toolbars

### Toolbar Components
**Location**: `/frontend/components/toolbar/`
**Purpose**: Toolbar components for workspace actions
**Features** (implied by directory structure):
- Filter controls
- Action buttons
- View options
- Search functionality

**Usage**: Used across workspaces for consistent action placement

**Dependencies**: Various UI components

---

## Filters

### Filter Components
**Location**: `/frontend/components/filters/`
**Purpose**: Filter controls for data refinement
**Features** (implied by directory structure):
- Date range filters
- Category filters
- Account filters
- Status filters
- Custom filter controls

**Usage**: Used across workspaces for data filtering

**Dependencies**: Various UI components

---

## Loading

### Skeleton
**Location**: `/frontend/components/ui/skeleton.tsx`
**Purpose**: Loading skeletons for content placeholders
**Features**:
- Animated loading placeholder
- Customizable size and shape
- Responsive design

**Usage**:
```tsx
<Skeleton className="h-4 w-20" />
```

**Dependencies**: None
**Props**:
- `className`: CSS classes for size/shape

---

### DashboardSkeleton
**Location**: `/frontend/components/dashboard/dashboard-skeleton.tsx`
**Purpose**: Dashboard loading state with multiple skeletons
**Features**:
- Multiple skeleton placeholders
- Layout matching actual dashboard
- Responsive design

**Usage**:
```tsx
<DashboardSkeleton />
```

**Dependencies**:
- `Skeleton`

**Props**: None

---

### DataStateWrapper
**Location**: `/frontend/components/ui/data-state-wrapper.tsx`
**Purpose**: Wrapper for data components with loading/error/empty states
**Features**:
- Loading state
- Error state with retry
- Empty state with message
- Responsive design

**Usage**:
```tsx
<DataStateWrapper
  isLoading={loading}
  isError={error}
  isEmpty={empty}
  onRetry={retryFunction}
>
  <DataComponent />
</DataStateWrapper>
```

**Dependencies**: None
**Props**:
- `isLoading`: Loading state
- `isError`: Error state
- `isEmpty`: Empty state
- `emptyMessage`: Custom empty message
- `onRetry`: Retry function
- `children`: Content to wrap

---

## Evidence

### Evidence Components
**Location**: `/frontend/components/evidence/`
**Purpose**: Evidence chain visualization components
**Features** (implied by directory structure):
- Evidence chain display
- Calculation step visualization
- Data source attribution
- Confidence indicators

**Usage**: Used in workspaces to show evidence for metrics and insights

**Dependencies**: Various UI components

---

## Widgets

### RecurringChargesWidget
**Location**: `/frontend/components/dashboard/recurring-charges-widget.tsx`
**Purpose**: Recurring subscription pattern visualization
**Features**:
- Recurring charge detection
- Amount visualization
- Trend analysis
- Responsive design

**Usage**:
```tsx
<RecurringChargesWidget />
```

**Dependencies**:
- `useOverview` hook
- `Card` components

**Props**: None

---

### TopMerchantsWidget
**Location**: `/frontend/components/dashboard/top-merchants-widget.tsx`
**Purpose**: Top merchant spending visualization
**Features**:
- Merchant spending ranking
- Amount visualization
- Responsive design

**Usage**:
```tsx
<TopMerchantsWidget />
```

**Dependencies**:
- `useAnalytics` hook
- `Card` components

**Props**: None

---

## UI Components

### Badge
**Location**: `/frontend/components/ui/badge.tsx`
**Purpose**: Status and category indicators
**Features**:
- Color-coded badges
- Variants for different statuses
- Responsive design

**Usage**:
```tsx
<Badge variant="secondary">Label</Badge>
```

**Dependencies**: None
**Props**:
- `variant`: Badge style variant
- `className`: Optional CSS classes

---

### Button
**Location**: `/frontend/components/ui/button.tsx`
**Purpose**: Interactive buttons with various styles
**Features**:
- Multiple variants (primary, secondary, ghost, etc.)
- Size options
- Loading state
- Responsive design

**Usage**:
```tsx
<Button variant="primary" size="sm">Click</Button>
```

**Dependencies**: None
**Props**:
- `variant`: Button style
- `size`: Button size
- `disabled`: Disabled state
- `onClick`: Click handler

---

### Input
**Location**: `/frontend/components/ui/input.tsx`
**Purpose**: Form input fields
**Features**:
- Styled input field
- Responsive design
- Dark/light mode support

**Usage**:
```tsx
<Input placeholder="Enter text" />
```

**Dependencies**: None
**Props**: Standard HTML input props

---

### Select
**Location**: `/frontend/components/ui/select.tsx`
**Purpose**: Dropdown select component
**Features**:
- Styled select dropdown
- Responsive design
- Dark/light mode support

**Usage**:
```tsx
<Select>
  <SelectTrigger>
    <SelectValue placeholder="Select" />
  </SelectTrigger>
  <SelectContent>
    <SelectItem value="option1">Option 1</SelectItem>
  </SelectContent>
</Select>
```

**Dependencies**: Radix UI select primitives
**Props**: Standard select props

---

### Progress
**Location**: `/frontend/components/ui/progress.tsx`
**Purpose**: Progress indicators
**Features**:
- Linear progress bar
- Customizable colors
- Responsive design

**Usage**:
```tsx
<Progress value={75} />
```

**Dependencies**: None
**Props**:
- `value`: Progress percentage

---

### Separator
**Location**: `/frontend/components/ui/separator.tsx`
**Purpose**: Visual separators between elements
**Features**:
- Horizontal/vertical separators
- Responsive design

**Usage**:
```tsx
<Separator />
```

**Dependencies**: None
**Props**:
- `orientation`: Horizontal or vertical

---

### Switch
**Location**: `/frontend/components/ui/switch.tsx`
**Purpose**: Toggle switches
**Features**:
- On/off toggle
- Responsive design
- Dark/light mode support

**Usage**:
```tsx
<Switch checked={enabled} onCheckedChange={setEnabled} />
```

**Dependencies**: Radix UI switch primitive
**Props**:
- `checked`: Toggle state
- `onCheckedChange`: State change handler

---

### Tabs
**Location**: `/frontend/components/ui/tabs.tsx`
**Purpose**: Tabbed interface component
**Features**:
- Tab navigation
- Content panels
- Responsive design

**Usage**:
```tsx
<Tabs defaultValue="tab1">
  <TabsList>
    <TabsTrigger value="tab1">Tab 1</TabsTrigger>
  </TabsList>
  <TabsContent value="tab1">Content</TabsContent>
</Tabs>
```

**Dependencies**: Radix UI tabs primitives
**Props**: Standard tabs props

---

## Layout Components

### MainLayout
**Location**: `/frontend/components/layout/main-layout.tsx`
**Purpose**: Main application layout with sidebar
**Features**:
- Responsive layout
- Sidebar integration
- Main content area
- Collapsible sidebar

**Usage**:
```tsx
<MainLayout>{children}</MainLayout>
```

**Dependencies**:
- `Sidebar`
- `useAppStore`

**Props**:
- `children`: Content to render

---

### Sidebar
**Location**: `/frontend/components/layout/sidebar.tsx`
**Purpose**: Primary navigation sidebar
**Features**:
- Navigation sections
- Net worth display
- Theme toggle
- Responsive design
- Mobile support

**Usage**:
```tsx
<Sidebar />
```

**Dependencies**:
- `useNetWorth` hook
- `ThemeToggle`
- Navigation configuration

**Props**:
- `sidebarCollapsed`: Collapsed state
- `toggleSidebar`: Toggle function

---

## Workspace Components

### Workspace-Specific Components
**Location**: `/frontend/components/{workspace}/`
**Purpose**: Components specific to individual workspaces
**Workspaces** (implied by directory structure):
- `accounts`: Account management components
- `behaviour`: Behavior analysis components
- `cards`: Credit card components
- `cashflow`: Cash flow components
- `forecast`: Forecasting components
- `import`: Data import components
- `investments`: Investment components
- `loans`: Loan components
- `net-worth`: Net worth components
- `reconciliation`: Reconciliation components
- `transaction-table`: Transaction table components

**Features**:
- Workspace-specific visualizations
- Domain-specific controls
- Data integration

---

## Component Categorization

### Cards
| Component               | Purpose                                      | Location                                  |
|-------------------------|----------------------------------------------|-------------------------------------------|
| Card                    | Basic content container                      | `/ui/card.tsx`                           |
| BehaviorScoreCard       | Financial health score visualization         | `/dashboard/behavior-score-card.tsx`     |

### Charts
| Component               | Purpose                                      | Location                                  |
|-------------------------|----------------------------------------------|-------------------------------------------|
| ChartContainer          | Chart wrapper with states                    | `/ui/chart-container.tsx`                |
| CashflowChart           | Cash flow trend visualization                | `/dashboard/cashflow-chart.tsx`          |
| CategorySpendChart      | Category spending visualization              | `/dashboard/category-spend-chart.tsx`    |
| Sparkline               | Mini line charts                             | `/ui/sparkline.tsx`                      |

### Tables
| Component               | Purpose                                      | Location                                  |
|-------------------------|----------------------------------------------|-------------------------------------------|
| Table                   | Basic table structure                        | `/ui/table.tsx`                          |
| RecentTransactions      | Transaction listing with categorization      | `/dashboard/recent-transactions.tsx`     |

### Panels
| Component               | Purpose                                      | Location                                  |
|-------------------------|----------------------------------------------|-------------------------------------------|
| InsightsPanel           | Behavioral insights display                  | `/dashboard/insights-panel.tsx`          |
| AnalyticsSummaryBar     | Key metrics summary                          | `/dashboard/analytics-summary-bar.tsx`   |

### Dialogs
| Component               | Purpose                                      | Location                                  |
|-------------------------|----------------------------------------------|-------------------------------------------|
| Dialog                  | Modal dialog                                 | `/ui/dialog.tsx`                         |
| ExplainButton           | Explanation dialog trigger                   | `/ui/explain-button.tsx`                |

### Toolbars
| Component               | Purpose                                      | Location                                  |
|-------------------------|----------------------------------------------|-------------------------------------------|
| Toolbar components      | Workspace action controls                    | `/toolbar/`                              |

### Filters
| Component               | Purpose                                      | Location                                  |
|-------------------------|----------------------------------------------|-------------------------------------------|
| Filter components       | Data filtering controls                      | `/filters/`                              |

### Loading
| Component               | Purpose                                      | Location                                  |
|-------------------------|----------------------------------------------|-------------------------------------------|
| Skeleton                | Loading placeholders                         | `/ui/skeleton.tsx`                       |
| DashboardSkeleton       | Dashboard loading state                      | `/dashboard/dashboard-skeleton.tsx`      |
| DataStateWrapper        | Data state management                        | `/ui/data-state-wrapper.tsx`             |

### Evidence
| Component               | Purpose                                      | Location                                  |
|-------------------------|----------------------------------------------|-------------------------------------------|
| Evidence components     | Evidence chain visualization                 | `/evidence/`                             |

### Widgets
| Component               | Purpose                                      | Location                                  |
|-------------------------|----------------------------------------------|-------------------------------------------|
| RecurringChargesWidget  | Recurring subscription visualization         | `/dashboard/recurring-charges-widget.tsx`|
| TopMerchantsWidget      | Top merchant spending visualization          | `/dashboard/top-merchants-widget.tsx`    |

### UI Components
| Component               | Purpose                                      | Location                                  |
|-------------------------|----------------------------------------------|-------------------------------------------|
| Badge                   | Status indicators                            | `/ui/badge.tsx`                          |
| Button                  | Interactive buttons                          | `/ui/button.tsx`                         |
| Input                   | Form input fields                            | `/ui/input.tsx`                          |
| Select                  | Dropdown selects                             | `/ui/select.tsx`                         |
| Progress                | Progress indicators                          | `/ui/progress.tsx`                       |
| Separator               | Visual separators                            | `/ui/separator.tsx`                      |
| Switch                  | Toggle switches                              | `/ui/switch.tsx`                         |
| Tabs                    | Tabbed interfaces                            | `/ui/tabs.tsx`                           |

### Layout Components
| Component               | Purpose                                      | Location                                  |
|-------------------------|----------------------------------------------|-------------------------------------------|
| MainLayout              | Main application layout                      | `/layout/main-layout.tsx`                |
| Sidebar                 | Primary navigation sidebar                   | `/layout/sidebar.tsx`                    |

### Workspace Components
| Workspace               | Purpose                                      | Location                                  |
|-------------------------|----------------------------------------------|-------------------------------------------|
| Accounts                | Account management components                | `/accounts/`                             |
| Behaviour               | Behavior analysis components                 | `/behaviour/`                            |
| Cards                   | Credit card components                       | `/cards/`                                |
| Cashflow                | Cash flow components                         | `/cashflow/`                             |
| Forecast                | Forecasting components                       | `/forecast/`                             |
| Import                  | Data import components                       | `/import/`                               |
| Investments             | Investment components                        | `/investments/`                          |
| Loans                   | Loan components                              | `/loans/`                                |
| Net Worth               | Net worth components                         | `/net-worth/`                            |
| Reconciliation          | Reconciliation components                    | `/reconciliation/`                       |
| Transaction Table       | Transaction table components                 | `/transaction-table/`                    |

## Component Dependencies

### Core Dependencies
1. **Radix UI**: Dialog, Select, Switch, Tabs primitives
2. **Lucide Icons**: Various icons for UI elements
3. **Recharts**: Charting library (dynamically imported)
4. **Tailwind CSS**: Styling framework
5. **React**: Core UI framework
6. **Next.js**: Framework for SSR/SSG

### Component Hierarchy
```
MainLayout
├── Sidebar
└── Content
    ├── DashboardPage
    │   ├── ChartContainer
    │   │   ├── CashflowChart
    │   │   ├── CategorySpendChart
    │   │   └── BehaviorScoreCard
    │   ├── InsightsPanel
    │   ├── RecentTransactions
    │   ├── RecurringChargesWidget
    │   ├── TopMerchantsWidget
    │   └── AnalyticsSummaryBar
    ├── WorkspacePages
    │   ├── Card components
    │   ├── Table components
    │   ├── Filter components
    │   └── Toolbar components
    └── UI Components
        ├── Dialog
        │   └── ExplainButton
        ├── Badge
        ├── Button
        ├── Input
        ├── Select
        ├── Progress
        ├── Separator
        ├── Switch
        └── Tabs
```

## Component Reusability

### Highly Reusable Components
1. **Card**: Used across all workspaces for content grouping
2. **ChartContainer**: Used for all chart visualizations
3. **Table**: Used for all tabular data displays
4. **Dialog**: Used for all modal dialogs
5. **Button**: Used for all interactive actions
6. **Badge**: Used for status indicators and categorization
7. **Skeleton**: Used for loading states
8. **DataStateWrapper**: Used for data state management

### Workspace-Specific Components
1. **BehaviorScoreCard**: Specific to behavior workspace
2. **CashflowChart**: Specific to cash flow workspace
3. **CategorySpendChart**: Specific to spending analysis
4. **RecurringChargesWidget**: Specific to subscription analysis
5. **TopMerchantsWidget**: Specific to merchant analysis
6. **Workspace-specific components**: Tailored to individual workspaces

### Utility Components
1. **ExplainButton**: Used for metric explanations
2. **Sparkline**: Used for compact data visualization
3. **Separator**: Used for visual separation
4. **Progress**: Used for progress indicators

## Component Gaps

### Missing Components
1. **Financial KPI Cards**: Standardized financial metric cards
2. **Amortization Schedule**: Loan amortization visualization
3. **Utilization Gauge**: Credit utilization visualization
4. **Net Worth Trend**: Net worth trend visualization
5. **Pattern Visualization**: Spending pattern visualization
6. **Alert Components**: Financial alert displays
7. **Recommendation Components**: Actionable recommendation displays
8. **Evidence Chain**: Detailed evidence chain visualization
9. **Scenario Comparison**: Side-by-side scenario comparison
10. **Forecast Visualization**: Financial forecast visualization

### Component Improvements
1. **Customizable Dashboards**: User-defined component layouts
2. **Component Docking**: Drag-and-drop component arrangement
3. **Component Resizing**: Adjustable component sizes
4. **Component Collapsing**: Expand/collapse components
5. **Component Templates**: Predefined component layouts
6. **Component Sharing**: Share component configurations
7. **Component Export**: Export component data
8. **Component Bookmarking**: Save favorite components
9. **Component History**: Component view history
10. **Component Analytics**: Component usage analytics