/**
 * Reconciliation Workspace Page - Stage 8E-C2 Production Visual System Migration
 *
 * Table Surface - Main analysis surface for reconciliation.
 * Shell provides: Header, Toolbar, Breadcrumbs, Selection Summary, Evidence Drawer.
 *
 * Migrated: Wrapped in Surface/Panel primitives, removed legacy padding.
 */

'use client';

import { ReconciliationMatchCard } from '@/components/reconciliation/reconciliation-match-card';
import { ReconciliationSummaryBar } from '@/components/reconciliation/reconciliation-summary-bar';
import { ReconciliationEmptyState } from '@/components/reconciliation/reconciliation-empty-state';
import { usePendingReconciliations } from '@/lib/hooks/use-reconciliation';
import { Surface } from '@/components/primitives/surface/surface';
import { Panel, PanelHeader, PanelBody } from '@/components/primitives/panel/panel';
import { Stack } from '@/components/primitives/layout/stack';
import { Grid } from '@/components/primitives/layout/grid';

/**
 * Reconciliation Workspace Page
 * Table Surface - Composed with Surface/Panel primitives
 * Shell provides: Header, Toolbar, Filter Panel, Selection Summary, Evidence Drawer
 */
export default function ReconciliationPage() {
  const { data, loading, error } = usePendingReconciliations();

  if (loading) {
    return (
      <Surface variant="default" density="none" className="flex flex-col h-full">
        <Panel fill>
          <PanelHeader title="Reconciliation" />
          <PanelBody loading>
            <div className="p-4">
              <p>Loading pending matches...</p>
            </div>
          </PanelBody>
        </Panel>
      </Surface>
    );
  }

  if (error) {
    return (
      <Surface variant="default" density="none" className="flex flex-col h-full">
        <Panel fill>
          <PanelHeader title="Reconciliation" />
          <PanelBody error={error.message}>
            <div className="p-4">
              <p className="text-red-500">Error loading reconciliations: {error.message}</p>
            </div>
          </PanelBody>
        </Panel>
      </Surface>
    );
  }

  const matches = data?.reconciliations ?? [];

  return (
    <Surface variant="default" density="none" className="flex flex-col h-full">
      <Panel fill>
        <PanelHeader title="Reconciliation" />
        <PanelBody scrollable>
          <Stack gap={4} className="p-4">
            <ReconciliationSummaryBar />
            
            {matches.length === 0 ? (
              <ReconciliationEmptyState />
            ) : (
              <Grid gap={4} className="grid-cols-1 md:grid-cols-2 lg:grid-cols-3">
                {matches.map((match) => (
                  <ReconciliationMatchCard key={match.id} match={match} />
                ))}
              </Grid>
            )}
          </Stack>
        </PanelBody>
      </Panel>
    </Surface>
  );
}