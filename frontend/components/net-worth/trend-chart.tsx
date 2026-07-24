/**
 * Net Worth Trend Chart - Stage 4 Net Worth Intelligence Workspace
 *
 * Displays net worth history over time with interactive date range.
 *
 * Architecture Flow: Backend → API → DTO → Mapper → ViewModel → Capability → Workspace → Components → Page
 */

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { AlertCircle, LineChart } from 'lucide-react';
import { formatINR, formatDateDisplay } from '@/lib/utils/format';
import type { NetWorthViewModel, NetWorthHistoricalSnapshotViewModel } from '@/types/net-worth-view-model';

/**
 * Net Worth Trend Chart Props
 */
interface TrendChartProps {
  netWorth: NetWorthViewModel | null;
  loading: boolean;
  error: Error | null;
}

/**
 * Date Range Selector Props
 */
interface DateRangeSelectorProps {
  selectedPeriod: string;
  onPeriodChange: (period: string) => void;
}

/**
 * Date Range Selector Component
 */
function DateRangeSelector({ selectedPeriod, onPeriodChange }: DateRangeSelectorProps) {
  const periods = ['1M', '3M', '6M', '1Y', 'ALL'];

  return (
    <div className="flex gap-1" role="radiogroup" aria-label="Date range selector">
      {periods.map((period) => (
        <button
          key={period}
          onClick={() => onPeriodChange(period)}
          className={`px-2 py-1 text-xs rounded ${
            selectedPeriod === period
              ? 'bg-[var(--color-info-100)] text-[var(--color-info-700)]'
              : 'bg-[var(--surface-raised)] text-[var(--text-secondary)] hover:bg-[var(--surface-interactive)]'
          }`}
          role="radio"
          aria-checked={selectedPeriod === period}
          aria-label={`Select ${period} period`}
        >
          {period}
        </button>
      ))}
    </div>
  );
}

/**
 * Simple Bar Chart for Historical Data
 * Renders a simple text-based trend visualization
 */
function SimpleTrendVisualization({
  snapshots,
}: {
  snapshots: NetWorthHistoricalSnapshotViewModel[];
}) {
  if (snapshots.length === 0) {
    return (
      <p className="text-xs text-[var(--text-tertiary)] text-center py-4">
        No historical data available
      </p>
    );
  }

  // Find min and max for scaling
  const values = snapshots.map((s) => s.net_worth_paise);
  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = max - min || 1;

  return (
    <div className="space-y-2" role="table" aria-label="Net worth trend data">
      {snapshots.slice(-10).map((snapshot) => (
        <div key={snapshot.date} className="flex items-center gap-2 text-xs">
          <span className="w-20 text-[var(--text-tertiary)]" aria-label={snapshot.date}>
            {formatDateDisplay(snapshot.date)}
          </span>
          <div className="flex-1 bg-[var(--surface-raised)] rounded h-4 relative">
            <div
              className="bg-[var(--color-info-500)] rounded h-4"
              style={{
                width: `${((snapshot.net_worth_paise - min) / range) * 100}%`,
              }}
              aria-label={`Net worth: ${formatINR(snapshot.net_worth_paise)}`}
            />
          </div>
          <span className="w-20 text-right" aria-label={formatINR(snapshot.net_worth_paise)}>
            {formatINR(snapshot.net_worth_paise)}
          </span>
        </div>
      ))}
    </div>
  );
}

/**
 * Net Worth Trend Chart Component
 *
 * Shows net worth history with date range selector.
 */
export function TrendChart({ netWorth, loading, error }: TrendChartProps) {
  // Loading state
  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>
            <Skeleton className="h-5 w-32" />
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
          <CardTitle>Trend</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-2 text-[var(--color-negative-600)]">
            <AlertCircle className="h-4 w-4" />
            <span className="text-sm">Failed to load trend data</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  // Empty state
  if (!netWorth) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Trend</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-[var(--text-tertiary)] text-sm">No historical data available</p>
        </CardContent>
      </Card>
    );
  }

  // Historical snapshots are computed from account balance history
  // When account balance snapshots are available, they will be mapped to net worth snapshots
  // For now, display a production-safe empty state
  const snapshots: NetWorthHistoricalSnapshotViewModel[] = netWorth.historical_snapshots || [];

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <LineChart className="h-5 w-5" />
          Trend
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          <DateRangeSelector selectedPeriod="1M" onPeriodChange={() => {}} />
          <SimpleTrendVisualization snapshots={snapshots} />
        </div>
      </CardContent>
    </Card>
  );
}