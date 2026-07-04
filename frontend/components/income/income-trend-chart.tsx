"use client";

import { useMemo } from "react";
import { useMonthlyCashflow } from "@/lib/hooks/use-finance-data";
import { formatPaise, formatMonth } from "@/lib/format";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { WidgetErrorFallback } from "@/components/dashboard/widget-error-fallback";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";
import { TrendingUp } from "lucide-react";
import { cn } from "@/lib/utils";
interface ChartData {
  month: string;
  income: number;
}

interface MonthlyCashflowItem {
  month: string;
  income_paise: number;
}

export function IncomeTrendChart({ className }: { className?: string }) {
  const { data, loading, error, refetch } = useMonthlyCashflow();

  const chartData: ChartData[] = useMemo(() => {
    if (!data?.months) return [];
    return data.months
      .map((m: MonthlyCashflowItem) => ({
        month: m.month?.slice(0, 7),
        income: m.income_paise || 0,
      }))
      .sort((a: ChartData, b: ChartData) => new Date(a.month).getTime() - new Date(b.month).getTime());
  }, [data]);

  if (loading) {
    return (
      <Card className={cn("h-[350px]", className)}>
        <CardHeader className="pb-2">
          <div className="h-5 w-48 bg-muted rounded animate-pulse" />
        </CardHeader>
        <CardContent className="h-[280px] flex items-center justify-center">
          <div className="w-full h-[200px] bg-muted/30 rounded animate-pulse" />
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className={cn("h-[350px]", className)}>
        <CardContent className="h-full flex items-center justify-center">
          <WidgetErrorFallback title="Income Trend" error={error.message} onRetry={refetch} />
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className={cn("h-[350px]", className)}>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-semibold flex items-center gap-2">
          <TrendingUp className="h-4 w-4" />
          Income Trend (12 Months)
        </CardTitle>
      </CardHeader>
      <CardContent className="h-[280px]">
        {chartData.length > 0 ? (
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartData} margin={{ top: 10, right: 10, left: 0, bottom: 20 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--muted-foreground) / 0.2)" vertical={false} />
              <XAxis
                dataKey="month"
                tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 11 }}
                tickFormatter={(value) => formatMonth(value).split(" ")[0] || ""}
                axisLine={false}
                tickLine={false}
                dy={10}
                type={"category" as const}
              />
              <YAxis
                tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 11 }}
                tickFormatter={(value) => `₹${(value / 100000).toFixed(1)}L`}
                axisLine={false}
                tickLine={false}
                width={50}
                type={"number" as const}
              />
              <Tooltip
                formatter={(value: number) => formatPaise(value)}
                labelFormatter={(label) => formatMonth(label)}
              />
              <Bar dataKey="income" name="Income" fill="#10B981" radius={[4, 4, 0, 0]} maxBarSize={50} />
            </BarChart>
          </ResponsiveContainer>
        ) : (
          <div className="h-full flex items-center justify-center text-muted-foreground">
            <p>No income data available</p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
