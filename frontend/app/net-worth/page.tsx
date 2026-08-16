/**
 * Net Worth Workspace Page - Stage 8E-C2 Production Visual System Migration
 */

'use client';

import { useNetWorthCapability } from '@/lib/capabilities/use-net-worth-capability';
import { useWorkspaceRegistration } from '@/lib/runtime';
import { NetWorthSummary } from '@/components/net-worth/net-worth-summary';
import { CompositionChart } from '@/components/net-worth/composition-chart';
import { TrendChart } from '@/components/net-worth/trend-chart';
import { AccountBreakdown } from '@/components/net-worth/account-breakdown';
import { InsightsPanel } from '@/components/net-worth/insights-panel';
import { Surface } from '@/components/primitives/surface/surface';
import { Panel, PanelHeader, PanelBody } from '@/components/primitives/panel/panel';
import { Stack } from '@/components/primitives/layout/stack';
import { Grid } from '@/components/primitives/layout/grid';

export default function NetWorthPage() {
  useWorkspaceRegistration({
    name: 'net-worth',
    label: 'Net Worth',
    icon: 'scale',
    deepLink: '/net-worth',
    defaultSurface: 'GRAPH',
    supportedCommands: ['date-range', 'period', 'export', 'refresh'],
    supportedFilters: ['date', 'account-type', 'period'],
    supportedSelections: ['account', 'investment'],
  });

  const { netWorth, loading, error } = useNetWorthCapability();

  return (
    <Surface variant="default" density="none" className="flex flex-col h-full">
      <Panel fill>
        <PanelHeader title="Net Worth" />
        <PanelBody scrollable>
          <Stack gap={4} className="p-4">
            <NetWorthSummary netWorth={netWorth} loading={loading} error={error} />
            <Grid gap={4} className="grid-cols-1 lg:grid-cols-2">
              <CompositionChart netWorth={netWorth} loading={loading} error={error} />
              <TrendChart netWorth={netWorth} loading={loading} error={error} />
            </Grid>
            <AccountBreakdown netWorth={netWorth} loading={loading} error={error} />
            <InsightsPanel netWorth={netWorth} loading={loading} error={error} />
          </Stack>
        </PanelBody>
      </Panel>
    </Surface>
  );
}
