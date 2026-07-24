/**
 * Balance Trend Chart - Stage 4 Accounts Intelligence Workspace
 *
 * Visualizes balance history over time for selected account or all accounts.
 *
 * Architecture Flow: Backend → API → DTO → Mapper → ViewModel → Capability → Workspace → Components → Page
 */

import { Card, CardContent } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { AlertCircle } from 'lucide-react';
import { formatINRCompact } from '@/lib/utils/format';
import type { AccountsViewModel } from '@/types/accounts-view-model';

/**
 * Balance Trend Chart Props
 */
interface BalanceTrendProps {
  accounts: AccountsViewModel | null;
  loading: boolean;
  error: Error | null;
}

/**
 * Balance Trend Chart Component
 *
 * Shows balance history as a simple line chart representation.
 */
export function BalanceTrend({ accounts, loading, error }: BalanceTrendProps) {
  // Loading state
  if (loading) {
    return (
      <Card>
        <CardContent className="p-6">
          <Skeleton className="h-4 w-32 mb-4" />
          <Skeleton className="h-64 w-full" />
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
            <span className="text-sm">Failed to load balance history</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  // Empty state
  if (!accounts || !accounts.balance_history || accounts.balance_history.length === 0) {
    return (
      <Card>
        <CardContent className="p-6">
          <p className="text-gray-500 text-sm">No balance history available</p>
        </CardContent>
      </Card>
    );
  }

  const { balance_history } = accounts;

  // Calculate min/max for chart scaling
  const balances = balance_history.map(h => h.balance_paise);
  const minBalance = Math.min(...balances);
  const maxBalance = Math.max(...balances);
  const range = maxBalance - minBalance || 1;

  return (
    <Card>
      <CardContent className="p-6">
        <div className="space-y-4">
          {/* Chart Title */}
          <p className="text-sm text-gray-500">Balance Trend</p>

          {/* Simple Line Chart Representation */}
          <div className="h-64 relative">
            {/* Y-axis labels */}
            <div className="absolute left-0 top-0 bottom-0 w-16 flex flex-col justify-between text-xs text-gray-500">
              <span>{formatINRCompact(maxBalance)}</span>
              <span>{formatINRCompact((maxBalance + minBalance) / 2)}</span>
              <span>{formatINRCompact(minBalance)}</span>
            </div>

            {/* Chart area */}
            <div className="ml-16 h-full border-l border-b border-gray-200 relative">
              {/* Line chart - simple SVG path */}
              <svg className="w-full h-full" viewBox={`0 0 ${balance_history.length - 1} 100`}>
                {balance_history.length > 1 && (
                  <polyline
                    points={balance_history.map((h, i) => {
                      const x = i;
                      const y = 100 - ((h.balance_paise - minBalance) / range * 100);
                      return `${x},${y}`;
                    }).join(' ')}
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    className="text-blue-500"
                  />
                )}
              </svg>
            </div>
          </div>

          {/* X-axis labels */}
          <div className="ml-16 flex justify-between text-xs text-gray-500">
            <span>{balance_history[0]?.date}</span>
            <span>{balance_history[balance_history.length - 1]?.date}</span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}