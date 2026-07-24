/**
 * Reconciliation Filters - Stage 4 Reconciliation Intelligence Workspace
 *
 * Filter reconciliation by status and bank.
 *
 * Architecture Flow: Backend → API → DTO → Mapper → ViewModel → Capability → Workspace → Components → Page
 */

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Filter, X } from 'lucide-react';
import type { ReconciliationStatus } from '@/types/reconciliation-view-model';

/**
 * Reconciliation Filters Props
 */
interface ReconciliationFiltersProps {
  statuses: string[];
  banks: string[];
  onStatusesChange: (statuses: string[]) => void;
  onBanksChange: (banks: string[]) => void;
  onClearFilters: () => void;
  onApplyFilters: () => void;
}

/**
 * Available status options
 */
const STATUS_OPTIONS: ReconciliationStatus[] = ['pending', 'confirmed', 'rejected', 'disputed'];

/**
 * Reconciliation Filters Component
 */
export function ReconciliationFilters({
  statuses,
  banks,
  onStatusesChange,
  onBanksChange,
  onClearFilters,
  onApplyFilters,
}: ReconciliationFiltersProps) {
  const hasActiveFilters = statuses.length > 0 || banks.length > 0;

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

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Statuses Filter */}
        <div className="space-y-2">
          <Label>Status</Label>
          <div className="flex flex-wrap gap-1">
            {STATUS_OPTIONS.map((status) => (
              <button
                key={status}
                onClick={() => {
                  const newStatuses = statuses.includes(status)
                    ? statuses.filter((s) => s !== status)
                    : [...statuses, status];
                  onStatusesChange(newStatuses);
                }}
                className={`px-2 py-1 text-xs rounded ${
                  statuses.includes(status)
                    ? 'bg-blue-100 text-blue-700'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}
                aria-pressed={statuses.includes(status)}
              >
                {status}
              </button>
            ))}
          </div>
        </div>

        {/* Banks Filter */}
        <div className="space-y-2">
          <Label htmlFor="banks">Banks</Label>
          <Input
            id="banks"
            placeholder="e.g., SBI, HDFC, ICICI"
            value={banks.join(', ')}
            onChange={(e) => {
              const b = e.target.value
                .split(',')
                .map((i) => i.trim())
                .filter((i) => i.length > 0);
              onBanksChange(b);
            }}
          />
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