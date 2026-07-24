/**
 * Cashflow Filters - Stage 4 Cashflow Truth Workspace
 *
 * Filter controls for cashflow data.
 *
 * Architecture Flow: Backend → API → DTO → Mapper → ViewModel → Capability → Workspace → Components → Page
 */

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Calendar, Filter, X } from 'lucide-react';
import type { CashflowFiltersViewModel } from '@/types/cashflow-view-model';

/**
 * Cashflow Filters Props
 */
interface CashflowFiltersProps {
  filters: CashflowFiltersViewModel;
  onDateRangeChange: (range: { from?: string; to?: string } | null) => void;
  onCategoriesChange: (categories: string[]) => void;
  onMerchantsChange: (merchants: string[]) => void;
  onClearFilters: () => void;
  onApplyFilters: () => void;
}

/**
 * Cashflow Filters Component
 *
 * Provides filter controls for date range, categories, merchants, and amount range.
 */
export function CashflowFilters({
  filters,
  onDateRangeChange,
  onCategoriesChange,
  onMerchantsChange,
  onClearFilters,
  onApplyFilters,
}: CashflowFiltersProps) {
  const hasActiveFilters = 
    filters.date_range || 
    filters.categories?.length || 
    filters.merchants?.length || 
    filters.amount_range;

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
        {/* Date Range Filter */}
        <div className="space-y-2">
          <Label htmlFor="date-from">Date From</Label>
          <div className="relative">
            <Calendar className="absolute left-2 top-2.5 h-4 w-4 text-gray-500" />
            <Input
              id="date-from"
              type="date"
              className="pl-8"
              value={filters.date_range?.from || ''}
              onChange={(e) => onDateRangeChange({
                ...filters.date_range,
                from: e.target.value || undefined,
              })}
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
              value={filters.date_range?.to || ''}
              onChange={(e) => onDateRangeChange({
                ...filters.date_range,
                to: e.target.value || undefined,
              })}
            />
          </div>
        </div>

        {/* Categories Filter */}
        <div className="space-y-2">
          <Label htmlFor="categories">Categories</Label>
          <Input
            id="categories"
            placeholder="e.g., groceries, rent, salary"
            value={filters.categories?.join(', ') || ''}
            onChange={(e) => {
              const categories = e.target.value
                .split(',')
                .map(c => c.trim())
                .filter(c => c.length > 0);
              onCategoriesChange(categories);
            }}
          />
        </div>

        {/* Merchants Filter */}
        <div className="space-y-2">
          <Label htmlFor="merchants">Merchants</Label>
          <Input
            id="merchants"
            placeholder="e.g., Amazon, Swiggy"
            value={filters.merchants?.join(', ') || ''}
            onChange={(e) => {
              const merchants = e.target.value
                .split(',')
                .map(m => m.trim())
                .filter(m => m.length > 0);
              onMerchantsChange(merchants);
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