/**
 * Net Worth Workspace Page - Stage 8B Workspace Integration & Surface Migration
 *
 * Graph Surface - Main analysis surface for net worth.
 * Shell provides: Header, Toolbar, Breadcrumbs, Selection Summary, Evidence Drawer.
 */

'use client';

import { useNetWorthCapability } from '@/lib/capabilities/use-net-worth-capability';
import { NetWorthSummary } from '@/components/net-worth/net-worth-summary';
import { CompositionChart } from '@/components/net-worth/composition-chart';
import { TrendChart } from '@/components/net-worth/trend-chart';
import { AccountBreakdown } from '@/components/net-worth/account-breakdown';
import { InsightsPanel } from '@/components/net-worth/insights-panel';

/**
 * Net Worth Workspace Page
 * Graph Surface - Only the analysis surface content
 * Shell provides: Header, Toolbar, Filter Panel, Selection Summary, Evidence Drawer
 */
export default function NetWorthPage() {
  const {
    netWorth,
    loading,
    error,
  } = useNetWorthCapability();

  return (
    <div className="p-4 space-y-4">
      {/* Graph Surface - Main content only (no header, no toolbar) */}
      
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
  );
}