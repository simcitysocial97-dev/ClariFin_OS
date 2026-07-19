/**
 * Amortization Schedule - Stage 4 Loans Intelligence Workspace
 *
 * Displays loan amortization schedule with payment breakdown.
 *
 * Architecture Flow: Backend → API → DTO → Mapper → ViewModel → Capability → Workspace → Components → Page
 */

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { AlertCircle } from 'lucide-react';
import { formatINR } from '@/lib/utils/format';
import type { LoansViewModel, AmortizationEntryViewModel } from '@/types/loans-view-model';

/**
 * Amortization Schedule Props
 */
interface AmortizationScheduleProps {
  loans: LoansViewModel | null;
  loading: boolean;
  error: Error | null;
}

/**
 * Amortization Entry Row Component
 */
function AmortizationRow({ entry }: { entry: AmortizationEntryViewModel }) {
  return (
    <tr className="border-b">
      <td className="p-2 text-sm">{entry.payment_number}</td>
      <td className="p-2 text-sm">{entry.date}</td>
      <td className="p-2 text-sm text-right">{formatINR(entry.principal_paise)}</td>
      <td className="p-2 text-sm text-right">{formatINR(entry.interest_paise)}</td>
      <td className="p-2 text-sm text-right font-medium">{formatINR(entry.emi_paise)}</td>
      <td className="p-2 text-sm text-right">{formatINR(entry.balance_paise)}</td>
    </tr>
  );
}

/**
 * Amortization Schedule Component
 */
export function AmortizationSchedule({ loans, loading, error }: AmortizationScheduleProps) {
  // Loading state
  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>
            <Skeleton className="h-5 w-40" />
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            <Skeleton className="h-4 w-full" />
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
          <CardTitle>Amortization Schedule</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-2 text-red-600">
            <AlertCircle className="h-4 w-4" />
            <span className="text-sm">Failed to load amortization data</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  // Empty state
  if (!loans || !loans.amortization || loans.amortization.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Amortization Schedule</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-gray-500 text-sm">No amortization data available</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Amortization Schedule</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b">
                <th className="p-2 text-left">#</th>
                <th className="p-2 text-left">Date</th>
                <th className="p-2 text-right">Principal</th>
                <th className="p-2 text-right">Interest</th>
                <th className="p-2 text-right">EMI</th>
                <th className="p-2 text-right">Balance</th>
              </tr>
            </thead>
            <tbody>
              {loans.amortization.map((entry) => (
                <AmortizationRow key={entry.payment_number} entry={entry} />
              ))}
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  );
}