/**
 * Forecast Workspace Page - Stage 8B Workspace Integration & Surface Migration
 *
 * Simulation Surface - Main analysis surface for forecast.
 * Shell provides: Header, Toolbar, Breadcrumbs, Selection Summary, Evidence Drawer.
 */

'use client';

import { useForecastCapability } from '@/lib/capabilities/use-forecast-capability';
import { ForecastSummary } from '@/components/forecast/forecast-summary';
import { NetWorthProjection } from '@/components/forecast/net-worth-projection';
import { CashflowProjection } from '@/components/forecast/cashflow-projection';
import { ScenarioComparison } from '@/components/forecast/scenario-comparison';
import { InsightsPanel } from '@/components/forecast/forecast-insights-panel';
import { CrossNavigation } from '@/components/forecast/cross-navigation';
import { ForecastPageSkeleton } from '@/components/forecast/loading-skeleton';
import { ForecastErrorState } from '@/components/forecast/error-state';
import { ForecastEmptyState } from '@/components/forecast/empty-state';

/**
 * Forecast Workspace Page
 * Simulation Surface - Only the analysis surface content
 * Shell provides: Header, Toolbar, Filter Panel, Selection Summary, Evidence Drawer
 */
export default function ForecastPage() {
  const {
    forecast,
    loading,
    error,
  } = useForecastCapability();

  // Show loading skeleton
  if (loading) {
    return <ForecastPageSkeleton />;
  }

  // Show error state
  if (error) {
    return (
      <div className="p-4">
        <ForecastErrorState message={error.message} onRetry={() => {}} />
      </div>
    );
  }

  // Show empty state
  if (!forecast) {
    return (
      <div className="p-4">
        <ForecastEmptyState onAction={() => {}} />
      </div>
    );
  }

  return (
    <div className="p-4 space-y-4">
      {/* Simulation Surface - Main content only (no header, no toolbar) */}
      
      {/* Summary Card */}
      <ForecastSummary summary={forecast.summary} loading={loading} error={error} />

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <NetWorthProjection projections={forecast.net_worth_projections} loading={loading} error={error} />
        <CashflowProjection projections={forecast.cashflow_projections} loading={loading} error={error} />
      </div>

      {/* Scenario Comparison */}
      <ScenarioComparison scenarios={forecast.scenarios} loading={loading} error={error} />

      {/* Insights Panel */}
      <InsightsPanel forecast={forecast} loading={loading} error={error} />

      {/* Cross Navigation */}
      <CrossNavigation crossReferences={forecast.navigation?.cross_references} />
    </div>
  );
}