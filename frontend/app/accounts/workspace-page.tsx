/**
 * Accounts Workspace Page - Stage 4 Accounts Intelligence Workspace
 *
 * Composes all accounts components into a complete workspace page.
 *
 * Architecture Flow: Backend → API → DTO → Mapper → ViewModel → Capability → Workspace → Components → Page
 */

'use client';

import { useAccountsCapability } from '@/lib/capabilities/use-accounts-capability';
import { AccountsSummary } from '@/components/accounts/accounts-summary';
import { BalanceTrend } from '@/components/accounts/balance-trend';
import { TypeBreakdown } from '@/components/accounts/type-breakdown';
import { TransactionList } from '@/components/accounts/transaction-list';
import { InsightsPanel } from '@/components/accounts/insights-panel';
import { EvidenceDrawer } from '@/components/accounts/evidence-drawer';
import { AccountsToolbar } from '@/components/accounts/accounts-toolbar';

/**
 * Accounts Workspace Page
 */
export default function AccountsPage() {
  const {
    accounts,
    loading,
    error,
    accountTypes,
    institutions,
    statuses,
    dateRange,
    balanceRange,
    isEvidenceDrawerOpen,
    setAccountTypes,
    setInstitutions,
    setStatuses,
    setDateRange,
    setBalanceRange,
    clearFilters,
    refresh,
    toggleEvidenceDrawer,
  } = useAccountsCapability();

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Toolbar */}
      <AccountsToolbar
        onRefresh={refresh}
        onExport={() => {}}
        searchQuery=""
        onSearchChange={() => {}}
        accountTypes={accountTypes}
        institutions={institutions}
        statuses={statuses}
        dateRange={dateRange}
        balanceRange={balanceRange}
        onAccountTypesChange={setAccountTypes}
        onInstitutionsChange={setInstitutions}
        onStatusesChange={setStatuses}
        onDateRangeChange={setDateRange}
        onBalanceRangeChange={setBalanceRange}
        onClearFilters={clearFilters}
        onApplyFilters={() => {}}
      />

      {/* Main Content */}
      <div className="p-4 space-y-4">
        {/* Summary Card */}
        <AccountsSummary accounts={accounts} loading={loading} error={error} />

        {/* Charts Row */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <BalanceTrend accounts={accounts} loading={loading} error={error} />
          <TypeBreakdown accounts={accounts} loading={loading} error={error} />
        </div>

        {/* Transaction List */}
        <TransactionList accounts={accounts} loading={loading} error={error} />

        {/* Insights Panel */}
        <InsightsPanel accounts={accounts} loading={loading} error={error} />
      </div>

      {/* Evidence Drawer */}
      <EvidenceDrawer
        accounts={accounts}
        isOpen={isEvidenceDrawerOpen}
        onClose={toggleEvidenceDrawer}
      />
    </div>
  );
}