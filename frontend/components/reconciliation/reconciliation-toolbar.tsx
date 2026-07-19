/**
 * Reconciliation Toolbar - Stage 4 Reconciliation Intelligence Workspace
 *
 * Toolbar with search, filters, and actions for reconciliation workspace.
 *
 * Architecture Flow: Backend → API → DTO → Mapper → ViewModel → Capability → Workspace → Components → Page
 */

import { Button } from '@/components/ui/button';
import { RefreshCw, Download } from 'lucide-react';
import { ReconciliationSearch } from './reconciliation-search';
import { ReconciliationFilters } from './reconciliation-filters';

/**
 * Reconciliation Toolbar Props
 */
interface ReconciliationToolbarProps {
  onRefresh: () => void;
  onExport: () => void;
  searchQuery: string;
  onSearchChange: (query: string) => void;
  statuses: string[];
  banks: string[];
  onStatusesChange: (statuses: string[]) => void;
  onBanksChange: (banks: string[]) => void;
  onClearFilters: () => void;
  onApplyFilters: () => void;
}

/**
 * Reconciliation Toolbar Component
 */
export function ReconciliationToolbar({
  onRefresh,
  onExport,
  searchQuery,
  onSearchChange,
  statuses,
  banks,
  onStatusesChange,
  onBanksChange,
  onClearFilters,
  onApplyFilters,
}: ReconciliationToolbarProps) {
  return (
    <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 p-4 bg-white border-b">
      {/* Left side: Search and Filters */}
      <div className="flex items-center gap-2">
        <ReconciliationSearch searchQuery={searchQuery} onSearchChange={onSearchChange} />
        <ReconciliationFilters
          statuses={statuses}
          banks={banks}
          onStatusesChange={onStatusesChange}
          onBanksChange={onBanksChange}
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