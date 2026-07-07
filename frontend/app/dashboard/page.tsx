"use client";

/**
 * Dashboard Page - v2.1.0
 * =========================
 * * Compact, enterprise-grade financial dashboard surfacing all backend intelligence.
 * Includes isolated component-level error boundaries to avoid total page failures.
 * * Layout:
 * - Header Row
 * - KPI Row (4 cards)
 * - Analytics Summary Bar
 * - Main Content (2-column on desktop)
 * - Secondary Row (3-column on desktop)
 * - Footer
 */

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { TrendingUp, TrendingDown, PiggyBank, Home, Shield, Activity } from "lucide-react";
import { DashboardSkeleton } from "@/components/dashboard/dashboard-skeleton";
import { ErrorFallback } from "@/components/error-boundary";
import { ErrorBoundary } from "@/components/ui/error-boundary";
import { useDashboardMetrics } from "@/lib/hooks/use-dashboard-metrics";
import { useOverview } from "@/lib/hooks/use-overview";
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
// Internal Presentational Components
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
  const { data, loading, error, refetch, dataUpdatedAt } = useDashboardMetrics();
  const { data: overviewData } = useOverview();

  // Page Loading state
  if (loading) {
    return (
      <div className="container mx-auto py-6 space-y-6">
        <DashboardSkeleton />
      </div>
    );
  }

  // Page Global Error state (Hook failures)
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
            {overviewData?.months_of_data || 0} months of data
          </p>
        </div>
        <p className="text-xs text-muted-foreground">
          Last updated: {dataUpdatedAt ? new Date(dataUpdatedAt).toLocaleTimeString() : new Date().toLocaleTimeString()}
        </p>
      </div>

      {/* KPI Row - 4 Key Numbers (Using core data hook; isolated inside global layout checks above) */}
      <div data-testid="dashboard-kpi-row" className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div data-testid="kpi-net-cash-flow">
          <NetCashFlowCard amount_paise={data.net_cash_flow_paise} />
        </div>
        <div data-testid="kpi-savings-rate">
          <SavingsRateCard rate={data.savings_rate} />
        </div>
        <div data-testid="kpi-emi-ratio">
          <EMIRatioCard ratio={data.emi_ratio} />
        </div>
        <div data-testid="kpi-buffer-days">
          <BufferDaysCard days={data.buffer_days} />
        </div>
      </div>

      {/* Analytics Summary Bar */}
      <ErrorBoundary componentName="Analytics Summary Bar">
        <AnalyticsSummaryBar />
      </ErrorBoundary>

      {/* Main Content - 2-column on desktop, stack on mobile */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* LEFT COLUMN - 60% width (span 2 on lg) */}
        <div className="lg:col-span-2 space-y-6">
          {/* Cashflow Trend Chart */}
          <section>
            <h2 className="text-sm font-medium text-muted-foreground mb-3">
              Cashflow Trend
            </h2>
            <div data-testid="cashflow-chart-section">
              <ErrorBoundary componentName="Cashflow Chart">
                <CashflowChart />
              </ErrorBoundary>
            </div>
          </section>

          {/* Category Spend Chart */}
          <section>
            <h2 className="text-sm font-medium text-muted-foreground mb-3">
              Category Spend
            </h2>
            <ErrorBoundary componentName="Category Spend Chart">
              <CategorySpendChart />
            </ErrorBoundary>
          </section>
        </div>

        {/* RIGHT COLUMN - 40% width (span 1 on lg) */}
        <div className="space-y-6">
          <div data-testid="behavior-score-section">
            <ErrorBoundary componentName="Behavior Score">
              <BehaviorScoreCard />
            </ErrorBoundary>
          </div>
          
          <div data-testid="insights-section">
            <ErrorBoundary componentName="Insights Panel">
              <InsightsPanel />
            </ErrorBoundary>
          </div>
        </div>
      </div>

      {/* Secondary Row - 3 columns on desktop, stack on mobile */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <ErrorBoundary componentName="Recurring Charges">
          <RecurringChargesWidget />
        </ErrorBoundary>

        <ErrorBoundary componentName="Top Merchants">
          <TopMerchantsWidget />
        </ErrorBoundary>

        <div data-testid="recent-transactions-section">
          <ErrorBoundary componentName="Recent Transactions">
            <Card>
              <CardHeader>
                <CardTitle className="text-lg font-semibold">Recent Transactions</CardTitle>
              </CardHeader>
              <CardContent>
                <RecentTransactions transactions={data.recent_transactions.slice(0, 10)} />
              </CardContent>
            </Card>
          </ErrorBoundary>
        </div>
      </div>

      {/* Footer - Health Score */}
      <HealthScoreFooter score={data.financial_health_score} />
    </div>
  );
}
