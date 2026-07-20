/**
 * Cashflow Workspace Page - Stage 8B Workspace Integration & Surface Migration
 *
 * Sankey Surface - Main analysis surface for cashflow.
 * Shell provides: Header, Toolbar, Breadcrumbs, Selection Summary, Evidence Drawer.
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

/**
 * Cashflow Workspace Page
 * Sankey Surface - Only the analysis surface content
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
      <div className="p-4">
        <CashflowLoadingSkeleton />
      </div>
    );
  }

  // Error state
  if (error && !cashflow) {
    return (
      <div className="p-4">
        <CashflowErrorState error={error} onRetry={() => {}} />
      </div>
    );
  }

  // Empty state
  if (!cashflow) {
    return (
      <div className="p-4">
        <CashflowEmptyState onAddData={() => {}} />
      </div>
    );
  }

  return (
    <div className="p-4 space-y-4">
      {/* Sankey Surface - Main content only (no header, no toolbar) */}
      
      {/* Summary Card */}
      <CashflowSummary cashflow={cashflow} loading={loading} error={error} />

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <MonthlyTrend monthly={cashflow.monthly} loading={loading} error={error} />
        <CategoryBreakdown categories={cashflow.categories} loading={loading} error={error} />
      </div>

      {/* Transaction List */}
      <TransactionList transactions={cashflow.transactions} loading={loading} error={error} />

      {/* Insights Panel */}
      <InsightsPanel insights={cashflow.insights} loading={loading} error={error} />
    </div>
  );
}