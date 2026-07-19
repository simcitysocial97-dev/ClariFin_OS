/**
 * Net Worth Workspace Page - Stage 4 Net Worth Intelligence Workspace
 *
 * Composes all net worth components into a complete workspace page.
 *
 * Architecture Flow: Backend → API → DTO → Mapper → ViewModel → Capability → Workspace → Components → Page
 */

import { useNetWorthCapability } from '@/lib/capabilities/use-net-worth-capability';
import { NetWorthSummary } from '@/components/net-worth/net-worth-summary';
import { CompositionChart } from '@/components/net-worth/composition-chart';
import { TrendChart } from '@/components/net-worth/trend-chart';
import { AccountBreakdown } from '@/components/net-worth/account-breakdown';
import { InsightsPanel } from '@/components/net-worth/insights-panel';
import { EvidenceDrawer } from '@/components/net-worth/evidence-drawer';
import { NetWorthToolbar } from '@/components/net-worth/net-worth-toolbar';

/**
 * Net Worth Workspace Page
 */
export default function NetWorthPage() {
  const {
    netWorth,
    loading,
    error,
    dateRange,
    accountTypes,
    period,
    isEvidenceDrawerOpen,
    setDateRange,
    setAccountTypes,
    setPeriod,
    clearFilters,
    refresh,
    toggleEvidenceDrawer,
  } = useNetWorthCapability();

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Toolbar */}
      <NetWorthToolbar
        onRefresh={refresh}
        onExport={() => {}}
        dateRange={dateRange}
        accountTypes={accountTypes}
        period={period}
        onDateRangeChange={setDateRange}
        onAccountTypesChange={setAccountTypes}
        onPeriodChange={setPeriod}
        onClearFilters={clearFilters}
        searchQuery=""
        onSearchChange={() => {}}
      />

      {/* Main Content */}
      <div className="p-4 space-y-4">
        {/* Summary Card */}
        <NetWorthSummary netWorth={netWorth} loading={loading} error={error} />

        {/* Charts Row */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <CompositionChart netWorth={netWorth} loading={loading} error={error} />
          <TrendChart netWorth={netWorth} loading={loading} error={error} />
        </div>

        {/* Account Breakdown */}
        <AccountBreakdown netWorth={netWorth} loading={loading} error={error} />

        {/* Insights Panel */}
        <InsightsPanel netWorth={netWorth} loading={loading} error={error} />
      </div>

      {/* Evidence Drawer */}
      <EvidenceDrawer
        netWorth={netWorth}
        isOpen={isEvidenceDrawerOpen}
        onClose={toggleEvidenceDrawer}
      />
    </div>
  );
}