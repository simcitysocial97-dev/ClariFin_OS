/**
 * Dashboard Page - Stage 8E-C2 Production Visual System Migration
 *
 * Graph Surface - Main analysis surface for dashboard.
 * Shell provides: Header, Toolbar, Breadcrumbs, Selection Summary, Evidence Drawer.
 *
 * Migrated: Wrapped in Surface/Panel primitives, removed legacy padding.
 * Updated: Using MoneyValue primitive and semantic colors.
 */

"use client";

import { useRouter } from "next/navigation";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { TrendingUp, TrendingDown, PiggyBank, Home, Shield, Activity, Upload } from "lucide-react";
import { Button } from "@/components/ui/button";
import { DashboardSkeleton } from "@/components/dashboard/dashboard-skeleton";
import { ErrorFallback } from "@/components/error-boundary";
import { ErrorBoundary } from "@/components/ui/error-boundary";
import { useDashboardMetrics } from "@/lib/hooks/use-dashboard-metrics";
import { formatPercentage } from "@/lib/utils/format";
import { RecentTransactions } from "@/components/dashboard/recent-transactions";
import { CashflowChart } from "@/components/dashboard/cashflow-chart";
import { BehaviorScoreCard } from "@/components/dashboard/behavior-score-card";
import { InsightsPanel } from "@/components/dashboard/insights-panel";
import { AnalyticsSummaryBar } from "@/components/dashboard/analytics-summary-bar";
import { RecurringChargesWidget } from "@/components/dashboard/recurring-charges-widget";
import { TopMerchantsWidget } from "@/components/dashboard/top-merchants-widget";
import { CategorySpendChart } from "@/components/dashboard/category-spend-chart";
import { Surface } from "@/components/primitives/surface/surface";
import { Panel, PanelHeader, PanelBody } from "@/components/primitives/panel/panel";
import { Stack } from "@/components/primitives/layout/stack";
import { Grid } from "@/components/primitives/layout/grid";
import { MoneyValue } from "@/components/primitives/data-display/money-value";

// ============================================================
// Internal Presentational Components
// ============================================================

function NetCashFlowCard({ amount_paise }: { amount_paise: number }) {
  const isPositive = amount_paise >= 0;
  return (
    <Surface variant="raised" density="none" className="p-4">
      <Stack gap={2}>
        <p className="text-sm text-[var(--text-tertiary)]">Net Cash Flow</p>
        <div className="flex items-center gap-3">
          {isPositive ? (
            <TrendingUp className="h-8 w-8 text-[var(--color-positive-600)]" />
          ) : (
            <TrendingDown className="h-8 w-8 text-[var(--color-negative-600)]" />
          )}
          <MoneyValue 
            paise={amount_paise} 
            variant="large" 
            sign="auto"
          />
        </div>
        <p className="text-xs text-[var(--text-tertiary)]">
          {isPositive ? "Income exceeds expenses" : "Expenses exceed income"}
        </p>
      </Stack>
    </Surface>
  );
}

function SavingsRateCard({ rate }: { rate: number }) {
  const isGood = rate >= 20;
  return (
    <Surface variant="raised" density="none" className="p-4">
      <Stack gap={2}>
        <p className="text-sm font-medium text-[var(--text-secondary)] flex items-center gap-2">
          <PiggyBank className="h-4 w-4" />
          Savings Rate
        </p>
        <div className="flex items-baseline gap-2">
          <span className={`text-3xl font-bold ${isGood ? "text-[var(--color-positive-600)]" : "text-[var(--color-warning-600)]"}`}>
            {formatPercentage(rate)}
          </span>
        </div>
        <p className="text-xs text-[var(--text-tertiary)]">
          Target: 20% or higher
        </p>
      </Stack>
    </Surface>
  );
}

function EMIRatioCard({ ratio }: { ratio: number }) {
  const isHigh = ratio > 40;
  return (
    <Surface variant="raised" density="none" className={`p-4 ${isHigh ? "bg-[var(--color-negative-50)] border-[var(--color-negative-200)]" : ""}`}>
      <Stack gap={2}>
        <p className="text-sm font-medium text-[var(--text-secondary)] flex items-center gap-2">
          <Home className="h-4 w-4" />
          EMI Ratio
        </p>
        <div className="flex items-baseline gap-2">
          <span className={`text-3xl font-bold ${isHigh ? "text-[var(--color-negative-600)]" : "text-[var(--text-primary)]"}`}>
            {formatPercentage(ratio)}
          </span>
        </div>
        <p className="text-xs text-[var(--text-tertiary)]">
          {isHigh ? "High EMI burden - consider reducing" : "Healthy EMI level"}
        </p>
      </Stack>
    </Surface>
  );
}

function BufferDaysCard({ days }: { days: number }) {
  const isHealthy = days >= 30;
  const isAdequate = days >= 14;
  return (
    <Surface variant="raised" density="none" className={`p-4 ${isHealthy ? "bg-[var(--color-positive-50)] border-[var(--color-positive-200)]" : isAdequate ? "bg-[var(--color-warning-50)] border-[var(--color-warning-200)]" : "bg-[var(--color-negative-50)] border-[var(--color-negative-200)]"}`}>
      <Stack gap={2}>
        <p className="text-sm font-medium text-[var(--text-secondary)] flex items-center gap-2">
          <Shield className="h-4 w-4" />
          Buffer Days
        </p>
        <div className="flex items-baseline gap-2">
          <span className={`text-3xl font-bold ${isHealthy ? "text-[var(--color-positive-600)]" : isAdequate ? "text-[var(--color-warning-600)]" : "text-[var(--color-negative-600)]"}`}>
            {days.toFixed(0)}
          </span>
          <span className="text-sm text-[var(--text-tertiary)]">days</span>
        </div>
        <p className="text-xs text-[var(--text-tertiary)]">
          Target: 30+ days emergency fund
        </p>
      </Stack>
    </Surface>
  );
}

function HealthScoreFooter({ score }: { score: number | null | undefined }) {
  const getColor = (s: number) => {
    if (s >= 70) return "text-[var(--color-positive-600)]";
    if (s >= 40) return "text-[var(--color-warning-600)]";
    return "text-[var(--color-negative-600)]";
  };

  return (
    <Surface variant="raised" density="none" className="p-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Activity className="h-4 w-4 text-[var(--text-tertiary)]" />
          <span className="text-sm text-[var(--text-secondary)]">Financial Health Score</span>
        </div>
        {score == null ? (
          <span
            className="text-lg font-bold text-[var(--text-tertiary)]"
            title="Financial health score is not available until behaviour analysis runs"
          >
            —
          </span>
        ) : (
          <span className={`text-lg font-bold ${getColor(score)}`}>
            {score.toFixed(0)}/100
          </span>
        )}
      </div>
    </Surface>
  );
}

// ============================================================
// Main Page Component
// ============================================================

export default function DashboardPage() {
  const { data, loading, error, refetch } = useDashboardMetrics();
  const router = useRouter();
  // useOverview hook is available for future use

  // Page Loading state
  if (loading) {
    return (
      <main>
      <Surface variant="default" density="none" className="flex flex-col h-full">
        <Panel fill>
          <PanelHeader title="Dashboard" actions={
            <Button variant="outline" onClick={() => router.push('?upload=true')}>
              <Upload className="h-4 w-4 mr-2" />
              Upload
            </Button>
          } />
          <PanelBody loading>
            <div className="p-4">
              <DashboardSkeleton />
            </div>
          </PanelBody>
        </Panel>
      </Surface>
      </main>
    );
  }

  // Page Global Error state (Hook failures)
  if (error) {
    return (
      <main>
      <Surface variant="default" density="none" className="flex flex-col h-full">
        <Panel fill>
          <PanelHeader title="Dashboard" actions={
            <Button variant="outline" onClick={() => router.push('?upload=true')}>
              <Upload className="h-4 w-4 mr-2" />
              Upload
            </Button>
          } />
          <PanelBody error={error.message}>
            <div className="p-4">
              <ErrorFallback error={error} resetErrorBoundary={refetch} />
            </div>
          </PanelBody>
        </Panel>
      </Surface>
      </main>
    );
  }

  // No data state
  if (!data) {
    return (
      <main>
      <Surface variant="default" density="none" className="flex flex-col h-full">
        <Panel fill>
          <PanelHeader title="Dashboard" actions={
            <Button variant="outline" onClick={() => router.push('?upload=true')}>
              <Upload className="h-4 w-4 mr-2" />
              Upload
            </Button>
          } />
          <PanelBody empty emptyMessage="No data available">
            <div className="p-4">
              <Alert>
                <AlertTitle>No Data Available</AlertTitle>
                <AlertDescription>
                  Upload bank statements to see your financial dashboard.
                </AlertDescription>
              </Alert>
            </div>
          </PanelBody>
        </Panel>
      </Surface>
      </main>
    );
  }

  return (
    <main>
    <Surface variant="default" density="none" className="flex flex-col h-full">
      <Panel fill>
        <PanelHeader title="Dashboard" actions={
          <Button variant="outline" onClick={() => router.push('?upload=true')}>
            <Upload className="h-4 w-4 mr-2" />
            Upload
          </Button>
        } />
        <PanelBody scrollable>
          <Stack gap={4} className="p-4">
            {/* KPI Row - 4 Key Numbers */}
            <Grid gap={4} className="grid-cols-1 md:grid-cols-2 lg:grid-cols-4">
              <NetCashFlowCard amount_paise={data.net_cash_flow_paise} />
              <SavingsRateCard rate={data.savings_rate} />
              <EMIRatioCard ratio={data.emi_ratio} />
              <BufferDaysCard days={data.buffer_days} />
            </Grid>

            {/* Analytics Summary Bar */}
            <ErrorBoundary componentName="Analytics Summary Bar">
              <AnalyticsSummaryBar />
            </ErrorBoundary>

            {/* Upload Button */}

            {/* Main Content - 2-column on desktop, stack on mobile */}
            <Grid gap={4} className="grid-cols-1 lg:grid-cols-3">
              {/* LEFT COLUMN - 60% width (span 2 on lg) */}
              <div className="lg:col-span-2 space-y-4">
                {/* Cashflow Trend Chart */}
                <section>
                  <h2 className="text-sm font-medium text-[var(--text-tertiary)] mb-3">
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
                  <h2 className="text-sm font-medium text-[var(--text-tertiary)] mb-3">
                    Category Spend
                  </h2>
                  <ErrorBoundary componentName="Category Spend Chart">
                    <CategorySpendChart />
                  </ErrorBoundary>
                </section>
              </div>

              {/* RIGHT COLUMN - 40% width (span 1 on lg) */}
              <div className="space-y-4">
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
            </Grid>

            {/* Secondary Row - 3 columns on desktop, stack on mobile */}
            <Grid gap={4} className="grid-cols-1 md:grid-cols-2 lg:grid-cols-3">
              <ErrorBoundary componentName="Recurring Charges">
                <RecurringChargesWidget />
              </ErrorBoundary>

              <ErrorBoundary componentName="Top Merchants">
                <TopMerchantsWidget />
              </ErrorBoundary>

              <div data-testid="recent-transactions-section">
                <ErrorBoundary componentName="Recent Transactions">
                  <Surface variant="raised" density="none" className="p-4">
                    <Stack gap={3}>
                      <h2 className="text-lg font-semibold">Recent Transactions</h2>
                      <RecentTransactions
                        transactions={data.recent_transactions?.slice(0, 10) ?? []}
                        isLoading={loading}
                        isError={!!error}
                        onRetry={refetch}
                      />
                    </Stack>
                  </Surface>
                </ErrorBoundary>
              </div>
            </Grid>

            {/* Footer - Health Score */}
            <HealthScoreFooter score={data.financial_health_score} />
          </Stack>
        </PanelBody>
      </Panel>
    </Surface>
    </main>
  );
}