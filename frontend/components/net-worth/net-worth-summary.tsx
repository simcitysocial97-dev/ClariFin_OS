/**
 * Net Worth Summary Card - Stage 8E-C2 Production Visual System Migration
 *
 * Displays current net worth with trend indicator and period comparison.
 *
 * Architecture Flow: Backend → API → DTO → Mapper → ViewModel → Capability → Workspace → Components → Page
 */

import { Skeleton } from '@/components/ui/skeleton';
import { AlertCircle, TrendingUp, TrendingDown, Minus } from 'lucide-react';
import { formatPercentage } from '@/lib/utils/format';
import { MoneyValue } from '@/components/primitives/data-display/money-value';
import { Surface } from '@/components/primitives/surface/surface';
import type { NetWorthViewModel, NetWorthTrendDirection } from '@/types/net-worth-view-model';

/**
 * Net Worth Summary Card Props
 */
interface NetWorthSummaryProps {
  netWorth: NetWorthViewModel | null;
  loading: boolean;
  error: Error | null;
}

/**
 * Trend Icon Component
 * Displays the appropriate icon based on trend direction
 */
function TrendIcon({ direction }: { direction: NetWorthTrendDirection }) {
  switch (direction) {
    case 'up':
      return <TrendingUp className="h-4 w-4 text-[var(--color-positive-600)]" aria-label="Trending up" />;
    case 'down':
      return <TrendingDown className="h-4 w-4 text-[var(--color-negative-600)]" aria-label="Trending down" />;
    default:
      return <Minus className="h-4 w-4 text-[var(--text-tertiary)]" aria-label="No change" />;
  }
}

/**
 * Net Worth Summary Card Component
 *
 * Shows total net worth, assets, liabilities, and trend information.
 */
export function NetWorthSummary({ netWorth, loading, error }: NetWorthSummaryProps) {
  // Loading state
  if (loading) {
    return (
      <Surface variant="raised" density="none" className="p-4">
        <div className="space-y-4">
          <Skeleton className="h-4 w-24" />
          <Skeleton className="h-8 w-48" />
          <Skeleton className="h-4 w-32" />
        </div>
      </Surface>
    );
  }

  // Error state
  if (error) {
    return (
      <Surface variant="raised" density="none" className="p-4">
        <div className="flex items-center gap-2 text-[var(--color-negative-600)]">
          <AlertCircle className="h-4 w-4" />
          <span className="text-sm">Failed to load net worth data</span>
        </div>
      </Surface>
    );
  }

  // Empty state
  if (!netWorth) {
    return (
      <Surface variant="raised" density="none" className="p-4">
        <p className="text-[var(--text-tertiary)] text-sm">No net worth data available</p>
      </Surface>
    );
  }

  const { total_net_worth_paise, total_assets_paise, total_liabilities_paise, trend } = netWorth;

  return (
    <Surface variant="raised" density="none" className="p-4">
      <div className="space-y-4">
        {/* Net Worth Label */}
        <p className="text-sm text-[var(--text-tertiary)]">Net Worth</p>

        {/* Net Worth Amount */}
        <MoneyValue paise={total_net_worth_paise} variant="large" />

        {/* Trend Information */}
        {trend && (
          <div className="flex items-center gap-2">
            <TrendIcon direction={trend.direction} />
            <span className="text-sm text-[var(--text-secondary)]">
              {formatPercentage(trend.percentage_change)} from {trend.period}
            </span>
          </div>
        )}

        {/* Assets and Liabilities Breakdown */}
        <div className="grid grid-cols-2 gap-4 pt-4 border-t">
          <div>
            <p className="text-xs text-[var(--text-tertiary)]">Assets</p>
            <MoneyValue paise={total_assets_paise} variant="default" />
          </div>
          <div>
            <p className="text-xs text-[var(--text-tertiary)]">Liabilities</p>
            <MoneyValue paise={total_liabilities_paise} variant="default" />
          </div>
        </div>
      </div>
    </Surface>
  );
}