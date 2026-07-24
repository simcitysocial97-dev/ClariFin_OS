/**
 * Net Worth Loading Skeleton - Stage 4 Net Worth Intelligence Workspace
 *
 * Handles all loading states for net worth workspace.
 *
 * Architecture Flow: Backend → API → DTO → Mapper → ViewModel → Capability → Workspace → Components → Page
 */

import { Skeleton } from '@/components/ui/skeleton';

/**
 * Summary Card Skeleton
 */
export function SummaryCardSkeleton() {
  return (
    <div className="p-6 space-y-4">
      <Skeleton className="h-4 w-24" />
      <Skeleton className="h-8 w-48" />
      <Skeleton className="h-4 w-32" />
      <div className="grid grid-cols-2 gap-4 pt-4">
        <Skeleton className="h-10 w-full" />
        <Skeleton className="h-10 w-full" />
      </div>
    </div>
  );
}

/**
 * Composition Chart Skeleton
 */
export function CompositionChartSkeleton() {
  return (
    <div className="p-4 space-y-3">
      <Skeleton className="h-4 w-full" />
      <Skeleton className="h-4 w-full" />
      <Skeleton className="h-4 w-full" />
    </div>
  );
}

/**
 * Trend Chart Skeleton
 */
export function TrendChartSkeleton() {
  return (
    <div className="p-4 space-y-3">
      <Skeleton className="h-4 w-full" />
      <Skeleton className="h-4 w-full" />
      <Skeleton className="h-4 w-full" />
    </div>
  );
}

/**
 * Table Skeleton Rows
 */
export function TableSkeleton({ rows = 5 }: { rows?: number }) {
  return (
    <div className="p-4 space-y-2">
      {Array.from({ length: rows }).map((_, i) => (
        <Skeleton key={i} className="h-10 w-full" />
      ))}
    </div>
  );
}

/**
 * Full Page Loading Skeleton
 */
export function NetWorthLoadingSkeleton() {
  return (
    <div className="p-4 space-y-4">
      <SummaryCardSkeleton />
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <CompositionChartSkeleton />
        <TrendChartSkeleton />
      </div>
      <TableSkeleton />
    </div>
  );
}