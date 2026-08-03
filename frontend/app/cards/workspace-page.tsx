/**
 * Credit Cards Workspace Page - Stage 4 Credit Cards Intelligence Workspace
 */

'use client';

import { useCreditCardsCapability } from '@/lib/capabilities/use-credit-cards-capability';
import { useWorkspaceRegistration } from '@/lib/runtime';
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

export default function CreditCardsPage() {
  useWorkspaceRegistration({
    name: 'cards',
    label: 'Credit Cards',
    icon: 'credit-card',
    deepLink: '/cards',
    defaultSurface: 'TABLE',
    supportedCommands: ['filter', 'search', 'export', 'refresh'],
    supportedFilters: ['status', 'bank'],
    supportedSelections: ['card'],
  });

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

  if (loading) return <CreditCardsPageSkeleton />;
  if (error) return <CreditCardsErrorState message={error.message} onRetry={refresh} />;
  if (!creditCards || creditCards.cards.length === 0) return <CreditCardsEmptyState onAction={clearFilters} />;

  return (
    <div className="min-h-screen bg-gray-50">
      <CreditCardsToolbar
        onRefresh={refresh} onExport={() => {}} searchQuery="" onSearchChange={() => {}}
        statuses={statuses} banks={banks} onStatusesChange={setStatuses} onBanksChange={setBanks}
        onClearFilters={clearFilters} onApplyFilters={() => {}}
      />
      <div className="p-4 space-y-4">
        <CreditCardsSummary creditCards={creditCards} loading={loading} error={error} />
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <UtilizationChart creditCards={creditCards} loading={loading} error={error} />
          <SpendingByCategory creditCards={creditCards} loading={loading} error={error} />
        </div>
        <InsightsPanel cards={creditCards} loading={loading} error={error} />
        <CrossNavigation crossReferences={creditCards.navigation?.cross_references} />
      </div>
      <EvidenceDrawer cards={creditCards} isOpen={isEvidenceDrawerOpen} onClose={toggleEvidenceDrawer} />
    </div>
  );
}
