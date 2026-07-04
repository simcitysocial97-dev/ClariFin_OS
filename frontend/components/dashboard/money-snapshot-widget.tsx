"use client";

/**
 * Money Snapshot Widget
 * =====================
 * 
 * Shows this month's financial snapshot:
 * - Income (total_credit)
 * - Expenses (total_debit)
 * - Net Cashflow (income - expenses)
 * - Savings Rate (net / income * 100)
 * 
 * Uses formatPaise for all currency displays.
 */

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useMonthlyCashflowQuery } from "@/lib/hooks/use-query-finance";
import { formatPaise, formatPaiseCompact } from "@/lib/format";
import { WidgetErrorFallback } from "./widget-error-fallback";
import { Skeleton } from "@/components/ui/skeleton";
import { TrendingUp, TrendingDown, Wallet, PiggyBank } from "lucide-react";
import { cn } from "@/lib/utils";

interface MoneySnapshotWidgetProps {
  mode?: "personal" | "family";
}

interface MetricCardProps {
  label: string;
  value: string;
  subValue?: string;
  icon: React.ReactNode;
  trend?: "positive" | "negative" | "neutral";
  isCompact?: boolean;
}

function MetricCard({ label, value, subValue, icon, trend = "neutral", isCompact = false }: MetricCardProps) {
  const trendColors = {
    positive: "text-green-600 dark:text-green-400",
    negative: "text-red-600 dark:text-red-400",
    neutral: "text-muted-foreground",
  };

  return (
    <div className="flex items-start justify-between p-3 bg-muted/50 rounded-lg">
      <div className="flex-1 min-w-0">
        <p className="text-xs text-muted-foreground mb-1">{label}</p>
        <p className={cn("font-semibold truncate", trendColors[trend], isCompact ? "text-sm" : "text-base")}>
          {value}
        </p>
        {subValue && (
          <p className="text-[10px] text-muted-foreground mt-0.5">{subValue}</p>
        )}
      </div>
      <div className="p-2 bg-background rounded-md shrink-0 ml-2">
        {icon}
      </div>
    </div>
  );
}

function MoneySnapshotSkeleton() {
  return (
    <Card className="h-[280px]">
      <CardHeader className="pb-2">
        <Skeleton className="h-5 w-32" />
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="grid grid-cols-2 gap-3">
          <Skeleton className="h-[90px] w-full" />
          <Skeleton className="h-[90px] w-full" />
          <Skeleton className="h-[90px] w-full" />
          <Skeleton className="h-[90px] w-full" />
        </div>
      </CardContent>
    </Card>
  );
}

export function MoneySnapshotWidget({ mode = "personal" }: MoneySnapshotWidgetProps) {
  const { data, loading, error, refetch } = useMonthlyCashflowQuery();

  if (loading) {
    return <MoneySnapshotSkeleton />;
  }

  if (error) {
    return (
      <WidgetErrorFallback
        title="Money Snapshot"
        error={error.message}
        onRetry={refetch}
      />
    );
  }

  // Get the most recent month's data (first in the array, sorted desc)
  const months = data?.months || [];
  const currentMonth = months[0];

  // Empty state - no data
  if (!currentMonth) {
    return (
      <Card className="h-[280px]">
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-semibold">
            Money Snapshot
            {mode === "family" && <span className="text-muted-foreground ml-2">· Family</span>}
          </CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col items-center justify-center h-[200px] text-center">
          <p className="text-muted-foreground text-sm">No cashflow data yet</p>
          <p className="text-muted-foreground text-xs mt-1">
            Import transactions to see your monthly snapshot
          </p>
        </CardContent>
      </Card>
    );
  }

  // Get values from current month (in paise)
  const incomePaise = currentMonth.total_income_paise || 0;
  const expensePaise = currentMonth.total_expense_paise || 0;
  const netCashflowPaise = currentMonth.net_cashflow_paise || 0;
  const savingsRate = currentMonth.savings_rate || 0;
  
  // Determine if values are positive/negative for trend coloring
  const incomeTrend: "positive" | "negative" | "neutral" = incomePaise >= 0 ? "positive" : "negative";
  const expenseTrend: "positive" | "negative" | "neutral" = expensePaise > 0 ? "negative" : "neutral";
  const netTrend: "positive" | "negative" | "neutral" = netCashflowPaise >= 0 ? "positive" : "negative";
  const savingsTrend: "positive" | "negative" | "neutral" = savingsRate >= 20 ? "positive" : savingsRate >= 0 ? "neutral" : "negative";

  return (
    <Card className="h-[280px]">
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-semibold">
          Money Snapshot
          {mode === "family" && <span className="text-muted-foreground ml-2">· Family</span>}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 gap-3">
          <MetricCard
            label="Income"
            value={formatPaiseCompact(incomePaise)}
            subValue={formatPaise(incomePaise)}
            icon={<TrendingUp className="h-4 w-4 text-green-600" />}
            trend={incomeTrend}
          />
          <MetricCard
            label="Expenses"
            value={formatPaiseCompact(expensePaise)}
            subValue={formatPaise(expensePaise)}
            icon={<TrendingDown className="h-4 w-4 text-red-600" />}
            trend={expenseTrend}
          />
          <MetricCard
            label="Net Cashflow"
            value={formatPaiseCompact(netCashflowPaise)}
            subValue={formatPaise(netCashflowPaise)}
            icon={<Wallet className="h-4 w-4 text-blue-600" />}
            trend={netTrend}
          />
          <MetricCard
            label="Savings Rate"
            value={`${savingsRate.toFixed(1)}%`}
            subValue={savingsRate >= 20 ? "Good job!" : savingsRate >= 0 ? "Keep saving" : "Overspending"}
            icon={<PiggyBank className="h-4 w-4 text-amber-600" />}
            trend={savingsTrend}
          />
        </div>
      </CardContent>
    </Card>
  );
}
