/**
 * Behaviour Filters - Stage 4 Behaviour Intelligence Workspace
 *
 * Filter behaviour by period.
 *
 * Architecture Flow: Backend → API → DTO → Mapper → ViewModel → Capability → Workspace → Components → Page
 */

import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Filter, X } from 'lucide-react';

/**
 * Behaviour Filters Props
 */
interface BehaviourFiltersProps {
  period: string;
  onPeriodChange: (period: string) => void;
  onClearFilters: () => void;
  onApplyFilters: () => void;
}

/**
 * Available period options
 */
const PERIOD_OPTIONS = ['1M', '3M', '6M', '1Y', '2Y', 'ALL'];

/**
 * Behaviour Filters Component
 */
export function BehaviourFilters({
  period,
  onPeriodChange,
  onClearFilters,
  onApplyFilters,
}: BehaviourFiltersProps) {
  const hasActiveFilters = period !== 'ALL';

  return (
    <div className="space-y-4 p-4 border rounded-lg bg-gray-50">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Filter className="h-4 w-4" />
          <h3 className="font-medium">Filters</h3>
        </div>
        {hasActiveFilters && (
          <Button
            variant="ghost"
            size="sm"
            onClick={onClearFilters}
            className="text-xs"
          >
            <X className="h-3 w-3 mr-1" />
            Clear
          </Button>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-1 gap-4">
        {/* Period Filter */}
        <div className="space-y-2">
          <Select value={period} onValueChange={onPeriodChange}>
            <SelectTrigger className="w-full">
              <SelectValue placeholder="Select period" />
            </SelectTrigger>
            <SelectContent>
              {PERIOD_OPTIONS.map((p) => (
                <SelectItem key={p} value={p}>
                  {p}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>

      <div className="flex justify-end">
        <Button onClick={onApplyFilters} size="sm">
          Apply Filters
        </Button>
      </div>
    </div>
  );
}