/**
 * Loans Summary Card - Stage 4 Loans Intelligence Workspace
 *
 * Displays aggregated loan summary with total outstanding and EMI.
 *
 * Architecture Flow: Backend → API → DTO → Mapper → ViewModel → Capability → Workspace → Components → Page
 */

import { Card, CardContent } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { AlertCircle } from 'lucide-react';
import { formatINR, formatINRCompact } from '@/lib/utils/format';
import type { LoansViewModel } from '@/types/loans-view-model';

/**
 * Loans Summary Card Props
 */
interface LoansSummaryProps {
  loans: LoansViewModel | null;
  loading: boolean;
  error: Error | null;
}

/**
 * Loans Summary Card Component
 *
 * Shows total outstanding across all loans, total EMI, and loan count.
 */
export function LoansSummary({ loans, loading, error }: LoansSummaryProps) {
  // Loading state
  if (loading) {
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

  // Error state
  if (error) {
    return (
      <Card>
        <CardContent className="p-6">
          <div className="flex items-center gap-2 text-red-600">
            <AlertCircle className="h-4 w-4" />
            <span className="text-sm">Failed to load loans data</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  // Empty state
  if (!loans) {
    return (
      <Card>
        <CardContent className="p-6">
          <p className="text-gray-500 text-sm">No loans data available</p>
        </CardContent>
      </Card>
    );
  }

  const { total_outstanding_paise, total_emi_paise, loan_count } = loans;

  return (
    <Card>
      <CardContent className="p-6">
        <div className="space-y-4">
          {/* Total Outstanding Label */}
          <p className="text-sm text-gray-500">Total Outstanding</p>

          {/* Total Outstanding Amount */}
          <p className="text-3xl font-bold" aria-label="Total loan outstanding">
            {formatINR(total_outstanding_paise)}
          </p>

          {/* Loan Count and EMI */}
          <div className="grid grid-cols-2 gap-4 pt-4">
            <div>
              <p className="text-xs text-gray-500">Active Loans</p>
              <p className="text-lg font-medium">{loan_count}</p>
            </div>
            <div>
              <p className="text-xs text-gray-500">Total EMI</p>
              <p className="text-lg font-medium" aria-label="Total monthly EMI">
                {formatINRCompact(total_emi_paise)}
              </p>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}