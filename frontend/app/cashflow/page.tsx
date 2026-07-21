/**
 * Cashflow Workspace Page - Stage 8E-C2 Production Visual System Migration
 *
 * Sankey Surface - Main analysis surface for cashflow.
 * Shell provides: Header, Toolbar, Breadcrumbs, Selection Summary, Evidence Drawer.
 *
 * Migrated: Wrapped in Surface/Panel primitives, removed legacy padding.
 */

'use client';

import { useCashflowCapability } from '@/lib/capabilities/use-cashflow-capability';
import { CashflowSummary } from '@/components/cashflow/cashflow-summary';
import { MonthlyTrend } from '@/components/cashflow/monthly-trend';
import { CategoryBreakdown } from '@/components/cashflow/category-breakdown';
import { TransactionList } from '@/components/cashflow/transaction-list';
import { InsightsPanel } from '@/components/cashflow/insights-panel';
import { CashflowLoadingSkeleton } from '@/components/cashflow/loading-skeleton';
import { CashflowErrorState } from '@/components/cashflow/error-state';
import { CashflowEmptyState } from '@/components/cashflow/empty-state';
import { Surface } from '@/components/primitives/surface/surface';
import { Panel, PanelHeader, PanelBody } from '@/components/primitives/panel/panel';
import { Stack } from '@/components/primitives/layout/stack';
import { Grid } from '@/components/primitives/layout/grid';

/**
 * Cashflow Workspace Page
 * Sankey Surface - Composed with Surface/Panel primitives
 * Shell provides: Header, Toolbar, Filter Panel, Selection Summary, Evidence Drawer
 */
export default function CashflowPage() {
  const {
    cashflow,
    loading,
    error,
  } = useCashflowCapability();

  // Loading state
  if (loading && !cashflow) {
    return (
      <Surface variant="default" density="none" className="flex flex-col h-full">
        <Panel fill>
          <PanelHeader title="Cashflow" />
          <PanelBody loading>
            <div className="p-4">
              <CashflowLoadingSkeleton />
            </div>
          </PanelBody>
        </Panel>
      </Surface>
    );
  }

  // Error state
  if (error && !cashflow) {
    return (
      <Surface variant="default" density="none" className="flex flex-col h-full">
        <Panel fill>
          <PanelHeader title="Cashflow" />
          <PanelBody error={error.message}>
            <div className="p-4">
              <CashflowErrorState error={error} onRetry={() => {}} />
            </div>
          </PanelBody>
        </Panel>
      </Surface>
    );
  }

  // Empty state
  if (!cashflow) {
    return (
      <Surface variant="default" density="none" className="flex flex-col h-full">
        <Panel fill>
          <PanelHeader title="Cashflow" />
          <PanelBody empty emptyMessage="No cashflow data available">
            <div className="p-4">
              <CashflowEmptyState onAddData={() => {}} />
            </div>
          </PanelBody>
        </Panel>
      </Surface>
    );
  }

  return (
    <Surface variant="default" density="none" className="flex flex-col h-full">
      <Panel fill>
        <PanelHeader title="Cashflow" />
        <PanelBody scrollable>
          <Stack gap={4} className="p-4">
            {/* Summary Card */}
            <CashflowSummary cashflow={cashflow} loading={loading} error={error} />

            {/* Charts Row */}
            <Grid gap={4} className="grid-cols-1 lg:grid-cols-2">
              <MonthlyTrend monthly={cashflow.monthly} loading={loading} error={error} />
              <CategoryBreakdown categories={cashflow.categories} loading={loading} error={error} />
            </Grid>

            {/* Transaction List */}
            <TransactionList transactions={cashflow.transactions} loading={loading} error={error} />

            {/* Insights Panel */}
            <InsightsPanel insights={cashflow.insights} loading={loading} error={error} />
          </Stack>
        </PanelBody>
      </Panel>
    </Surface>
  );
}