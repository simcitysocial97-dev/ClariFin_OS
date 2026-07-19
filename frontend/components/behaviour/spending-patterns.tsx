/**
 * Spending Patterns - Stage 4 Behaviour Intelligence Workspace
 *
 * Displays spending pattern analysis with category breakdown.
 *
 * Architecture Flow: Backend → API → DTO → Mapper → ViewModel → Capability → Workspace → Components → Page
 */

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { AlertCircle, TrendingUp, TrendingDown, Minus } from 'lucide-react';
import { formatINR } from '@/lib/utils/format';
import type { SpendingPatternViewModel } from '@/types/behaviour-view-model';

/**
 * Spending Patterns Props
 */
interface SpendingPatternsProps {
  patterns: SpendingPatternViewModel[];
  loading: boolean;
  error: Error | null;
}

/**
 * Get trend icon
 */
function getTrendIcon(trend: string) {
  switch (trend) {
    case 'increasing':
      return <TrendingUp className="h-4 w-4 text-red-600" />;
    case 'decreasing':
      return <TrendingDown className="h-4 w-4 text-green-600" />;
    case 'stable':
    default:
      return <Minus className="h-4 w-4 text-gray-600" />;
  }
}

/**
 * Spending Patterns Component
 *
 * Shows a list of spending patterns with category, amount, percentage, and trend.
 */
export function SpendingPatterns({ patterns, loading, error }: SpendingPatternsProps) {
  // Loading state
  if (loading) {
    return (
      <Card>
        <CardHeader>
          <Skeleton className="h-5 w-40" />
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {Array.from({ length: 5 }).map((_, i) => (
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
          <div className="flex items-center gap-2 text-red-600">
            <AlertCircle className="h-4 w-4" />
            <span className="text-sm">Failed to load spending patterns</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  // Empty state
  if (!patterns || patterns.length === 0) {
    return (
      <Card>
        <CardContent className="p-6">
          <p className="text-gray-500 text-sm">No spending patterns found</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Spending Patterns</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {patterns.map((pattern) => (
            <div key={pattern.category} className="flex items-center justify-between p-3 border rounded-lg">
              <div className="flex-1">
                <p className="font-medium capitalize">{pattern.category}</p>
                <div className="flex items-center gap-2 mt-1">
                  {getTrendIcon(pattern.trend)}
                  <span className="text-xs text-gray-500">
                    {pattern.month_over_month_change >= 0 ? '+' : ''}
                    {pattern.month_over_month_change.toFixed(1)}%
                  </span>
                </div>
              </div>
              <div className="text-right">
                <p className="font-medium" aria-label={`${pattern.category} amount`}>
                  {formatINR(pattern.amount_paise)}
                </p>
                <p className="text-xs text-gray-500" aria-label={`${pattern.category} percentage`}>
                  {pattern.percentage.toFixed(1)}%
                </p>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}