/**
 * Investments Loading Skeleton - Stage 4 Investments Intelligence Workspace
 *
 * Loading state components for investments workspace.
 *
 * Architecture Flow: Backend → API → DTO → Mapper → ViewModel → Capability → Workspace → Components → Page
 */

import { Skeleton } from '@/components/ui/skeleton';
import { Card, CardContent } from '@/components/ui/card';

/**
 * Investments Summary Loading Skeleton
 */
export function InvestmentsSummarySkeleton() {
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
 * Investments Performance Chart Loading Skeleton
 */
export function InvestmentsPerformanceSkeleton() {
  return (
    <Card>
      <CardContent className="p-6">
        <Skeleton className="h-4 w-28 mb-4" />
        <Skeleton className="h-48 w-full" />
      </CardContent>
    </Card>
  );
}

/**
 * Investments Asset Allocation Loading Skeleton
 */
export function InvestmentsAssetAllocationSkeleton() {
  return (
    <Card>
      <CardContent className="p-6">
        <Skeleton className="h-4 w-28 mb-4" />
        <Skeleton className="h-48 w-full" />
      </CardContent>
    </Card>
  );
}

/**
 * Investments Holdings Table Loading Skeleton
 */
export function InvestmentsHoldingsSkeleton() {
  return (
    <Card>
      <CardContent className="p-6">
        <Skeleton className="h-4 w-24 mb-4" />
        <div className="space-y-2">
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="flex items-center justify-between py-2">
              <Skeleton className="h-4 w-32" />
              <Skeleton className="h-4 w-16" />
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

/**
 * Investments Full Page Loading Skeleton
 */
export function InvestmentsPageSkeleton() {
  return (
    <div className="min-h-screen bg-gray-50">
      <div className="p-4 space-y-4">
        <InvestmentsSummarySkeleton />
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <InvestmentsPerformanceSkeleton />
          <InvestmentsAssetAllocationSkeleton />
        </div>
        <InvestmentsHoldingsSkeleton />
      </div>
    </div>
  );
}