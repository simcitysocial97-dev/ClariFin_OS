/**
 * Forecast Summary Card - Stage 4 Forecast Intelligence Workspace
 *
 * Displays aggregated forecast summary with projected growth.
 *
 * Architecture Flow: Backend → API → DTO → Mapper → ViewModel → Capability → Workspace → Components → Page
 */

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { AlertCircle, TrendingUp, TrendingDown, BarChart3 } from 'lucide-react';
import { formatINR } from '@/lib/utils/format';
import type { ForecastSummaryViewModel } from '@/types/forecast-view-model';

/**
 * Forecast Summary Props
 */
interface ForecastSummaryProps {
  summary: ForecastSummaryViewModel | null;
  loading: boolean;
  error: Error | null;
}

/**
 * Forecast Summary Card Component
 *
 * Shows current net worth, projected net worth, and growth percentage.
 */
export function ForecastSummary({ summary, loading, error }: ForecastSummaryProps) {
  // Loading state
  if (loading) {
    return (
      <Card>
        <CardHeader>
          <Skeleton className="h-5 w-32" />
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <Skeleton className="h-8 w-48" />
            <Skeleton className="h-12 w-32" />
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
          <div className="flex items-center gap-2 text-[var(--color-negative-600)]">
            <AlertCircle className="h-4 w-4" />
            <span className="text-sm">Failed to load forecast summary</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  // Empty state
  if (!summary) {
    return (
      <Card>
        <CardContent className="p-6">
          <p className="text-[var(--text-tertiary)] text-sm">No forecast data available</p>
        </CardContent>
      </Card>
    );
  }

  const { current_net_worth_paise, projected_net_worth_paise, projected_growth_percentage, horizon_months } = summary;

  // Determine growth color
  const growthColor = projected_growth_percentage >= 0 ? 'text-[var(--color-positive-600)]' : 'text-[var(--color-negative-600)]';
  const GrowthIcon = projected_growth_percentage >= 0 ? TrendingUp : TrendingDown;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <BarChart3 className="h-5 w-5" />
          Forecast Summary ({horizon_months} months)
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {/* Current Net Worth */}
          <div>
            <p className="text-sm text-gray-500">Current Net Worth</p>
            <p className="text-xl font-bold" aria-label="Current net worth">
              {formatINR(current_net_worth_paise)}
            </p>
          </div>

          {/* Projected Net Worth */}
          <div>
            <p className="text-sm text-gray-500">Projected Net Worth</p>
            <p className="text-2xl font-bold" aria-label="Projected net worth">
              {formatINR(projected_net_worth_paise)}
            </p>
          </div>

          {/* Growth Indicator */}
          <div className="flex items-center gap-2 pt-2">
            <GrowthIcon className={`h-5 w-5 ${growthColor}`} />
            <span className={`text-lg font-medium ${growthColor}`} aria-label="Projected growth">
              {projected_growth_percentage >= 0 ? '+' : ''}
              {projected_growth_percentage.toFixed(1)}%
            </span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}