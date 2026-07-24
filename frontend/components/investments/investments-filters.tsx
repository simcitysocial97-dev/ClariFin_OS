/**
 * Investments Filters - Stage 4 Investments Intelligence Workspace
 *
 * Filter investments by type, institution, and status.
 *
 * Architecture Flow: Backend → API → DTO → Mapper → ViewModel → Capability → Workspace → Components → Page
 */

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Filter, X } from 'lucide-react';
import type { InvestmentType, InvestmentStatus } from '@/types/investments-view-model';

/**
 * Investments Filters Props
 */
interface InvestmentsFiltersProps {
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
 * Available investment type options
 */
const INVESTMENT_TYPE_OPTIONS: InvestmentType[] = ['stocks', 'mutual_funds', 'bonds', 'fd', 'ppf', 'gold', 'other'];

/**
 * Available status options
 */
const STATUS_OPTIONS: InvestmentStatus[] = ['active', 'closed', 'matured'];

/**
 * Investments Filters Component
 */
export function InvestmentsFilters({
  investmentTypes,
  institutions,
  statuses,
  onInvestmentTypesChange,
  onInstitutionsChange,
  onStatusesChange,
  onClearFilters,
  onApplyFilters,
}: InvestmentsFiltersProps) {
  const hasActiveFilters =
    investmentTypes.length > 0 ||
    institutions.length > 0 ||
    statuses.length > 0;

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

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Investment Types Filter */}
        <div className="space-y-2">
          <Label>Investment Types</Label>
          <div className="flex flex-wrap gap-1">
            {INVESTMENT_TYPE_OPTIONS.map((type) => (
              <button
                key={type}
                onClick={() => {
                  const newTypes = investmentTypes.includes(type)
                    ? investmentTypes.filter((t) => t !== type)
                    : [...investmentTypes, type];
                  onInvestmentTypesChange(newTypes);
                }}
                className={`px-2 py-1 text-xs rounded ${
                  investmentTypes.includes(type)
                    ? 'bg-blue-100 text-blue-700'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}
                aria-pressed={investmentTypes.includes(type)}
              >
                {type}
              </button>
            ))}
          </div>
        </div>

        {/* Institutions Filter */}
        <div className="space-y-2">
          <Label htmlFor="institutions">Institutions</Label>
          <Input
            id="institutions"
            placeholder="e.g., Zerodha, Groww, ICICI"
            value={institutions.join(', ')}
            onChange={(e) => {
              const inst = e.target.value
                .split(',')
                .map((i) => i.trim())
                .filter((i) => i.length > 0);
              onInstitutionsChange(inst);
            }}
          />
        </div>

        {/* Statuses Filter */}
        <div className="space-y-2">
          <Label>Statuses</Label>
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
      </div>

      <div className="flex justify-end">
        <Button onClick={onApplyFilters} size="sm">
          Apply Filters
        </Button>
      </div>
    </div>
  );
}