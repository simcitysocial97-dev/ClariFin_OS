/**
 * Holdings Table - Stage 4 Investments Intelligence Workspace
 *
 * Displays investment holdings in a table format.
 *
 * Architecture Flow: Backend → API → DTO → Mapper → ViewModel → Capability → Workspace → Components → Page
 */

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { AlertCircle } from 'lucide-react';
import { formatINR } from '@/lib/utils/format';
import type { InvestmentsViewModel, HoldingViewModel } from '@/types/investments-view-model';

/**
 * Holdings Table Props
 */
interface HoldingsTableProps {
  investments: InvestmentsViewModel | null;
  loading: boolean;
  error: Error | null;
}

/**
 * Holding Row Component
 */
function HoldingRow({ holding }: { holding: HoldingViewModel }) {
  return (
    <tr className="border-b">
      <td className="p-2 text-sm">{holding.name}</td>
      <td className="p-2 text-sm capitalize">{holding.type}</td>
      <td className="p-2 text-sm text-right">{holding.quantity}</td>
      <td className="p-2 text-sm text-right">{formatINR(holding.current_value_paise)}</td>
      <td className="p-2 text-sm text-right">
        <span className={holding.returns_percentage >= 0 ? 'text-green-600' : 'text-red-600'}>
          {holding.returns_percentage >= 0 ? '+' : ''}{holding.returns_percentage.toFixed(2)}%
        </span>
      </td>
    </tr>
  );
}

/**
 * Holdings Table Component
 */
export function HoldingsTable({ investments, loading, error }: HoldingsTableProps) {
  // Loading state
  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>
            <Skeleton className="h-5 w-24" />
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
          <CardTitle>Holdings</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-2 text-red-600">
            <AlertCircle className="h-4 w-4" />
            <span className="text-sm">Failed to load holdings data</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  // Empty state
  if (!investments || !investments.holdings || investments.holdings.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Holdings</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-gray-500 text-sm">No holdings data available</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Holdings</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b">
                <th className="p-2 text-left">Name</th>
                <th className="p-2 text-left">Type</th>
                <th className="p-2 text-right">Quantity</th>
                <th className="p-2 text-right">Value</th>
                <th className="p-2 text-right">Returns</th>
              </tr>
            </thead>
            <tbody>
              {investments.holdings.map((holding) => (
                <HoldingRow key={holding.id} holding={holding} />
              ))}
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  );
}