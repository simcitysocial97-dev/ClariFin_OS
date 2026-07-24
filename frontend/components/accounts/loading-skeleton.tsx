/**
 * Accounts Loading Skeleton - Stage 4 Accounts Intelligence Workspace
 *
 * Loading state components for accounts workspace.
 *
 * Architecture Flow: Backend → API → DTO → Mapper → ViewModel → Capability → Workspace → Components → Page
 */

import { Skeleton } from '@/components/ui/skeleton';
import { Card, CardContent } from '@/components/ui/card';

/**
 * Accounts Summary Loading Skeleton
 */
export function AccountsSummarySkeleton() {
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
 * Accounts Balance Trend Loading Skeleton
 */
export function AccountsBalanceTrendSkeleton() {
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
 * Accounts Type Breakdown Loading Skeleton
 */
export function AccountsTypeBreakdownSkeleton() {
  return (
    <Card>
      <CardContent className="p-6">
        <Skeleton className="h-4 w-24 mb-4" />
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
 * Accounts Transaction List Loading Skeleton
 */
export function AccountsTransactionListSkeleton() {
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
 * Accounts Full Page Loading Skeleton
 */
export function AccountsPageSkeleton() {
  return (
    <div className="min-h-screen bg-gray-50">
      <div className="p-4 space-y-4">
        <AccountsSummarySkeleton />
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <AccountsBalanceTrendSkeleton />
          <AccountsTypeBreakdownSkeleton />
        </div>
        <AccountsTransactionListSkeleton />
      </div>
    </div>
  );
}