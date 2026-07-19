/**
 * Forecast Loading Skeleton - Stage 4 Forecast Intelligence Workspace
 *
 * Loading state components for forecast workspace.
 *
 * Architecture Flow: Backend → API → DTO → Mapper → ViewModel → Capability → Workspace → Components → Page
 */

import { Skeleton } from '@/components/ui/skeleton';
import { Card, CardContent } from '@/components/ui/card';

/**
 * Forecast Summary Loading Skeleton
 */
export function ForecastSummarySkeleton() {
  return (
    <Card>
      <CardContent className="p-6">
        <div className="space-y-4">
          <Skeleton className="h-4 w-24" />
          <Skeleton className="h-8 w-48" />
          <Skeleton className="h-4 w-32" />
          <div className="grid grid-cols-3 gap-4 pt-4">
            <Skeleton className="h-12" />
            <Skeleton className="h-12" />
            <Skeleton className="h-12" />
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

/**
 * Forecast Net Worth Projection Loading Skeleton
 */
export function ForecastNetWorthProjectionSkeleton() {
  return (
    <Card>
      <CardContent className="p-6">
        <Skeleton className="h-4 w-32 mb-4" />
        <Skeleton className="h-48 w-full" />
      </CardContent>
    </Card>
  );
}

/**
 * Forecast Cashflow Projection Loading Skeleton
 */
export function ForecastCashflowProjectionSkeleton() {
  return (
    <Card>
      <CardContent className="p-6">
        <Skeleton className="h-4 w-32 mb-4" />
        <Skeleton className="h-48 w-full" />
      </CardContent>
    </Card>
  );
}

/**
 * Forecast Scenario Comparison Loading Skeleton
 */
export function ForecastScenarioComparisonSkeleton() {
  return (
    <Card>
      <CardContent className="p-6">
        <Skeleton className="h-4 w-32 mb-4" />
        <div className="space-y-2">
          {Array.from({ length: 3 }).map((_, i) => (
            <div key={i} className="flex items-center justify-between py-2">
              <Skeleton className="h-4 w-24" />
              <Skeleton className="h-4 w-16" />
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

/**
 * Forecast Full Page Loading Skeleton
 */
export function ForecastPageSkeleton() {
  return (
    <div className="min-h-screen bg-gray-50">
      <div className="p-4 space-y-4">
        <ForecastSummarySkeleton />
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <ForecastNetWorthProjectionSkeleton />
          <ForecastCashflowProjectionSkeleton />
        </div>
        <ForecastScenarioComparisonSkeleton />
      </div>
    </div>
  );
}