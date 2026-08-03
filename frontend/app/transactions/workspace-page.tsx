/**
 * Transaction Workspace Page - Stage 3 Transaction Intelligence Workspace
 */

'use client';

import { useTransactionCapability } from '@/lib/capabilities/use-transaction-capability';
import { useWorkspaceRegistration } from '@/lib/runtime';
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

function TransactionWorkspacePageComponent() {
  useWorkspaceRegistration({
    name: 'transactions',
    label: 'Transactions',
    icon: 'receipt',
    deepLink: '/transactions',
    defaultSurface: 'TABLE',
    supportedCommands: ['search', 'selection', 'export', 'explain', 'filter'],
    supportedFilters: ['date', 'category', 'merchant', 'amount', 'status', 'search'],
    supportedSelections: ['transaction'],
  });

  const capability = useTransactionCapability();

  if (capability.loading) {
    return (
      <Surface variant="default" density="none" className="flex flex-col h-full" role="main" tabIndex={0} aria-label="Transaction Intelligence Workspace">
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

  if (capability.error) {
    return (
      <Surface variant="default" density="none" className="flex flex-col h-full" role="main" tabIndex={0} aria-label="Transaction Intelligence Workspace">
        <Panel fill>
          <PanelHeader title="Transactions" />
          <div className="p-4">
            <ErrorMessage message={capability.error.message} onRetry={capability.refresh} />
          </div>
        </Panel>
      </Surface>
    );
  }

  if (capability.transactions.length === 0) {
    return (
      <Surface variant="default" density="none" className="flex flex-col h-full" role="main" tabIndex={0} aria-label="Transaction Intelligence Workspace">
        <Panel fill>
          <PanelHeader title="Transactions" />
          <div className="p-4">
            <EmptyState onAction={capability.clearFilters} />
          </div>
        </Panel>
      </Surface>
    );
  }

  return (
    <Surface variant="default" density="none" className="flex flex-col h-full" role="main" tabIndex={0} aria-label="Transaction Intelligence Workspace">
      <Panel fill>
        <PanelHeader title="Transactions" />
        <WorkspaceToolbar
          onSearchClick={() => {}} onFilterToggle={() => {}} onGroupToggle={capability.toggleGroup}
          onSortToggle={() => {}} onExport={() => {}} onRefresh={capability.refresh} onSettings={() => {}}
          transactionCount={capability.transactions.length} activeFilterCount={0} loading={capability.loading}
        />
        <FilterPanel
          filters={{
            searchQuery: capability.searchQuery, dateFilter: capability.dateFilter,
            categoryFilter: capability.categoryFilter, merchantFilter: capability.merchantFilter,
            amountFilter: capability.amountFilter, statusFilter: capability.statusFilter,
          }}
          onFiltersChange={() => {}} availableCategories={[]} availableMerchants={[]}
        />
        <PanelBody scrollable>
          <TransactionTable
            transactions={capability.transactions} loading={capability.loading}
            onRowClick={() => {}} onSelectionChange={() => {}} selectedIds={capability.selectedIds}
          />
        </PanelBody>
        <InsightPanel transactions={capability.transactions} groupBy={capability.groupBy} />
        <SelectionSummary
          count={capability.selectedIds.size} total={capability.total}
          onClear={capability.clearSelection} onSelectAll={capability.selectAllVisible}
        />
      </Panel>
      <EvidenceDrawer state={{ isOpen: false, transactionId: null, evidence: [], loading: false, error: null }} onClose={() => {}} />
      <div className="h-12 border-t border-[var(--border-default)] flex items-center justify-between px-3">
        <PaginationControls
          page={capability.page} limit={capability.limit} total={capability.total}
          onPageChange={capability.setPage} onLimitChange={capability.setLimit}
        />
      </div>
    </Surface>
  );
}

export const TransactionWorkspacePage = TransactionWorkspacePageComponent;
