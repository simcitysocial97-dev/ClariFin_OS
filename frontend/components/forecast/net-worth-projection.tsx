/**
 * Net Worth Projection - Stage 4 Forecast Intelligence Workspace
 *
 * Displays net worth projection chart.
 *
 * Geometry comes from `lib/visualization/chart-geometry`, which is total: it
 * emits finite coordinates for an empty series, a single point, a zero range
 * and non-numeric input alike. The arithmetic here previously produced
 * `NaN` (`i / (length - 1)` with one point, `(v - min) / range` with a flat
 * series) and the browser rejected the resulting `<path>`/`<polyline>`.
 *
 * Architecture Flow: Backend → API → DTO → Mapper → ViewModel → Capability → Workspace → Components → Page
 */

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { AlertCircle, TrendingUp } from 'lucide-react';
import { formatINR } from '@/lib/utils/format';
import {
  describeRejections,
  projectSeries,
  toPathData,
  toPolylinePoints,
} from '@/lib/visualization/chart-geometry';
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

  // Invalid backend data is rejected and disclosed, not drawn. A value the
  // authority could not produce is never coerced into geometry.
  const projection = projectSeries(projections.map((p) => p.projected_paise));
  const rejectionNote = describeRejections(projection.rejected);
  const linePoints = toPolylinePoints(projection.samples);
  const bandPath = toPathData(projection.samples);
  const drawable = projection.samples.length >= 2;

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
            <svg viewBox="0 0 400 180" className="w-full h-full" data-testid="net-worth-projection-chart">
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

              {/* A line needs two points. One point is drawn as a marker, not
                  as a zero-length segment, so no invalid geometry is emitted. */}
              {drawable ? (
                <>
                  <path d={bandPath} fill="rgba(99, 103, 241, 0.1)" stroke="none" />
                  <polyline
                    points={linePoints}
                    fill="none"
                    stroke="rgb(99, 103, 241)"
                    strokeWidth="2"
                  />
                </>
              ) : (
                projection.samples.map((sample, i) => (
                  <circle
                    key={i}
                    cx={sample.x}
                    cy={sample.y}
                    r="3"
                    fill="rgb(99, 103, 241)"
                    data-testid="net-worth-projection-single-point"
                  />
                ))
              )}
            </svg>
          </div>

          {projection.isDegenerateRange && drawable && (
            <p className="text-xs text-gray-500" data-testid="net-worth-projection-flat">
              Every projected month is identical, so the series is drawn on one level.
            </p>
          )}

          {rejectionNote && (
            <p className="text-xs text-amber-700" data-testid="net-worth-projection-rejected">
              {rejectionNote} projection value(s) were rejected and are not drawn.
            </p>
          )}

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
                {projections.slice(0, 6).map((projectionRow) => (
                  <tr key={projectionRow.date} className="border-b">
                    <td className="py-2">{new Date(projectionRow.date).toLocaleDateString('en-IN')}</td>
                    <td className="py-2 text-right" aria-label="Projected net worth">
                      {formatINR(projectionRow.projected_paise)}
                    </td>
                    <td className="py-2 text-right" aria-label="Confidence range">
                      <span className="text-xs text-gray-500">
                        {formatINR(projectionRow.lower_bound_paise)} - {formatINR(projectionRow.upper_bound_paise)}
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