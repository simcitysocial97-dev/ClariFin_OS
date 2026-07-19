/**
 * Forecast Workspace Page - Stage 4 Forecast Intelligence Workspace
 *
 * Composes all forecast components into a complete workspace page.
 *
 * Architecture Flow: Backend → API → DTO → Mapper → ViewModel → Capability → Workspace → Components → Page
 */

'use client';

import { useForecastCapability } from '@/lib/capabilities/use-forecast-capability';
import { ForecastSummary } from '@/components/forecast/forecast-summary';
import { NetWorthProjection } from '@/components/forecast/net-worth-projection';
import { CashflowProjection } from '@/components/forecast/cashflow-projection';
import { ScenarioComparison } from '@/components/forecast/scenario-comparison';
import { InsightsPanel } from '@/components/forecast/forecast-insights-panel';
import { EvidenceDrawer } from '@/components/forecast/forecast-evidence-drawer';
import { ForecastToolbar } from '@/components/forecast/forecast-toolbar';
import { CrossNavigation } from '@/components/forecast/cross-navigation';
import { ForecastPageSkeleton } from '@/components/forecast/loading-skeleton';
import { ForecastErrorState } from '@/components/forecast/error-state';
import { ForecastEmptyState } from '@/components/forecast/empty-state';

/**
 * Forecast Workspace Page
 */
export default function ForecastPage() {
  const {
    forecast,
    loading,
    error,
    horizon,
    scenarios,
    isEvidenceDrawerOpen,
    setHorizon,
    setScenarios,
    clearFilters,
    refresh,
    toggleEvidenceDrawer,
  } = useForecastCapability();

  // Show loading skeleton
  if (loading) {
    return <ForecastPageSkeleton />;
  }

  // Show error state
  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 p-4">
        <ForecastErrorState message={error.message} onRetry={refresh} />
      </div>
    );
  }

  // Show empty state
  if (!forecast) {
    return (
      <div className="min-h-screen bg-gray-50 p-4">
        <ForecastEmptyState onAction={clearFilters} />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Toolbar */}
      <ForecastToolbar
        onRefresh={refresh}
        onExport={() => {}}
        searchQuery=""
        onSearchChange={() => {}}
        horizon={horizon}
        scenarios={scenarios}
        onHorizonChange={setHorizon}
        onScenariosChange={setScenarios}
        onClearFilters={clearFilters}
        onApplyFilters={() => {}}
      />

      {/* Main Content */}
      <div className="p-4 space-y-4">
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

      {/* Evidence Drawer */}
      <EvidenceDrawer
        forecast={forecast}
        isOpen={isEvidenceDrawerOpen}
        onClose={toggleEvidenceDrawer}
      />
    </div>
  );
}