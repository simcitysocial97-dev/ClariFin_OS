/**
 * Net Worth Summary Card - Stage 4 Net Worth Intelligence Workspace
 *
 * Displays current net worth with trend indicator and period comparison.
 *
 * Architecture Flow: Backend → API → DTO → Mapper → ViewModel → Capability → Workspace → Components → Page
 */

import { Card, CardContent } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { AlertCircle, TrendingUp, TrendingDown, Minus } from 'lucide-react';
import { formatINR, formatPercentage } from '@/lib/utils/format';
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
      return <TrendingUp className="h-4 w-4 text-green-500" aria-label="Trending up" />;
    case 'down':
      return <TrendingDown className="h-4 w-4 text-red-500" aria-label="Trending down" />;
    default:
      return <Minus className="h-4 w-4 text-gray-500" aria-label="No change" />;
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
      <Card>
        <CardContent className="p-6">
          <div className="space-y-4">
            <Skeleton className="h-4 w-24" />
            <Skeleton className="h-8 w-48" />
            <Skeleton className="h-4 w-32" />
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
            <span className="text-sm">Failed to load net worth data</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  // Empty state
  if (!netWorth) {
    return (
      <Card>
        <CardContent className="p-6">
          <p className="text-gray-500 text-sm">No net worth data available</p>
        </CardContent>
      </Card>
    );
  }

  const { total_net_worth_paise, total_assets_paise, total_liabilities_paise, trend } = netWorth;

  return (
    <Card>
      <CardContent className="p-6">
        <div className="space-y-4">
          {/* Net Worth Label */}
          <p className="text-sm text-gray-500">Net Worth</p>

          {/* Net Worth Amount */}
          <p className="text-3xl font-bold" aria-label="Total net worth">
            {formatINR(total_net_worth_paise)}
          </p>

          {/* Trend Information */}
          {trend && (
            <div className="flex items-center gap-2">
              <TrendIcon direction={trend.direction} />
              <span className="text-sm text-gray-600">
                {formatPercentage(trend.percentage_change)} from {trend.period}
              </span>
            </div>
          )}

          {/* Assets and Liabilities Breakdown */}
          <div className="grid grid-cols-2 gap-4 pt-4 border-t">
            <div>
              <p className="text-xs text-gray-500">Assets</p>
              <p className="text-sm font-medium" aria-label="Total assets">
                {formatINR(total_assets_paise)}
              </p>
            </div>
            <div>
              <p className="text-xs text-gray-500">Liabilities</p>
              <p className="text-sm font-medium" aria-label="Total liabilities">
                {formatINR(total_liabilities_paise)}
              </p>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}