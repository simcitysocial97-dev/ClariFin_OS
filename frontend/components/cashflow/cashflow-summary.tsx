/**
 * Cashflow Summary Card - Stage 8E-C2 Production Visual System Migration
 *
 * Displays current cashflow summary with income, expenses, and net cashflow.
 *
 * Architecture Flow: Backend → API → DTO → Mapper → ViewModel → Capability → Workspace → Components → Page
 */

import { Card, CardContent } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { AlertCircle, TrendingUp, TrendingDown, Minus } from 'lucide-react';
import { formatPercentage } from '@/lib/utils/format';
import { MoneyValue } from '@/components/primitives/data-display/money-value';
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
      return <TrendingUp className="h-4 w-4 text-green-500" aria-label="Trending up" />;
    case 'down':
      return <TrendingDown className="h-4 w-4 text-red-500" aria-label="Trending down" />;
    default:
      return <Minus className="h-4 w-4 text-gray-500" aria-label="No change" />;
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
            <span className="text-sm">Failed to load cashflow data</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  // Empty state
  if (!cashflow) {
    return (
      <Card>
        <CardContent className="p-6">
          <p className="text-gray-500 text-sm">No cashflow data available</p>
        </CardContent>
      </Card>
    );
  }

  const { total_income_paise, total_expenses_paise, net_cashflow_paise, trend } = cashflow;

  return (
    <Card>
      <CardContent className="p-6">
        <div className="space-y-4">
          {/* Cashflow Label */}
          <p className="text-sm text-gray-500">Net Cashflow</p>

          {/* Net Cashflow Amount */}
          <MoneyValue paise={net_cashflow_paise} variant="large" />

          {/* Trend Information */}
          {trend && (
            <div className="flex items-center gap-2">
              <TrendIcon direction={trend.direction} />
              <span className="text-sm text-gray-600">
                {formatPercentage(trend.percentage_change)} from {trend.period}
              </span>
            </div>
          )}

          {/* Income and Expenses Breakdown */}
          <div className="grid grid-cols-2 gap-4 pt-4 border-t">
            <div>
              <p className="text-xs text-gray-500">Income</p>
              <MoneyValue paise={total_income_paise} variant="default" sign="positive" />
            </div>
            <div>
              <p className="text-xs text-gray-500">Expenses</p>
              <MoneyValue paise={total_expenses_paise} variant="default" sign="negative" />
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}