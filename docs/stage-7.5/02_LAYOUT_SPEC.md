# Layout Specification - Stage 7.5

## Overview

This document specifies the visual layout patterns, component composition, and responsive design rules for the ClariFin_OS experience.

---

## Global Layout Structure

### Root Layout (`app/layout.tsx`)
```
<ThemeProvider>
  <QueryProvider>
    <MemberProvider>
      <ErrorBoundary>
        <MainLayout>
          {children}
        </MainLayout>
      </ErrorBoundary>
      <Toaster />
    </MemberProvider>
  </QueryProvider>
</ThemeProvider>
```

### Main Layout (`components/layout/main-layout.tsx`)
```
<div className="min-h-screen bg-background">
  <Sidebar />
  <main className="lg:ml-64 transition-all duration-300 min-h-screen">
    <div className="container mx-auto p-6 lg:p-8">
      {children}
    </div>
  </main>
</div>
```

---

## Sidebar Layout (`components/layout/sidebar.tsx`)

### Desktop Layout
- Fixed position, left-aligned
- Width: 224px (56) or 56px (collapsed)
- Full height, flex column
- Header: Logo + App name
- Net Worth chip with formatted value
- Navigation sections with grouped items
- Footer: Settings + Theme toggle

### Mobile Layout
- Sheet (slide-out drawer)
- Trigger button (Menu icon) fixed top-left
- Same content structure as desktop

### Navigation Structure
```
Header
  └── Wallet icon + "ClariFin" (when expanded)

Net Worth Chip
  └── Wallet icon + balance display

Navigation Sections
  └── Overview
      └── Dashboard (LayoutDashboard icon)
  └── Manage
      └── Transactions (ArrowUpDown icon)
      └── Accounts (Building2 icon)
      └── Credit Cards (CreditCard icon)

Footer
  └── Collapse button (desktop)
  └── Settings (Settings icon)
  └── Theme toggle
```

---

## Workspace Layout Patterns

### Pattern A: Standard Workspace (Dashboard, Accounts, Cards, Loans, Investments)

```
<div className="container mx-auto py-6 space-y-6">
  {/* Header Row */}
  <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
    <div>
      <h1 className="text-2xl font-bold">Title</h1>
      <p className="text-gray-500 text-sm">Description</p>
    </div>
    <ActionButtons />
  </div>

  {/* Summary Cards Row (optional) */}
  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
    <SummaryCard />
  </div>

  {/* Main Content */}
  <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
    <div className="lg:col-span-2 space-y-6">
      <Section>
        <h2 className="text-sm font-medium text-muted-foreground mb-3">Section Title</h2>
        <Content />
      </Section>
    </div>
    <div className="space-y-6">
      <Section />
    </div>
  </div>

  {/* Error/Empty States */}
  {error && <Alert />}
  {empty && <EmptyState />}
</div>
```

### Pattern B: Intelligence Workspace (Net Worth, Cashflow, Behaviour, Forecast)

```
<div className="min-h-screen bg-gray-50">
  {/* Toolbar */}
  <WorkspaceToolbar
    onRefresh={refresh}
    onExport={export}
    onSearchChange={setSearch}
    onClearFilters={clearFilters}
    onApplyFilters={apply}
    {...workspaceSpecificProps}
  />

  {/* Main Content */}
  <div className="p-4 space-y-4">
    {/* Summary Card */}
    <SummaryComponent />

    {/* Charts Row */}
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
      <ChartComponent1 />
      <ChartComponent2 />
    </div>

    {/* Additional Sections */}
    <SectionComponent />

    {/* Insights Panel */}
    <InsightsPanel />
  </div>

  {/* Evidence Drawer */}
  <EvidenceDrawer />
</div>
```

### Pattern C: Transaction Intelligence Workspace

```
<div className="flex flex-col h-full min-h-screen bg-background" role="main">
  {/* Toolbar Region */}
  <WorkspaceToolbar />

  {/* Filter Panel Region */}
  <FilterPanel />

  {/* Transaction Table Region (flex grow) */}
  <div className="flex-1 overflow-auto">
    <TransactionTable />
  </div>

  {/* Pagination Controls */}
  <PaginationControls />

  {/* Selection Summary (conditional) */}
  {selectedIds.size > 0 && <SelectionSummary />}

  {/* Insight Panel */}
  <InsightPanel />

  {/* Action Drawer */}
  <ActionDrawer />

  {/* Evidence Drawer */}
  <EvidenceDrawer />
</div>
```

### Pattern D: Command Center

```
<div className="h-screen flex flex-col">
  {/* Header */}
  <header className="border-b p-4 bg-white">
    <h1 className="text-2xl font-bold">Command Center</h1>
    <PanelTabs />
  </header>

  {/* Main Content (flex-1) */}
  <div className="flex-1 flex overflow-hidden">
    {/* Left Panel (flex-1) */}
    <div className="flex-1 border-r">
      {activePanel === 'graph' && <MoneyGraph />}
      {activePanel === 'timeline' && <Timeline />}
      {activePanel === 'insights' && <InsightFeed />}
      {activePanel === 'search' && <GlobalSearch />}
      {activePanel === 'preview' && <WorkspacePreviews />}
      {activePanel === 'context' && <ContextPanel />}
    </div>

    {/* Right Panel (w-80, conditional) */}
    {activePanel !== 'context' && (
      <div className="w-80 border-l">
        <ContextPanel />
      </div>
    )}
  </div>
</div>
```

---

## Grid System

### Responsive Breakpoints
- `grid-cols-1` - Mobile (default)
- `md:grid-cols-2` - Medium screens (768px+)
- `lg:grid-cols-3` - Large screens (1024px+)
- `lg:grid-cols-4` - Extra large (1280px+)

### Common Patterns
- **KPI Row**: `grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4`
- **Summary Cards**: `grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4`
- **Two-column Content**: `grid grid-cols-1 lg:grid-cols-2 gap-6`
- **Three-column Content**: `grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4`

---

## Component Layout Specifications

### Card Component
```tsx
<Card>
  <CardHeader className="pb-2">
    <CardTitle className="text-sm font-medium">Title</CardTitle>
  </CardHeader>
  <CardContent>
    <div className="flex items-baseline gap-2">
      <span className="text-3xl font-bold">Value</span>
    </div>
    <p className="text-xs text-gray-500 mt-2">Description</p>
  </CardContent>
</Card>
```

### Toolbar Component
- Fixed height header
- Left: Title or controls
- Right: Action buttons
- Background: `bg-white` or `bg-gray-50`
- Border: `border-b`

### Evidence Drawer
- Right-side slide-out panel
- Width: 350-400px
- Header with title and close button
- Content: Evidence items, calculations, sources
- Footer: Confidence score, related nodes

---

## Color System

### Semantic Colors
- **Positive/Income**: `text-green-600`, `bg-green-50`, `border-green-200`
- **Negative/Expense**: `text-red-600`, `bg-red-50`, `border-red-200`
- **Warning**: `text-amber-600`, `bg-amber-50`, `border-amber-200`
- **Neutral**: `text-gray-600`, `bg-gray-100`, `text-muted-foreground`

### Health Score Colors
- **Healthy** (70+): `text-green-600`
- **Warning** (40-69): `text-amber-600`
- **Critical** (<40): `text-red-600`

---

## Typography

### Headings
- Page title: `text-2xl font-bold`
- Section title: `text-lg font-semibold`
- Card title: `text-sm font-medium`

### Body
- Primary text: `text-sm`
- Secondary text: `text-xs text-gray-500` or `text-muted-foreground`
- Labels: `text-xs font-semibold uppercase tracking-widest`

---

## Spacing System

### Container Padding
- Page container: `p-6 lg:p-8` (inside main layout)
- Workspace content: `p-4`
- Card content: `p-4`

### Gaps
- Section gaps: `space-y-6` (major), `space-y-4` (minor)
- Grid gaps: `gap-4` (standard), `gap-6` (wide)

---

## State Handling Patterns

### Loading States
- Skeleton components with `animate-pulse`
- Spinner for inline loading
- Full-page skeleton for workspace loading

### Error States
- Alert component with `variant="destructive"`
- Error message with retry button
- Error boundary for component-level isolation

### Empty States
- Centered content with icon
- Actionable message
- Primary action button

---

## Keyboard Navigation

### Global Shortcuts
- `Ctrl/Cmd + F` - Focus search
- `Ctrl/Cmd + R` - Refresh
- `Escape` - Close evidence drawer

### Transaction Workspace
- `Ctrl/Cmd + G` - Toggle group
- `Ctrl/Cmd + S` - Toggle sort
- `Ctrl/Cmd + A` - Select all visible
- `Delete` - Clear selection

---

## Layout Configuration

### Command Center Panels
```typescript
interface PanelState {
  id: PanelId;
  visible: boolean;
  width?: number;  // default varies by panel
  height?: number;
}

const defaultLayout: LayoutConfig = {
  panels: {
    graph: { id: 'graph', visible: true, width: 800, height: 600 },
    timeline: { id: 'timeline', visible: true, width: 400, height: 300 },
    insights: { id: 'insights', visible: true, width: 300, height: 400 },
    search: { id: 'search', visible: true, width: 300, height: 200 },
    preview: { id: 'preview', visible: true, width: 350, height: 350 },
    context: { id: 'context', visible: true, width: 350, height: 400 },
  },
  favorites: [],
  savedLayouts: {},
};
```

### Persistence
- Layout saved to `localStorage` under key `command-center-layout`
- Favorites and saved layouts persist across sessions

---

## Responsive Design Rules

### Mobile First
- All layouts stack vertically on mobile
- Sidebar becomes slide-out sheet
- Grid columns reduce to 1 on small screens

### Touch Targets
- Minimum 44x44px for interactive elements
- Adequate spacing between touch targets

### Overflow Handling
- Tables and lists: `overflow-auto` with max-height
- Drawers: `max-h-[60vh]` for scroll containment
- Content areas: `flex-1` with scroll management