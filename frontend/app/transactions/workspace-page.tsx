/**
 * Transaction Workspace Page - Stage 8E-C2 Production Visual System Migration
 *
 * Investigation Table Surface - Main analysis surface for transactions.
 * Shell provides: Header, Toolbar, Filter Panel, Selection Summary, Evidence Drawer.
 *
 * Migrated: Wrapped in Surface primitive, removed legacy padding.
 */

'use client';

import { useEffect, memo, useCallback } from 'react';
import { useTransactionCapability } from '@/lib/capabilities/use-transaction-capability';
import { LoadingSpinner } from '@/components/loading/loading-spinner';
import { ErrorMessage } from '@/components/loading/error-message';
import { EmptyState } from '@/components/loading/empty-state';
import { TransactionTable } from '@/components/transaction-table/transaction-table';
import { PaginationControls } from '@/components/transaction-table/pagination-controls';
import { Surface } from '@/components/primitives/surface/surface';
import { Panel, PanelHeader, PanelBody } from '@/components/primitives/panel/panel';
import type { TransactionViewModel } from '@/types/transaction-view-model';

/**
 * Transaction Workspace Page
 * Investigation Table Surface - Composed with Surface/Panel primitives
 * Shell provides: Header, Toolbar, Filter Panel, Selection Summary, Evidence Drawer
 */
function TransactionWorkspacePageComponent() {
  const capability = useTransactionCapability();

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
      <Surface variant="default" density="none" className="flex flex-col h-full">
        <Panel fill>
          <PanelHeader title="Transactions" />
          <PanelBody loading>
            <div className="flex flex-col items-center justify-center min-h-[400px] p-4">
              <LoadingSpinner size="lg" />
              {capability.loadingTimeout && (
                <p className="mt-4 text-sm text-muted-foreground" role="status">
                  {capability.loadingTimeoutMessage}
                </p>
              )}
            </div>
          </PanelBody>
        </Panel>
      </Surface>
    );
  }

  // Error state
  if (capability.error) {
    return (
      <Surface variant="default" density="none" className="flex flex-col h-full">
        <Panel fill>
          <PanelHeader title="Transactions" />
          <PanelBody error={capability.error.message}>
            <ErrorMessage
              message={capability.error.message}
              onRetry={capability.refresh}
            />
          </PanelBody>
        </Panel>
      </Surface>
    );
  }

  // Empty state
  if (capability.transactions.length === 0) {
    return (
      <Surface variant="default" density="none" className="flex flex-col h-full">
        <Panel fill>
          <PanelHeader title="Transactions" />
          <PanelBody empty emptyMessage="No transactions found">
            <EmptyState onAction={capability.clearFilters} />
          </PanelBody>
        </Panel>
      </Surface>
    );
  }

  return (
    <Surface variant="default" density="none" className="flex flex-col h-full">
      <Panel fill>
        <PanelHeader title="Transactions" />
        <PanelBody scrollable>
          <TransactionTable
            transactions={capability.transactions}
            loading={capability.loading}
            onRowClick={handleRowClick}
            onSelectionChange={handleSelectionChange}
            selectedIds={capability.selectedIds}
          />
        </PanelBody>
      </Panel>
      
      {/* Pagination Controls */}
      <div className="h-12 border-t border-[var(--border-default)] flex items-center justify-between px-3">
        <PaginationControls
          page={capability.page}
          limit={capability.limit}
          total={capability.total}
          onPageChange={capability.setPage}
          onLimitChange={capability.setLimit}
        />
      </div>
    </Surface>
  );
}

// Export memoized component for performance
export const TransactionWorkspacePage = memo(TransactionWorkspacePageComponent);