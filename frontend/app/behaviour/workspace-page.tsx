/**
 * Behaviour Workspace Page - Stage 4 Behaviour Intelligence Workspace
 *
 * Composes all behaviour components into a complete workspace page.
 *
 * Architecture Flow: Backend → API → DTO → Mapper → ViewModel → Capability → Workspace → Components → Page
 */

'use client';

import { useBehaviourCapability } from '@/lib/capabilities/use-behaviour-capability';
import { BehaviourScore } from '@/components/behaviour/behaviour-score';
import { SpendingPatterns } from '@/components/behaviour/spending-patterns';
import { SavingsRate } from '@/components/behaviour/savings-rate';
import { DebtHealth } from '@/components/behaviour/debt-health';
import { WellnessRadar } from '@/components/behaviour/wellness-radar';
import { InsightsPanel } from '@/components/behaviour/behaviour-insights-panel';
import { EvidenceDrawer } from '@/components/behaviour/behaviour-evidence-drawer';
import { BehaviourToolbar } from '@/components/behaviour/behaviour-toolbar';
import { CrossNavigation } from '@/components/behaviour/cross-navigation';
import { BehaviourPageSkeleton } from '@/components/behaviour/loading-skeleton';
import { BehaviourErrorState } from '@/components/behaviour/error-state';
import { BehaviourEmptyState } from '@/components/behaviour/empty-state';

/**
 * Behaviour Workspace Page
 */
export default function BehaviourPage() {
  const {
    behaviour,
    loading,
    error,
    period,
    isEvidenceDrawerOpen,
    setPeriod,
    clearFilters,
    refresh,
    toggleEvidenceDrawer,
  } = useBehaviourCapability();

  // Show loading skeleton
  if (loading) {
    return <BehaviourPageSkeleton />;
  }

  // Show error state
  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 p-4">
        <BehaviourErrorState message={error.message} onRetry={refresh} />
      </div>
    );
  }

  // Show empty state
  if (!behaviour) {
    return (
      <div className="min-h-screen bg-gray-50 p-4">
        <BehaviourEmptyState onAction={clearFilters} />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Toolbar */}
      <BehaviourToolbar
        onRefresh={refresh}
        onExport={() => {}}
        searchQuery=""
        onSearchChange={() => {}}
        period={period}
        onPeriodChange={setPeriod}
        onClearFilters={clearFilters}
        onApplyFilters={() => {}}
      />

      {/* Main Content */}
      <div className="p-4 space-y-4">
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

      {/* Evidence Drawer */}
      <EvidenceDrawer
        behaviour={behaviour}
        isOpen={isEvidenceDrawerOpen}
        onClose={toggleEvidenceDrawer}
      />
    </div>
  );
}