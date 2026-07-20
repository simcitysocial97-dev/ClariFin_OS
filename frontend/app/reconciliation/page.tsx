/**
 * Reconciliation Workspace Page - Stage 8B Workspace Integration & Surface Migration
 *
 * Table Surface - Main analysis surface for reconciliation.
 * Shell provides: Header, Toolbar, Breadcrumbs, Selection Summary, Evidence Drawer.
 */

'use client';

import { ReconciliationMatchCard } from '@/components/reconciliation/reconciliation-match-card';
import { ReconciliationSummaryBar } from '@/components/reconciliation/reconciliation-summary-bar';
import { ReconciliationEmptyState } from '@/components/reconciliation/reconciliation-empty-state';
import { usePendingReconciliations } from '@/lib/hooks/use-reconciliation';

/**
 * Reconciliation Workspace Page
 * Table Surface - Only the analysis surface content
 * Shell provides: Header, Toolbar, Filter Panel, Selection Summary, Evidence Drawer
 */
export default function ReconciliationPage() {
  const { data, loading, error } = usePendingReconciliations();

  if (loading) {
    return (
      <div className="p-4">
        <p>Loading pending matches...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4">
        <p className="text-red-500">Error loading reconciliations: {error.message}</p>
      </div>
    );
  }

  const matches = data?.reconciliations ?? [];

  return (
    <div className="p-4 space-y-4">
      {/* Table Surface - Main content only (no header, no toolbar) */}
      
      <ReconciliationSummaryBar />
      
      {matches.length === 0 ? (
        <ReconciliationEmptyState />
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {matches.map((match) => (
            <ReconciliationMatchCard key={match.id} match={match} />
          ))}
        </div>
      )}
    </div>
  );
}