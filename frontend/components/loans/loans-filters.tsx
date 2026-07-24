/**
 * Loans Filters - Stage 4 Loans Intelligence Workspace
 *
 * Filter loans by type, lender, and status.
 *
 * Architecture Flow: Backend → API → DTO → Mapper → ViewModel → Capability → Workspace → Components → Page
 */

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Filter, X } from 'lucide-react';
import type { LoanType, LoanStatus } from '@/types/loans-view-model';

/**
 * Loans Filters Props
 */
interface LoansFiltersProps {
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
 * Available loan type options
 */
const LOAN_TYPE_OPTIONS: LoanType[] = ['personal', 'home', 'car', 'education', 'other'];

/**
 * Available status options
 */
const STATUS_OPTIONS: LoanStatus[] = ['active', 'closed', 'defaulted'];

/**
 * Loans Filters Component
 */
export function LoansFilters({
  loanTypes,
  lenders,
  statuses,
  onLoanTypesChange,
  onLendersChange,
  onStatusesChange,
  onClearFilters,
  onApplyFilters,
}: LoansFiltersProps) {
  const hasActiveFilters =
    loanTypes.length > 0 ||
    lenders.length > 0 ||
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
        {/* Loan Types Filter */}
        <div className="space-y-2">
          <Label>Loan Types</Label>
          <div className="flex flex-wrap gap-1">
            {LOAN_TYPE_OPTIONS.map((type) => (
              <button
                key={type}
                onClick={() => {
                  const newTypes = loanTypes.includes(type)
                    ? loanTypes.filter((t) => t !== type)
                    : [...loanTypes, type];
                  onLoanTypesChange(newTypes);
                }}
                className={`px-2 py-1 text-xs rounded ${
                  loanTypes.includes(type)
                    ? 'bg-blue-100 text-blue-700'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}
                aria-pressed={loanTypes.includes(type)}
              >
                {type}
              </button>
            ))}
          </div>
        </div>

        {/* Lenders Filter */}
        <div className="space-y-2">
          <Label htmlFor="lenders">Lenders</Label>
          <Input
            id="lenders"
            placeholder="e.g., SBI, HDFC, ICICI"
            value={lenders.join(', ')}
            onChange={(e) => {
              const l = e.target.value
                .split(',')
                .map((i) => i.trim())
                .filter((i) => i.length > 0);
              onLendersChange(l);
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