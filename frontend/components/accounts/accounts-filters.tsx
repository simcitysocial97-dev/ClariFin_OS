/**
 * Accounts Filters - Stage 4 Accounts Intelligence Workspace
 *
 * Filter accounts by type, institution, status, date range, and balance range.
 *
 * Architecture Flow: Backend → API → DTO → Mapper → ViewModel → Capability → Workspace → Components → Page
 */

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Calendar, Filter, X } from 'lucide-react';
import type { AccountType, AccountStatus } from '@/types/accounts-view-model';

/**
 * Accounts Filters Props
 */
interface AccountsFiltersProps {
  accountTypes: string[];
  institutions: string[];
  statuses: string[];
  dateRange: { from?: string; to?: string } | null;
  balanceRange: { min?: number; max?: number } | null;
  onAccountTypesChange: (types: string[]) => void;
  onInstitutionsChange: (institutions: string[]) => void;
  onStatusesChange: (statuses: string[]) => void;
  onDateRangeChange: (range: { from?: string; to?: string } | null) => void;
  onBalanceRangeChange: (range: { min?: number; max?: number } | null) => void;
  onClearFilters: () => void;
  onApplyFilters: () => void;
}

/**
 * Available account type options
 */
const ACCOUNT_TYPE_OPTIONS: AccountType[] = ['savings', 'current', 'credit_card', 'investment', 'loan', 'other'];

/**
 * Available status options
 */
const STATUS_OPTIONS: AccountStatus[] = ['active', 'inactive', 'closed'];

/**
 * Accounts Filters Component
 */
export function AccountsFilters({
  accountTypes,
  institutions,
  statuses,
  dateRange,
  balanceRange,
  onAccountTypesChange,
  onInstitutionsChange,
  onStatusesChange,
  onDateRangeChange,
  onBalanceRangeChange,
  onClearFilters,
  onApplyFilters,
}: AccountsFiltersProps) {
  const hasActiveFilters =
    accountTypes.length > 0 ||
    institutions.length > 0 ||
    statuses.length > 0 ||
    dateRange ||
    balanceRange;

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

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Account Types Filter */}
        <div className="space-y-2">
          <Label>Account Types</Label>
          <div className="flex flex-wrap gap-1">
            {ACCOUNT_TYPE_OPTIONS.map((type) => (
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
        </div>

        {/* Institutions Filter */}
        <div className="space-y-2">
          <Label htmlFor="institutions">Institutions</Label>
          <Input
            id="institutions"
            placeholder="e.g., SBI, HDFC, ICICI"
            value={institutions.join(', ')}
            onChange={(e) => {
              const insts = e.target.value
                .split(',')
                .map((i) => i.trim())
                .filter((i) => i.length > 0);
              onInstitutionsChange(insts);
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

        {/* Date Range Filter */}
        <div className="space-y-2">
          <Label htmlFor="date-from">Date From</Label>
          <div className="relative">
            <Calendar className="absolute left-2 top-2.5 h-4 w-4 text-gray-500" />
            <Input
              id="date-from"
              type="date"
              className="pl-8"
              value={dateRange?.from || ''}
              onChange={(e) =>
                onDateRangeChange({
                  ...dateRange,
                  from: e.target.value || undefined,
                })
              }
            />
          </div>
        </div>

        <div className="space-y-2">
          <Label htmlFor="date-to">Date To</Label>
          <div className="relative">
            <Calendar className="absolute left-2 top-2.5 h-4 w-4 text-gray-500" />
            <Input
              id="date-to"
              type="date"
              className="pl-8"
              value={dateRange?.to || ''}
              onChange={(e) =>
                onDateRangeChange({
                  ...dateRange,
                  to: e.target.value || undefined,
                })
              }
            />
          </div>

          {/* Balance Range Filter */}
          <div className="space-y-2">
            <Label htmlFor="balance-min">Min Balance (₹)</Label>
            <Input
              id="balance-min"
              type="number"
              placeholder="0"
              value={balanceRange?.min || ''}
              onChange={(e) =>
                onBalanceRangeChange({
                  ...balanceRange,
                  min: e.target.value ? parseInt(e.target.value) * 100 : undefined,
                })
              }
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="balance-max">Max Balance (₹)</Label>
            <Input
              id="balance-max"
              type="number"
              placeholder="No limit"
              value={balanceRange?.max ? balanceRange.max / 100 : ''}
              onChange={(e) =>
                onBalanceRangeChange({
                  ...balanceRange,
                  max: e.target.value ? parseInt(e.target.value) * 100 : undefined,
                })
              }
            />
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