/**
 * Transaction Workspace Page - Stage 8B Workspace Integration & Surface Migration
 *
 * Investigation Table Surface - Main analysis surface for transactions.
 * Uses the capability layer for state management.
 * Optimized with React.memo and useMemo for performance.
 *
 * Migrated: Removed header, toolbar, filter panel, selection summary, evidence drawer.
 * These are now provided by the OS Shell.
 */

'use client';

import { useEffect, useRef, memo, useCallback } from 'react';
import { useTransactionCapability } from '@/lib/capabilities/use-transaction-capability';
import { LoadingSpinner } from '@/components/loading/loading-spinner';
import { ErrorMessage } from '@/components/loading/error-message';
import { EmptyState } from '@/components/loading/empty-state';
import { TransactionTable } from '@/components/transaction-table/transaction-table';
import { PaginationControls } from '@/components/transaction-table/pagination-controls';
import type { TransactionViewModel } from '@/types/transaction-view-model';

/**
 * Transaction Workspace Page
 * Investigation Table Surface - Only the analysis surface content
 * Shell provides: Header, Toolbar, Filter Panel, Selection Summary, Evidence Drawer
 */
function TransactionWorkspacePageComponent() {
  const capability = useTransactionCapability();
  const containerRef = useRef<HTMLDivElement>(null);

  // Keyboard navigation handler - now handled by TopCommandBar
  // This is kept for workspace-specific shortcuts
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

      // Ctrl/Cmd + G: Toggle group
      if ((event.ctrlKey || event.metaKey) && event.key === 'g') {
        event.preventDefault();
        capability.toggleGroup();
      }

      // Ctrl/Cmd + R: Refresh
      if ((event.ctrlKey || event.metaKey) && event.key === 'r') {
        event.preventDefault();
        capability.refresh();
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
  }, [capability]);

  // Memoize row click handler - selection is now handled by SelectionRuntime
  const handleRowClick = useCallback((_tx: TransactionViewModel) => {
    // Selection is handled by the table component via SelectionRuntime
  }, []);

  // Memoize selection change handler
  const handleSelectionChange = useCallback((id: string, selected: boolean) => {
    if (selected) {
      capability.toggleSelection(id);
    }
  }, [capability]);

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
      className="flex flex-col h-full bg-background dark:bg-background focus:outline-none"
      role="main"
      aria-label="Transaction Intelligence Workspace"
    >
      {/* Investigation Table Surface - Main content only */}
      <div className="flex-1 overflow-auto">
        <TransactionTable
          transactions={capability.transactions}
          loading={capability.loading}
          onRowClick={handleRowClick}
          onSelectionChange={handleSelectionChange}
          selectedIds={capability.selectedIds}
        />
      </div>

      {/* Pagination Controls */}
      <PaginationControls
        page={capability.page}
        limit={capability.limit}
        total={capability.total}
        onPageChange={capability.setPage}
        onLimitChange={capability.setLimit}
      />
    </div>
  );
}

// Export memoized component for performance
export const TransactionWorkspacePage = memo(TransactionWorkspacePageComponent);