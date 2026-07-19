/**
 * Category Breakdown - Stage 4 Cashflow Truth Workspace
 *
 * Displays expense and income breakdown by category.
 *
 * Architecture Flow: Backend → API → DTO → Mapper → ViewModel → Capability → Workspace → Components → Page
 */

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { AlertCircle } from 'lucide-react';
import { formatINR } from '@/lib/utils/format';
import type { CashflowCategoryViewModel } from '@/types/cashflow-view-model';

/**
 * Category Breakdown Props
 */
interface CategoryBreakdownProps {
  categories: CashflowCategoryViewModel[];
  loading: boolean;
  error: Error | null;
}

/**
 * Category Breakdown Component
 *
 * Shows a list of categories with their amounts and percentages.
 */
export function CategoryBreakdown({ categories, loading, error }: CategoryBreakdownProps) {
  // Loading state
  if (loading) {
    return (
      <Card>
        <CardHeader>
          <Skeleton className="h-5 w-32" />
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {Array.from({ length: 5 }).map((_, i) => (
              <Skeleton key={i} className="h-12 w-full" />
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  // Error state
  if (error) {
    return (
      <Card>
        <CardContent className="p-6">
          <div className="flex items-center gap-2 text-red-600">
            <AlertCircle className="h-4 w-4" />
            <span className="text-sm">Failed to load category data</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  // Empty state
  if (!categories || categories.length === 0) {
    return (
      <Card>
        <CardContent className="p-6">
          <p className="text-gray-500 text-sm">No category data available</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Category Breakdown</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {categories.map((category) => (
            <div key={category.category_id} className="space-y-1">
              <div className="flex justify-between items-center">
                <span className="text-sm font-medium">{category.category_name}</span>
                <span className="text-sm font-semibold">
                  {formatINR(category.amount_paise)}
                </span>
              </div>
              <div className="flex items-center gap-2">
                <div className="flex-1 bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-blue-500 h-2 rounded-full"
                    style={{ width: `${category.percentage}%` }}
                  />
                </div>
                <span className="text-xs text-gray-500 w-12 text-right">
                  {category.percentage.toFixed(1)}%
                </span>
              </div>
              <p className="text-xs text-gray-400">
                {category.transaction_count} transactions
              </p>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}