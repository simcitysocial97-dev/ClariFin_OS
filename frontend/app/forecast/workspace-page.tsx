/**
 * Forecast Workspace Page - Stage 8E-C2 Production Visual System Migration
 *
 * Simulation Surface - Main analysis surface for forecast.
 * Shell provides: Header, Toolbar, Breadcrumbs, Selection Summary, Evidence Drawer.
 *
 * Migrated: Wrapped in Surface/Panel primitives, removed legacy padding.
 */

'use client';

import { useEffect, useMemo } from 'react';
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
import { Surface } from '@/components/primitives/surface/surface';
import { Panel, PanelHeader, PanelBody } from '@/components/primitives/panel/panel';
import { Stack } from '@/components/primitives/layout/stack';
import { Grid } from '@/components/primitives/layout/grid';
import { commandCenterRuntime } from '@/lib/command-center';

/**
 * Forecast Workspace Page
 * Simulation Surface - Composed with Surface/Panel primitives
 * Shell provides: Header, Toolbar, Filter Panel, Selection Summary, Evidence Drawer
 */
export default function ForecastPage() {
  const {
    forecast,
    loading,
    error,
  } = useForecastCapability();

  // Build view model for shared runtime
  const viewModels = useMemo(() => ({
    forecast: { forecast },
  }), [forecast]);

  // Register workspace with CommandCenterRuntime on mount
  useEffect(() => {
    // Build graph for shared runtime
    commandCenterRuntime.build(viewModels);

    // Register workspace actions
    const workspaceRegistration = {
      name: 'forecast' as const,
      label: 'Forecast',
      icon: 'crystal-ball',
      deepLink: '/forecast',
      viewModelKey: 'forecast',
      description: 'Financial projections and scenarios',
      defaultSurface: 'SIMULATION' as const,
      graphAdapter: 'forecast',
      supportedCommands: ['horizon', 'scenarios', 'refresh', 'simulate'],
      supportedFilters: ['horizon', 'scenarios'],
      supportedSelections: ['projection'],
      inspectorSections: ['context', 'projections', 'scenarios', 'insights'],
      keyboardShortcuts: {
        'h': 'horizon',
        's': 'scenarios',
        'r': 'refresh',
      },
    };

    commandCenterRuntime.registerWorkspace(workspaceRegistration);

    return () => {
      commandCenterRuntime.unregisterWorkspace('forecast');
    };
  }, [viewModels]);

  // Show loading skeleton
  if (loading) {
    return (
      <Surface variant="default" density="none" className="flex flex-col h-full">
        <Panel fill>
          <PanelHeader title="Forecast" />
          <PanelBody loading>
            <div className="p-4">
              <ForecastPageSkeleton />
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
          <PanelHeader title="Forecast" />
          <PanelBody error={error.message}>
            <div className="p-4">
              <ForecastErrorState message={error.message} onRetry={() => {}} />
            </div>
          </PanelBody>
        </Panel>
      </Surface>
    );
  }

  // Show empty state
  if (!forecast) {
    return (
      <Surface variant="default" density="none" className="flex flex-col h-full">
        <Panel fill>
          <PanelHeader title="Forecast" />
          <PanelBody empty emptyMessage="No forecast data available">
            <div className="p-4">
              <ForecastEmptyState onAction={() => {}} />
            </div>
          </PanelBody>
        </Panel>
      </Surface>
    );
  }

  return (
    <Surface variant="default" density="none" className="flex flex-col h-full">
      <Panel fill>
        <PanelHeader title="Forecast" />
        <PanelBody scrollable>
          <Stack gap={4} className="p-4">
            {/* Summary Card */}
            <ForecastSummary summary={forecast.summary} loading={loading} error={error} />

            {/* Charts Row */}
            <Grid gap={4} className="grid-cols-1 lg:grid-cols-2">
              <NetWorthProjection projections={forecast.net_worth_projections} loading={loading} error={error} />
              <CashflowProjection projections={forecast.cashflow_projections} loading={loading} error={error} />
            </Grid>

            {/* Scenario Comparison */}
            <ScenarioComparison scenarios={forecast.scenarios} loading={loading} error={error} />

            {/* Insights Panel */}
            <InsightsPanel forecast={forecast} loading={loading} error={error} />

            {/* Cross Navigation */}
            <CrossNavigation crossReferences={forecast.navigation?.cross_references} />
          </Stack>
        </PanelBody>
      </Panel>
    </Surface>
  );
}