/**
 * Monthly Trend Chart - Stage 4 Cashflow Truth Workspace
 *
 * Displays monthly income and expense trends over time.
 *
 * Architecture Flow: Backend → API → DTO → Mapper → ViewModel → Capability → Workspace → Components → Page
 */

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { AlertCircle } from 'lucide-react';
import { formatINR } from '@/lib/utils/format';
import type { CashflowMonthlyViewModel } from '@/types/cashflow-view-model';

/**
 * Monthly Trend Chart Props
 */
interface MonthlyTrendProps {
  monthly: CashflowMonthlyViewModel[];
  loading: boolean;
  error: Error | null;
}

/**
 * Monthly Trend Chart Component
 *
 * Shows a simple bar chart representation of monthly income vs expenses.
 */
export function MonthlyTrend({ monthly, loading, error }: MonthlyTrendProps) {
  // Loading state
  if (loading) {
    return (
      <Card>
        <CardHeader>
          <Skeleton className="h-5 w-32" />
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {Array.from({ length: 6 }).map((_, i) => (
              <Skeleton key={i} className="h-12 w-full" />
            ))}
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
            <span className="text-sm">Failed to load monthly trend data</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  // Empty state
  if (!monthly || monthly.length === 0) {
    return (
      <Card>
        <CardContent className="p-6">
          <p className="text-[var(--text-tertiary)] text-sm">No monthly data available</p>
        </CardContent>
      </Card>
    );
  }

  // Calculate max value for scaling
  const maxValue = Math.max(
    ...monthly.map(m => Math.max(m.income_paise, m.expenses_paise))
  );

  return (
    <Card>
      <CardHeader>
        <CardTitle>Monthly Trend</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {monthly.map((m) => (
            <div key={m.month} className="space-y-2">
              <div className="flex justify-between text-sm">
                <span className="font-medium">{m.month}</span>
                <span className="text-gray-500">
                  {formatINR(m.net_paise)} net
                </span>
              </div>
              <div className="flex gap-1 h-8">
                {/* Income bar */}
                <div
                  className="bg-green-500 rounded-l"
                  style={{
                    width: `${(m.income_paise / maxValue) * 100}%`,
                  }}
                  title={`Income: ${formatINR(m.income_paise)}`}
                />
                {/* Expense bar */}
                <div
                  className="bg-red-500 rounded-r"
                  style={{
                    width: `${(m.expenses_paise / maxValue) * 100}%`,
                  }}
                  title={`Expenses: ${formatINR(m.expenses_paise)}`}
                />
              </div>
              <div className="flex justify-between text-xs text-gray-500">
                <span>{formatINR(m.income_paise)} income</span>
                <span>{formatINR(m.expenses_paise)} expenses</span>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}