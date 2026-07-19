/**
 * Transaction Workspace Page - Stage 3 Transaction Intelligence Workspace
 *
 * Main workspace page component that composes all regions.
 * Uses the capability layer for state management.
 */

'use client';

import { useTransactionCapability } from '@/lib/capabilities/use-transaction-capability';
import { useEvidence } from '@/lib/evidence/use-evidence';
import { FilterPanel } from '@/components/filters/filter-panel';
import { LoadingSpinner } from '@/components/loading/loading-spinner';
import { ErrorMessage } from '@/components/loading/error-message';
import { EmptyState } from '@/components/loading/empty-state';
import { EvidenceDrawer } from '@/components/evidence/evidence-drawer';
import { WorkspaceToolbar } from '@/components/toolbar/workspace-toolbar';
import { SelectionSummary } from '@/components/selection/selection-summary';
import { InsightPanel } from '@/components/workspace/insight-panel';
import { ActionDrawer } from '@/components/workspace/action-drawer';
import { TransactionTable } from '@/components/transaction-table/transaction-table';

/**
 * Transaction Workspace Page
 * Composes all workspace regions using the capability layer
 * Responsive layout with proper spacing and overflow handling
 * Dark mode support with bg-background classes
 */
export function TransactionWorkspacePage() {
  const capability = useTransactionCapability();
  const evidence = useEvidence();

  // Loading state
  if (capability.loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px] p-4 bg-background dark:bg-background">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  // Error state
  if (capability.error) {
    return (
      <div className="p-4 sm:p-6 bg-background dark:bg-background">
        <ErrorMessage
          message={capability.error.message}
          onRetry={capability.refresh}
        />
      </div>
    );
  }

  // Empty state
  if (capability.transactions.length === 0) {
    return (
      <div className="p-4 sm:p-6 bg-background dark:bg-background">
        <EmptyState onAction={capability.clearFilters} />
      </div>
    );
  }

  // Calculate active filter count
  const activeFilterCount = [
    capability.searchQuery,
    capability.dateFilter,
    ...capability.categoryFilter,
    ...capability.merchantFilter,
    capability.amountFilter,
    ...capability.statusFilter,
  ].filter(Boolean).length;

  return (
    <div className="flex flex-col h-full min-h-screen bg-background dark:bg-background">
      {/* Toolbar Region - Responsive */}
      <WorkspaceToolbar
        transactionCount={capability.total}
        activeFilterCount={activeFilterCount}
        loading={capability.loading}
        onSearchClick={() => {}}
        onFilterToggle={() => {}}
        onGroupToggle={capability.toggleGroup}
        onSortToggle={() => {}}
        onExport={() => {}}
        onRefresh={capability.refresh}
        onSettings={() => {}}
      />

      {/* Filter Panel Region - Responsive */}
      <FilterPanel
        filters={{
          searchQuery: capability.searchQuery,
          dateFilter: capability.dateFilter,
          categoryFilter: capability.categoryFilter,
          merchantFilter: capability.merchantFilter,
          amountFilter: capability.amountFilter,
          statusFilter: capability.statusFilter,
        }}
        onFiltersChange={(filters) => {
          capability.setSearchQuery(filters.searchQuery);
          capability.setDateFilter(filters.dateFilter);
          capability.setCategoryFilter(filters.categoryFilter);
          capability.setMerchantFilter(filters.merchantFilter);
          capability.setAmountFilter(filters.amountFilter);
          capability.setStatusFilter(filters.statusFilter);
        }}
      />

      {/* Transaction Table Region - Flex grow with overflow */}
      <div className="flex-1 overflow-auto bg-background dark:bg-background">
        <TransactionTable
          transactions={capability.transactions}
          loading={capability.loading}
          onRowClick={(tx) => {
            evidence.openEvidence(tx.id, tx.evidence || []);
          }}
          onSelectionChange={(id, selected) => {
            if (selected) {
              capability.toggleSelection(id);
            }
          }}
          selectedIds={capability.selectedIds}
        />
      </div>

      {/* Selection Summary Region */}
      {capability.selectedIds.size > 0 && (
        <SelectionSummary
          count={capability.selectedIds.size}
          total={capability.total}
          onClear={capability.clearSelection}
          onSelectAll={capability.selectAllVisible}
        />
      )}

      {/* Insight Panel Region */}
      <InsightPanel
        transactions={capability.transactions}
        groupBy={capability.groupBy}
      />

      {/* Action Drawer Region */}
      <ActionDrawer
        selectedCount={capability.selectedIds.size}
        onBulkAction={capability.executeBulkAction}
        onClearSelection={capability.clearSelection}
      />

      {/* Evidence Drawer */}
      <EvidenceDrawer
        state={evidence}
        onClose={evidence.closeEvidence}
      />
    </div>
  );
}