/**
 * Investments Workspace Page - Stage 4 Investments Intelligence Workspace
 */

'use client';

import { useInvestmentsCapability } from '@/lib/capabilities/use-investments-capability';
import { useWorkspaceRegistration } from '@/lib/runtime';
import { InvestmentsSummary } from '@/components/investments/investments-summary';
import { PerformanceChart } from '@/components/investments/performance-chart';
import { AssetAllocation } from '@/components/investments/asset-allocation';
import { HoldingsTable } from '@/components/investments/holdings-table';
import { InsightsPanel } from '@/components/investments/investments-insights-panel';
import { EvidenceDrawer } from '@/components/investments/investments-evidence-drawer';
import { InvestmentsToolbar } from '@/components/investments/investments-toolbar';
import { CrossNavigation } from '@/components/investments/cross-navigation';
import { InvestmentsPageSkeleton } from '@/components/investments/loading-skeleton';
import { InvestmentsErrorState } from '@/components/investments/error-state';
import { InvestmentsEmptyState } from '@/components/investments/empty-state';

export default function InvestmentsPage() {
  useWorkspaceRegistration({
    name: 'investments',
    label: 'Investments',
    icon: 'trending-up',
    deepLink: '/investments',
    defaultSurface: 'TABLE',
    supportedCommands: ['filter', 'search', 'export', 'refresh'],
    supportedFilters: ['investment-type', 'institution', 'status'],
    supportedSelections: ['investment'],
  });

  const {
    investments, loading, error, investmentTypes, institutions, statuses,
    isEvidenceDrawerOpen, setInvestmentTypes, setInstitutions, setStatuses,
    clearFilters, refresh, toggleEvidenceDrawer,
  } = useInvestmentsCapability();

  if (loading) return <InvestmentsPageSkeleton />;
  if (error) return <InvestmentsErrorState message={error.message} onRetry={refresh} />;
  if (!investments || investments.investments.length === 0) return <InvestmentsEmptyState onAction={clearFilters} />;

  return (
    <div className="min-h-screen bg-gray-50">
      <InvestmentsToolbar
        onRefresh={refresh} onExport={() => {}} searchQuery="" onSearchChange={() => {}}
        investmentTypes={investmentTypes} institutions={institutions} statuses={statuses}
        onInvestmentTypesChange={setInvestmentTypes} onInstitutionsChange={setInstitutions} onStatusesChange={setStatuses}
        onClearFilters={clearFilters} onApplyFilters={() => {}}
      />
      <div className="p-4 space-y-4">
        <InvestmentsSummary investments={investments} loading={loading} error={error} />
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <PerformanceChart investments={investments} loading={loading} error={error} />
          <AssetAllocation investments={investments} loading={loading} error={error} />
        </div>
        <HoldingsTable investments={investments} loading={loading} error={error} />
        <InsightsPanel investments={investments} loading={loading} error={error} />
        <CrossNavigation crossReferences={investments.navigation?.cross_references} />
      </div>
      <EvidenceDrawer investments={investments} isOpen={isEvidenceDrawerOpen} onClose={toggleEvidenceDrawer} />
    </div>
  );
}
