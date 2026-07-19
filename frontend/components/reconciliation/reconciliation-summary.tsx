/**
 * Reconciliation Summary Card - Stage 4 Reconciliation Intelligence Workspace
 *
 * Displays aggregated reconciliation summary with total statements and discrepancies.
 *
 * Architecture Flow: Backend → API → DTO → Mapper → ViewModel → Capability → Workspace → Components → Page
 */

import { Card, CardContent } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { AlertCircle, AlertTriangle } from 'lucide-react';
import { formatINR } from '@/lib/utils/format';
import type { ReconciliationSummaryViewModel } from '@/types/reconciliation-view-model';

/**
 * Reconciliation Summary Props
 */
interface ReconciliationSummaryProps {
  statements: ReconciliationSummaryViewModel[];
  loading: boolean;
  error: Error | null;
}

/**
 * Reconciliation Summary Card Component
 *
 * Shows total statements, total discrepancies, and overall match rate.
 */
export function ReconciliationSummary({ statements, loading, error }: ReconciliationSummaryProps) {
  // Loading state
  if (loading) {
    return (
      <Card>
        <CardContent className="p-6">
          <div className="space-y-4">
            <Skeleton className="h-4 w-24" />
            <Skeleton className="h-8 w-48" />
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

  // Error state
  if (error) {
    return (
      <Card>
        <CardContent className="p-6">
          <div className="flex items-center gap-2 text-red-600">
            <AlertCircle className="h-4 w-4" />
            <span className="text-sm">Failed to load reconciliation data</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  // Empty state
  if (!statements || statements.length === 0) {
    return (
      <Card>
        <CardContent className="p-6">
          <p className="text-gray-500 text-sm">No reconciliation data available</p>
        </CardContent>
      </Card>
    );
  }

  // Calculate totals
  const totalDebit = statements.reduce((sum, s) => sum + s.total_debit_paise, 0);
  const totalCredit = statements.reduce((sum, s) => sum + s.total_credit_paise, 0);
  const pendingCount = statements.filter(s => s.status === 'pending').length;
  const discrepancyCount = statements.filter(s => s.status === 'disputed').length;

  return (
    <Card>
      <CardContent className="p-6">
        <div className="space-y-4">
          {/* Total Statements Label */}
          <p className="text-sm text-gray-500">Total Statements</p>

          {/* Statement Count */}
          <p className="text-3xl font-bold" aria-label="Total statements">
            {statements.length}
          </p>

          {/* Summary Stats */}
          <div className="grid grid-cols-3 gap-4 pt-4">
            <div>
              <p className="text-xs text-gray-500">Total Debit</p>
              <p className="text-lg font-medium" aria-label="Total debit amount">
                {formatINR(totalDebit)}
              </p>
            </div>
            <div>
              <p className="text-xs text-gray-500">Total Credit</p>
              <p className="text-lg font-medium" aria-label="Total credit amount">
                {formatINR(totalCredit)}
              </p>
            </div>
            <div>
              <p className="text-xs text-gray-500">Pending</p>
              <p className="text-lg font-medium" aria-label="Pending reconciliations">
                {pendingCount}
              </p>
            </div>
          </div>

          {/* Discrepancy Alert */}
          {discrepancyCount > 0 && (
            <div className="flex items-center gap-2 pt-2 text-amber-600">
              <AlertTriangle className="h-4 w-4" />
              <span className="text-sm font-medium">
                {discrepancyCount} statement{discrepancyCount !== 1 ? 's' : ''} with discrepancies
              </span>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}