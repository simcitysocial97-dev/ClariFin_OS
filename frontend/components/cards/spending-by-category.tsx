/**
 * Spending by Category - Stage 4 Credit Cards Intelligence Workspace
 *
 * Displays credit card spending breakdown by category.
 *
 * Architecture Flow: Backend → API → DTO → Mapper → ViewModel → Capability → Workspace → Components → Page
 */

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { AlertCircle } from 'lucide-react';
import { formatINRCompact } from '@/lib/utils/format';
import type { CreditCardsViewModel, SpendingByCategoryViewModel } from '@/types/credit-cards-view-model';

/**
 * Spending by Category Props
 */
interface SpendingByCategoryProps {
  creditCards: CreditCardsViewModel | null;
  loading: boolean;
  error: Error | null;
}

/**
 * Spending Category Item Component
 */
function SpendingCategoryItem({ spending }: { spending: SpendingByCategoryViewModel }) {
  return (
    <div className="border-b pb-3 mb-3 last:border-0 last:pb-0 last:mb-0">
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm font-medium">{spending.category}</span>
        <span className="text-sm text-gray-500">{spending.transaction_count} transactions</span>
      </div>
      <div className="flex items-center justify-between">
        <span className="text-sm" aria-label="Spending amount">
          {formatINRCompact(spending.amount_paise)}
        </span>
        <span className="text-xs text-gray-500">{spending.percentage}%</span>
      </div>
    </div>
  );
}

/**
 * Spending by Category Component
 */
export function SpendingByCategory({ creditCards, loading, error }: SpendingByCategoryProps) {
  // Loading state
  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>
            <Skeleton className="h-5 w-40" />
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-full" />
          </div>
        </CardContent>
      </Card>
    );
  }

  // Error state
  if (error) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Spending by Category</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-2 text-red-600">
            <AlertCircle className="h-4 w-4" />
            <span className="text-sm">Failed to load spending data</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  // Empty state
  if (!creditCards || !creditCards.spending || creditCards.spending.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Spending by Category</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-gray-500 text-sm">No spending data available</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Spending by Category</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          {creditCards.spending.map((spending) => (
            <SpendingCategoryItem key={`${spending.card_id}-${spending.category}`} spending={spending} />
          ))}
        </div>
      </CardContent>
    </Card>
  );
}