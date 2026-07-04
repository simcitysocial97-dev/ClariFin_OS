"use client";

/**
 * Net Worth Trend Widget
 * ======================
 * 
 * Smooth area chart showing 12-month net worth trend.
 * Includes empty state CTA to generate first snapshot.
 */

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { useNetWorthTrendQuery } from "@/lib/hooks/use-query-finance";
import { formatPaise, formatMonth } from "@/lib/format";
import { ChartWidgetSkeleton } from "./skeletons";
import { WidgetErrorFallback } from "./widget-error-fallback";
import { 
  AreaChart, 
  Area, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer
} from "recharts";
import { Camera } from "lucide-react";
import { cn } from "@/lib/utils";

interface NetWorthTrendWidgetProps {
  mode?: "personal" | "family";
}

interface TrendData {
  month: string;
  net_worth_paise: number;
}

// Format large numbers compactly
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

// Custom tooltip
function CustomTooltip({ active, payload, label }: { 
  active?: boolean; 
  payload?: Array<{ value: number }>;
  label?: string;
}) {
  if (active && payload && payload.length && payload[0]) {
    return (
      <div className="bg-popover border rounded-lg p-3 shadow-lg">
        <p className="font-medium text-sm">{formatMonth(label || "")}</p>
        <p className="text-sm text-muted-foreground">
          {formatPaise(payload[0].value)}
        </p>
      </div>
    );
  }
  return null;
}

export function NetWorthTrendWidget({ mode = "personal" }: NetWorthTrendWidgetProps) {
  const { data, loading, error, refetch } = useNetWorthTrendQuery(12);

  if (loading) {
    return <ChartWidgetSkeleton />;
  }

  if (error) {
    return (
      <WidgetErrorFallback
        title="Net Worth Trend"
        error={error.message}
        onRetry={refetch}
      />
    );
  }

  // Transform data for the chart
  const trendData: TrendData[] = (data?.trend || [])
    .map((item) => ({
      month: item.month,
      net_worth_paise: item.net_worth_paise,
    }))
    .sort((a, b) => new Date(a.month).getTime() - new Date(b.month).getTime());

  // Empty state - no snapshots yet
  if (trendData.length === 0) {
    return (
      <Card className="h-[320px]">
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-semibold">Net Worth Trend</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col items-center justify-center h-[250px] text-center px-6">
          <Camera className="h-10 w-10 text-muted-foreground/50 mb-3" />
          <p className="text-muted-foreground text-sm">No snapshots yet</p>
          <p className="text-muted-foreground text-xs mt-1 max-w-[200px]">
            Generate your first monthly snapshot to start tracking your net worth trend
          </p>
          <Button variant="outline" size="sm" className="mt-4">
            Generate First Snapshot
          </Button>
        </CardContent>
      </Card>
    );
  }

  // Calculate trend direction
  const firstValue = trendData[0]?.net_worth_paise || 0;
  const lastValue = trendData[trendData.length - 1]?.net_worth_paise || 0;
  const isPositive = lastValue >= firstValue;

  return (
    <Card className="h-[320px]">
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-semibold flex items-center gap-2">
          Net Worth Trend (12 Months)
          {mode === "family" && <span className="text-muted-foreground">· Family</span>}
          <span className={cn(
            "text-xs ml-auto",
            isPositive ? "text-green-500" : "text-red-500"
          )}>
            {isPositive ? "+" : ""}
            {formatCompact(lastValue - firstValue)}
          </span>
        </CardTitle>
      </CardHeader>
      <CardContent className="h-[250px]">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart
            data={trendData}
            margin={{ top: 10, right: 10, left: 0, bottom: 20 }}
          >
            <defs>
              <linearGradient id="networthGradient" x1="0" y1="0" x2="0" y2="1">
                <stop 
                  offset="5%" 
                  stopColor="hsl(var(--chart-1))" 
                  stopOpacity={0.3}
                />
                <stop 
                  offset="95%" 
                  stopColor="hsl(var(--chart-1))" 
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
              tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 11 }}
              tickFormatter={(value) => formatMonth(value).split(" ")[0] || ""}
              axisLine={false}
              tickLine={false}
              dy={10}
              interval={Math.floor(trendData.length / 6)}
            />
            <YAxis
              tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 11 }}
              tickFormatter={formatCompact}
              axisLine={false}
              tickLine={false}
              width={50}
            />
            <Tooltip content={<CustomTooltip />} />
            <Area
              type="monotone"
              dataKey="net_worth_paise"
              stroke="hsl(var(--chart-1))"
              strokeWidth={2}
              fill="url(#networthGradient)"
            />
          </AreaChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}
