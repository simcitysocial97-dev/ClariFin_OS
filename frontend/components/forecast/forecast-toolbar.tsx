/**
 * Forecast Toolbar - Stage 4 Forecast Intelligence Workspace
 *
 * Toolbar with search, filters, and actions for forecast workspace.
 *
 * Architecture Flow: Backend → API → DTO → Mapper → ViewModel → Capability → Workspace → Components → Page
 */

import { Button } from '@/components/ui/button';
import { RefreshCw, Download } from 'lucide-react';
import { ForecastSearch } from './forecast-search';
import { ForecastFilters } from './forecast-filters';

/**
 * Forecast Toolbar Props
 */
interface ForecastToolbarProps {
  onRefresh: () => void;
  onExport: () => void;
  searchQuery: string;
  onSearchChange: (query: string) => void;
  horizon: number;
  scenarios: string[];
  onHorizonChange: (horizon: number) => void;
  onScenariosChange: (scenarios: string[]) => void;
  onClearFilters: () => void;
  onApplyFilters: () => void;
}

/**
 * Forecast Toolbar Component
 */
export function ForecastToolbar({
  onRefresh,
  onExport,
  searchQuery,
  onSearchChange,
  horizon,
  scenarios,
  onHorizonChange,
  onScenariosChange,
  onClearFilters,
  onApplyFilters,
}: ForecastToolbarProps) {
  return (
    <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 p-4 bg-white border-b">
      {/* Left side: Search and Filters */}
      <div className="flex items-center gap-2">
        <ForecastSearch searchQuery={searchQuery} onSearchChange={onSearchChange} />
        <ForecastFilters
          horizon={horizon}
          scenarios={scenarios}
          onHorizonChange={onHorizonChange}
          onScenariosChange={onScenariosChange}
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