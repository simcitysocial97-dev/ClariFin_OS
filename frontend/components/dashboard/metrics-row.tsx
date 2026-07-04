"use client";

/**
 * Metrics Row
 * ===========
 * 
 * Four key metric cards displaying:
 * - Net Worth
 * - Monthly Cash Flow
 * - Total Liabilities
 * - Savings Rate
 */

import { Card, CardContent } from "@/components/ui/card";
import { useNetWorthQuery, useCashflowBreakdownQuery } from "@/lib/hooks/use-query-finance";
import { formatPaise } from "@/lib/format";
import { 
  Wallet, 
  TrendingUp, 
  TrendingDown, 
  PiggyBank, 
  Landmark,
  ArrowUpRight,
  ArrowDownRight,
  Minus
} from "lucide-react";
import { cn } from "@/lib/utils";
import { MetricCardSkeleton } from "./skeletons";
import { WidgetErrorFallback } from "./widget-error-fallback";

interface MetricsRowProps {
  mode?: "personal" | "family";
}

interface MetricCardProps {
  title: string;
  value: string;
  subtitle: string;
  icon: React.ReactNode;
  trend?: "up" | "down" | "neutral";
  variant?: "default" | "success" | "warning" | "danger";
}

function MetricCard({ title, value, subtitle, icon, trend, variant = "default" }: MetricCardProps) {
  const variantStyles = {
    default: "bg-card",
    success: "bg-green-500/5 border-green-500/20",
    warning: "bg-amber-500/5 border-amber-500/20",
    danger: "bg-red-500/5 border-red-500/20",
  };

  const trendIcons = {
    up: <ArrowUpRight className="h-3 w-3" />,
    down: <ArrowDownRight className="h-3 w-3" />,
    neutral: <Minus className="h-3 w-3" />,
  };

  const trendColors = {
    up: "text-green-500",
    down: "text-red-500",
    neutral: "text-muted-foreground",
  };

  return (
    <Card className={cn(variantStyles[variant], "border")}>
      <CardContent className="p-4">
        <div className="flex items-start justify-between">
          <div className="flex-1 min-w-0">
            <p className="text-xs text-muted-foreground uppercase tracking-wide">{title}</p>
            <p className="text-xl font-bold mt-1 truncate">{value}</p>
            <p className="text-xs text-muted-foreground mt-0.5">{subtitle}</p>
            {trend && (
              <div className={cn("flex items-center gap-1 mt-1 text-xs", trendColors[trend])}>
                {trendIcons[trend]}
              </div>
            )}
          </div>
          <div className="text-muted-foreground ml-2">{icon}</div>
        </div>
      </CardContent>
    </Card>
  );
}

export function MetricsRow({ mode = "personal" }: MetricsRowProps) {
  const { data: netWorthData, loading: netWorthLoading, error: netWorthError, refetch: refetchNetWorth } = useNetWorthQuery();
  const { data: cashflowData, loading: cashflowLoading, error: cashflowError, refetch: refetchCashflow } = useCashflowBreakdownQuery();

  // Loading state
  if (netWorthLoading || cashflowLoading) {
    return <MetricCardSkeleton />;
  }

  // Error state
  if (netWorthError || cashflowError) {
    return (
      <WidgetErrorFallback
        title="Failed to load metrics"
        error={netWorthError?.message || cashflowError?.message}
        onRetry={() => {
          refetchNetWorth();
          refetchCashflow();
        }}
      />
    );
  }

  // Calculate metrics
  const netWorth = netWorthData?.net_worth_paise || 0;
  const totalAssets = netWorthData?.total_assets_paise || 0;
  const totalLiabilities = netWorthData?.total_liabilities_paise || 0;
  
  // Cash flow calculations
  const income = cashflowData?.total_income_paise || 0;
  const expenses = cashflowData?.total_expense_paise || 0;
  const cashFlow = income - expenses;
  
  // Savings rate calculation
  const savingsRate = income > 0 ? ((income - expenses) / income) * 100 : 0;
  
  // Determine savings rate color
  const getSavingsRateVariant = () => {
    if (savingsRate >= 20) return "success";
    if (savingsRate >= 10) return "warning";
    return "danger";
  };

  // Determine cash flow trend
  const getCashFlowTrend = (): "up" | "down" | "neutral" => {
    if (cashFlow > 0) return "up";
    if (cashFlow < 0) return "down";
    return "neutral";
  };

  const metrics: MetricCardProps[] = [
    {
      title: "Net Worth",
      value: formatPaise(netWorth),
      subtitle: mode === "family" ? "Family total" : "Personal net worth",
      icon: <Wallet className="h-4 w-4" />,
      trend: netWorth >= 0 ? "up" : "down",
      variant: netWorth >= 0 ? "success" : "danger",
    },
    {
      title: "Monthly Cash Flow",
      value: formatPaise(cashFlow),
      subtitle: `${formatPaise(income)} in · ${formatPaise(expenses)} out`,
      icon: cashFlow >= 0 ? <TrendingUp className="h-4 w-4" /> : <TrendingDown className="h-4 w-4" />,
      trend: getCashFlowTrend(),
      variant: cashFlow >= 0 ? "success" : "danger",
    },
    {
      title: "Total Liabilities",
      value: formatPaise(totalLiabilities),
      subtitle: "Outstanding debt",
      icon: <Landmark className="h-4 w-4" />,
      variant: totalLiabilities > totalAssets * 0.5 ? "warning" : "default",
    },
    {
      title: "Savings Rate",
      value: `${savingsRate.toFixed(1)}%`,
      subtitle: savingsRate >= 20 ? "Excellent!" : savingsRate >= 10 ? "Good" : "Needs improvement",
      icon: <PiggyBank className="h-4 w-4" />,
      variant: getSavingsRateVariant(),
    },
  ];

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
      {metrics.map((metric) => (
        <MetricCard key={metric.title} {...metric} />
      ))}
    </div>
  );
}
