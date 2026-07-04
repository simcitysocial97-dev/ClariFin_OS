"use client";

/**
 * Net Worth History Chart
 * =======================
 *
 * Interactive Area Chart showing Net Worth growth over time.
 * Displays Assets, Liabilities, and Net Worth lines.
 */

import { useNetWorthTrend } from "@/lib/hooks/use-finance-data";
import { formatPaise, formatPaiseCompact, formatMonth } from "@/lib/format";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { WidgetErrorFallback } from "@/components/dashboard/widget-error-fallback";
import { Button } from "@/components/ui/button";
import { Camera } from "lucide-react";
import { cn } from "@/lib/utils";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";

interface NetWorthHistoryChartProps {
  months?: number;
  className?: string;
}

interface ChartDataPoint {
  month: string;
  assets: number;
  liabilities: number;
  netWorth: number;
}

// Custom tooltip component
interface TooltipProps {
  active?: boolean;
  payload?: Array<{
    value: number;
    name: string;
    color: string;
  }>;
  label?: string;
}

function CustomTooltip({ active, payload, label }: TooltipProps) {
  if (active && payload && payload.length) {
    return (
      <div className="bg-popover border rounded-lg p-3 shadow-lg">
        <p className="font-medium text-sm mb-2">{formatMonth(label || "")}</p>
        <div className="space-y-1">
          {payload.map((entry, index) => (
            <p
              key={index}
              className="text-sm flex items-center gap-2"
              style={{ color: entry.color }}
            >
              <span
                className="w-2 h-2 rounded-full"
                style={{ backgroundColor: entry.color }}
              />
              {entry.name}: {formatPaise(entry.value)}
            </p>
          ))}
        </div>
      </div>
    );
  }
  return null;
}

export function NetWorthHistoryChart({
  months = 24,
  className,
}: NetWorthHistoryChartProps) {
  const { trend, loading, error, refetch } = useNetWorthTrend();

  if (loading) {
    return (
      <Card className={cn("h-[400px]", className)}>
        <CardHeader className="pb-2">
          <div className="h-5 w-40 bg-muted rounded animate-pulse" />
        </CardHeader>
        <CardContent className="h-[320px] flex items-center justify-center">
          <div className="w-full h-[250px] bg-muted/30 rounded animate-pulse" />
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className={cn("h-[400px]", className)}>
        <CardContent className="h-full flex items-center justify-center">
          <WidgetErrorFallback
            title="Net Worth History"
            error={error.message}
            onRetry={refetch}
          />
        </CardContent>
      </Card>
    );
  }

  // Transform data for the chart
  const chartData: ChartDataPoint[] = (trend || [])
    .map((item: { month: string; total_assets_paise: number; total_liabilities_paise: number }) => ({
      month: item.month,
      assets: item.total_assets_paise || 0,
      liabilities: item.total_liabilities_paise || 0,
      netWorth: (item.total_assets_paise || 0) - (item.total_liabilities_paise || 0),
    }))
    .sort(
      (a, b) => new Date(a.month).getTime() - new Date(b.month).getTime()
    );

  // Empty state - no snapshots yet
  if (chartData.length === 0) {
    return (
      <Card className={cn("h-[400px]", className)}>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-semibold">
            Net Worth History ({months} Months)
          </CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col items-center justify-center h-[320px] text-center px-6">
          <Camera className="h-10 w-10 text-muted-foreground/50 mb-3" />
          <p className="text-muted-foreground text-sm">No snapshots yet</p>
          <p className="text-muted-foreground text-xs mt-1 max-w-[280px]">
            Generate your first monthly snapshot to start tracking your net worth
            history
          </p>
          <Button variant="outline" size="sm" className="mt-4">
            Generate First Snapshot
          </Button>
        </CardContent>
      </Card>
    );
  }

  // Calculate trend direction
  const firstValue = chartData[0]?.netWorth || 0;
  const lastValue = chartData[chartData.length - 1]?.netWorth || 0;
  const isPositive = lastValue >= firstValue;

  return (
    <Card className={cn("h-[400px]", className)}>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-semibold flex items-center gap-2">
          Net Worth History ({months} Months)
          <span
            className={cn(
              "text-xs ml-auto",
              isPositive ? "text-green-500" : "text-red-500"
            )}
          >
            {isPositive ? "+" : ""}
            {formatPaiseCompact(lastValue - firstValue)} total
          </span>
        </CardTitle>
      </CardHeader>
      <CardContent className="h-[320px]">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart
            data={chartData}
            margin={{ top: 10, right: 10, left: 0, bottom: 20 }}
          >
            <defs>
              <linearGradient id="assetsGradient" x1="0" y1="0" x2="0" y2="1">
                <stop
                  offset="5%"
                  stopColor="#10B981"
                  stopOpacity={0.3}
                />
                <stop
                  offset="95%"
                  stopColor="#10B981"
                  stopOpacity={0}
                />
              </linearGradient>
              <linearGradient id="liabilitiesGradient" x1="0" y1="0" x2="0" y2="1">
                <stop
                  offset="5%"
                  stopColor="#EF4444"
                  stopOpacity={0.3}
                />
                <stop
                  offset="95%"
                  stopColor="#EF4444"
                  stopOpacity={0}
                />
              </linearGradient>
              <linearGradient id="netWorthGradient" x1="0" y1="0" x2="0" y2="1">
                <stop
                  offset="5%"
                  stopColor="#3B82F6"
                  stopOpacity={0.3}
                />
                <stop
                  offset="95%"
                  stopColor="#3B82F6"
                  stopOpacity={0}
                />
              </linearGradient>
            </defs>
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
              tickFormatter={(value: string) => formatMonth(value).split(" ")[0] || ""}
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
              height={36}
              iconType="circle"
              wrapperStyle={{ paddingBottom: "10px" }}
            />
            <Area
              type="monotone"
              dataKey="assets"
              name="Assets"
              stroke="#10B981"
              strokeWidth={2}
              fill="url(#assetsGradient)"
            />
            <Area
              type="monotone"
              dataKey="liabilities"
              name="Liabilities"
              stroke="#EF4444"
              strokeWidth={2}
              fill="url(#liabilitiesGradient)"
            />
            <Area
              type="monotone"
              dataKey="netWorth"
              name="Net Worth"
              stroke="#3B82F6"
              strokeWidth={2}
              fill="url(#netWorthGradient)"
            />
          </AreaChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}
