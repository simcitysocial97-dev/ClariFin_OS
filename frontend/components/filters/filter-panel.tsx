/**
 * Filter Panel Component - Stage 3 Transaction Intelligence Workspace
 *
 * Container component for all filter controls.
 */

'use client';

import { DateFilter } from './date-filter';
import { CategoryFilter } from './category-filter';
import { MerchantFilter } from './merchant-filter';
import { AmountFilter } from './amount-filter';
import { StatusFilter } from './status-filter';
import type { TransactionFilters } from '@/lib/filters/types';

interface FilterPanelProps {
  filters: TransactionFilters;
  onFiltersChange: (filters: TransactionFilters) => void;
  availableCategories?: string[];
  availableMerchants?: string[];
}

/**
 * Filter Panel Component
 * Composes all filter components in a horizontal layout
 */
export function FilterPanel({
  filters,
  onFiltersChange,
  availableCategories = [],
  availableMerchants = [],
}: FilterPanelProps) {
  return (
    <div className="flex flex-wrap items-center gap-2 p-4 border-b bg-background">
      <DateFilter
        value={filters.dateFilter}
        onChange={(dateFilter) => onFiltersChange({ ...filters, dateFilter })}
      />
      <CategoryFilter
        value={filters.categoryFilter}
        onChange={(categoryFilter) => onFiltersChange({ ...filters, categoryFilter })}
        availableCategories={availableCategories}
      />
      <MerchantFilter
        value={filters.merchantFilter}
        onChange={(merchantFilter) => onFiltersChange({ ...filters, merchantFilter })}
        availableMerchants={availableMerchants}
      />
      <AmountFilter
        value={filters.amountFilter}
        onChange={(amountFilter) => onFiltersChange({ ...filters, amountFilter })}
      />
      <StatusFilter
        value={filters.statusFilter}
        onChange={(statusFilter) => onFiltersChange({ ...filters, statusFilter })}
      />
    </div>
  );
}