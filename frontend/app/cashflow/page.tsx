/**
 * Cashflow Workspace Page - Stage 4 Cashflow Truth Workspace
 *
 * Composes all cashflow components into a complete workspace page.
 *
 * Architecture Flow: Backend → API → DTO → Mapper → ViewModel → Capability → Workspace → Components → Page
 */

'use client';

import { useCashflowCapability } from '@/lib/capabilities/use-cashflow-capability';
import { CashflowSummary } from '@/components/cashflow/cashflow-summary';
import { MonthlyTrend } from '@/components/cashflow/monthly-trend';
import { CategoryBreakdown } from '@/components/cashflow/category-breakdown';
import { TransactionList } from '@/components/cashflow/transaction-list';
import { InsightsPanel } from '@/components/cashflow/insights-panel';
import { EvidenceDrawer } from '@/components/cashflow/evidence-drawer';
import { CashflowToolbar } from '@/components/cashflow/cashflow-toolbar';
import { CashflowLoadingSkeleton } from '@/components/cashflow/loading-skeleton';
import { CashflowErrorState } from '@/components/cashflow/error-state';
import { CashflowEmptyState } from '@/components/cashflow/empty-state';

/**
 * Cashflow Workspace Page
 */
export default function CashflowPage() {
  const {
    cashflow,
    loading,
    error,
    isEvidenceDrawerOpen,
    refresh,
    toggleEvidenceDrawer,
  } = useCashflowCapability();

  // Loading state
  if (loading && !cashflow) {
    return (
      <div className="min-h-screen bg-gray-50">
        <div className="p-4">
          <CashflowLoadingSkeleton />
        </div>
      </div>
    );
  }

  // Error state
  if (error && !cashflow) {
    return (
      <div className="min-h-screen bg-gray-50">
        <div className="p-4">
          <CashflowErrorState error={error} onRetry={refresh} />
        </div>
      </div>
    );
  }

  // Empty state
  if (!cashflow) {
    return (
      <div className="min-h-screen bg-gray-50">
        <div className="p-4">
          <CashflowEmptyState />
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Toolbar */}
      <CashflowToolbar
        onRefresh={refresh}
        onExport={() => {}}
        onShare={() => {}}
        onShowEvidence={toggleEvidenceDrawer}
        onSearch={() => {}}
        onClearSearch={() => {}}
      />

      {/* Main Content */}
      <div className="p-4 space-y-4">
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

      {/* Evidence Drawer */}
      <EvidenceDrawer
        isOpen={isEvidenceDrawerOpen}
        onClose={toggleEvidenceDrawer}
        evidenceChain={cashflow.evidence_chain}
      />
    </div>
  );
}