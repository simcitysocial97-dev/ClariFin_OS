/**
 * Behaviour Loading Skeleton - Stage 4 Behaviour Intelligence Workspace
 *
 * Loading state components for behaviour workspace.
 *
 * Architecture Flow: Backend → API → DTO → Mapper → ViewModel → Capability → Workspace → Components → Page
 */

import { Skeleton } from '@/components/ui/skeleton';
import { Card, CardContent } from '@/components/ui/card';

/**
 * Behaviour Score Loading Skeleton
 */
export function BehaviourScoreSkeleton() {
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
 * Behaviour Spending Patterns Loading Skeleton
 */
export function BehaviourSpendingPatternsSkeleton() {
  return (
    <Card>
      <CardContent className="p-6">
        <Skeleton className="h-4 w-32 mb-4" />
        <div className="space-y-2">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="flex items-center justify-between">
              <Skeleton className="h-4 w-20" />
              <Skeleton className="h-4 w-16" />
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

/**
 * Behaviour Wellness Radar Loading Skeleton
 */
export function BehaviourWellnessRadarSkeleton() {
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
 * Behaviour Savings Rate Loading Skeleton
 */
export function BehaviourSavingsRateSkeleton() {
  return (
    <Card>
      <CardContent className="p-6">
        <Skeleton className="h-4 w-24 mb-4" />
        <div className="space-y-2">
          {Array.from({ length: 3 }).map((_, i) => (
            <div key={i} className="flex items-center justify-between">
              <Skeleton className="h-4 w-20" />
              <Skeleton className="h-4 w-16" />
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

/**
 * Behaviour Full Page Loading Skeleton
 */
export function BehaviourPageSkeleton() {
  return (
    <div className="min-h-screen bg-gray-50">
      <div className="p-4 space-y-4">
        <BehaviourScoreSkeleton />
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <BehaviourSpendingPatternsSkeleton />
          <BehaviourWellnessRadarSkeleton />
        </div>
        <BehaviourSavingsRateSkeleton />
      </div>
    </div>
  );
}