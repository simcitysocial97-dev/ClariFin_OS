/**
 * Credit Cards Toolbar - Stage 4 Credit Cards Intelligence Workspace
 *
 * Toolbar with search, filters, and actions for credit cards workspace.
 *
 * Architecture Flow: Backend → API → DTO → Mapper → ViewModel → Capability → Workspace → Components → Page
 */

import { Button } from '@/components/ui/button';
import { RefreshCw, Download } from 'lucide-react';
import { CreditCardsSearch } from './cards-search';
import { CreditCardsFilters } from './cards-filters';

/**
 * Credit Cards Toolbar Props
 */
interface CreditCardsToolbarProps {
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
 * Credit Cards Toolbar Component
 */
export function CreditCardsToolbar({
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
}: CreditCardsToolbarProps) {
  return (
    <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 p-4 bg-white border-b">
      {/* Left side: Search and Filters */}
      <div className="flex items-center gap-2">
        <CreditCardsSearch searchQuery={searchQuery} onSearchChange={onSearchChange} />
        <CreditCardsFilters
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