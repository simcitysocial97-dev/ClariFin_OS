/**
 * Net Worth Toolbar - Stage 4 Net Worth Intelligence Workspace
 *
 * Provides toolbar with actions for net worth workspace.
 *
 * Architecture Flow: Backend → API → DTO → Mapper → ViewModel → Capability → Workspace → Components → Page
 */

import { Button } from '@/components/ui/button';
import { RefreshCw, Download } from 'lucide-react';
import { NetWorthFilters } from './net-worth-filters';
import { NetWorthSearch } from './net-worth-search';

/**
 * Net Worth Toolbar Props
 */
interface NetWorthToolbarProps {
  onRefresh: () => void;
  onExport: () => void;
  dateRange: { from?: string; to?: string } | null;
  accountTypes: string[];
  period: string;
  onDateRangeChange: (range: { from?: string; to?: string } | null) => void;
  onAccountTypesChange: (types: string[]) => void;
  onPeriodChange: (period: string) => void;
  onClearFilters: () => void;
  searchQuery: string;
  onSearchChange: (query: string) => void;
}

/**
 * Net Worth Toolbar Component
 */
export function NetWorthToolbar({
  onRefresh,
  onExport,
  dateRange,
  accountTypes,
  period,
  onDateRangeChange,
  onAccountTypesChange,
  onPeriodChange,
  onClearFilters,
  searchQuery,
  onSearchChange,
}: NetWorthToolbarProps) {
  return (
    <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 p-4 bg-white border-b">
      {/* Left side: Search and Filters */}
      <div className="flex items-center gap-2">
        <NetWorthSearch searchQuery={searchQuery} onSearchChange={onSearchChange} />
        <NetWorthFilters
          dateRange={dateRange}
          accountTypes={accountTypes}
          period={period}
          onDateRangeChange={onDateRangeChange}
          onAccountTypesChange={onAccountTypesChange}
          onPeriodChange={onPeriodChange}
          onClearFilters={onClearFilters}
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