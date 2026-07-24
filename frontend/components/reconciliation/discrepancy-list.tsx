/**
 * Discrepancy List - Stage 4 Reconciliation Intelligence Workspace
 *
 * Displays a list of discrepancies with their details and status.
 *
 * Architecture Flow: Backend → API → DTO → Mapper → ViewModel → Capability → Workspace → Components → Page
 */

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { AlertCircle, AlertTriangle, CheckCircle, XCircle, HelpCircle } from 'lucide-react';
import { formatINR } from '@/lib/utils/format';
import type { DiscrepancyViewModel, ReconciliationStatus } from '@/types/reconciliation-view-model';

/**
 * Discrepancy List Props
 */
interface DiscrepancyListProps {
  discrepancies: DiscrepancyViewModel[];
  loading: boolean;
  error: Error | null;
}

/**
 * Get status icon for discrepancy
 */
function getStatusIcon(status: ReconciliationStatus) {
  switch (status) {
    case 'confirmed':
      return <CheckCircle className="h-4 w-4 text-green-600" />;
    case 'rejected':
      return <XCircle className="h-4 w-4 text-red-600" />;
    case 'disputed':
      return <AlertTriangle className="h-4 w-4 text-amber-600" />;
    case 'pending':
    default:
      return <HelpCircle className="h-4 w-4 text-gray-600" />;
  }
}

/**
 * Get status badge class
 */
function getStatusBadgeClass(status: ReconciliationStatus) {
  switch (status) {
    case 'confirmed':
      return 'bg-green-100 text-green-800';
    case 'rejected':
      return 'bg-red-100 text-red-800';
    case 'disputed':
      return 'bg-amber-100 text-amber-800';
    case 'pending':
    default:
      return 'bg-gray-100 text-gray-800';
  }
}

/**
 * Discrepancy List Component
 *
 * Shows a table of discrepancies with transaction ID, type, expected vs actual amounts, and status.
 */
export function DiscrepancyList({ discrepancies, loading, error }: DiscrepancyListProps) {
  // Loading state
  if (loading) {
    return (
      <Card>
        <CardHeader>
          <Skeleton className="h-5 w-40" />
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {Array.from({ length: 5 }).map((_, i) => (
              <Skeleton key={i} className="h-12 w-full" />
            ))}
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
            <span className="text-sm">Failed to load discrepancies</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  // Empty state
  if (!discrepancies || discrepancies.length === 0) {
    return (
      <Card>
        <CardContent className="p-6">
          <p className="text-gray-500 text-sm">No discrepancies found</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Discrepancies ({discrepancies.length})</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b">
                <th className="text-left py-2 font-medium">Transaction</th>
                <th className="text-left py-2 font-medium">Type</th>
                <th className="text-right py-2 font-medium">Expected</th>
                <th className="text-right py-2 font-medium">Actual</th>
                <th className="text-right py-2 font-medium">Difference</th>
                <th className="text-center py-2 font-medium">Status</th>
              </tr>
            </thead>
            <tbody>
              {discrepancies.map((discrepancy) => (
                <tr key={discrepancy.id} className="border-b hover:bg-gray-50">
                  <td className="py-2">
                    #{discrepancy.transaction_id}
                  </td>
                  <td className="py-2 capitalize">
                    {discrepancy.type}
                  </td>
                  <td className="py-2 text-right" aria-label="Expected amount">
                    {formatINR(discrepancy.expected_paise)}
                  </td>
                  <td className="py-2 text-right" aria-label="Actual amount">
                    {formatINR(discrepancy.actual_paise)}
                  </td>
                  <td className="py-2 text-right" aria-label="Difference amount">
                    <span className={discrepancy.difference_paise >= 0 ? 'text-green-600' : 'text-red-600'}>
                      {formatINR(Math.abs(discrepancy.difference_paise))}
                    </span>
                  </td>
                  <td className="py-2 text-center">
                    <div className="flex items-center justify-center gap-1">
                      {getStatusIcon(discrepancy.status)}
                      <span className={`text-xs px-2 py-1 rounded-full ${getStatusBadgeClass(discrepancy.status)}`}>
                        {discrepancy.status}
                      </span>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  );
}