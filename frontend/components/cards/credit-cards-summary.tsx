/**
 * Credit Cards Summary - Stage 4 Credit Cards Intelligence Workspace
 *
 * Displays aggregated credit card summary with total balance and due.
 *
 * Architecture Flow: Backend → API → DTO → Mapper → ViewModel → Capability → Workspace → Components → Page
 */

import { Card, CardContent } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { AlertCircle } from 'lucide-react';
import { formatINR, formatINRCompact } from '@/lib/utils/format';
import type { CreditCardsViewModel } from '@/types/credit-cards-view-model';

/**
 * Credit Cards Summary Props
 */
interface CreditCardsSummaryProps {
  creditCards: CreditCardsViewModel | null;
  loading: boolean;
  error: Error | null;
}

/**
 * Credit Cards Summary Component
 *
 * Shows total balance, total due, and available credit across all cards.
 */
export function CreditCardsSummary({ creditCards, loading, error }: CreditCardsSummaryProps) {
  // Loading state
  if (loading) {
    return (
      <Card>
        <CardContent className="p-6">
          <div className="space-y-4">
            <Skeleton className="h-4 w-24" />
            <Skeleton className="h-8 w-48" />
            <Skeleton className="h-4 w-32" />
            <div className="grid grid-cols-3 gap-4 pt-4">
              <Skeleton className="h-12" />
              <Skeleton className="h-12" />
              <Skeleton className="h-12" />
            </div>
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
            <span className="text-sm">Failed to load credit cards data</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  // Empty state
  if (!creditCards) {
    return (
      <Card>
        <CardContent className="p-6">
          <p className="text-gray-500 text-sm">No credit cards data available</p>
        </CardContent>
      </Card>
    );
  }

  const { total_balance_paise, total_due_paise, total_available_paise, card_count } = creditCards;

  return (
    <Card>
      <CardContent className="p-6">
        <div className="space-y-4">
          {/* Total Balance Label */}
          <p className="text-sm text-gray-500">Total Balance</p>

          {/* Total Balance Amount */}
          <p className="text-3xl font-bold" aria-label="Total credit card balance">
            {formatINR(total_balance_paise)}
          </p>

          {/* Card Count */}
          <p className="text-sm text-gray-600">
            {card_count} card{card_count !== 1 ? 's' : ''}
          </p>

          {/* Summary Stats */}
          <div className="grid grid-cols-2 gap-4 pt-4">
            <div>
              <p className="text-xs text-gray-500">Total Due</p>
              <p className="text-sm font-medium" aria-label="Total due amount">
                {formatINRCompact(total_due_paise)}
              </p>
            </div>
            <div>
              <p className="text-xs text-gray-500">Available Credit</p>
              <p className="text-sm font-medium" aria-label="Available credit">
                {formatINRCompact(total_available_paise)}
              </p>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}