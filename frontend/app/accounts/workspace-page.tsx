/**
 * Accounts Workspace Page - Stage 8E-C2 Production Visual System Migration
 *
 * Relationship Explorer Surface - Main analysis surface for accounts.
 * Shell provides: Header, Toolbar, Breadcrumbs, Selection Summary, Evidence Drawer.
 *
 * Migrated: Wrapped in Surface/Panel primitives, removed legacy padding.
 * Registered with CommandCenterRuntime for selection sync.
 */

'use client';

import { useEffect, useMemo } from 'react';
import { useAccountsCapability } from '@/lib/capabilities/use-accounts-capability';
import { AccountsSummary } from '@/components/accounts/accounts-summary';
import { BalanceTrend } from '@/components/accounts/balance-trend';
import { TypeBreakdown } from '@/components/accounts/type-breakdown';
import { TransactionList } from '@/components/accounts/transaction-list';
import { InsightsPanel } from '@/components/accounts/insights-panel';
import { EvidenceDrawer } from '@/components/accounts/evidence-drawer';
import { EmptyState } from '@/components/loading/empty-state';
import { Surface } from '@/components/primitives/surface/surface';
import { Panel, PanelHeader, PanelBody } from '@/components/primitives/panel/panel';
import { Stack } from '@/components/primitives/layout/stack';
import { Grid } from '@/components/primitives/layout/grid';
import { commandCenterRuntime } from '@/lib/command-center';
import { LoadingSpinner } from '@/components/loading/loading-spinner';

/**
 * Accounts Workspace Page
 * Relationship Explorer Surface - Composed with Surface/Panel primitives
 * Shell provides: Header, Toolbar, Filter Panel, Selection Summary, Evidence Drawer
 */
export default function AccountsPage() {
  const {
    accounts,
    loading,
    error,
    loadingTimeout,
    loadingTimeoutMessage,
    isEvidenceDrawerOpen,
    refresh,
    toggleEvidenceDrawer,
  } = useAccountsCapability();

  // Build view model for shared runtime
  const viewModels = useMemo(() => ({
    accounts: { accounts },
  }), [accounts]);

  // Register workspace with CommandCenterRuntime on mount
  useEffect(() => {
    // Build graph for shared runtime
    commandCenterRuntime.build(viewModels);

    // Register workspace actions
    const workspaceRegistration = {
      name: 'accounts' as const,
      label: 'Accounts',
      icon: 'wallet',
      deepLink: '/accounts',
      viewModelKey: 'accounts',
      description: 'Account relationships and balance analysis',
      defaultSurface: 'GRAPH' as const,
      graphAdapter: 'accounts',
      supportedCommands: ['filter', 'search', 'export', 'refresh'],
      supportedFilters: ['account-type', 'institution', 'status', 'balance'],
      supportedSelections: ['account'],
      inspectorSections: ['context', 'evidence', 'related', 'transactions'],
      keyboardShortcuts: {
        'f': 'filter',
        'r': 'refresh',
        'e': 'export',
      },
    };

    commandCenterRuntime.registerWorkspace(workspaceRegistration);

    return () => {
      commandCenterRuntime.unregisterWorkspace('accounts');
    };
  }, [viewModels]);

  // Loading state
  if (loading) {
    return (
      <Surface variant="default" density="none" className="flex flex-col h-full">
        <Panel fill>
          <PanelHeader title="Accounts" />
          <PanelBody loading>
            <div className="flex flex-col items-center justify-center min-h-[400px] p-4">
              <LoadingSpinner size="lg" />
              {loadingTimeout && (
                <p className="mt-4 text-sm text-[var(--text-tertiary)]" role="status">
                  {loadingTimeoutMessage}
                </p>
              )}
            </div>
          </PanelBody>
        </Panel>
      </Surface>
    );
  }

  // Error state
  if (error) {
    return (
      <Surface variant="default" density="none" className="flex flex-col h-full">
        <Panel fill>
          <PanelHeader title="Accounts" />
          <PanelBody error={error.message}>
            <div className="flex flex-col items-center justify-center min-h-[400px] p-4">
              <p className="text-sm text-[var(--color-negative-600)]">{error.message}</p>
              <button
                onClick={refresh}
                className="mt-4 px-4 py-2 text-sm bg-[var(--color-info-500)] text-white rounded hover:bg-[var(--color-info-600)]"
              >
                Retry
              </button>
            </div>
          </PanelBody>
        </Panel>
      </Surface>
    );
  }

  // Empty state
  if (!accounts || accounts.accounts.length === 0) {
    return (
      <Surface variant="default" density="none" className="flex flex-col h-full">
        <Panel fill>
          <PanelHeader title="Accounts" />
          <PanelBody empty emptyMessage="No accounts found">
            <EmptyState onAction={refresh} />
          </PanelBody>
        </Panel>
      </Surface>
    );
  }

  return (
    <Surface variant="default" density="none" className="flex flex-col h-full">
      <Panel fill>
        <PanelHeader title="Accounts" />
        <PanelBody scrollable>
          <Stack gap={4} className="p-4">
            {/* Summary Card */}
            <AccountsSummary accounts={accounts} loading={loading} error={error} />

            {/* Charts Row */}
            <Grid gap={4} className="grid-cols-1 lg:grid-cols-2">
              <BalanceTrend accounts={accounts} loading={loading} error={error} />
              <TypeBreakdown accounts={accounts} loading={loading} error={error} />
            </Grid>

            {/* Transaction List */}
            <TransactionList accounts={accounts} loading={loading} error={error} />

            {/* Insights Panel */}
            <InsightsPanel accounts={accounts} loading={loading} error={error} />
          </Stack>
        </PanelBody>
      </Panel>

      {/* Evidence Drawer */}
      <EvidenceDrawer
        accounts={accounts}
        isOpen={isEvidenceDrawerOpen}
        onClose={toggleEvidenceDrawer}
      />
    </Surface>
  );
}
