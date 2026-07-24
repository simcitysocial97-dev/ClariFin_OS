/**
 * Investments Workspace Page - Stage 4 Investments Intelligence Workspace
 *
 * Composes all investments components into a complete workspace page.
 *
 * Architecture Flow: Backend → API → DTO → Mapper → ViewModel → Capability → Workspace → Components → Page
 */

'use client';

import { useInvestmentsCapability } from '@/lib/capabilities/use-investments-capability';
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

/**
 * Investments Workspace Page
 */
export default function InvestmentsPage() {
  const {
    investments,
    loading,
    error,
    investmentTypes,
    institutions,
    statuses,
    isEvidenceDrawerOpen,
    setInvestmentTypes,
    setInstitutions,
    setStatuses,
    clearFilters,
    refresh,
    toggleEvidenceDrawer,
  } = useInvestmentsCapability();

  // Show loading skeleton
  if (loading) {
    return <InvestmentsPageSkeleton />;
  }

  // Show error state
  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 p-4">
        <InvestmentsErrorState message={error.message} onRetry={refresh} />
      </div>
    );
  }

  // Show empty state
  if (!investments || investments.investments.length === 0) {
    return (
      <div className="min-h-screen bg-gray-50 p-4">
        <InvestmentsEmptyState onAction={clearFilters} />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Toolbar */}
      <InvestmentsToolbar
        onRefresh={refresh}
        onExport={() => {}}
        searchQuery=""
        onSearchChange={() => {}}
        investmentTypes={investmentTypes}
        institutions={institutions}
        statuses={statuses}
        onInvestmentTypesChange={setInvestmentTypes}
        onInstitutionsChange={setInstitutions}
        onStatusesChange={setStatuses}
        onClearFilters={clearFilters}
        onApplyFilters={() => {}}
      />

      {/* Main Content */}
      <div className="p-4 space-y-4">
        {/* Summary Card */}
        <InvestmentsSummary investments={investments} loading={loading} error={error} />

        {/* Charts Row */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <PerformanceChart investments={investments} loading={loading} error={error} />
          <AssetAllocation investments={investments} loading={loading} error={error} />
        </div>

        {/* Holdings Table */}
        <HoldingsTable investments={investments} loading={loading} error={error} />

        {/* Insights Panel */}
        <InsightsPanel investments={investments} loading={loading} error={error} />

        {/* Cross Navigation */}
        <CrossNavigation crossReferences={investments.navigation?.cross_references} />
      </div>

      {/* Evidence Drawer */}
      <EvidenceDrawer
        investments={investments}
        isOpen={isEvidenceDrawerOpen}
        onClose={toggleEvidenceDrawer}
      />
    </div>
  );
}