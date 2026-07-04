"use client";

/**
 * Investments Widget
 * ==================
 * 
 * Shows investment summary with total invested vs current value.
 * Displays gain/loss with color-coded indicators.
 */

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { useInvestmentSummaryQuery } from "@/lib/hooks/use-query-finance";
import { formatPaise } from "@/lib/format";
import { ListWidgetSkeleton } from "./skeletons";
import { WidgetErrorFallback } from "./widget-error-fallback";
import { TrendingUp, TrendingDown, ArrowRight, Wallet } from "lucide-react";
import Link from "next/link";
import { cn } from "@/lib/utils";

interface InvestmentsWidgetProps {
  mode?: "personal" | "family";
}

export function InvestmentsWidget({ mode = "personal" }: InvestmentsWidgetProps) {
  const { data, loading, error, refetch } = useInvestmentSummaryQuery();

  if (loading) {
    return <ListWidgetSkeleton />;
  }

  if (error) {
    return (
      <WidgetErrorFallback
        title="Investments"
        error={error.message}
        onRetry={refetch}
      />
    );
  }

  const summary = data || {
    total_invested_paise: 0,
    total_current_value_paise: 0,
    total_gain_loss_paise: 0,
    gain_loss_percent: 0,
    count: 0,
  };

  const isProfitable = summary.total_gain_loss_paise >= 0;

  // Empty state
  if (summary.count === 0) {
    return (
      <Card className="h-[320px]">
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-semibold">Investments</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col items-center justify-center h-[250px] text-center px-6">
          <Wallet className="h-10 w-10 text-muted-foreground/50 mb-3" />
          <p className="text-muted-foreground text-sm">No investments tracked</p>
          <p className="text-muted-foreground text-xs mt-1">
            Add your investments to track portfolio performance
          </p>
          <Link href="/investments" className="mt-4">
            <Button variant="outline" size="sm">
              View Investments
              <ArrowRight className="h-4 w-4 ml-2" />
            </Button>
          </Link>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="h-[320px]">
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-semibold">
          Investments
          {mode === "family" && <span className="text-muted-foreground ml-2">· Family</span>}
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Total Value */}
        <div className="text-center py-2">
          <p className="text-xs text-muted-foreground uppercase tracking-wide">
            Current Value
          </p>
          <p className="text-2xl font-bold">
            {formatPaise(summary.total_current_value_paise)}
          </p>
          <div className={cn(
            "flex items-center justify-center gap-1 mt-1 text-sm",
            isProfitable ? "text-green-500" : "text-red-500"
          )}>
            {isProfitable ? (
              <TrendingUp className="h-4 w-4" />
            ) : (
              <TrendingDown className="h-4 w-4" />
            )}
            <span className="font-medium">
              {isProfitable ? "+" : ""}
              {formatPaise(Math.abs(summary.total_gain_loss_paise))}
            </span>
            <span className="text-xs">
              ({isProfitable ? "+" : ""}
              {summary.gain_loss_percent.toFixed(1)}%)
            </span>
          </div>
        </div>

        {/* Invested vs Current */}
        <div className="space-y-3">
          <div className="flex justify-between items-center">
            <span className="text-sm text-muted-foreground">Invested</span>
            <span className="text-sm font-mono">
              {formatPaise(summary.total_invested_paise)}
            </span>
          </div>
          <div className="h-px bg-border" />
          <div className="flex justify-between items-center">
            <span className="text-sm text-muted-foreground">Current</span>
            <span className="text-sm font-mono font-medium">
              {formatPaise(summary.total_current_value_paise)}
            </span>
          </div>
        </div>

        {/* Investment Count */}
        <div className="text-center">
          <p className="text-xs text-muted-foreground">
            {summary.count} investment{summary.count !== 1 ? "s" : ""}
          </p>
        </div>

        {/* View All Link */}
        <Link href="/investments">
          <Button variant="ghost" size="sm" className="w-full">
            View details
            <ArrowRight className="h-4 w-4 ml-2" />
          </Button>
        </Link>
      </CardContent>
    </Card>
  );
}
