"use client";

/**
 * Dashboard Page - Financial Operating System v1.0
 * =========================
 * Conversation-first financial dashboard with progressive disclosure.
 * 
 * Layout:
 * - Hero Row (Financial Health + Inbox)
 * - Wealth Section (Net Worth, Cash Position, Accounts, Investments)
 * - Spending Section (Cashflow, Categories, Merchants)
 * - Borrowing Section (Loans, Credit Cards)
 * - Journey Section (Timeline, Recommendations)
 */

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { TrendingUp } from "lucide-react";
import { DashboardSkeleton } from "@/components/dashboard/dashboard-skeleton";
import { ErrorFallback } from "@/components/error-boundary";
import { ErrorBoundary } from "@/components/ui/error-boundary";
import { useDashboardMetrics } from "@/lib/hooks/use-dashboard-metrics";
import { useOverview } from "@/lib/hooks/use-overview";
import { formatINR } from "@/lib/utils/format";
import { RecentTransactions } from "@/components/dashboard/recent-transactions";
import { CashflowChart } from "@/components/dashboard/cashflow-chart";
import { CategorySpendChart } from "@/components/dashboard/category-spend-chart";
import { FinancialHealthHero } from "@/components/dashboard/widgets/financial-health-hero";
import { FinancialInboxWidget } from "@/components/dashboard/widgets/financial-inbox-widget";

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
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Financial OS</h1>
          <p className="text-gray-500 text-sm">
            {overviewData?.months_of_data || 0} months of data
          </p>
        </div>
        <p className="text-xs text-muted-foreground">
          Last updated: {dataUpdatedAt ? new Date(dataUpdatedAt).toLocaleTimeString() : new Date().toLocaleTimeString()}
        </p>
      </div>

      {/* HERO ROW - Financial Health Conversation */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <Card>
            <CardContent className="pt-6">
              <FinancialHealthHero />
            </CardContent>
          </Card>
        </div>
        
        {/* Financial Inbox */}
        <div>
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-base flex items-center gap-2">
                Financial Inbox
              </CardTitle>
            </CardHeader>
            <CardContent>
              <FinancialInboxWidget />
            </CardContent>
          </Card>
        </div>
      </div>

      {/* WEALTH SECTION */}
      <section>
        <h2 className="text-sm font-medium text-muted-foreground mb-3 uppercase tracking-wider">Wealth</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">Net Worth</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-2xl font-bold">{formatINR(data.net_cash_flow_paise)}</p>
              <p className="text-xs text-muted-foreground mt-1">Assets - Liabilities</p>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">Cash Position</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-2xl font-bold">{formatINR(50000)}</p>
              <p className="text-xs text-muted-foreground mt-1">1 month ago: ₹3.8L</p>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">Accounts</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-2xl font-bold">4</p>
              <p className="text-xs text-muted-foreground mt-1">All synced</p>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">Investments</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-2xl font-bold">6</p>
              <p className="text-xs text-green-500 mt-1 flex items-center gap-1">
                <TrendingUp className="h-3 w-3" />
                +8.2% YTD
              </p>
            </CardContent>
          </Card>
        </div>
      </section>

      {/* BORROWING SECTION */}
      <section>
        <h2 className="text-sm font-medium text-muted-foreground mb-3 uppercase tracking-wider">Borrowing</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">Total Borrowing</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-2xl font-bold">{formatINR(1250000)}</p>
              <p className="text-xs text-muted-foreground mt-1">EMI: ₹15,200/mo</p>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">Home Loan</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-2xl font-bold">₹12.5L left</p>
              <p className="text-xs text-muted-foreground mt-1">12.5% interest</p>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">Credit Cards</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-2xl font-bold">₹8.2K due</p>
              <p className="text-xs text-amber-500 mt-1">Due: 3 days</p>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">Debt Health</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-2xl font-bold text-green-600">Healthy</p>
              <p className="text-xs text-muted-foreground mt-1">EMI ratio: 38%</p>
            </CardContent>
          </Card>
        </div>
      </section>

      {/* SPENDING SECTION */}
      <section>
        <h2 className="text-sm font-medium text-muted-foreground mb-3 uppercase tracking-wider">Spending</h2>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2">
            <ErrorBoundary componentName="Cashflow Chart">
              <CashflowChart />
            </ErrorBoundary>
          </div>
          <div>
            <ErrorBoundary componentName="Category Spend Chart">
              <CategorySpendChart />
            </ErrorBoundary>
          </div>
        </div>
      </section>

      {/* JOURNEY SECTION */}
      <section>
        <h2 className="text-sm font-medium text-muted-foreground mb-3 uppercase tracking-wider">Journey</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">Recent Transactions</CardTitle>
            </CardHeader>
            <CardContent>
              <RecentTransactions transactions={data.recent_transactions.slice(0, 5)} />
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">Financial Health Score</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-baseline gap-2">
                <span className="text-3xl font-bold">{data.financial_health_score}</span>
                <span className="text-sm text-muted-foreground">/100</span>
              </div>
              <p className="text-xs text-muted-foreground mt-2">
                Cashflow: stable | Debt: healthy | Savings: adequate
              </p>
            </CardContent>
          </Card>
        </div>
      </section>
    </div>
  );
}