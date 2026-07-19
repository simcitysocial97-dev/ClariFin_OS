/**
 * Asset Allocation - Stage 4 Investments Intelligence Workspace
 *
 * Displays investment asset allocation breakdown.
 *
 * Architecture Flow: Backend → API → DTO → Mapper → ViewModel → Capability → Workspace → Components → Page
 */

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { AlertCircle } from 'lucide-react';
import { formatINRCompact } from '@/lib/utils/format';
import type { InvestmentsViewModel, AssetAllocationViewModel } from '@/types/investments-view-model';

/**
 * Asset Allocation Props
 */
interface AssetAllocationProps {
  investments: InvestmentsViewModel | null;
  loading: boolean;
  error: Error | null;
}

/**
 * Asset Allocation Item Component
 */
function AllocationItem({ allocation }: { allocation: AssetAllocationViewModel }) {
  return (
    <div className="border-b pb-3 mb-3 last:border-0 last:pb-0 last:mb-0">
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm font-medium capitalize">{allocation.type}</span>
        <span className="text-sm text-gray-500">{allocation.count} holdings</span>
      </div>
      <div className="w-full bg-gray-200 rounded-full h-4 mb-2">
        <div
          className="bg-blue-500 h-4 rounded-full"
          style={{ width: `${allocation.percentage}%` }}
        />
      </div>
      <div className="flex justify-between text-xs text-gray-500">
        <span>{formatINRCompact(allocation.value_paise)}</span>
        <span>{allocation.percentage}%</span>
      </div>
    </div>
  );
}

/**
 * Asset Allocation Component
 */
export function AssetAllocation({ investments, loading, error }: AssetAllocationProps) {
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
          <CardTitle>Asset Allocation</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-2 text-red-600">
            <AlertCircle className="h-4 w-4" />
            <span className="text-sm">Failed to load allocation data</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  // Empty state
  if (!investments || !investments.allocation || investments.allocation.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Asset Allocation</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-gray-500 text-sm">No allocation data available</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Asset Allocation</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          {investments.allocation.map((allocation) => (
            <AllocationItem key={allocation.type} allocation={allocation} />
          ))}
        </div>
      </CardContent>
    </Card>
  );
}