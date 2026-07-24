/**
 * Accounts Toolbar - Stage 4 Accounts Intelligence Workspace
 *
 * Toolbar with search, filters, and actions for accounts workspace.
 *
 * Architecture Flow: Backend → API → DTO → Mapper → ViewModel → Capability → Workspace → Components → Page
 */

import { Button } from '@/components/ui/button';
import { RefreshCw, Download } from 'lucide-react';
import { AccountsSearch } from './accounts-search';
import { AccountsFilters } from './accounts-filters';

/**
 * Accounts Toolbar Props
 */
interface AccountsToolbarProps {
  onRefresh: () => void;
  onExport: () => void;
  searchQuery: string;
  onSearchChange: (query: string) => void;
  accountTypes: string[];
  institutions: string[];
  statuses: string[];
  dateRange: { from?: string; to?: string } | null;
  balanceRange: { min?: number; max?: number } | null;
  onAccountTypesChange: (types: string[]) => void;
  onInstitutionsChange: (institutions: string[]) => void;
  onStatusesChange: (statuses: string[]) => void;
  onDateRangeChange: (range: { from?: string; to?: string } | null) => void;
  onBalanceRangeChange: (range: { min?: number; max?: number } | null) => void;
  onClearFilters: () => void;
  onApplyFilters: () => void;
}

/**
 * Accounts Toolbar Component
 */
export function AccountsToolbar({
  onRefresh,
  onExport,
  searchQuery,
  onSearchChange,
  accountTypes,
  institutions,
  statuses,
  dateRange,
  balanceRange,
  onAccountTypesChange,
  onInstitutionsChange,
  onStatusesChange,
  onDateRangeChange,
  onBalanceRangeChange,
  onClearFilters,
  onApplyFilters,
}: AccountsToolbarProps) {
  return (
    <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 p-4 bg-white border-b">
      {/* Left side: Search and Filters */}
      <div className="flex items-center gap-2">
        <AccountsSearch searchQuery={searchQuery} onSearchChange={onSearchChange} />
        <AccountsFilters
          accountTypes={accountTypes}
          institutions={institutions}
          statuses={statuses}
          dateRange={dateRange}
          balanceRange={balanceRange}
          onAccountTypesChange={onAccountTypesChange}
          onInstitutionsChange={onInstitutionsChange}
          onStatusesChange={onStatusesChange}
          onDateRangeChange={onDateRangeChange}
          onBalanceRangeChange={onBalanceRangeChange}
          onClearFilters={onClearFilters}
          onApplyFilters={onApplyFilters}
        />
      </div>

      {/* Right side: Actions */}
      <div className="flex items-center gap-2">
        <Button variant="outline" size="sm" onClick={onRefresh}>
          <RefreshCw className="h-4 w-4 mr-2" />
          Refresh
        </Button>
        <Button variant="outline" size="sm" onClick={onExport}>
          <Download className="h-4 w-4 mr-2" />
          Export
        </Button>
      </div>
    </div>
  );
}