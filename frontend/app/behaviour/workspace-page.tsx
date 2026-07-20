/**
 * Behaviour Workspace Page - Stage 8B Workspace Integration & Surface Migration
 *
 * Timeline Surface - Main analysis surface for behaviour.
 * Shell provides: Header, Toolbar, Breadcrumbs, Selection Summary, Evidence Drawer.
 */

'use client';

import { useBehaviourCapability } from '@/lib/capabilities/use-behaviour-capability';
import { BehaviourScore } from '@/components/behaviour/behaviour-score';
import { SpendingPatterns } from '@/components/behaviour/spending-patterns';
import { SavingsRate } from '@/components/behaviour/savings-rate';
import { DebtHealth } from '@/components/behaviour/debt-health';
import { WellnessRadar } from '@/components/behaviour/wellness-radar';
import { InsightsPanel } from '@/components/behaviour/behaviour-insights-panel';
import { CrossNavigation } from '@/components/behaviour/cross-navigation';
import { BehaviourPageSkeleton } from '@/components/behaviour/loading-skeleton';
import { BehaviourErrorState } from '@/components/behaviour/error-state';
import { BehaviourEmptyState } from '@/components/behaviour/empty-state';

/**
 * Behaviour Workspace Page
 * Timeline Surface - Only the analysis surface content
 * Shell provides: Header, Toolbar, Filter Panel, Selection Summary, Evidence Drawer
 */
export default function BehaviourPage() {
  const {
    behaviour,
    loading,
    error,
  } = useBehaviourCapability();

  // Show loading skeleton
  if (loading) {
    return <BehaviourPageSkeleton />;
  }

  // Show error state
  if (error) {
    return (
      <div className="p-4">
        <BehaviourErrorState message={error.message} onRetry={() => {}} />
      </div>
    );
  }

  // Show empty state
  if (!behaviour) {
    return (
      <div className="p-4">
        <BehaviourEmptyState onAction={() => {}} />
      </div>
    );
  }

  return (
    <div className="p-4 space-y-4">
      {/* Timeline Surface - Main content only (no header, no toolbar) */}
      
      {/* Score Card */}
      <BehaviourScore score={behaviour.wellness_score} loading={loading} error={error} />

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <SpendingPatterns patterns={behaviour.spending_patterns} loading={loading} error={error} />
        <WellnessRadar wellnessRadar={behaviour.wellness_radar} loading={loading} error={error} />
      </div>

      {/* Additional Metrics */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <SavingsRate savingsRate={behaviour.savings_rate} loading={loading} error={error} />
        <DebtHealth debtHealth={behaviour.debt_health} loading={loading} error={error} />
      </div>

      {/* Insights Panel */}
      <InsightsPanel behaviour={behaviour} loading={loading} error={error} />

      {/* Cross Navigation */}
      <CrossNavigation crossReferences={behaviour.navigation?.cross_references} />
    </div>
  );
}