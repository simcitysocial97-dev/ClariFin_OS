/**
 * Behaviour Workspace Page - Stage 4 Behaviour Intelligence Workspace
 */

'use client';

import { useBehaviourCapability } from '@/lib/capabilities/use-behaviour-capability';
import { useWorkspaceRegistration } from '@/lib/runtime';
import { BehaviourScore } from '@/components/behaviour/behaviour-score';
import { SpendingPatterns } from '@/components/behaviour/spending-patterns';
import { WellnessRadar } from '@/components/behaviour/wellness-radar';
import { SavingsRate } from '@/components/behaviour/savings-rate';
import { DebtHealth } from '@/components/behaviour/debt-health';
import { InsightsPanel } from '@/components/behaviour/behaviour-insights-panel';
import { EvidenceDrawer } from '@/components/behaviour/behaviour-evidence-drawer';
import { BehaviourPageSkeleton } from '@/components/behaviour/loading-skeleton';
import { BehaviourErrorState } from '@/components/behaviour/error-state';
import { BehaviourEmptyState } from '@/components/behaviour/empty-state';

export default function BehaviourPage() {
  useWorkspaceRegistration({
    name: 'behaviour',
    label: 'Behaviour',
    icon: 'brain',
    deepLink: '/behaviour',
    defaultSurface: 'GRAPH',
    supportedCommands: ['period', 'export', 'refresh'],
    supportedFilters: ['period'],
    supportedSelections: [],
  });

  const {
    behaviour, loading, error, period, setPeriod, clearFilters, refresh,
  } = useBehaviourCapability();

  if (loading) return <BehaviourPageSkeleton />;
  if (error) return <BehaviourErrorState message={error.message} onRetry={refresh} />;
  if (!behaviour) return <BehaviourEmptyState onAction={clearFilters} />;

  return (
    <div className="min-h-screen bg-gray-50 p-4 space-y-4">
      <div className="flex items-center gap-2">
        <label className="text-sm">Period:</label>
        <select value={period} onChange={e => setPeriod(e.target.value)} className="text-sm border rounded px-2 py-1">
          <option value="">All Time</option>
          <option value="1m">1 Month</option>
          <option value="3m">3 Months</option>
          <option value="6m">6 Months</option>
          <option value="1y">1 Year</option>
        </select>
        <button onClick={refresh} className="text-sm px-3 py-1 bg-blue-500 text-white rounded hover:bg-blue-600">Refresh</button>
      </div>
      <BehaviourScore score={behaviour.wellness_score} loading={loading} error={error} />
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <SpendingPatterns patterns={behaviour.spending_patterns} loading={loading} error={error} />
        <WellnessRadar wellnessRadar={behaviour.wellness_radar} loading={loading} error={error} />
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <SavingsRate savingsRate={behaviour.savings_rate} loading={loading} error={error} />
        <DebtHealth debtHealth={behaviour.debt_health} loading={loading} error={error} />
      </div>
      <InsightsPanel behaviour={behaviour} loading={loading} error={error} />
      <EvidenceDrawer behaviour={behaviour} isOpen={false} onClose={() => {}} />
    </div>
  );
}
