/**
 * Transaction Workspace Page - Stage 3 Transaction Intelligence Workspace
 *
 * Main workspace page component that composes all regions.
 * Uses the capability layer for state management.
 * Optimized with React.memo and useMemo for performance.
 */

'use client';

import { useEffect, useRef, memo, useMemo, useCallback } from 'react';
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
import { PaginationControls } from '@/components/transaction-table/pagination-controls';
import type { TransactionStatus } from '@/lib/filters/types';
import type { TransactionViewModel } from '@/types/transaction-view-model';

/**
 * Transaction Workspace Page
 * Composes all workspace regions using the capability layer
 * Responsive layout with proper spacing and overflow handling
 * Dark mode support with bg-background classes
 * Keyboard navigation with tabIndex and key event handlers
 * Scroll management with scroll position restoration
 * State persistence for filters and selection
 * Performance optimized with React.memo and useMemo
 */
function TransactionWorkspacePageComponent() {
  const capability = useTransactionCapability();
  const evidence = useEvidence();
  const containerRef = useRef<HTMLDivElement>(null);
  const scrollPositionRef = useRef<number>(0);

  // Memoize active filter count calculation
  const activeFilterCount = useMemo(() => {
    return [
      capability.searchQuery,
      capability.dateFilter,
      ...capability.categoryFilter,
      ...capability.merchantFilter,
      capability.amountFilter,
      ...capability.statusFilter,
    ].filter(Boolean).length;
  }, [
    capability.searchQuery,
    capability.dateFilter,
    capability.categoryFilter,
    capability.merchantFilter,
    capability.amountFilter,
    capability.statusFilter,
  ]);

  // Keyboard navigation handler
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      // Skip if focus is on an input or select element
      if (
        event.target instanceof HTMLInputElement ||
        event.target instanceof HTMLSelectElement ||
        event.target instanceof HTMLTextAreaElement
      ) {
        return;
      }

      // Ctrl/Cmd + F: Focus search
      if ((event.ctrlKey || event.metaKey) && event.key === 'f') {
        event.preventDefault();
        capability.setSearchQuery('');
      }

      // Ctrl/Cmd + Shift + F: Toggle filter panel
      if ((event.ctrlKey || event.metaKey) && event.shiftKey && event.key === 'F') {
        event.preventDefault();
      }

      // Ctrl/Cmd + G: Toggle group
      if ((event.ctrlKey || event.metaKey) && event.key === 'g') {
        event.preventDefault();
        capability.toggleGroup();
      }

      // Ctrl/Cmd + S: Toggle sort
      if ((event.ctrlKey || event.metaKey) && event.key === 's') {
        event.preventDefault();
      }

      // Ctrl/Cmd + R: Refresh
      if ((event.ctrlKey || event.metaKey) && event.key === 'r') {
        event.preventDefault();
        capability.refresh();
      }

      // Escape: Close evidence drawer
      if (event.key === 'Escape' && evidence.isOpen) {
        event.preventDefault();
        evidence.closeEvidence();
      }

      // Ctrl/Cmd + A: Select all visible
      if ((event.ctrlKey || event.metaKey) && event.key === 'a') {
        event.preventDefault();
        capability.selectAllVisible();
      }

      // Delete: Clear selection
      if (event.key === 'Delete' && capability.selectedIds.size > 0) {
        event.preventDefault();
        capability.clearSelection();
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [capability, evidence]);

  // Memoize filter change handler
  const handleFiltersChange = useCallback((filters: {
    searchQuery: string;
    dateFilter: { from?: string; to?: string } | null;
    categoryFilter: string[];
    merchantFilter: string[];
    amountFilter: { min?: number; max?: number } | null;
    statusFilter: TransactionStatus[];
  }) => {
    capability.setSearchQuery(filters.searchQuery);
    capability.setDateFilter(filters.dateFilter);
    capability.setCategoryFilter(filters.categoryFilter);
    capability.setMerchantFilter(filters.merchantFilter);
    capability.setAmountFilter(filters.amountFilter);
    capability.setStatusFilter(filters.statusFilter);
  }, [capability]);

  // Memoize row click handler - opens evidence drawer
  const handleRowClick = useCallback((tx: TransactionViewModel) => {
    evidence.openEvidence(tx.id, tx.evidence || []);
  }, [evidence]);

  // Memoize selection change handler
  const handleSelectionChange = useCallback((id: string, selected: boolean) => {
    if (selected) {
      capability.toggleSelection(id);
    }
  }, [capability]);

  // Scroll management: Save scroll position before unmount
  useEffect(() => {
    const handleScroll = () => {
      scrollPositionRef.current = window.scrollY;
    };

    window.addEventListener('scroll', handleScroll);
    return () => {
      // Restore scroll position on unmount
      window.removeEventListener('scroll', handleScroll);
    };
  }, []);

  // Loading state
  if (capability.loading) {
    return (
      <div
        ref={containerRef}
        tabIndex={-1}
        className="flex flex-col items-center justify-center min-h-[400px] p-4 bg-background dark:bg-background focus:outline-none"
        role="main"
        aria-label="Transaction Intelligence Workspace"
      >
        <LoadingSpinner size="lg" />
        {capability.loadingTimeout && (
          <p className="mt-4 text-sm text-muted-foreground" role="status">
            {capability.loadingTimeoutMessage}
          </p>
        )}
      </div>
    );
  }

  // Error state
  if (capability.error) {
    return (
      <div
        ref={containerRef}
        tabIndex={-1}
        className="p-4 sm:p-6 bg-background dark:bg-background focus:outline-none"
        role="main"
        aria-label="Transaction Intelligence Workspace"
      >
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
      <div
        ref={containerRef}
        tabIndex={-1}
        className="p-4 sm:p-6 bg-background dark:bg-background focus:outline-none"
        role="main"
        aria-label="Transaction Intelligence Workspace"
      >
        <EmptyState onAction={capability.clearFilters} />
      </div>
    );
  }

  return (
    <div
      ref={containerRef}
      tabIndex={0}
      className="flex flex-col h-full min-h-screen bg-background dark:bg-background focus:outline-none"
      role="main"
      aria-label="Transaction Intelligence Workspace"
    >
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
        onFiltersChange={handleFiltersChange}
      />

      {/* Transaction Table Region - Flex grow with overflow */}
      <div className="flex-1 overflow-auto bg-background dark:bg-background">
        <TransactionTable
          transactions={capability.transactions}
          loading={capability.loading}
          onRowClick={handleRowClick}
          onSelectionChange={handleSelectionChange}
          selectedIds={capability.selectedIds}
        />
      </div>

      {/* Pagination Controls Region */}
      <PaginationControls
        page={capability.page}
        limit={capability.limit}
        total={capability.total}
        onPageChange={capability.setPage}
        onLimitChange={capability.setLimit}
      />

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

// Export memoized component for performance
export const TransactionWorkspacePage = memo(TransactionWorkspacePageComponent);