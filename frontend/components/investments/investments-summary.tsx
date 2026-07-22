/**
 * Investments Summary - Stage 4 Investments Intelligence Workspace
 *
 * Displays aggregated investments summary with total value and returns.
 *
 * Architecture Flow: Backend → API → DTO → Mapper → ViewModel → Capability → Workspace → Components → Page
 */

import { Card, CardContent } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { AlertCircle } from 'lucide-react';
import { formatINR, formatINRCompact } from '@/lib/utils/format';
import type { InvestmentsViewModel } from '@/types/investments-view-model';

/**
 * Investments Summary Props
 */
interface InvestmentsSummaryProps {
  investments: InvestmentsViewModel | null;
  loading: boolean;
  error: Error | null;
}

/**
 * Investments Summary Component
 *
 * Shows total value, total invested, and total returns across all investments.
 */
export function InvestmentsSummary({ investments, loading, error }: InvestmentsSummaryProps) {
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
          <div className="flex items-center gap-2 text-[var(--color-negative-600)]">
            <AlertCircle className="h-4 w-4" />
            <span className="text-sm">Failed to load investments data</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  // Empty state
  if (!investments) {
    return (
      <Card>
        <CardContent className="p-6">
          <p className="text-[var(--text-tertiary)] text-sm">No investments data available</p>
        </CardContent>
      </Card>
    );
  }

  const { total_value_paise, total_invested_paise, total_returns_paise, investment_count } = investments;

  return (
    <Card>
      <CardContent className="p-6">
        <div className="space-y-4">
          {/* Total Value Label */}
          <p className="text-sm text-gray-500">Total Value</p>

          {/* Total Value Amount */}
          <p className="text-3xl font-bold" aria-label="Total investment value">
            {formatINR(total_value_paise)}
          </p>

          {/* Investment Count */}
          <p className="text-sm text-gray-600">
            {investment_count} investment{investment_count !== 1 ? 's' : ''}
          </p>

          {/* Summary Stats */}
          <div className="grid grid-cols-2 gap-4 pt-4">
            <div>
              <p className="text-xs text-gray-500">Invested</p>
              <p className="text-sm font-medium" aria-label="Total invested">
                {formatINRCompact(total_invested_paise)}
              </p>
            </div>
            <div>
              <p className="text-xs text-gray-500">Returns</p>
              <p className="text-sm font-medium" aria-label="Total returns">
                {formatINRCompact(total_returns_paise)}
              </p>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}