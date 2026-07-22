/**
 * Net Worth Composition Chart - Stage 4 Net Worth Intelligence Workspace
 *
 * Visualizes net worth composition as assets vs liabilities breakdown.
 *
 * Architecture Flow: Backend → API → DTO → Mapper → ViewModel → Capability → Workspace → Components → Page
 */

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { AlertCircle, PieChart } from 'lucide-react';
import { formatINR } from '@/lib/utils/format';
import type { NetWorthViewModel, NetWorthBreakdownItemViewModel } from '@/types/net-worth-view-model';

/**
 * Net Worth Composition Chart Props
 */
interface CompositionChartProps {
  netWorth: NetWorthViewModel | null;
  loading: boolean;
  error: Error | null;
}

/**
 * Breakdown Item Component
 * Displays a single item in the composition breakdown
 */
function BreakdownItem({ item }: { item: NetWorthBreakdownItemViewModel }) {
  const isLiability = item.balance_paise < 0;
  const displayValue = Math.abs(item.balance_paise);

  return (
    <div className="flex items-center justify-between py-2">
      <div className="flex items-center gap-2">
        <div
          className={`w-3 h-3 rounded-full ${
            isLiability ? 'bg-[var(--color-negative-500)]' : 'bg-[var(--color-positive-500)]'
          }`}
          aria-label={isLiability ? 'Liability' : 'Asset'}
        />
        <span className="text-sm">{item.name}</span>
      </div>
      <div className="text-right">
        <span className="text-sm font-medium">{formatINR(displayValue)}</span>
        <span className="text-xs text-[var(--text-tertiary)] ml-1">{item.percentage.toFixed(1)}%</span>
      </div>
    </div>
  );
}

/**
 * Net Worth Composition Chart Component
 *
 * Shows asset and liability categories with their values.
 */
export function CompositionChart({ netWorth, loading, error }: CompositionChartProps) {
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
          <CardTitle>Composition</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-2 text-[var(--color-negative-600)]">
            <AlertCircle className="h-4 w-4" />
            <span className="text-sm">Failed to load composition data</span>
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
          <CardTitle>Composition</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-[var(--text-tertiary)] text-sm">No accounts configured for net worth calculation</p>
        </CardContent>
      </Card>
    );
  }

  const { composition } = netWorth;
  const { asset_breakdown, liability_breakdown } = composition;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <PieChart className="h-5 w-5" />
          Composition
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {/* Assets Section */}
          <div>
            <h3 className="text-sm font-medium text-[var(--color-positive-600)] mb-2">Assets</h3>
            {asset_breakdown.length === 0 ? (
              <p className="text-xs text-[var(--text-tertiary)]">No assets to display</p>
            ) : (
              <div className="space-y-1">
                {asset_breakdown.map((item) => (
                  <BreakdownItem key={item.id} item={item} />
                ))}
              </div>
            )}
          </div>

          {/* Liabilities Section */}
          <div>
            <h3 className="text-sm font-medium text-[var(--color-negative-600)] mb-2">Liabilities</h3>
            {liability_breakdown.length === 0 ? (
              <p className="text-xs text-[var(--text-tertiary)]">No liabilities to display</p>
            ) : (
              <div className="space-y-1">
                {liability_breakdown.map((item) => (
                  <BreakdownItem key={item.id} item={item} />
                ))}
              </div>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}