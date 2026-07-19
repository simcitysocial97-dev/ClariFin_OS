/**
 * Net Worth Filters - Stage 4 Net Worth Intelligence Workspace
 *
 * Filter net worth view by account type, date range, and period.
 *
 * Architecture Flow: Backend → API → DTO → Mapper → ViewModel → Capability → Workspace → Components → Page
 */

import { Button } from '@/components/ui/button';
import { Filter, X } from 'lucide-react';

/**
 * Net Worth Filters Props
 */
interface NetWorthFiltersProps {
  dateRange: { from?: string; to?: string } | null;
  accountTypes: string[];
  period: string;
  onDateRangeChange: (range: { from?: string; to?: string } | null) => void;
  onAccountTypesChange: (types: string[]) => void;
  onPeriodChange: (period: string) => void;
  onClearFilters: () => void;
}

/**
 * Net Worth Filters Component
 */
export function NetWorthFilters({
  accountTypes,
  period,
  onAccountTypesChange,
  onPeriodChange,
  onClearFilters,
}: NetWorthFiltersProps) {
  const accountTypeOptions = ['savings', 'current', 'investment', 'loan', 'credit_card'];
  const periodOptions = ['1M', '3M', '6M', '1Y', 'ALL'];

  const activeFilterCount =
    (accountTypes.length > 0 ? 1 : 0) +
    (period !== '1M' ? 1 : 0);

  return (
    <div className="flex items-center gap-2">
      <div className="relative">
        <Button variant="outline" size="sm" className="relative">
          <Filter className="h-4 w-4 mr-2" />
          Filters
          {activeFilterCount > 0 && (
            <span className="absolute -top-1 -right-1 bg-blue-500 text-white text-xs rounded-full h-5 w-5 flex items-center justify-center">
              {activeFilterCount}
            </span>
          )}
        </Button>
      </div>

      {/* Account Types Filter */}
      <div className="flex flex-wrap gap-1">
        {accountTypeOptions.map((type) => (
          <button
            key={type}
            onClick={() => {
              const newTypes = accountTypes.includes(type)
                ? accountTypes.filter((t) => t !== type)
                : [...accountTypes, type];
              onAccountTypesChange(newTypes);
            }}
            className={`px-2 py-1 text-xs rounded ${
              accountTypes.includes(type)
                ? 'bg-blue-100 text-blue-700'
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            }`}
            aria-pressed={accountTypes.includes(type)}
          >
            {type}
          </button>
        ))}
      </div>

      {/* Period Filter */}
      <div className="flex flex-wrap gap-1">
        {periodOptions.map((p) => (
          <button
            key={p}
            onClick={() => onPeriodChange(p)}
            className={`px-2 py-1 text-xs rounded ${
              period === p
                ? 'bg-blue-100 text-blue-700'
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            }`}
            aria-pressed={period === p}
          >
            {p}
          </button>
        ))}
      </div>

      {activeFilterCount > 0 && (
        <Button variant="ghost" size="sm" onClick={onClearFilters}>
          <X className="h-3 w-3 mr-1" />
          Clear
        </Button>
      )}
    </div>
  );
}
