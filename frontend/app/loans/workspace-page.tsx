/**
 * Loans Workspace Page - Stage 4 Loans Intelligence Workspace
 *
 * Composes all loans components into a complete workspace page.
 *
 * Architecture Flow: Backend → API → DTO → Mapper → ViewModel → Capability → Workspace → Components → Page
 */

'use client';

import { useLoansCapability } from '@/lib/capabilities/use-loans-capability';
import { LoansSummary } from '@/components/loans/loans-summary';
import { AmortizationSchedule } from '@/components/loans/amortization-schedule';
import { PaymentProgress } from '@/components/loans/payment-progress';
import { InterestAnalysis } from '@/components/loans/interest-analysis';
import { InsightsPanel } from '@/components/loans/loans-insights-panel';
import { EvidenceDrawer } from '@/components/loans/loans-evidence-drawer';
import { LoansToolbar } from '@/components/loans/loans-toolbar';
import { CrossNavigation } from '@/components/loans/cross-navigation';
import { LoansPageSkeleton } from '@/components/loans/loading-skeleton';
import { LoansErrorState } from '@/components/loans/error-state';
import { LoansEmptyState } from '@/components/loans/empty-state';

/**
 * Loans Workspace Page
 */
export default function LoansPage() {
  const {
    loans,
    loading,
    error,
    loanTypes,
    lenders,
    statuses,
    isEvidenceDrawerOpen,
    setLoanTypes,
    setLenders,
    setStatuses,
    clearFilters,
    refresh,
    toggleEvidenceDrawer,
  } = useLoansCapability();

  // Show loading skeleton
  if (loading) {
    return <LoansPageSkeleton />;
  }

  // Show error state
  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 p-4">
        <LoansErrorState message={error.message} onRetry={refresh} />
      </div>
    );
  }

  // Show empty state
  if (!loans || loans.loans.length === 0) {
    return (
      <div className="min-h-screen bg-gray-50 p-4">
        <LoansEmptyState onAction={clearFilters} />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Toolbar */}
      <LoansToolbar
        onRefresh={refresh}
        onExport={() => {}}
        searchQuery=""
        onSearchChange={() => {}}
        loanTypes={loanTypes}
        lenders={lenders}
        statuses={statuses}
        onLoanTypesChange={setLoanTypes}
        onLendersChange={setLenders}
        onStatusesChange={setStatuses}
        onClearFilters={clearFilters}
        onApplyFilters={() => {}}
      />

      {/* Main Content */}
      <div className="p-4 space-y-4">
        {/* Summary Card */}
        <LoansSummary loans={loans} loading={loading} error={error} />

        {/* Charts Row */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <AmortizationSchedule loans={loans} loading={loading} error={error} />
          <PaymentProgress loans={loans} loading={loading} error={error} />
        </div>

        {/* Interest Analysis */}
        <InterestAnalysis loans={loans} loading={loading} error={error} />

        {/* Insights Panel */}
        <InsightsPanel loans={loans} loading={loading} error={error} />

        {/* Cross Navigation */}
        <CrossNavigation crossReferences={loans.navigation?.cross_references} />
      </div>

      {/* Evidence Drawer */}
      <EvidenceDrawer
        loans={loans}
        isOpen={isEvidenceDrawerOpen}
        onClose={toggleEvidenceDrawer}
      />
    </div>
  );
}