/**
 * Loans Toolbar - Stage 4 Loans Intelligence Workspace
 *
 * Toolbar with search, filters, and actions for loans workspace.
 *
 * Architecture Flow: Backend → API → DTO → Mapper → ViewModel → Capability → Workspace → Components → Page
 */

import { Button } from '@/components/ui/button';
import { RefreshCw, Download } from 'lucide-react';
import { LoansSearch } from './loans-search';
import { LoansFilters } from './loans-filters';

/**
 * Loans Toolbar Props
 */
interface LoansToolbarProps {
  onRefresh: () => void;
  onExport: () => void;
  searchQuery: string;
  onSearchChange: (query: string) => void;
  loanTypes: string[];
  lenders: string[];
  statuses: string[];
  onLoanTypesChange: (types: string[]) => void;
  onLendersChange: (lenders: string[]) => void;
  onStatusesChange: (statuses: string[]) => void;
  onClearFilters: () => void;
  onApplyFilters: () => void;
}

/**
 * Loans Toolbar Component
 */
export function LoansToolbar({
  onRefresh,
  onExport,
  searchQuery,
  onSearchChange,
  loanTypes,
  lenders,
  statuses,
  onLoanTypesChange,
  onLendersChange,
  onStatusesChange,
  onClearFilters,
  onApplyFilters,
}: LoansToolbarProps) {
  return (
    <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 p-4 bg-white border-b">
      {/* Left side: Search and Filters */}
      <div className="flex items-center gap-2">
        <LoansSearch searchQuery={searchQuery} onSearchChange={onSearchChange} />
        <LoansFilters
          loanTypes={loanTypes}
          lenders={lenders}
          statuses={statuses}
          onLoanTypesChange={onLoanTypesChange}
          onLendersChange={onLendersChange}
          onStatusesChange={onStatusesChange}
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