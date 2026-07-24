/**
 * Investments Toolbar - Stage 4 Investments Intelligence Workspace
 *
 * Toolbar with search, filters, and actions for investments workspace.
 *
 * Architecture Flow: Backend → API → DTO → Mapper → ViewModel → Capability → Workspace → Components → Page
 */

import { Button } from '@/components/ui/button';
import { RefreshCw, Download } from 'lucide-react';
import { InvestmentsSearch } from './investments-search';
import { InvestmentsFilters } from './investments-filters';

/**
 * Investments Toolbar Props
 */
interface InvestmentsToolbarProps {
  onRefresh: () => void;
  onExport: () => void;
  searchQuery: string;
  onSearchChange: (query: string) => void;
  investmentTypes: string[];
  institutions: string[];
  statuses: string[];
  onInvestmentTypesChange: (types: string[]) => void;
  onInstitutionsChange: (institutions: string[]) => void;
  onStatusesChange: (statuses: string[]) => void;
  onClearFilters: () => void;
  onApplyFilters: () => void;
}

/**
 * Investments Toolbar Component
 */
export function InvestmentsToolbar({
  onRefresh,
  onExport,
  searchQuery,
  onSearchChange,
  investmentTypes,
  institutions,
  statuses,
  onInvestmentTypesChange,
  onInstitutionsChange,
  onStatusesChange,
  onClearFilters,
  onApplyFilters,
}: InvestmentsToolbarProps) {
  return (
    <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 p-4 bg-white border-b">
      {/* Left side: Search and Filters */}
      <div className="flex items-center gap-2">
        <InvestmentsSearch searchQuery={searchQuery} onSearchChange={onSearchChange} />
        <InvestmentsFilters
          investmentTypes={investmentTypes}
          institutions={institutions}
          statuses={statuses}
          onInvestmentTypesChange={onInvestmentTypesChange}
          onInstitutionsChange={onInstitutionsChange}
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