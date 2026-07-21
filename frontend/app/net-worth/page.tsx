/**
 * Net Worth Workspace Page - Stage 8E-C2 Production Visual System Migration
 *
 * Graph Surface - Main analysis surface for net worth.
 * Shell provides: Header, Toolbar, Breadcrumbs, Selection Summary, Evidence Drawer.
 *
 * Migrated: Wrapped in Surface/Panel primitives, removed legacy padding.
 */

'use client';

import { useNetWorthCapability } from '@/lib/capabilities/use-net-worth-capability';
import { NetWorthSummary } from '@/components/net-worth/net-worth-summary';
import { CompositionChart } from '@/components/net-worth/composition-chart';
import { TrendChart } from '@/components/net-worth/trend-chart';
import { AccountBreakdown } from '@/components/net-worth/account-breakdown';
import { InsightsPanel } from '@/components/net-worth/insights-panel';
import { Surface } from '@/components/primitives/surface/surface';
import { Panel, PanelHeader, PanelBody } from '@/components/primitives/panel/panel';
import { Stack } from '@/components/primitives/layout/stack';
import { Grid } from '@/components/primitives/layout/grid';

/**
 * Net Worth Workspace Page
 * Graph Surface - Composed with Surface/Panel primitives
 * Shell provides: Header, Toolbar, Filter Panel, Selection Summary, Evidence Drawer
 */
export default function NetWorthPage() {
  const {
    netWorth,
    loading,
    error,
  } = useNetWorthCapability();

  return (
    <Surface variant="default" density="none" className="flex flex-col h-full">
      <Panel fill>
        <PanelHeader title="Net Worth" />
        <PanelBody scrollable>
          <Stack gap={4} className="p-4">
            {/* Summary Card */}
            <NetWorthSummary netWorth={netWorth} loading={loading} error={error} />

            {/* Charts Row */}
            <Grid gap={4} className="grid-cols-1 lg:grid-cols-2">
              <CompositionChart netWorth={netWorth} loading={loading} error={error} />
              <TrendChart netWorth={netWorth} loading={loading} error={error} />
            </Grid>

            {/* Account Breakdown */}
            <AccountBreakdown netWorth={netWorth} loading={loading} error={error} />

            {/* Insights Panel */}
            <InsightsPanel netWorth={netWorth} loading={loading} error={error} />
          </Stack>
        </PanelBody>
      </Panel>
    </Surface>
  );
}