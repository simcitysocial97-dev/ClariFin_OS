/**
 * Interest Analysis - Stage 4 Loans Intelligence Workspace
 *
 * Displays interest analysis for each loan.
 *
 * Architecture Flow: Backend → API → DTO → Mapper → ViewModel → Capability → Workspace → Components → Page
 */

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { AlertCircle } from 'lucide-react';
import { formatINR } from '@/lib/utils/format';
import type { LoansViewModel, InterestAnalysisViewModel } from '@/types/loans-view-model';

/**
 * Interest Analysis Props
 */
interface InterestAnalysisProps {
  loans: LoansViewModel | null;
  loading: boolean;
  error: Error | null;
}

/**
 * Interest Analysis Item Component
 */
function InterestAnalysisItem({ analysis }: { analysis: InterestAnalysisViewModel }) {
  return (
    <div className="border-b pb-3 mb-3 last:border-0 last:pb-0 last:mb-0">
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm font-medium">Loan {analysis.loan_id}</span>
        <span className="text-sm text-gray-500">Ratio: {analysis.interest_ratio.toFixed(2)}</span>
      </div>
      <div className="grid grid-cols-3 gap-2 text-xs">
        <div>
          <span className="text-gray-500">Total:</span>
          <p className="font-medium">{formatINR(analysis.total_interest_paise)}</p>
        </div>
        <div>
          <span className="text-gray-500">Paid:</span>
          <p className="font-medium">{formatINR(analysis.paid_interest_paise)}</p>
        </div>
        <div>
          <span className="text-gray-500">Remaining:</span>
          <p className="font-medium">{formatINR(analysis.remaining_interest_paise)}</p>
        </div>
      </div>
    </div>
  );
}

/**
 * Interest Analysis Component
 */
export function InterestAnalysis({ loans, loading, error }: InterestAnalysisProps) {
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
          <CardTitle>Interest Analysis</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-2 text-red-600">
            <AlertCircle className="h-4 w-4" />
            <span className="text-sm">Failed to load interest analysis</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  // Empty state
  if (!loans || !loans.interest_analysis || loans.interest_analysis.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Interest Analysis</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-gray-500 text-sm">No interest analysis data available</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Interest Analysis</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          {loans.interest_analysis.map((analysis) => (
            <InterestAnalysisItem key={analysis.loan_id} analysis={analysis} />
          ))}
        </div>
      </CardContent>
    </Card>
  );
}