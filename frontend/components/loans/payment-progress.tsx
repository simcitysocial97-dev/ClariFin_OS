/**
 * Payment Progress - Stage 4 Loans Intelligence Workspace
 *
 * Displays payment progress for each loan.
 *
 * Architecture Flow: Backend → API → DTO → Mapper → ViewModel → Capability → Workspace → Components → Page
 */

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { AlertCircle } from 'lucide-react';
import type { LoansViewModel, PaymentProgressViewModel } from '@/types/loans-view-model';

/**
 * Payment Progress Props
 */
interface PaymentProgressProps {
  loans: LoansViewModel | null;
  loading: boolean;
  error: Error | null;
}

/**
 * Payment Progress Item Component
 */
function PaymentProgressItem({ progress }: { progress: PaymentProgressViewModel }) {
  return (
    <div className="border-b pb-3 mb-3 last:border-0 last:pb-0 last:mb-0">
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm font-medium">Loan {progress.loan_id}</span>
        <span className="text-sm text-gray-500">{progress.total_payments} payments</span>
      </div>
      <div className="w-full bg-gray-200 rounded-full h-2 mb-2">
        <div
          className="bg-blue-500 h-2 rounded-full"
          style={{ width: `${progress.principal_percentage}%` }}
        />
      </div>
      <div className="flex justify-between text-xs text-gray-500">
        <span>Principal: {progress.principal_percentage}%</span>
        <span>Interest: {progress.interest_percentage}%</span>
      </div>
    </div>
  );
}

/**
 * Payment Progress Component
 */
export function PaymentProgress({ loans, loading, error }: PaymentProgressProps) {
  // Loading state
  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>
            <Skeleton className="h-5 w-32" />
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-full" />
          </div>
        </CardContent>
      </Card>
    );
  }

  // Error state
  if (error) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Payment Progress</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-2 text-red-600">
            <AlertCircle className="h-4 w-4" />
            <span className="text-sm">Failed to load payment progress</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  // Empty state
  if (!loans || !loans.payment_progress || loans.payment_progress.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Payment Progress</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-gray-500 text-sm">No payment progress data available</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Payment Progress</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          {loans.payment_progress.map((progress) => (
            <PaymentProgressItem key={progress.loan_id} progress={progress} />
          ))}
        </div>
      </CardContent>
    </Card>
  );
}