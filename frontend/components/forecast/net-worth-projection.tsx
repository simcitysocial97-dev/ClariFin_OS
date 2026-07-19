/**
 * Net Worth Projection - Stage 4 Forecast Intelligence Workspace
 *
 * Displays net worth projection chart.
 *
 * Architecture Flow: Backend → API → DTO → Mapper → ViewModel → Capability → Workspace → Components → Page
 */

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { AlertCircle, TrendingUp } from 'lucide-react';
import { formatINR } from '@/lib/utils/format';
import type { NetWorthProjectionViewModel } from '@/types/forecast-view-model';

/**
 * Net Worth Projection Props
 */
interface NetWorthProjectionProps {
  projections: NetWorthProjectionViewModel[];
  loading: boolean;
  error: Error | null;
}

/**
 * Net Worth Projection Component
 *
 * Shows a line chart of net worth projections over time.
 */
export function NetWorthProjection({ projections, loading, error }: NetWorthProjectionProps) {
  // Loading state
  if (loading) {
    return (
      <Card>
        <CardHeader>
          <Skeleton className="h-5 w-40" />
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <Skeleton className="h-48 w-full" />
            <div className="grid grid-cols-3 gap-2">
              {Array.from({ length: 6 }).map((_, i) => (
                <Skeleton key={i} className="h-4" />
              ))}
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
            <span className="text-sm">Failed to load net worth projection</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  // Empty state
  if (!projections || projections.length === 0) {
    return (
      <Card>
        <CardContent className="p-6">
          <p className="text-gray-500 text-sm">No projection data available</p>
        </CardContent>
      </Card>
    );
  }

  // Calculate chart dimensions
  const maxValue = Math.max(...projections.map(p => p.upper_bound_paise));
  const minValue = Math.min(...projections.map(p => p.lower_bound_paise));
  const range = maxValue - minValue;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <TrendingUp className="h-5 w-5" />
          Net Worth Projection
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {/* Simple Line Chart Visualization */}
          <div className="relative h-48">
            <svg viewBox="0 0 400 180" className="w-full h-full">
              {/* Grid lines */}
              {[0, 1, 2, 3, 4, 5].map((i) => (
                <line
                  key={i}
                  x1="0"
                  y1={30 + i * 30}
                  x2="400"
                  y2={30 + i * 30}
                  stroke="currentColor"
                  strokeOpacity="0.1"
                  strokeWidth="1"
                />
              ))}
              
              {/* Confidence interval area - simplified */}
              <path
                d={`M ${projections.map((p, i) => {
                  const x = (i / (projections.length - 1)) * 380 + 10;
                  const y = 30 + (1 - (p.projected_paise - minValue) / range) * 120;
                  return `${x},${y}`;
                }).join(' ')}`}
                fill="rgba(99, 103, 241, 0.1)"
                stroke="none"
              />
              
              {/* Projection line */}
              <polyline
                points={projections.map((p, i) => {
                  const x = (i / (projections.length - 1)) * 380 + 10;
                  const y = 30 + (1 - (p.projected_paise - minValue) / range) * 120;
                  return `${x},${y}`;
                }).join(' ')}
                fill="none"
                stroke="rgb(99, 103, 241)"
                strokeWidth="2"
              />
            </svg>
          </div>

          {/* Projection Data Table */}
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b">
                  <th className="text-left py-2 font-medium">Date</th>
                  <th className="text-right py-2 font-medium">Projected</th>
                  <th className="text-right py-2 font-medium">Range</th>
                </tr>
              </thead>
              <tbody>
                {projections.slice(0, 6).map((projection) => (
                  <tr key={projection.date} className="border-b">
                    <td className="py-2">{new Date(projection.date).toLocaleDateString('en-IN')}</td>
                    <td className="py-2 text-right" aria-label="Projected net worth">
                      {formatINR(projection.projected_paise)}
                    </td>
                    <td className="py-2 text-right" aria-label="Confidence range">
                      <span className="text-xs text-gray-500">
                        {formatINR(projection.lower_bound_paise)} - {formatINR(projection.upper_bound_paise)}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}