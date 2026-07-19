/**
 * Reconciliation Workspace Page - Stage 4 Reconciliation Intelligence Workspace
 *
 * Composes all reconciliation components into a complete workspace page.
 *
 * Architecture Flow: Backend → API → DTO → Mapper → ViewModel → Capability → Workspace → Components → Page
 */

'use client';

import { useReconciliationCapability } from '@/lib/capabilities/use-reconciliation-capability';
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

/**
 * Reconciliation Workspace Page
 */
export default function ReconciliationPage() {
  const {
    reconciliation,
    loading,
    error,
    status,
    banks,
    isEvidenceDrawerOpen,
    setStatus,
    setBanks,
    clearFilters,
    refresh,
    toggleEvidenceDrawer,
  } = useReconciliationCapability();

  // Show loading skeleton
  if (loading) {
    return <ReconciliationPageSkeleton />;
  }

  // Show error state
  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 p-4">
        <ReconciliationErrorState message={error.message} onRetry={refresh} />
      </div>
    );
  }

  // Show empty state
  if (!reconciliation || reconciliation.statements.length === 0) {
    return (
      <div className="min-h-screen bg-gray-50 p-4">
        <ReconciliationEmptyState onAction={clearFilters} />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Toolbar */}
      <ReconciliationToolbar
        onRefresh={refresh}
        onExport={() => {}}
        searchQuery=""
        onSearchChange={() => {}}
        statuses={status}
        banks={banks}
        onStatusesChange={setStatus}
        onBanksChange={setBanks}
        onClearFilters={clearFilters}
        onApplyFilters={() => {}}
      />

      {/* Main Content */}
      <div className="p-4 space-y-4">
        {/* Summary Card */}
        <ReconciliationSummary statements={reconciliation.statements} loading={loading} error={error} />

        {/* Charts Row */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <StatusOverview statusOverview={reconciliation.status_overview} loading={loading} error={error} />
          <DiscrepancyList discrepancies={reconciliation.discrepancies} loading={loading} error={error} />
        </div>

        {/* Audit Trail */}
        <AuditTrail auditTrail={reconciliation.audit_trail} loading={loading} error={error} />

        {/* Insights Panel */}
        <InsightsPanel reconciliation={reconciliation} loading={loading} error={error} />

        {/* Cross Navigation */}
        <CrossNavigation crossReferences={reconciliation.navigation?.cross_references} />
      </div>

      {/* Evidence Drawer */}
      <EvidenceDrawer
        reconciliation={reconciliation}
        isOpen={isEvidenceDrawerOpen}
        onClose={toggleEvidenceDrawer}
      />
    </div>
  );
}