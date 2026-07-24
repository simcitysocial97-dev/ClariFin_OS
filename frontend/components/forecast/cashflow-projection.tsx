/**
 * Cashflow Projection - Stage 4 Forecast Intelligence Workspace
 *
 * Displays cashflow projection chart.
 *
 * Architecture Flow: Backend → API → DTO → Mapper → ViewModel → Capability → Workspace → Components → Page
 */

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { AlertCircle } from 'lucide-react';
import { formatINR } from '@/lib/utils/format';
import type { CashflowProjectionViewModel } from '@/types/forecast-view-model';

/**
 * Cashflow Projection Props
 */
interface CashflowProjectionProps {
  projections: CashflowProjectionViewModel[];
  loading: boolean;
  error: Error | null;
}

/**
 * Cashflow Projection Component
 *
 * Shows a bar chart of cashflow projections over time.
 */
export function CashflowProjection({ projections, loading, error }: CashflowProjectionProps) {
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
  const maxValue = Math.max(...projections.map(p => Math.max(p.income_paise, p.expenses_paise)));

  return (
    <Card>
      <CardHeader>
        <CardTitle>Cashflow Projection</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {/* Simple Bar Chart Visualization */}
          <div className="relative h-48">
            <svg viewBox="0 0 400 180" className="w-full h-full">
              {/* Bars */}
              {projections.map((p, i) => {
                const x = (i / (projections.length - 1)) * 350 + 25;
                const barWidth = 30;
                const incomeHeight = (p.income_paise / maxValue) * 120;
                const expenseHeight = (p.expenses_paise / maxValue) * 120;
                
                return (
                  <g key={p.month}>
                    {/* Income bar */}
                    <rect
                      x={x - barWidth / 2}
                      y={150 - incomeHeight}
                      width={barWidth / 2}
                      height={incomeHeight}
                      fill="rgb(34, 197, 94)"
                    />
                    {/* Expense bar */}
                    <rect
                      x={x}
                      y={150 - expenseHeight}
                      width={barWidth / 2}
                      height={expenseHeight}
                      fill="rgb(239, 68, 68)"
                    />
                  </g>
                );
              })}
            </svg>
          </div>

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
                {projections.slice(0, 6).map((projection) => (
                  <tr key={projection.month} className="border-b">
                    <td className="py-2">{projection.month}</td>
                    <td className="py-2 text-right" aria-label="Projected income">
                      <span className="text-green-600">
                        {formatINR(projection.income_paise)}
                      </span>
                    </td>
                    <td className="py-2 text-right" aria-label="Projected expenses">
                      <span className="text-red-600">
                        {formatINR(projection.expenses_paise)}
                      </span>
                    </td>
                    <td className="py-2 text-right" aria-label="Net cashflow">
                      <span className={projection.net_paise >= 0 ? 'text-green-600' : 'text-red-600'}>
                        {formatINR(projection.net_paise)}
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