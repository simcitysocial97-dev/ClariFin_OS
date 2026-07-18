'use client';

import { useEffect, useState } from 'react';
import { formatINR } from '@/lib/utils/format';
import { ChartContainer } from '@/components/ui/chart-container';
import { ExplainButton } from '@/components/ui/explain-button';
import { useCashflow } from '@/lib/hooks/use-cashflow';

// Dynamically import recharts to avoid SSR issues
import dynamic from 'next/dynamic';

// Type-safe dynamic imports for recharts components
const ComposedChart = dynamic(() => import('recharts').then((mod) => mod.ComposedChart), { ssr: false, loading: () => null }) as typeof import('recharts').ComposedChart;
const Bar = dynamic(() => import('recharts').then((mod) => mod.Bar), { ssr: false, loading: () => null }) as typeof import('recharts').Bar;
const Line = dynamic(() => import('recharts').then((mod) => mod.Line), { ssr: false, loading: () => null }) as typeof import('recharts').Line;
const XAxis = dynamic(() => import('recharts').then((mod) => mod.XAxis), { ssr: false, loading: () => null }) as typeof import('recharts').XAxis;
const YAxis = dynamic(() => import('recharts').then((mod) => mod.YAxis), { ssr: false, loading: () => null }) as typeof import('recharts').YAxis;
const CartesianGrid = dynamic(() => import('recharts').then((mod) => mod.CartesianGrid), { ssr: false, loading: () => null }) as typeof import('recharts').CartesianGrid;
const Tooltip = dynamic(() => import('recharts').then((mod) => mod.Tooltip), { ssr: false, loading: () => null }) as typeof import('recharts').Tooltip;
const ResponsiveContainer = dynamic(() => import('recharts').then((mod) => mod.ResponsiveContainer), { ssr: false, loading: () => null }) as typeof import('recharts').ResponsiveContainer;
const Legend = dynamic(() => import('recharts').then((mod) => mod.Legend), { ssr: false, loading: () => null }) as typeof import('recharts').Legend;

interface CashflowChartProps {
  months?: number;
}

export function CashflowChart({ months = 6 }: CashflowChartProps) {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  const { data, isLoading, isError, refetch } = useCashflow(months);

  // Format paise value for chart display
  const formatPaiseForChart = (paise: number) => {
    const rupees = paise / 100;
    if (rupees >= 100000) {
      return `₹${(rupees / 100000).toFixed(0)}L`;
    }
    if (rupees >= 1000) {
      return `₹${(rupees / 1000).toFixed(0)}K`;
    }
    return `₹${rupees}`;
  };

  // Check for empty data safely utilizing Zod structural parameters
  const isEmpty = !data || !data.months || data.months.length === 0;

  if (!mounted) {
    return (
      <ChartContainer isLoading={true} isError={false} isEmpty={false} children={null} />
    );
  }

  return (
    <div className="w-full">
      <div className="mb-3 flex items-center justify-end">
        <ExplainButton
          title="Cashflow Trend"
          explanation="Monthly income vs expenses over time. Shows your net cash flow pattern to help identify spending trends and saving opportunities."
        />
      </div>
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
                margin={{ top: 20, right: 30, left: 80, bottom: 20 }}
              >
                <defs>
                  <linearGradient id="incomeBar" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="hsl(var(--primary))" stopOpacity={0.8} />
                    <stop offset="95%" stopColor="hsl(var(--primary))" stopOpacity={0.6} />
                  </linearGradient>
                  <linearGradient id="expenseBar" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="hsl(var(--destructive))" stopOpacity={0.8} />
                    <stop offset="95%" stopColor="hsl(var(--destructive))" stopOpacity={0.6} />
                  </linearGradient>
                </defs>
                <CartesianGrid
                  strokeDasharray="3 3"
                  stroke="hsl(var(--muted-foreground) / 0.2)"
                  vertical={false}
                />
                <XAxis
                  dataKey="month_label"
                  tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 11 }}
                  axisLine={false}
                  tickLine={false}
                />
                <YAxis
                  tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 11 }}
                  axisLine={false}
                  tickLine={false}
                  tickFormatter={formatPaiseForChart}
                  domain={[0, 'dataMax + 100000']}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: 'hsl(var(--popover))',
                    border: '1px solid hsl(var(--border))',
                    borderRadius: '8px',
                    color: 'hsl(var(--popover-foreground))',
                    fontSize: '12px',
                  }}
                  formatter={(value) => [formatINR(Number(value)), '']}
                />
                <Legend
                  wrapperStyle={{ fontSize: '12px' }}
                  iconSize={10}
                />
                <Bar
                  dataKey="income_paise"
                  name="Income"
                  fill="url(#incomeBar)"
                  radius={[4, 4, 0, 0]}
                  barSize={20}
                />
                <Bar
                  dataKey="expense_paise"
                  name="Expense"
                  fill="url(#expenseBar)"
                  radius={[4, 4, 0, 0]}
                  barSize={20}
                />
                <Line
                  type="monotone"
                  dataKey="net_paise"
                  name="Net"
                  stroke="hsl(var(--green-600))"
                  strokeWidth={2}
                  dot={{ r: 4, fill: 'hsl(var(--green-600))' }}
                  activeDot={{ r: 6, fill: 'hsl(var(--green-600))' }}
                />
              </ComposedChart>
            </ResponsiveContainer>
          </div>
        )}
      </ChartContainer>
    </div>
  );
}