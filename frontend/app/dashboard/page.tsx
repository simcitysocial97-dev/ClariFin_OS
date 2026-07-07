"use client";

/**
 * Dashboard Page - v2.0.0
 * =========================
 * 
 * Compact, enterprise-grade financial dashboard surfacing all backend intelligence.
 * 
 * Layout:
 * - Header Row
 * - KPI Row (4 cards)
 * - Analytics Summary Bar
 * - Main Content (2-column on desktop)
 * - Secondary Row (3-column on desktop)
 * - Footer
 */

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { AlertTriangle, TrendingUp, TrendingDown, PiggyBank, Home, Shield, Activity } from "lucide-react";
import { DashboardSkeleton } from "@/components/dashboard/dashboard-skeleton";
import { ErrorFallback } from "@/components/error-boundary";
import { useDashboardMetrics } from "@/lib/hooks/use-dashboard-metrics";
import { formatINR, formatPercentage } from "@/lib/utils/format";
import { RecentTransactions } from "@/components/dashboard/recent-transactions";
import { CashflowChart } from "@/components/dashboard/cashflow-chart";
import { BehaviorScoreCard } from "@/components/dashboard/behavior-score-card";
import { InsightsPanel } from "@/components/dashboard/insights-panel";
import { AnalyticsSummaryBar } from "@/components/dashboard/analytics-summary-bar";
import { RecurringChargesWidget } from "@/components/dashboard/recurring-charges-widget";
import { TopMerchantsWidget } from "@/components/dashboard/top-merchants-widget";
import { CategorySpendChart } from "@/components/dashboard/category-spend-chart";

// ============================================================
// Components
// ============================================================

function NetCashFlowCard({ amount_paise }: { amount_paise: number }) {
  const isPositive = amount_paise >= 0;
  return (
    <Card className={`${isPositive ? "bg-green-50 border-green-200" : "bg-red-50 border-red-200"}`}>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium text-gray-600">Net Cash Flow</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="flex items-center gap-3">
          {isPositive ? (
            <TrendingUp className="h-8 w-8 text-green-600" />
          ) : (
            <TrendingDown className="h-8 w-8 text-red-600" />
          )}
          <span className={`text-3xl font-bold ${isPositive ? "text-green-600" : "text-red-600"}`}>
            {formatINR(amount_paise)}
          </span>
        </div>
        <p className="text-xs text-gray-500 mt-2">
          {isPositive ? "Income exceeds expenses" : "Expenses exceed income"}
        </p>
      </CardContent>
    </Card>
  );
}

function SavingsRateCard({ rate }: { rate: number }) {
  const isGood = rate >= 0.2;
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium text-gray-600 flex items-center gap-2">
          <PiggyBank className="h-4 w-4" />
          Savings Rate
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="flex items-baseline gap-2">
          <span className={`text-3xl font-bold ${isGood ? "text-green-600" : "text-amber-600"}`}>
            {formatPercentage(rate)}
          </span>
        </div>
        <p className="text-xs text-gray-500 mt-2">
          Target: 20% or higher
        </p>
      </CardContent>
    </Card>
  );
}

function EMIRatioCard({ ratio }: { ratio: number }) {
  const isHigh = ratio > 0.4;
  return (
    <Card className={isHigh ? "bg-red-50 border-red-200" : ""}>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium text-gray-600 flex items-center gap-2">
          <Home className="h-4 w-4" />
          EMI Ratio
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="flex items-baseline gap-2">
          <span className={`text-3xl font-bold ${isHigh ? "text-red-600" : "text-gray-900"}`}>
            {formatPercentage(ratio)}
          </span>
        </div>
        <p className="text-xs text-gray-500 mt-2">
          {isHigh ? "High EMI burden - consider reducing" : "Healthy EMI level"}
        </p>
      </CardContent>
    </Card>
  );
}

function BufferDaysCard({ days }: { days: number }) {
  const isHealthy = days >= 30;
  const isAdequate = days >= 14;
  return (
    <Card className={isHealthy ? "bg-green-50 border-green-200" : isAdequate ? "bg-amber-50 border-amber-200" : "bg-red-50 border-red-200"}>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium text-gray-600 flex items-center gap-2">
          <Shield className="h-4 w-4" />
          Buffer Days
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="flex items-baseline gap-2">
          <span className={`text-3xl font-bold ${isHealthy ? "text-green-600" : isAdequate ? "text-amber-600" : "text-red-600"}`}>
            {days.toFixed(0)}
          </span>
          <span className="text-sm text-gray-500">days</span>
        </div>
        <p className="text-xs text-gray-500 mt-2">
          Target: 30+ days emergency fund
        </p>
      </CardContent>
    </Card>
  );
}

function SevenDayTrend({ trend }: { trend: number }) {
  const isUp = trend > 0;
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium text-gray-600">7-Day Spend Trend</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="flex items-center gap-2">
          {isUp ? (
            <TrendingUp className="h-5 w-5 text-red-500" />
          ) : (
            <TrendingDown className="h-5 w-5 text-green-500" />
          )}
          <span className={`text-xl font-bold ${isUp ? "text-red-600" : "text-green-600"}`}>
            {isUp ? "+" : ""}{(trend * 100).toFixed(0)}%
          </span>
        </div>
        <p className="text-xs text-gray-500 mt-2">
          {isUp ? "Spending increasing" : "Spending decreasing"}
        </p>
      </CardContent>
    </Card>
  );
}

function CategoryDriftAlert({ alert }: { alert: string | null }) {
  if (!alert) return null;
  return (
    <Alert className="bg-amber-50 border-amber-200">
      <AlertTriangle className="h-4 w-4 text-amber-600" />
      <AlertTitle className="text-amber-800">Spending Alert</AlertTitle>
      <AlertDescription className="text-amber-700">{alert}</AlertDescription>
    </Alert>
  );
}

function HealthScoreFooter({ score }: { score: number }) {
  const getColor = (s: number) => {
    if (s >= 70) return "text-green-600";
    if (s >= 40) return "text-amber-600";
    return "text-red-600";
  };
  
  return (
    <Card className="bg-gray-50 border-gray-200">
      <CardContent className="py-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Activity className="h-4 w-4 text-gray-500" />
            <span className="text-sm text-gray-600">Financial Health Score</span>
          </div>
          <span className={`text-lg font-bold ${getColor(score)}`}>
            {score.toFixed(0)}/100
          </span>
        </div>
      </CardContent>
    </Card>
  );
}

// ============================================================
// Main Page Component
// ============================================================

export default function DashboardPage() {
  const { data, loading, error, refetch } = useDashboardMetrics();

  // Loading state
  if (loading) {
    return (
      <div className="container mx-auto py-6 space-y-6">
        <DashboardSkeleton />
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="container mx-auto py-6">
        <ErrorFallback error={error} resetErrorBoundary={refetch} />
      </div>
    );
  }

  // No data state
  if (!data) {
    return (
      <div className="container mx-auto py-6">
        <Alert>
          <AlertTitle>No Data Available</AlertTitle>
          <AlertDescription>
            Upload bank statements to see your financial dashboard.
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  return (
    <div className="container mx-auto py-6 space-y-6">
      {/* Header Row */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Dashboard</h1>
          <p className="text-gray-500 text-sm">
            {data.months_of_data || 0} months of data
          </p>
        </div>
        <p className="text-xs text-muted-foreground">
          Last updated: {new Date().toLocaleTimeString()}
        </p>
      </div>

      {/* KPI Row - 4 Key Numbers */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <NetCashFlowCard amount_paise={data.net_cash_flow_paise} />
        <SavingsRateCard rate={data.savings_rate} />
        <EMIRatioCard ratio={data.emi_ratio} />
        <BufferDaysCard days={data.buffer_days} />
      </div>

      {/* Analytics Summary Bar */}
      <AnalyticsSummaryBar />

      {/* Main Content - 2-column on desktop, stack on mobile */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* LEFT COLUMN - 60% width (span 2 on lg) */}
        <div className="lg:col-span-2 space-y-6">
          {/* Cashflow Trend Chart */}
          <section>
            <h2 className="text-sm font-medium text-muted-foreground mb-3">
              Cashflow Trend
            </h2>
            <CashflowChart />
          </section>

          {/* Category Spend Chart */}
          <section>
            <h2 className="text-sm font-medium text-muted-foreground mb-3">
              Category Spend
            </h2>
            <CategorySpendChart />
          </section>
        </div>

        {/* RIGHT COLUMN - 40% width (span 1 on lg) */}
        <div className="space-y-6">
          <BehaviorScoreCard />
          <InsightsPanel />
        </div>
      </div>

      {/* Secondary Row - 3 columns on desktop, stack on mobile */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <RecurringChargesWidget />
        <TopMerchantsWidget />
        <Card>
          <CardHeader>
            <CardTitle className="text-lg font-semibold">Recent Transactions</CardTitle>
          </CardHeader>
          <CardContent>
            <RecentTransactions transactions={data.recent_transactions.slice(0, 10)} />
          </CardContent>
        </Card>
      </div>

      {/* Footer - Health Score */}
      <HealthScoreFooter score={data.financial_health_score} />
    </div>
  );
}