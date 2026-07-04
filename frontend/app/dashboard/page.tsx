"use client";

/**
 * Dashboard Page - Personal Finance MVP v1.0.0
 * =================================================
 * 
 * Simplified single-mode dashboard answering 4 questions:
 * 1. Net Cash Flow
 * 2. Savings Rate %
 * 3. EMI Ratio %
 * 4. Buffer Days
 * 
 * No mode system. No localStorage fallback.
 * Backend is sole source of truth.
 */

import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { AlertTriangle, TrendingUp, TrendingDown, PiggyBank, Home, Shield, Activity } from "lucide-react";
import { RecentTransactions } from "@/components/dashboard/recent-transactions";
// ============================================================
// Types
// ============================================================

interface DashboardData {
  net_cash_flow: number;
  savings_rate: number;
  emi_ratio: number;
  buffer_days: number;
  financial_health_score: number;
  seven_day_trend: number;
  category_drift_alert: string | null;
  recent_transactions: any[];
}

// ============================================================
// Utility Functions
// ============================================================

function formatINR(amount: number): string {
  if (amount === 0) return "₹0";
  const negative = amount < 0;
  const absAmount = Math.abs(amount);
  const formatted = new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0,
  }).format(absAmount);
  return negative ? `-${formatted}` : formatted;
}

function formatPercent(value: number): string {
  return `${(value * 100).toFixed(0)}%`;
}

// ============================================================
// Components
// ============================================================

function NetCashFlowCard({ amount }: { amount: number }) {
  const isPositive = amount >= 0;
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
            {formatINR(amount)}
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
            {formatPercent(rate)}
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
            {formatPercent(ratio)}
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
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchData() {
      try {
        const response = await fetch("http://localhost:8000/api/dashboard/summary");
        if (!response.ok) {
          throw new Error("Failed to fetch dashboard data");
        }
        const dashboardData = await response.json();
        setData(dashboardData);
      } catch (err) {
        setError(err instanceof Error ? err.message : "An error occurred");
      } finally {
        setLoading(false);
      }
    }

    fetchData();
  }, []);

  // Loading state
  if (loading) {
    return (
      <div className="container mx-auto py-6 space-y-6">
        <Skeleton className="h-8 w-48" />
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <Skeleton key={i} className="h-32" />
          ))}
        </div>
        <Skeleton className="h-48" />
      </div>
    );
  }

  // Error state - BLOCKING (no fallback)
  if (error) {
    return (
      <div className="container mx-auto py-6">
        <Alert variant="destructive" className="mb-4">
          <AlertTriangle className="h-4 w-4" />
          <AlertTitle>Unable to Load Dashboard</AlertTitle>
          <AlertDescription>
            {error}. Please ensure the backend server is running at http://localhost:8000
          </AlertDescription>
        </Alert>
        <Card className="p-6 text-center">
          <p className="text-gray-600 mb-4">
            The dashboard requires a connection to the backend server.
          </p>
          <p className="text-sm text-gray-500">
            Start the backend with: <code className="bg-gray-100 px-2 py-1 rounded">cd backend && uvicorn src.api:app --reload --port 8000</code>
          </p>
        </Card>
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
      <div>
        <h1 className="text-2xl font-bold">Financial Dashboard</h1>
        <p className="text-gray-500 text-sm">Your personal finance overview</p>
      </div>

      {/* Primary Metrics - 4 Key Numbers */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <NetCashFlowCard amount={data.net_cash_flow} />
        <SavingsRateCard rate={data.savings_rate} />
        <EMIRatioCard ratio={data.emi_ratio} />
        <BufferDaysCard days={data.buffer_days} />
      </div>

      {/* Secondary Row - Trend & Alerts */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <SevenDayTrend trend={data.seven_day_trend} />
        <CategoryDriftAlert alert={data.category_drift_alert} />
      </div>

      {/* Recent Transactions */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg font-semibold">Recent Transactions</CardTitle>
        </CardHeader>
        <CardContent>
          <RecentTransactions transactions={data.recent_transactions.slice(0, 10)} />
        </CardContent>
      </Card>

      {/* Footer - Health Score */}
      <HealthScoreFooter score={data.financial_health_score} />
    </div>
  );
}
