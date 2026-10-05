/**
 * Cashflow Projection - Stage 4 Forecast Intelligence Workspace
 *
 * Displays cashflow projection chart.
 *
 * Geometry comes from `lib/visualization/chart-geometry`, which is total: it
 * emits finite coordinates for an empty series, a single point, a zero range
 * and non-numeric input alike. The arithmetic here previously produced `NaN`
 * twice over — `i / (length - 1)` with one point, and `value / maxValue` when
 * every value was 0.
 *
 * When the backend reports that no projection could be produced, this renders
 * an explicit unavailable state carrying the backend's own reason. It does not
 * render an empty-looking chart, which would read as "nothing to show" rather
 * than "no projection exists".
 *
 * Architecture Flow: Backend → API → DTO → Mapper → ViewModel → Capability → Workspace → Components → Page
 */

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { AlertCircle, LineChart } from 'lucide-react';
import { formatINR } from '@/lib/utils/format';
import {
  DEFAULT_VIEWPORT,
  describeRejections,
  projectSeries,
} from '@/lib/visualization/chart-geometry';
import type { CashflowProjectionViewModel } from '@/types/forecast-view-model';

/** Plot area inside the SVG viewBox, matching the net worth chart. */
const PLOT = {
  ...DEFAULT_VIEWPORT,
  paddingTop: 30,
  paddingBottom: 30,
};

/** Bar width for one month's income/expense pair. */
const BAR_WIDTH = 30;

/** Height of a bar at the top of the plot area, in SVG user units. */
const MAX_BAR_HEIGHT = 120;

/**
 * Cashflow Projection Props
 */
interface CashflowProjectionProps {
  projections: CashflowProjectionViewModel[];
  loading: boolean;
  error: Error | null;
  /**
   * Provenance of the series, as reported by the authority. When `status` is
   * `'unavailable'` the backend returned no projection on purpose and this
   * component says so rather than showing an empty chart.
   */
  basis?: {
    status: 'available' | 'unavailable';
    reason?: string | null;
    model?: string | null;
    confidenceBps?: number | null;
    historyMonths?: number;
    projectedMonths?: number;
  };
}

/**
 * Cashflow Projection Component
 *
 * Shows a bar chart of cashflow projections over time.
 */
export function CashflowProjection({ projections, loading, error, basis }: CashflowProjectionProps) {
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
            <span className="text-sm">Failed to load cashflow projection</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  const unavailable = basis?.status === 'unavailable';

  // Explicit unavailable state. The absence is reported with the authority's
  // own reason instead of an empty-looking chart.
  if (unavailable || !projections || projections.length === 0) {
    const reason = basis?.reason ?? 'No measured monthly cashflow history is available.';
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <LineChart className="h-5 w-5" />
            Cashflow Projection
          </CardTitle>
        </CardHeader>
        <CardContent className="p-6">
          <div className="flex items-start gap-2" data-testid="cashflow-projection-unavailable">
            <AlertCircle className="mt-0.5 h-4 w-4 shrink-0 text-gray-400" />
            <div>
              <p className="text-sm font-medium text-gray-900">Cashflow forecasting unavailable</p>
              <p className="mt-1 text-sm text-gray-500">{reason}</p>
              {basis && basis.historyMonths !== undefined && (
                <p className="mt-1 text-xs text-gray-400">
                  Measured months of history: {basis.historyMonths}
                </p>
              )}
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  // Bars are scaled against the largest magnitude present, guarded so a
  // zero-valued series cannot divide by zero.
  const projection = projectSeries(
    projections.map((p) => p.income_paise),
    PLOT
  );
  const expenseProjection = projectSeries(
    projections.map((p) => p.expenses_paise),
    PLOT
  );
  const rejectionNote = describeRejections([...projection.rejected, ...expenseProjection.rejected]);

  const plotWidth = PLOT.width - PLOT.paddingLeft - PLOT.paddingRight;
  const slotWidth = projections.length > 0 ? plotWidth / projections.length : plotWidth;
  // Cap the pair inside its slot so neighbouring months do not overlap.
  const barWidth = Math.max(2, Math.min(BAR_WIDTH / 2, slotWidth / 2));

  const barHeight = (sample: { y: number } | undefined) => {
    if (!sample) return 0;
    const top = PLOT.paddingTop;
    return Math.max(0, Math.min(MAX_BAR_HEIGHT, top + MAX_BAR_HEIGHT - sample.y));
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Cashflow Projection</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {/* Bar Chart Visualization */}
          <div className="relative h-48">
            <svg viewBox="0 0 400 180" className="w-full h-full" data-testid="cashflow-projection-chart">
              {projection.samples.map((incomeSample, i) => {
                const expenseSample = expenseProjection.samples[i];
                const centre =
                  PLOT.paddingLeft + slotWidth * (i + 0.5);
                const incomeHeight = barHeight(incomeSample);
                const expenseHeight = barHeight(expenseSample);

                return (
                  <g key={incomeSample.index}>
                    {/* Income bar */}
                    <rect
                      x={centre - barWidth}
                      y={PLOT.paddingTop + MAX_BAR_HEIGHT - incomeHeight}
                      width={barWidth}
                      height={incomeHeight}
                      fill="rgb(34, 197, 94)"
                    />
                    {/* Expense bar */}
                    <rect
                      x={centre}
                      y={PLOT.paddingTop + MAX_BAR_HEIGHT - expenseHeight}
                      width={barWidth}
                      height={expenseHeight}
                      fill="rgb(239, 68, 68)"
                    />
                  </g>
                );
              })}
            </svg>
          </div>

          {rejectionNote && (
            <p className="text-xs text-amber-700" data-testid="cashflow-projection-rejected">
              {rejectionNote} projection value(s) were rejected and are not drawn.
            </p>
          )}

          {basis?.reason && (
            <p className="text-xs text-gray-500" data-testid="cashflow-projection-note">
              {basis.reason}
            </p>
          )}

          {basis?.model && (
            <p className="text-xs text-gray-400" data-testid="cashflow-projection-provenance">
              {basis.model}
              {basis.historyMonths !== undefined && ` · ${basis.historyMonths} measured months`}
              {basis.confidenceBps !== undefined && basis.confidenceBps !== null &&
                ` · confidence ${(basis.confidenceBps / 100).toFixed(2)}%`}
            </p>
          )}

          {/* Projection Data Table */}
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b">
                  <th className="text-left py-2 font-medium">Month</th>
                  <th className="text-right py-2 font-medium">Income</th>
                  <th className="text-right py-2 font-medium">Expenses</th>
                  <th className="text-right py-2 font-medium">Net</th>
                </tr>
              </thead>
              <tbody>
                {projections.slice(0, 6).map((projectionRow) => (
                  <tr key={projectionRow.month} className="border-b">
                    <td className="py-2">{projectionRow.month}</td>
                    <td className="py-2 text-right" aria-label="Projected income">
                      <span className="text-green-600">
                        {formatINR(projectionRow.income_paise)}
                      </span>
                    </td>
                    <td className="py-2 text-right" aria-label="Projected expenses">
                      <span className="text-red-600">
                        {formatINR(projectionRow.expenses_paise)}
                      </span>
                    </td>
                    <td className="py-2 text-right" aria-label="Net cashflow">
                      <span className={projectionRow.net_paise >= 0 ? 'text-green-600' : 'text-red-600'}>
                        {formatINR(projectionRow.net_paise)}
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