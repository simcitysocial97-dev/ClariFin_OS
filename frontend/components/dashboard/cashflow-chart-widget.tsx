"use client";

/**
 * Cash Flow Chart Widget
 * ======================
 * 
 * Bar chart showing 6 months of Income vs Expenses.
 * Uses shadcn/ui chart component with Recharts.
 */

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useMonthlyCashflowQuery } from "@/lib/hooks/use-query-finance";
import { formatPaise, formatMonth } from "@/lib/format";
import { ChartWidgetSkeleton } from "./skeletons";
import { WidgetErrorFallback } from "./widget-error-fallback";
import { 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  Legend
} from "recharts";

interface CashflowChartWidgetProps {
  mode?: "personal" | "family";
}

interface CashflowData {
  month: string;
  income: number;
  expenses: number;
}

// Format large numbers compactly (e.g., 100000 -> 1L)
function formatCompact(value: number): string {
  if (value >= 10000000) {
    return `₹${(value / 10000000).toFixed(1)}Cr`;
  }
  if (value >= 100000) {
    return `₹${(value / 100000).toFixed(1)}L`;
  }
  if (value >= 1000) {
    return `₹${(value / 1000).toFixed(0)}k`;
  }
  return `₹${value}`;
}

// Custom tooltip for the chart
function CustomTooltip({ active, payload, label }: { 
  active?: boolean; 
  payload?: Array<{ name: string; value: number; color: string }>;
  label?: string;
}) {
  if (active && payload && payload.length) {
    return (
      <div className="bg-popover border rounded-lg p-3 shadow-lg">
        <p className="font-medium text-sm mb-2">{formatMonth(label || "")}</p>
        <div className="space-y-1">
          {payload.map((entry, index) => (
            <div key={index} className="flex items-center gap-2 text-sm">
              <div 
                className="w-3 h-3 rounded-full" 
                style={{ backgroundColor: entry.color }}
              />
              <span className="capitalize">{entry.name}:</span>
              <span className="font-mono font-medium">
                {formatPaise(entry.value)}
              </span>
            </div>
          ))}
        </div>
      </div>
    );
  }
  return null;
}

export function CashflowChartWidget({ mode = "personal" }: CashflowChartWidgetProps) {
  const { data, loading, error, refetch } = useMonthlyCashflowQuery();

  if (loading) {
    return <ChartWidgetSkeleton />;
  }

  if (error) {
    return (
      <WidgetErrorFallback
        title="Cash Flow Chart"
        error={error.message}
        onRetry={refetch}
      />
    );
  }

  // Transform data for the chart
  const chartData: CashflowData[] = data?.months?.map((item) => ({
    month: item.month,
    income: item.total_income_paise,
    expenses: item.total_expense_paise,
  })) || [];

  // Empty state
  if (chartData.length === 0) {
    return (
      <Card className="h-[320px]">
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-semibold">Cash Flow (6 Months)</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col items-center justify-center h-[250px] text-center">
          <p className="text-muted-foreground text-sm">No cash flow data available</p>
          <p className="text-muted-foreground text-xs mt-1">
            Upload statements to see your income vs expenses
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="h-[320px]">
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-semibold">
          Cash Flow (6 Months)
          {mode === "family" && <span className="text-muted-foreground ml-2">· Family</span>}
        </CardTitle>
      </CardHeader>
      <CardContent className="h-[250px]">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            data={chartData}
            margin={{ top: 10, right: 10, left: 0, bottom: 20 }}
            barGap={4}
          >
            <CartesianGrid 
              strokeDasharray="3 3" 
              stroke="hsl(var(--muted-foreground) / 0.2)" 
              vertical={false}
            />
            <XAxis
              dataKey="month"
              tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 11 }}
              tickFormatter={(value) => formatMonth(value).split(" ")[0] || ""}
              axisLine={false}
              tickLine={false}
              dy={10}
            />
            <YAxis
              tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 11 }}
              tickFormatter={formatCompact}
              axisLine={false}
              tickLine={false}
              width={50}
            />
            <Tooltip content={<CustomTooltip />} />
            <Legend 
              wrapperStyle={{ paddingTop: "10px" }}
              iconType="circle"
            />
            <Bar
              dataKey="income"
              name="income"
              fill="hsl(var(--chart-1))"
              radius={[4, 4, 0, 0]}
              maxBarSize={40}
            />
            <Bar
              dataKey="expenses"
              name="expenses"
              fill="hsl(var(--chart-2))"
              radius={[4, 4, 0, 0]}
              maxBarSize={40}
            />
          </BarChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}
