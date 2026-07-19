/**
 * Credit Cards Loading Skeleton - Stage 4 Credit Cards Intelligence Workspace
 *
 * Loading state components for credit cards workspace.
 *
 * Architecture Flow: Backend → API → DTO → Mapper → ViewModel → Capability → Workspace → Components → Page
 */

import { Skeleton } from '@/components/ui/skeleton';
import { Card, CardContent } from '@/components/ui/card';

/**
 * Credit Cards Summary Loading Skeleton
 */
export function CreditCardsSummarySkeleton() {
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
 * Credit Cards Utilization Chart Loading Skeleton
 */
export function CreditCardsUtilizationSkeleton() {
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
 * Credit Cards Spending by Category Loading Skeleton
 */
export function CreditCardsSpendingSkeleton() {
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
 * Credit Cards Statement History Loading Skeleton
 */
export function CreditCardsStatementHistorySkeleton() {
  return (
    <Card>
      <CardContent className="p-6">
        <Skeleton className="h-4 w-32 mb-4" />
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
 * Credit Cards Full Page Loading Skeleton
 */
export function CreditCardsPageSkeleton() {
  return (
    <div className="min-h-screen bg-gray-50">
      <div className="p-4 space-y-4">
        <CreditCardsSummarySkeleton />
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <CreditCardsUtilizationSkeleton />
          <CreditCardsSpendingSkeleton />
        </div>
        <CreditCardsStatementHistorySkeleton />
      </div>
    </div>
  );
}