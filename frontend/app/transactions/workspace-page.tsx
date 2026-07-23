/**
 * Transaction Workspace Page - Stage 8E-C2 Production Visual System Migration
 *
 * Investigation Table Surface - Main analysis surface for transactions.
 * Shell provides: Header, Toolbar, Filter Panel, Selection Summary, Evidence Drawer.
 *
 * Migrated: Wrapped in Surface primitive, removed legacy padding.
 * Pass 3: Registered capabilities with CommandCenterRuntime, selection sync.
 */

'use client';

import { useEffect, memo, useCallback, useMemo } from 'react';
import { useTransactionCapability } from '@/lib/capabilities/use-transaction-capability';
import { LoadingSpinner } from '@/components/loading/loading-spinner';
import { ErrorMessage } from '@/components/loading/error-message';
import { EmptyState } from '@/components/loading/empty-state';
import { TransactionTable } from '@/components/transaction-table/transaction-table';
import { PaginationControls } from '@/components/transaction-table/pagination-controls';
import { Surface } from '@/components/primitives/surface/surface';
import { Panel, PanelHeader, PanelBody } from '@/components/primitives/panel/panel';
import { WorkspaceToolbar } from '@/components/toolbar/workspace-toolbar';
import { FilterPanel } from '@/components/filters/filter-panel';
import { InsightPanel } from '@/components/workspace/insight-panel';
import { EvidenceDrawer } from '@/components/evidence/evidence-drawer';
import { SelectionSummary } from '@/components/selection/selection-summary';
import { commandCenterRuntime } from '@/lib/command-center';
import type { TransactionViewModel } from '@/types/transaction-view-model';

/**
 * Transaction Workspace Page
 * Investigation Table Surface - Composed with Surface/Panel primitives
 * Shell provides: Header, Toolbar, Filter Panel, Selection Summary, Evidence Drawer
 * Pass 3: Registers capabilities with CommandCenterRuntime
 */
function TransactionWorkspacePageComponent() {
  const capability = useTransactionCapability();

  // Build graph data for shared runtime
  const viewModels = useMemo(() => ({
    transactions: { transactions: capability.transactions },
  }), [capability.transactions]);

  // Register workspace with CommandCenterRuntime on mount
  useEffect(() => {
    // Build graph for shared runtime
    commandCenterRuntime.build(viewModels);

    // Register workspace actions
    const workspaceRegistration = {
      name: 'transactions' as const,
      label: 'Transactions',
      icon: 'receipt',
      deepLink: '/transactions',
      viewModelKey: 'transactions',
      description: 'Transaction history and categorization',
      defaultSurface: 'TABLE' as const,
      graphAdapter: 'transactions',
      supportedCommands: ['search', 'selection', 'export', 'explain', 'filter'],
      supportedFilters: ['date', 'category', 'merchant', 'amount', 'status', 'search'],
      supportedSelections: ['transaction'],
      inspectorSections: ['context', 'evidence', 'related', 'actions'],
      keyboardShortcuts: {
        'f': 'search',
        'F': 'filter',
        'g': 'group',
        's': 'sort',
        'r': 'refresh',
        'a': 'select-all',
        'Delete': 'delete',
        'Escape': 'close-evidence',
      },
    };

    commandCenterRuntime.registerWorkspace(workspaceRegistration);

    return () => {
      commandCenterRuntime.unregisterWorkspace('transactions');
    };
  }, [viewModels]);

  // Sync selection to shared runtime
  useEffect(() => {
    if (capability.selectedIds.size > 0) {
      const nodeIds = Array.from(capability.selectedIds).map(id => `transaction:${id}`);
      commandCenterRuntime.selectNodes(nodeIds);
    } else {
      commandCenterRuntime.clearSelection();
    }
  }, [capability.selectedIds]);

  // Memoize row click handler - publishes to shared runtime
  const handleRowClick = useCallback((tx: TransactionViewModel) => {
    // Publish selection to shared runtime
    commandCenterRuntime.selectNodes([`transaction:${tx.id}`]);
  }, []);

  // Memoize selection change handler
  const handleSelectionChange = useCallback((id: string, selected: boolean) => {
    if (selected) {
      capability.toggleSelection(id);
    }
  }, [capability]);

  // Loading state - PanelBody swallows children when loading=true, render directly inside Panel
  if (capability.loading) {
    return (
      <Surface variant="default" density="none" className="flex flex-col h-full" role="main" aria-label="Transaction Intelligence Workspace" tabIndex={0}>
        <Panel fill>
          <PanelHeader title="Transactions" />
          <div className="flex flex-col items-center justify-center min-h-[400px] p-4">
            <LoadingSpinner size="lg" />
            {capability.loadingTimeout && (
              <p className="mt-4 text-sm text-[var(--text-tertiary)]" role="status">
                {capability.loadingTimeoutMessage}
              </p>
            )}
          </div>
        </Panel>
      </Surface>
    );
  }

  // Error state - PanelBody swallows children when error is set, render directly inside Panel
  if (capability.error) {
    return (
      <Surface variant="default" density="none" className="flex flex-col h-full" role="main" aria-label="Transaction Intelligence Workspace" tabIndex={0}>
        <Panel fill>
          <PanelHeader title="Transactions" />
          <div className="p-4">
            <ErrorMessage
              message={capability.error.message}
              onRetry={capability.refresh}
            />
          </div>
        </Panel>
      </Surface>
    );
  }

  // Empty state - PanelBody swallows children when empty=true, render directly inside Panel
  if (capability.transactions.length === 0) {
    return (
      <Surface variant="default" density="none" className="flex flex-col h-full" role="main" aria-label="Transaction Intelligence Workspace" tabIndex={0}>
        <Panel fill>
          <PanelHeader title="Transactions" />
          <div className="p-4">
            <EmptyState onAction={capability.clearFilters} />
          </div>
        </Panel>
      </Surface>
    );
  }

  // Normal state - full workspace with toolbar, filters, table, evidence drawer
  const filterPanelFilters = {
    searchQuery: capability.searchQuery,
    dateFilter: capability.dateFilter,
    categoryFilter: capability.categoryFilter,
    merchantFilter: capability.merchantFilter,
    amountFilter: capability.amountFilter,
    statusFilter: capability.statusFilter,
  };

  const activeFilterCount = [
    capability.dateFilter,
    capability.categoryFilter.length > 0,
    capability.merchantFilter.length > 0,
    capability.amountFilter,
    capability.statusFilter.length > 0,
  ].filter(Boolean).length;

  return (
    <Surface variant="default" density="none" className="flex flex-col h-full" role="main" aria-label="Transaction Intelligence Workspace" tabIndex={0}>
      <Panel fill>
        <PanelHeader title="Transactions" />
        <WorkspaceToolbar
          onSearchClick={() => {}}
          onFilterToggle={() => {}}
          onGroupToggle={capability.toggleGroup}
          onSortToggle={() => {}}
          onExport={() => {}}
          onRefresh={capability.refresh}
          onSettings={() => {}}
          transactionCount={capability.transactions.length}
          activeFilterCount={activeFilterCount}
          loading={capability.loading}
        />
        <FilterPanel
          filters={filterPanelFilters}
          onFiltersChange={(filters) => {
            capability.setDateFilter(filters.dateFilter);
            capability.setCategoryFilter(filters.categoryFilter);
            capability.setMerchantFilter(filters.merchantFilter);
            capability.setAmountFilter(filters.amountFilter);
            capability.setStatusFilter(filters.statusFilter);
          }}
          availableCategories={[]}
          availableMerchants={[]}
        />
        <PanelBody scrollable>
          <TransactionTable
            transactions={capability.transactions}
            loading={capability.loading}
            onRowClick={handleRowClick}
            onSelectionChange={handleSelectionChange}
            selectedIds={capability.selectedIds}
          />
        </PanelBody>
        <InsightPanel
          transactions={capability.transactions}
          groupBy={capability.groupBy}
        />
        <SelectionSummary
          count={capability.selectedIds.size}
          total={capability.total}
          onClear={capability.clearSelection}
          onSelectAll={capability.selectAllVisible}
        />
      </Panel>

      {/* Evidence Drawer */}
      <EvidenceDrawer
        state={{
          isOpen: false,
          transactionId: null,
          evidence: [],
          loading: false,
          error: null,
        }}
        onClose={() => {}}
      />

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