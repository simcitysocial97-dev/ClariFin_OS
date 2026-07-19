/**
 * Performance Chart - Stage 4 Investments Intelligence Workspace
 *
 * Visualizes investment performance over time.
 *
 * Architecture Flow: Backend → API → DTO → Mapper → ViewModel → Capability → Workspace → Components → Page
 */

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { AlertCircle } from 'lucide-react';
import type { InvestmentsViewModel } from '@/types/investments-view-model';

/**
 * Performance Chart Props
 */
interface PerformanceChartProps {
  investments: InvestmentsViewModel | null;
  loading: boolean;
  error: Error | null;
}

/**
 * Performance Chart Component
 */
export function PerformanceChart({ investments, loading, error }: PerformanceChartProps) {
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
          <Skeleton className="h-48 w-full" />
        </CardContent>
      </Card>
    );
  }

  // Error state
  if (error) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Performance</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-2 text-red-600">
            <AlertCircle className="h-4 w-4" />
            <span className="text-sm">Failed to load performance data</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  // Empty state
  if (!investments || !investments.performance || investments.performance.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Performance</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-gray-500 text-sm">No performance data available</p>
        </CardContent>
      </Card>
    );
  }

  const { performance } = investments;

  // Calculate min/max for chart scaling
  const values = performance.map(p => p.value_paise);
  const minBalance = Math.min(...values);
  const maxBalance = Math.max(...values);
  const range = maxBalance - minBalance || 1;

  return (
    <Card>
      <CardHeader>
        <CardTitle>Performance</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="h-48 relative">
          {/* Chart area */}
          <svg className="w-full h-full" viewBox={`0 0 ${performance.length - 1} 100`}>
            {performance.length > 1 && (
              <polyline
                points={performance.map((p, i) => {
                  const x = i;
                  const y = 100 - ((p.value_paise - minBalance) / range * 100);
                  return `${x},${y}`;
                }).join(' ')}
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                className="text-blue-500"
              />
            )}
          </svg>
        </div>
      </CardContent>
    </Card>
  );
}