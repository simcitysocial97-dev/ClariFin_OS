/**
 * Status Overview Card - Stage 4 Reconciliation Intelligence Workspace
 *
 * Displays reconciliation status overview with match rate and transaction counts.
 *
 * Architecture Flow: Backend → API → DTO → Mapper → ViewModel → Capability → Workspace → Components → Page
 */

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { AlertCircle, CheckCircle, Clock, AlertTriangle } from 'lucide-react';
import type { StatusOverviewViewModel } from '@/types/reconciliation-view-model';

/**
 * Status Overview Props
 */
interface StatusOverviewProps {
  statusOverview: StatusOverviewViewModel | null;
  loading: boolean;
  error: Error | null;
}

/**
 * Status Overview Card Component
 *
 * Shows total transactions, reconciled count, pending count, discrepancies, and match rate.
 */
export function StatusOverview({ statusOverview, loading, error }: StatusOverviewProps) {
  // Loading state
  if (loading) {
    return (
      <Card>
        <CardHeader>
          <Skeleton className="h-5 w-32" />
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <Skeleton className="h-16 w-full" />
            <div className="grid grid-cols-3 gap-4">
              <Skeleton className="h-12" />
              <Skeleton className="h-12" />
              <Skeleton className="h-12" />
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
            <span className="text-sm">Failed to load status overview</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  // Empty state
  if (!statusOverview) {
    return (
      <Card>
        <CardContent className="p-6">
          <p className="text-gray-500 text-sm">No status data available</p>
        </CardContent>
      </Card>
    );
  }

  const { total_transactions, reconciled, pending, discrepancies, match_rate } = statusOverview;

  // Determine match rate color
  const matchRateColor = match_rate >= 95 ? 'text-green-600' : match_rate >= 80 ? 'text-amber-600' : 'text-red-600';

  return (
    <Card>
      <CardHeader>
        <CardTitle>Reconciliation Status</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {/* Match Rate */}
          <div className="text-center py-4">
            <p className="text-sm text-gray-500 mb-1">Match Rate</p>
            <p className={`text-4xl font-bold ${matchRateColor}`} aria-label="Match rate percentage">
              {match_rate.toFixed(1)}%
            </p>
          </div>

          {/* Status Stats */}
          <div className="grid grid-cols-3 gap-4">
            <div className="text-center">
              <div className="flex items-center justify-center gap-1 mb-1">
                <CheckCircle className="h-4 w-4 text-green-600" />
                <span className="text-xs text-gray-500">Reconciled</span>
              </div>
              <p className="text-lg font-medium" aria-label="Reconciled count">
                {reconciled}
              </p>
            </div>
            <div className="text-center">
              <div className="flex items-center justify-center gap-1 mb-1">
                <Clock className="h-4 w-4 text-amber-600" />
                <span className="text-xs text-gray-500">Pending</span>
              </div>
              <p className="text-lg font-medium" aria-label="Pending count">
                {pending}
              </p>
            </div>
            <div className="text-center">
              <div className="flex items-center justify-center gap-1 mb-1">
                <AlertTriangle className="h-4 w-4 text-red-600" />
                <span className="text-xs text-gray-500">Discrepancies</span>
              </div>
              <p className="text-lg font-medium" aria-label="Discrepancy count">
                {discrepancies}
              </p>
            </div>
          </div>

          {/* Total Transactions */}
          <div className="pt-2 border-t">
            <p className="text-xs text-gray-500">Total Transactions</p>
            <p className="text-sm font-medium" aria-label="Total transactions">
              {total_transactions}
            </p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}