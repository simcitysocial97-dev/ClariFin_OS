/**
 * Behaviour Toolbar - Stage 4 Behaviour Intelligence Workspace
 *
 * Toolbar with search, filters, and actions for behaviour workspace.
 *
 * Architecture Flow: Backend → API → DTO → Mapper → ViewModel → Capability → Workspace → Components → Page
 */

import { Button } from '@/components/ui/button';
import { RefreshCw, Download } from 'lucide-react';
import { BehaviourSearch } from './behaviour-search';
import { BehaviourFilters } from './behaviour-filters';

/**
 * Behaviour Toolbar Props
 */
interface BehaviourToolbarProps {
  onRefresh: () => void;
  onExport: () => void;
  searchQuery: string;
  onSearchChange: (query: string) => void;
  period: string;
  onPeriodChange: (period: string) => void;
  onClearFilters: () => void;
  onApplyFilters: () => void;
}

/**
 * Behaviour Toolbar Component
 */
export function BehaviourToolbar({
  onRefresh,
  onExport,
  searchQuery,
  onSearchChange,
  period,
  onPeriodChange,
  onClearFilters,
  onApplyFilters,
}: BehaviourToolbarProps) {
  return (
    <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 p-4 bg-white border-b">
      {/* Left side: Search and Filters */}
      <div className="flex items-center gap-2">
        <BehaviourSearch searchQuery={searchQuery} onSearchChange={onSearchChange} />
        <BehaviourFilters
          period={period}
          onPeriodChange={onPeriodChange}
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