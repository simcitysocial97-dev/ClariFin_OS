"use client";

/**
 * Net Worth Header
 * ================
 *
 * Hero section showing Current Net Worth, Total Assets, Total Liabilities,
 * and Month-over-Month change.
 */

import { useNetWorth, useNetWorthTrend } from "@/lib/hooks/use-finance-data";
import { formatPaise, formatPaiseCompact } from "@/lib/format";
import { WidgetErrorFallback } from "@/components/dashboard/widget-error-fallback";
import { TrendingUp, TrendingDown, Minus } from "lucide-react";
import { cn } from "@/lib/utils";

interface NetWorthHeaderProps {
  className?: string;
}

export function NetWorthHeader({ className }: NetWorthHeaderProps) {
  const { data: netWorth, loading, error, refetch } = useNetWorth();
  const { trend } = useNetWorthTrend(); // Last 2 months for MoM calculation

  if (loading) {
    return (
      <div className={cn("text-center py-8 space-y-4", className)}>
        <div className="animate-pulse space-y-4">
          <div className="h-4 w-32 bg-muted mx-auto rounded" />
          <div className="h-16 w-64 bg-muted mx-auto rounded" />
          <div className="flex items-center justify-center gap-4">
            <div className="h-6 w-32 bg-muted rounded" />
            <div className="h-6 w-4 bg-muted rounded" />
            <div className="h-6 w-32 bg-muted rounded" />
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={cn("py-4", className)}>
        <WidgetErrorFallback
          title="Net Worth Summary"
          error={error.message}
          onRetry={refetch}
        />
      </div>
    );
  }

  const assets = netWorth?.total_assets_paise || 0;
  const liabilities = netWorth?.total_liabilities_paise || 0;
  const netWorthValue = assets - liabilities;
  const isPositive = netWorthValue >= 0;

  // Calculate MoM change
  let momChange = 0;
  let momPercent = 0;
  if (trend && trend.length >= 2) {
    const current = trend[trend.length - 1]?.net_worth_paise || 0;
    const previous = trend[trend.length - 2]?.net_worth_paise || 0;
    if (previous !== 0) {
      momChange = current - previous;
      momPercent = (momChange / Math.abs(previous)) * 100;
    }
  }

  const MomIcon = momChange > 0 ? TrendingUp : momChange < 0 ? TrendingDown : Minus;
  const momColor = momChange > 0 ? "text-green-600" : momChange < 0 ? "text-red-600" : "text-muted-foreground";
  const momSign = momChange > 0 ? "+" : "";

  return (
    <div className={cn("text-center py-8", className)}>
      {/* Label */}
      <p className="text-muted-foreground mb-2 text-sm uppercase tracking-wide">
        Current Net Worth
      </p>

      {/* Main Value */}
      <h1
        className={cn(
          "text-5xl font-bold tracking-tight",
          isPositive ? "text-green-600" : "text-red-600"
        )}
      >
        {isPositive ? "+" : ""}
        {formatPaise(netWorthValue)}
      </h1>

      {/* MoM Change */}
      {momChange !== 0 && (
        <div className={cn("flex items-center justify-center gap-2 mt-2", momColor)}>
          <MomIcon className="h-4 w-4" />
          <span className="text-sm font-medium">
            {momSign}
            {formatPaiseCompact(Math.abs(momChange))} ({momSign}
            {momPercent.toFixed(1)}%) this month
          </span>
        </div>
      )}

      {/* Assets & Liabilities */}
      <div className="flex items-center justify-center gap-6 mt-6 text-lg">
        <div className="flex items-center gap-2">
          <span className="text-green-600 font-medium">
            Assets: {formatPaiseCompact(assets)}
          </span>
        </div>
        <span className="text-muted-foreground">|</span>
        <div className="flex items-center gap-2">
          <span className="text-red-600 font-medium">
            Liabilities: {formatPaiseCompact(liabilities)}
          </span>
        </div>
      </div>
    </div>
  );
}
