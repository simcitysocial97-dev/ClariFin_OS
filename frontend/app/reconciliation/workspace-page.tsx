/**
 * Reconciliation Workspace Page - Stage 4 Reconciliation Intelligence Workspace
 */

'use client';

import { useReconciliationCapability } from '@/lib/capabilities/use-reconciliation-capability';
import { useWorkspaceRegistration } from '@/lib/runtime';
import { ReconciliationSummary } from '@/components/reconciliation/reconciliation-summary';
import { StatusOverview } from '@/components/reconciliation/status-overview';
import { DiscrepancyList } from '@/components/reconciliation/discrepancy-list';
import { AuditTrail } from '@/components/reconciliation/audit-trail';
import { InsightsPanel } from '@/components/reconciliation/reconciliation-insights-panel';
import { EvidenceDrawer } from '@/components/reconciliation/reconciliation-evidence-drawer';
import { ReconciliationToolbar } from '@/components/reconciliation/reconciliation-toolbar';
import { CrossNavigation } from '@/components/reconciliation/cross-navigation';
import { ReconciliationPageSkeleton } from '@/components/reconciliation/loading-skeleton';
import { ReconciliationErrorState } from '@/components/reconciliation/error-state';
import { ReconciliationEmptyState } from '@/components/reconciliation/empty-state';

export default function ReconciliationPage() {
  useWorkspaceRegistration({
    name: 'reconciliation',
    label: 'Reconciliation',
    icon: 'check-square',
    deepLink: '/reconciliation',
    defaultSurface: 'TABLE',
    supportedCommands: ['filter', 'search', 'export', 'refresh'],
    supportedFilters: ['status', 'bank'],
    supportedSelections: ['reconciliation'],
  });

  const {
    reconciliation, loading, error, status, banks, isEvidenceDrawerOpen,
    setStatus, setBanks, clearFilters, refresh, toggleEvidenceDrawer,
  } = useReconciliationCapability();

  if (loading) return <ReconciliationPageSkeleton />;
  if (error) return <ReconciliationErrorState message={error.message} onRetry={refresh} />;
  if (!reconciliation || reconciliation.statements.length === 0) return <ReconciliationEmptyState onAction={clearFilters} />;

  return (
    <div className="min-h-screen bg-gray-50">
      <ReconciliationToolbar
        onRefresh={refresh} onExport={() => {}} searchQuery="" onSearchChange={() => {}}
        statuses={status} banks={banks} onStatusesChange={setStatus} onBanksChange={setBanks}
        onClearFilters={clearFilters} onApplyFilters={() => {}}
      />
      <div className="p-4 space-y-4">
        <ReconciliationSummary statements={reconciliation.statements} loading={loading} error={error} />
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <StatusOverview statusOverview={reconciliation.status_overview} loading={loading} error={error} />
          <DiscrepancyList discrepancies={reconciliation.discrepancies} loading={loading} error={error} />
        </div>
        <AuditTrail auditTrail={reconciliation.audit_trail} loading={loading} error={error} />
        <InsightsPanel reconciliation={reconciliation} loading={loading} error={error} />
        <CrossNavigation crossReferences={reconciliation.navigation?.cross_references} />
      </div>
      <EvidenceDrawer reconciliation={reconciliation} isOpen={isEvidenceDrawerOpen} onClose={toggleEvidenceDrawer} />
    </div>
  );
}
