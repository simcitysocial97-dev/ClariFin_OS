/**
 * Forecast Workspace Page - Stage 4 Forecast Intelligence Workspace
 */

'use client';

import { useForecastCapability } from '@/lib/capabilities/use-forecast-capability';
import { useWorkspaceRegistration } from '@/lib/runtime';
import { ForecastSummary } from '@/components/forecast/forecast-summary';
import { NetWorthProjection } from '@/components/forecast/net-worth-projection';
import { CashflowProjection } from '@/components/forecast/cashflow-projection';
import { ScenarioComparison } from '@/components/forecast/scenario-comparison';
import { InsightsPanel } from '@/components/forecast/forecast-insights-panel';
import { EvidenceDrawer } from '@/components/forecast/forecast-evidence-drawer';
import { ForecastPageSkeleton } from '@/components/forecast/loading-skeleton';
import { ForecastErrorState } from '@/components/forecast/error-state';
import { ForecastEmptyState } from '@/components/forecast/empty-state';

export default function ForecastPage() {
  useWorkspaceRegistration({
    name: 'forecast',
    label: 'Forecast',
    icon: 'chart-line',
    deepLink: '/forecast',
    defaultSurface: 'CHARTS',
    supportedCommands: ['horizon', 'scenarios', 'export', 'refresh'],
    supportedFilters: ['horizon', 'scenario'],
    supportedSelections: [],
  });

  const {
    forecast, loading, error, horizon, setHorizon, clearFilters, refresh,
  } = useForecastCapability();

  if (loading) return <ForecastPageSkeleton />;
  if (error) return <ForecastErrorState message={error.message} onRetry={refresh} />;
  if (!forecast) return <ForecastEmptyState onAction={clearFilters} />;

  return (
    <div className="min-h-screen bg-gray-50 p-4 space-y-4">
      <div className="flex items-center gap-2">
        <label className="text-sm">Horizon (months):</label>
        <input
          type="number" min="1" max="60" value={horizon}
          onChange={e => setHorizon(Number(e.target.value))}
          className="w-20 text-sm border rounded px-2 py-1"
        />
        <button onClick={refresh} className="text-sm px-3 py-1 bg-blue-500 text-white rounded hover:bg-blue-600">Refresh</button>
      </div>
      <ForecastSummary summary={forecast.summary} loading={loading} error={error} />
      <NetWorthProjection projections={forecast.net_worth_projections} loading={loading} error={error} />
      <CashflowProjection projections={forecast.cashflow_projections} loading={loading} error={error} />
      <ScenarioComparison scenarios={forecast.scenarios} loading={loading} error={error} />
      <InsightsPanel forecast={forecast} loading={loading} error={error} />
      <EvidenceDrawer forecast={forecast} isOpen={false} onClose={() => {}} />
    </div>
  );
}
