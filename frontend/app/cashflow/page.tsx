/**
 * Cashflow Workspace Page - Stage 8E-C2 Production Visual System Migration
 */

'use client';

import { useCashflowCapability } from '@/lib/capabilities/use-cashflow-capability';
import { useWorkspaceRegistration } from '@/lib/runtime';
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

export default function CashflowPage() {
  useWorkspaceRegistration({
    name: 'cashflow',
    label: 'Cashflow',
    icon: 'arrow-left-right',
    deepLink: '/cashflow',
    defaultSurface: 'SANKEY',
    supportedCommands: ['refresh', 'export', 'evidence'],
    supportedFilters: ['date', 'period'],
    supportedSelections: ['transaction'],
  });

  const { cashflow, loading, error } = useCashflowCapability();

  if (loading && !cashflow) {
    return (
      <Surface variant="default" density="none" className="flex flex-col h-full">
        <Panel fill><PanelHeader title="Cashflow" /><PanelBody loading><div className="p-4"><CashflowLoadingSkeleton /></div></PanelBody></Panel>
      </Surface>
    );
  }
  if (error && !cashflow) {
    return (
      <Surface variant="default" density="none" className="flex flex-col h-full">
        <Panel fill><PanelHeader title="Cashflow" /><PanelBody error={error.message}><div className="p-4"><CashflowErrorState error={error} onRetry={() => {}} /></div></PanelBody></Panel>
      </Surface>
    );
  }
  if (!cashflow) {
    return (
      <Surface variant="default" density="none" className="flex flex-col h-full">
        <Panel fill><PanelHeader title="Cashflow" /><PanelBody empty emptyMessage="No cashflow data available"><div className="p-4"><CashflowEmptyState onAddData={() => {}} /></div></PanelBody></Panel>
      </Surface>
    );
  }

  return (
    <Surface variant="default" density="none" className="flex flex-col h-full">
      <Panel fill>
        <PanelHeader title="Cashflow" />
        <PanelBody scrollable>
          <Stack gap={4} className="p-4">
            <CashflowSummary cashflow={cashflow} loading={loading} error={error} />
            <Grid gap={4} className="grid-cols-1 lg:grid-cols-2">
              <MonthlyTrend monthly={cashflow.monthly} loading={loading} error={error} />
              <CategoryBreakdown categories={cashflow.categories} loading={loading} error={error} />
            </Grid>
            <TransactionList transactions={cashflow.transactions} loading={loading} error={error} />
            <InsightsPanel insights={cashflow.insights} loading={loading} error={error} />
          </Stack>
        </PanelBody>
      </Panel>
    </Surface>
  );
}
