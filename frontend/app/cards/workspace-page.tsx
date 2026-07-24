/**
 * Credit Cards Workspace Page - Stage 4 Credit Cards Intelligence Workspace
 *
 * Composes all credit cards components into a complete workspace page.
 *
 * Architecture Flow: Backend → API → DTO → Mapper → ViewModel → Capability → Workspace → Components → Page
 */

'use client';

import { useCreditCardsCapability } from '@/lib/capabilities/use-credit-cards-capability';
import { CreditCardsSummary } from '@/components/cards/credit-cards-summary';
import { UtilizationChart } from '@/components/cards/utilization-chart';
import { SpendingByCategory } from '@/components/cards/spending-by-category';
import { InsightsPanel } from '@/components/cards/cards-insights-panel';
import { EvidenceDrawer } from '@/components/cards/cards-evidence-drawer';
import { CreditCardsToolbar } from '@/components/cards/cards-toolbar';
import { CrossNavigation } from '@/components/cards/cross-navigation';
import { CreditCardsPageSkeleton } from '@/components/cards/loading-skeleton';
import { CreditCardsErrorState } from '@/components/cards/error-state';
import { CreditCardsEmptyState } from '@/components/cards/empty-state';

/**
 * Credit Cards Workspace Page
 */
export default function CreditCardsPage() {
  const {
    creditCards,
    loading,
    error,
    statuses,
    banks,
    isEvidenceDrawerOpen,
    setStatuses,
    setBanks,
    clearFilters,
    refresh,
    toggleEvidenceDrawer,
  } = useCreditCardsCapability();

  // Show loading skeleton
  if (loading) {
    return <CreditCardsPageSkeleton />;
  }

  // Show error state
  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 p-4">
        <CreditCardsErrorState message={error.message} onRetry={refresh} />
      </div>
    );
  }

  // Show empty state
  if (!creditCards || creditCards.cards.length === 0) {
    return (
      <div className="min-h-screen bg-gray-50 p-4">
        <CreditCardsEmptyState onAction={clearFilters} />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Toolbar */}
      <CreditCardsToolbar
        onRefresh={refresh}
        onExport={() => {}}
        searchQuery=""
        onSearchChange={() => {}}
        statuses={statuses}
        banks={banks}
        onStatusesChange={setStatuses}
        onBanksChange={setBanks}
        onClearFilters={clearFilters}
        onApplyFilters={() => {}}
      />

      {/* Main Content */}
      <div className="p-4 space-y-4">
        {/* Summary Card */}
        <CreditCardsSummary creditCards={creditCards} loading={loading} error={error} />

        {/* Charts Row */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <UtilizationChart creditCards={creditCards} loading={loading} error={error} />
          <SpendingByCategory creditCards={creditCards} loading={loading} error={error} />
        </div>

        {/* Insights Panel */}
        <InsightsPanel cards={creditCards} loading={loading} error={error} />

        {/* Cross Navigation */}
        <CrossNavigation crossReferences={creditCards.navigation?.cross_references} />
      </div>

      {/* Evidence Drawer */}
      <EvidenceDrawer
        cards={creditCards}
        isOpen={isEvidenceDrawerOpen}
        onClose={toggleEvidenceDrawer}
      />
    </div>
  );
}