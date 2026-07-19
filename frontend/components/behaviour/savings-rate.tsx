/**
 * Savings Rate - Stage 4 Behaviour Intelligence Workspace
 *
 * Displays savings rate analysis.
 *
 * Architecture Flow: Backend → API → DTO → Mapper → ViewModel → Capability → Workspace → Components → Page
 */

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { AlertCircle, PiggyBank } from 'lucide-react';
import { formatINR } from '@/lib/utils/format';
import type { SavingsRateViewModel } from '@/types/behaviour-view-model';

/**
 * Savings Rate Props
 */
interface SavingsRateProps {
  savingsRate: SavingsRateViewModel | null | undefined;
  loading: boolean;
  error: Error | null;
}

/**
 * Savings Rate Component
 *
 * Shows the savings rate with income, savings, and period.
 */
export function SavingsRate({ savingsRate, loading, error }: SavingsRateProps) {
  // Loading state
  if (loading) {
    return (
      <Card>
        <CardHeader>
          <Skeleton className="h-5 w-32" />
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <Skeleton className="h-16 w-16 rounded-full mx-auto" />
            <Skeleton className="h-4 w-24 mx-auto" />
            <div className="grid grid-cols-2 gap-4">
              <Skeleton className="h-10" />
              <Skeleton className="h-10" />
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
            <span className="text-sm">Failed to load savings rate</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  // Empty state
  if (!savingsRate) {
    return (
      <Card>
        <CardContent className="p-6">
          <p className="text-gray-500 text-sm">No savings rate data available</p>
        </CardContent>
      </Card>
    );
  }

  // Convert basis points to percentage
  const percentage = (savingsRate.savings_rate_bps / 100).toFixed(1);

  // Determine rate color
  const rateColor = savingsRate.savings_rate_bps >= 200 ? 'text-green-600' : savingsRate.savings_rate_bps >= 100 ? 'text-amber-600' : 'text-red-600';

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <PiggyBank className="h-5 w-5" />
          Savings Rate
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {/* Savings Rate */}
          <div className="text-center">
            <p className="text-sm text-gray-500 mb-1">Savings Rate ({savingsRate.period})</p>
            <p className={`text-3xl font-bold ${rateColor}`} aria-label="Savings rate percentage">
              {percentage}%
            </p>
          </div>

          {/* Income and Savings */}
          <div className="grid grid-cols-2 gap-4 pt-2 border-t">
            <div>
              <p className="text-xs text-gray-500">Total Income</p>
              <p className="text-sm font-medium" aria-label="Total income">
                {formatINR(savingsRate.income_paise)}
              </p>
            </div>
            <div>
              <p className="text-xs text-gray-500">Total Savings</p>
              <p className="text-sm font-medium" aria-label="Total savings">
                {formatINR(savingsRate.savings_paise)}
              </p>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}