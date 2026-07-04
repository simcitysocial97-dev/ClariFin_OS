"use client";

/**
 * Net Worth Widget
 * ================
 * 
 * Shows current net worth with mini trend chart.
 * Uses formatPaise for currency display.
 */

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useNetWorthQuery, useNetWorthTrendQuery } from "@/lib/hooks/use-query-finance";
import { formatPaiseCompact } from "@/lib/format";
import { WidgetErrorFallback } from "./widget-error-fallback";
import { Skeleton } from "@/components/ui/skeleton";
import { TrendingUp, TrendingDown, Minus } from "lucide-react";
import { cn } from "@/lib/utils";

interface NetWorthWidgetProps {
  mode?: "personal" | "family";
}

function NetWorthSkeleton() {
  return (
    <Card className="h-[280px]">
      <CardHeader className="pb-2">
        <Skeleton className="h-5 w-28" />
      </CardHeader>
      <CardContent className="space-y-4">
        <Skeleton className="h-10 w-32" />
        <Skeleton className="h-4 w-24" />
        <div className="flex gap-1 h-[120px] items-end">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <Skeleton key={i} className="w-full" style={{ height: `${20 + i * 10}%` }} />
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

function MiniTrendChart({ data }: { data: { month: string; net_worth_paise: number }[] }) {
  // Take last 6 months
  const recentData = data.slice(-6);
  if (recentData.length === 0) return null;

  const maxValue = Math.max(...recentData.map(d => d.net_worth_paise));
  const minValue = Math.min(...recentData.map(d => d.net_worth_paise));
  const range = maxValue - minValue || 1;

  return (
    <div className="flex items-end gap-1 h-[80px] mt-4">
      {recentData.map((item, idx) => {
        const heightPercent = ((item.net_worth_paise - minValue) / range) * 70 + 30;
        return (
          <div
            key={idx}
            className="flex-1 bg-primary/20 rounded-t-sm relative group"
            style={{ height: `${heightPercent}%` }}
          >
            <div className="absolute bottom-0 left-0 right-0 bg-primary rounded-t-sm transition-all group-hover:bg-primary/80" 
                 style={{ height: '100%' }} />
            {/* Tooltip */}
            <div className="absolute -top-8 left-1/2 -translate-x-1/2 opacity-0 group-hover:opacity-100 transition-opacity bg-foreground text-background text-[10px] px-2 py-1 rounded whitespace-nowrap z-10">
              {formatPaiseCompact(item.net_worth_paise)}
            </div>
          </div>
        );
      })}
    </div>
  );
}

export function NetWorthWidget({ mode = "personal" }: NetWorthWidgetProps) {
  const { data: netWorth, loading: netWorthLoading, error: netWorthError, refetch: refetchNetWorth } = useNetWorthQuery();
  const { data: trendData, loading: trendLoading, error: trendError } = useNetWorthTrendQuery(6);

  const loading = netWorthLoading || trendLoading;
  const error = netWorthError || trendError;

  if (loading) {
    return <NetWorthSkeleton />;
  }

  if (error) {
    return (
      <WidgetErrorFallback
        title="Net Worth"
        error={error.message}
        onRetry={refetchNetWorth}
      />
    );
  }

  const currentNetWorth = netWorth?.net_worth_paise || 0;
  const trend = trendData?.trend || [];
  
  // Calculate month-over-month change
  const previousNetWorth = trend.length > 1 ? trend[trend.length - 2]?.net_worth_paise : currentNetWorth;
  const changePaise = currentNetWorth - (previousNetWorth || 0);
  const changePercent = previousNetWorth ? (changePaise / Math.abs(previousNetWorth)) * 100 : 0;

  const isPositive = changePaise >= 0;
  const TrendIcon = isPositive ? TrendingUp : changePaise < 0 ? TrendingDown : Minus;

  return (
    <Card className="h-[280px]">
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-semibold">
          Net Worth
          {mode === "family" && <span className="text-muted-foreground ml-2">· Family</span>}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-1">
          <p className="text-3xl font-bold tracking-tight">
            {formatPaiseCompact(currentNetWorth)}
          </p>
          <div className="flex items-center gap-2">
            <TrendIcon className={cn("h-4 w-4", isPositive ? "text-green-500" : changePaise < 0 ? "text-red-500" : "text-muted-foreground")} />
            <span className={cn("text-sm font-medium", isPositive ? "text-green-600" : changePaise < 0 ? "text-red-600" : "text-muted-foreground")}>
              {isPositive ? "+" : ""}{formatPaiseCompact(changePaise)} ({changePercent >= 0 ? "+" : ""}{changePercent.toFixed(1)}%)
            </span>
            <span className="text-xs text-muted-foreground">vs last month</span>
          </div>
        </div>

        {/* Mini Trend Chart */}
        {trend.length > 0 && (
          <MiniTrendChart data={trend} />
        )}
      </CardContent>
    </Card>
  );
}
