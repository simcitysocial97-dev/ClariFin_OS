"use client";

/**
 * Cash Flow Chart
 * ===============
 *
 * Visual representation of Money In vs Money Out.
 * Uses a stacked bar chart showing Income vs Expenses over time.
 */

import { useState } from "react";
import {
  useMonthlyCashflow,
  useCashflowBreakdown,
} from "@/lib/hooks/use-finance-data";
import { formatPaise, formatPaiseCompact, formatMonth } from "@/lib/format";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { WidgetErrorFallback } from "@/components/dashboard/widget-error-fallback";
import { cn } from "@/lib/utils";
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
} from "recharts";
import { ArrowRightLeft } from "lucide-react";

interface CashflowChartProps {
  months?: number;
  className?: string;
}

interface ChartDataPoint {
  month: string;
  income: number;
  expense: number;
  net: number;
}

// Custom tooltip
interface TooltipProps {
  active?: boolean;
  payload?: Array<{
    value: number;
    name: string;
    color: string;
  }>;
  label?: string;
}

// Breakdown item from API
interface BreakdownItem {
  paise: number;
  count?: number;
}

// Record of breakdown items
interface BreakdownMap {
  [key: string]: BreakdownItem;
}

function CustomTooltip({ active, payload, label }: TooltipProps) {
  if (active && payload && payload.length) {
    const income = payload.find((p) => p.name === "Income")?.value || 0;
    const expense = payload.find((p) => p.name === "Expense")?.value || 0;
    const net = income - expense;

    return (
      <div className="bg-popover border rounded-lg p-3 shadow-lg">
        <p className="font-medium text-sm mb-2">{formatMonth(label || "")}</p>
        <div className="space-y-1 text-sm">
          <p className="text-green-600">
            Income: {formatPaise(income)}
          </p>
          <p className="text-red-600">
            Expense: {formatPaise(expense)}
          </p>
          <div className="border-t pt-1 mt-1">
            <p className={cn(net >= 0 ? "text-green-600" : "text-red-600")}>
              Net: {net >= 0 ? "+" : ""}
              {formatPaise(net)}
            </p>
          </div>
        </div>
      </div>
    );
  }
  return null;
}

export function CashflowChart({
  months = 12,
  className,
}: CashflowChartProps) {
  const { data, loading, error, refetch } = useMonthlyCashflow();
  const [selectedMonth, setSelectedMonth] = useState<string>("");

  // Get breakdown for selected month
  const { data: breakdown } = useCashflowBreakdown();

  if (loading) {
    return (
      <Card className={cn("h-[450px]", className)}>
        <CardHeader className="pb-2">
          <div className="h-5 w-48 bg-muted rounded animate-pulse" />
        </CardHeader>
        <CardContent className="h-[370px] flex items-center justify-center">
          <div className="w-full h-[300px] bg-muted/30 rounded animate-pulse" />
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className={cn("h-[450px]", className)}>
        <CardContent className="h-full flex items-center justify-center">
          <WidgetErrorFallback
            title="Cash Flow Chart"
            error={error.message}
            onRetry={refetch}
          />
        </CardContent>
      </Card>
    );
  }

  const monthly = data?.months || [];
  const monthsList = monthly.map((m: { month: string }) => m.month);

  // Transform data for chart
  const chartData: ChartDataPoint[] = monthly.map(
    (m: { month: string; income_paise: number; expense_paise: number }) => ({
      month: m.month?.slice(0, 7),
      income: m.income_paise || 0,
      expense: m.expense_paise || 0,
      net: (m.income_paise || 0) - (m.expense_paise || 0),
    })
  );

  const currentMonth = monthly[monthly.length - 1];
  const incomeBySource = breakdown?.by_source || currentMonth?.by_source || {};
  const expenseByCategory =
    breakdown?.by_category || currentMonth?.by_category || {};

  return (
    <Card className={cn("h-[450px]", className)}>
      <CardHeader className="pb-2 flex flex-row items-center justify-between">
        <CardTitle className="text-sm font-semibold flex items-center gap-2">
          <ArrowRightLeft className="h-4 w-4" />
          Cash Flow Visualization ({months} Months)
        </CardTitle>
        <Select value={selectedMonth} onValueChange={setSelectedMonth}>
          <SelectTrigger className="w-40 h-8 text-xs">
            <SelectValue
              placeholder={currentMonth?.month?.slice(0, 7) || "Select month"}
            />
          </SelectTrigger>
          <SelectContent>
            {monthsList.map((m: string) => (
              <SelectItem key={m} value={m} className="text-xs">
                {m.slice(0, 7)}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </CardHeader>
      <CardContent>
        <div className="h-[280px]">
          {chartData.length > 0 ? (
            <ResponsiveContainer width="100%" height="100%">
              <ComposedChart
                data={chartData}
                margin={{ top: 10, right: 10, left: 0, bottom: 20 }}
              >
                <CartesianGrid
                  strokeDasharray="3 3"
                  stroke="hsl(var(--muted-foreground) / 0.2)"
                  vertical={false}
                />
                <XAxis
                  dataKey="month"
                  tick={{
                    fill: "hsl(var(--muted-foreground))",
                    fontSize: 11,
                  }}
                  axisLine={false}
                  tickLine={false}
                  dy={10}
                  interval={Math.floor(chartData.length / 6)}
                  type={"category" as const}
                />
                <YAxis
                  tick={{
                    fill: "hsl(var(--muted-foreground))",
                    fontSize: 11,
                  }}
                  tickFormatter={(value: number) => formatPaiseCompact(value)}
                  axisLine={false}
                  tickLine={false}
                  width={60}
                  type={"number" as const}
                />
                <Tooltip content={<CustomTooltip />} />
                <Legend
                  verticalAlign="top"
                  height={20}
                  iconType="circle"
                  wrapperStyle={{ paddingBottom: "10px" }}
                />
                <Bar
                  dataKey="income"
                  name="Income"
                  fill="#10B981"
                  radius={[4, 4, 0, 0]}
                  maxBarSize={50}
                />
                <Bar
                  dataKey="expense"
                  name="Expense"
                  fill="#EF4444"
                  radius={[4, 4, 0, 0]}
                  maxBarSize={50}
                />
                <Line
                  type="monotone"
                  dataKey="net"
                  name="Net Savings"
                  stroke="#3B82F6"
                  strokeWidth={2}
                  dot={false}
                />
              </ComposedChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-full flex items-center justify-center text-muted-foreground">
              <p>No cashflow data available</p>
            </div>
          )}
        </div>

        {/* Selected Month Breakdown */}
        {selectedMonth && (
          <div className="mt-4 pt-4 border-t grid grid-cols-2 gap-4 text-xs">
            <div>
              <p className="font-medium text-green-600 mb-1">Income Sources</p>
              <div className="space-y-1">
                {Object.entries(incomeBySource as BreakdownMap).length > 0 ? (
                  Object.entries(incomeBySource as BreakdownMap).map(
                    ([source, value]: [string, BreakdownItem]) => (
                      <div key={source} className="flex justify-between">
                        <span className="capitalize text-muted-foreground">
                          {source.replace(/_/g, " ")}
                        </span>
                        <span>{formatPaise(value.paise || 0)}</span>
                      </div>
                    )
                  )
                ) : (
                  <p className="text-muted-foreground">No data</p>
                )}
              </div>
            </div>
            <div>
              <p className="font-medium text-red-600 mb-1">Top Expenses</p>
              <div className="space-y-1">
                {Object.entries(expenseByCategory as BreakdownMap)
                  .sort(([, a]: [string, BreakdownItem], [, b]: [string, BreakdownItem]) => (b.paise || 0) - (a.paise || 0))
                  .slice(0, 4)
                  .map(([cat, value]: [string, BreakdownItem]) => (
                    <div key={cat} className="flex justify-between">
                      <span className="capitalize text-muted-foreground">
                        {cat.replace(/_/g, " ")}
                      </span>
                      <span>{formatPaise(value.paise || 0)}</span>
                    </div>
                  ))}
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
