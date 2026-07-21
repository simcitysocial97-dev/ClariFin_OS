/**
 * Behaviour Workspace Page - Stage 8E-C2 Production Visual System Migration
 *
 * Timeline Surface - Main analysis surface for behaviour.
 * Shell provides: Header, Toolbar, Breadcrumbs, Selection Summary, Evidence Drawer.
 *
 * Migrated: Wrapped in Surface/Panel primitives, removed legacy padding.
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
import { Surface } from '@/components/primitives/surface/surface';
import { Panel, PanelHeader, PanelBody } from '@/components/primitives/panel/panel';
import { Stack } from '@/components/primitives/layout/stack';
import { Grid } from '@/components/primitives/layout/grid';

/**
 * Behaviour Workspace Page
 * Timeline Surface - Composed with Surface/Panel primitives
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
    return (
      <Surface variant="default" density="none" className="flex flex-col h-full">
        <Panel fill>
          <PanelHeader title="Behaviour" />
          <PanelBody loading>
            <div className="p-4">
              <BehaviourPageSkeleton />
            </div>
          </PanelBody>
        </Panel>
      </Surface>
    );
  }

  // Show error state
  if (error) {
    return (
      <Surface variant="default" density="none" className="flex flex-col h-full">
        <Panel fill>
          <PanelHeader title="Behaviour" />
          <PanelBody error={error.message}>
            <div className="p-4">
              <BehaviourErrorState message={error.message} onRetry={() => {}} />
            </div>
          </PanelBody>
        </Panel>
      </Surface>
    );
  }

  // Show empty state
  if (!behaviour) {
    return (
      <Surface variant="default" density="none" className="flex flex-col h-full">
        <Panel fill>
          <PanelHeader title="Behaviour" />
          <PanelBody empty emptyMessage="No behaviour data available">
            <div className="p-4">
              <BehaviourEmptyState onAction={() => {}} />
            </div>
          </PanelBody>
        </Panel>
      </Surface>
    );
  }

  return (
    <Surface variant="default" density="none" className="flex flex-col h-full">
      <Panel fill>
        <PanelHeader title="Behaviour" />
        <PanelBody scrollable>
          <Stack gap={4} className="p-4">
            {/* Score Card */}
            <BehaviourScore score={behaviour.wellness_score} loading={loading} error={error} />

            {/* Charts Row */}
            <Grid gap={4} className="grid-cols-1 lg:grid-cols-2">
              <SpendingPatterns patterns={behaviour.spending_patterns} loading={loading} error={error} />
              <WellnessRadar wellnessRadar={behaviour.wellness_radar} loading={loading} error={error} />
            </Grid>

            {/* Additional Metrics */}
            <Grid gap={4} className="grid-cols-1 lg:grid-cols-2">
              <SavingsRate savingsRate={behaviour.savings_rate} loading={loading} error={error} />
              <DebtHealth debtHealth={behaviour.debt_health} loading={loading} error={error} />
            </Grid>

            {/* Insights Panel */}
            <InsightsPanel behaviour={behaviour} loading={loading} error={error} />

            {/* Cross Navigation */}
            <CrossNavigation crossReferences={behaviour.navigation?.cross_references} />
          </Stack>
        </PanelBody>
      </Panel>
    </Surface>
  );
}