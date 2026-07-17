'use client';

import { formatINR, formatINRCompact } from '@/lib/utils/format';
import { ChartContainer } from '@/components/ui/chart-container';
import { useCashflow } from '@/lib/capabilities/cashflow';
import {
  ComposedChart,
  Bar,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from '@/lib/chart/recharts';
import {
  CHART_MARGINS,
  CARTESIAN_GRID_PROPS,
  TOOLTIP_CONTENT_STYLE,
  LEGEND_WRAPPER_STYLE,
  LEGEND_ICON_SIZE,
  BAR_SIZE,
  BAR_RADIUS,
} from '@/lib/chart/chart-config';
import { CHART_COLORS, CHART_GRADIENTS, getGradientFill } from '@/lib/chart/chart-colors';

interface CashflowChartProps {
  months?: number;
}

export function CashflowChart({ months = 6 }: CashflowChartProps) {
  const { data, isLoading, isError, refetch } = useCashflow(months);

  // Check for empty data
  const isEmpty = !data || !data.months || data.months.length === 0;

  return (
    <ChartContainer
      isLoading={isLoading}
      isError={isError}
      isEmpty={isEmpty}
      onRetry={refetch}
      title="Cashflow Trend"
    >
      {data && data.months && data.months.length > 0 && (
        <div className="h-[300px]">
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart
              data={data.months}
              margin={CHART_MARGINS.default}
            >
              <defs>
                <linearGradient id={CHART_GRADIENTS.income.id} x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor={CHART_GRADIENTS.income.startColor} stopOpacity={CHART_GRADIENTS.income.startOpacity} />
                  <stop offset="95%" stopColor={CHART_GRADIENTS.income.endColor} stopOpacity={CHART_GRADIENTS.income.endOpacity} />
                </linearGradient>
                <linearGradient id={CHART_GRADIENTS.expense.id} x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor={CHART_GRADIENTS.expense.startColor} stopOpacity={CHART_GRADIENTS.expense.startOpacity} />
                  <stop offset="95%" stopColor={CHART_GRADIENTS.expense.endColor} stopOpacity={CHART_GRADIENTS.expense.endOpacity} />
                </linearGradient>
              </defs>
              <CartesianGrid
                strokeDasharray={CARTESIAN_GRID_PROPS.strokeDasharray}
                stroke={CARTESIAN_GRID_PROPS.stroke}
                vertical={CARTESIAN_GRID_PROPS.vertical}
              />
              <XAxis
                dataKey="monthLabel"
                tick={{ fill: CHART_COLORS.mutedForeground, fontSize: 11 }}
                axisLine={false}
                tickLine={false}
              />
              <YAxis
                tick={{ fill: CHART_COLORS.mutedForeground, fontSize: 11 }}
                axisLine={false}
                tickLine={false}
                tickFormatter={formatINRCompact}
                domain={[0, 'dataMax + 100000']}
              />
              <Tooltip
                contentStyle={TOOLTIP_CONTENT_STYLE}
                formatter={(value) => [formatINR(Number(value)), '']}
              />
              <Legend
                wrapperStyle={LEGEND_WRAPPER_STYLE}
                iconSize={LEGEND_ICON_SIZE}
              />
              <Bar
                dataKey="incomePaise"
                name="Income"
                fill={getGradientFill(CHART_GRADIENTS.income.id)}
                radius={BAR_RADIUS}
                barSize={BAR_SIZE}
              />
              <Bar
                dataKey="expensePaise"
                name="Expense"
                fill={getGradientFill(CHART_GRADIENTS.expense.id)}
                radius={BAR_RADIUS}
                barSize={BAR_SIZE}
              />
              <Line
                type="monotone"
                dataKey="netPaise"
                name="Net"
                stroke={CHART_COLORS.success}
                strokeWidth={2}
                dot={{ r: 4, fill: CHART_COLORS.success }}
                activeDot={{ r: 6, fill: CHART_COLORS.success }}
              />
            </ComposedChart>
          </ResponsiveContainer>
        </div>
      )}
    </ChartContainer>
  );
}