/**
 * Cashflow Summary Card - Stage 8E-C2 Production Visual System Migration
 *
 * Displays current cashflow summary with income, expenses, and net cashflow.
 *
 * Architecture Flow: Backend → API → DTO → Mapper → ViewModel → Capability → Workspace → Components → Page
 */

import { Skeleton } from '@/components/ui/skeleton';
import { AlertCircle, TrendingUp, TrendingDown, Minus } from 'lucide-react';
import { formatPercentage } from '@/lib/utils/format';
import { MoneyValue } from '@/components/primitives/data-display/money-value';
import { Surface } from '@/components/primitives/surface/surface';
import type { CashflowViewModel, CashflowTrendDirection } from '@/types/cashflow-view-model';

/**
 * Cashflow Summary Card Props
 */
interface CashflowSummaryProps {
  cashflow: CashflowViewModel | null;
  loading: boolean;
  error: Error | null;
}

/**
 * Trend Icon Component
 * Displays the appropriate icon based on trend direction
 */
function TrendIcon({ direction }: { direction: CashflowTrendDirection }) {
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
 * Cashflow Summary Card Component
 *
 * Shows total income, expenses, and net cashflow with trend information.
 */
export function CashflowSummary({ cashflow, loading, error }: CashflowSummaryProps) {
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
          <span className="text-sm">Failed to load cashflow data</span>
        </div>
      </Surface>
    );
  }

  // Empty state
  if (!cashflow) {
    return (
      <Surface variant="raised" density="none" className="p-4">
        <p className="text-[var(--text-tertiary)] text-sm">No cashflow data available</p>
      </Surface>
    );
  }

  const { total_income_paise, total_expenses_paise, net_cashflow_paise, trend } = cashflow;

  return (
    <Surface variant="raised" density="none" className="p-4">
      <div className="space-y-4">
        {/* Cashflow Label */}
        <p className="text-sm text-[var(--text-tertiary)]">Net Cashflow</p>

        {/* Net Cashflow Amount */}
        <MoneyValue paise={net_cashflow_paise} variant="large" />

        {/* Trend Information */}
        {trend && (
          <div className="flex items-center gap-2">
            <TrendIcon direction={trend.direction} />
            <span className="text-sm text-[var(--text-secondary)]">
              {formatPercentage(trend.percentage_change)} from {trend.period}
            </span>
          </div>
        )}

        {/* Income and Expenses Breakdown */}
        <div className="grid grid-cols-2 gap-4 pt-4 border-t">
          <div>
            <p className="text-xs text-[var(--text-tertiary)]">Income</p>
            <MoneyValue paise={total_income_paise} variant="default" sign="positive" />
          </div>
          <div>
            <p className="text-xs text-[var(--text-tertiary)]">Expenses</p>
            <MoneyValue paise={total_expenses_paise} variant="default" sign="negative" />
          </div>
        </div>
      </div>
    </Surface>
  );
}