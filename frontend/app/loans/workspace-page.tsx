/**
 * Loans Workspace Page - Stage 4 Loans Intelligence Workspace
 */

'use client';

import { useLoansCapability } from '@/lib/capabilities/use-loans-capability';
import { useWorkspaceRegistration } from '@/lib/runtime';
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

export default function LoansPage() {
  useWorkspaceRegistration({
    name: 'loans',
    label: 'Loans',
    icon: 'landmark',
    deepLink: '/loans',
    defaultSurface: 'TABLE',
    supportedCommands: ['filter', 'search', 'export', 'refresh'],
    supportedFilters: ['loan-type', 'lender', 'status'],
    supportedSelections: ['loan'],
  });

  const {
    loans, loading, error, loanTypes, lenders, statuses,
    isEvidenceDrawerOpen, setLoanTypes, setLenders, setStatuses,
    clearFilters, refresh, toggleEvidenceDrawer,
  } = useLoansCapability();

  if (loading) return <LoansPageSkeleton />;
  if (error) return <LoansErrorState message={error.message} onRetry={refresh} />;
  if (!loans || loans.loans.length === 0) return <LoansEmptyState onAction={clearFilters} />;

  return (
    <div className="min-h-screen bg-gray-50">
      <LoansToolbar
        onRefresh={refresh} onExport={() => {}} searchQuery="" onSearchChange={() => {}}
        loanTypes={loanTypes} lenders={lenders} statuses={statuses}
        onLoanTypesChange={setLoanTypes} onLendersChange={setLenders} onStatusesChange={setStatuses}
        onClearFilters={clearFilters} onApplyFilters={() => {}}
      />
      <div className="p-4 space-y-4">
        <LoansSummary loans={loans} loading={loading} error={error} />
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <AmortizationSchedule loans={loans} loading={loading} error={error} />
          <PaymentProgress loans={loans} loading={loading} error={error} />
        </div>
        <InterestAnalysis loans={loans} loading={loading} error={error} />
        <InsightsPanel loans={loans} loading={loading} error={error} />
        <CrossNavigation crossReferences={loans.navigation?.cross_references} />
      </div>
      <EvidenceDrawer loans={loans} isOpen={isEvidenceDrawerOpen} onClose={toggleEvidenceDrawer} />
    </div>
  );
}
