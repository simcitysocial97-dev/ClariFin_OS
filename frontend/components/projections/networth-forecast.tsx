"use client";

/**
 * Net Worth Forecast Component
 * ============================
 * Tab 1: Displays net worth projection with duration selector and milestones
 */

import { useState, useMemo } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { TrendingUp, Target, Percent } from "lucide-react";
import { useNetWorthProjection } from "@/lib/hooks/use-finance-data";
import { formatPaiseCompact } from "@/lib/format";
import { ProjectionChart } from "./projection-chart";

const DURATIONS = [
  { label: "1 Year", months: 12 },
  { label: "3 Years", months: 36 },
  { label: "5 Years", months: 60 },
  { label: "10 Years", months: 120 },
];

export function NetWorthForecast() {
  const [selectedDuration, setSelectedDuration] = useState(60); // Default 5 years
  const { data, loading, error } = useNetWorthProjection();

  const chartData = useMemo(() => {
    if (!data?.projections) return [];
    return data.projections.map((p) => ({
      month: p.month,
      "Projected Assets": p.projected_assets_paise,
      "Projected Liabilities": p.projected_liabilities_paise,
      "Projected Net Worth": p.projected_net_worth_paise,
    }));
  }, [data]);

  const milestone = useMemo(() => {
    if (!data?.projections) return null;
    const oneCrore = 10000000; // 1 Crore in paise
    const hit = data.projections.find((p) => p.projected_net_worth_paise >= oneCrore);
    if (hit) {
      const date = new Date(hit.month);
      return date.toLocaleDateString("en-IN", { month: "long", year: "numeric" });
    }
    return null;
  }, [data]);

  const summary = data?.summary;
  const assumptions = data?.assumptions;

  if (loading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-10 w-96" />
        <Skeleton className="h-96" />
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Skeleton className="h-32" />
          <Skeleton className="h-32" />
          <Skeleton className="h-32" />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <Card className="p-8 text-center">
        <p className="text-destructive">Failed to load projection data</p>
        <p className="text-muted-foreground text-sm mt-2">{error.message}</p>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Duration Selector */}
      <div className="flex flex-wrap gap-2">
        {DURATIONS.map((duration) => (
          <Button
            key={duration.months}
            variant={selectedDuration === duration.months ? "default" : "outline"}
            size="sm"
            onClick={() => setSelectedDuration(duration.months)}
          >
            {duration.label}
          </Button>
        ))}
      </div>

      {/* Milestone Alert */}
      {milestone && (
        <div className="bg-gradient-to-r from-primary/10 to-primary/5 border border-primary/20 rounded-lg p-4 flex items-center gap-4">
          <div className="bg-primary/10 p-3 rounded-full">
            <Target className="h-6 w-6 text-primary" />
          </div>
          <div>
            <p className="font-semibold text-lg">
              You&apos;ll reach ₹1 Crore net worth by
            </p>
            <p className="text-primary font-bold text-xl">{milestone}</p>
          </div>
        </div>
      )}

      {/* Chart */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <TrendingUp className="h-5 w-5" />
            Net Worth Projection
          </CardTitle>
        </CardHeader>
        <CardContent>
          <ProjectionChart
            data={chartData}
            lines={[
              {
                key: "Projected Assets",
                name: "Assets",
                color: "#22c55e",
                type: "area",
              },
              {
                key: "Projected Liabilities",
                name: "Liabilities",
                color: "#ef4444",
                type: "line",
              },
              {
                key: "Projected Net Worth",
                name: "Net Worth",
                color: "#3b82f6",
                type: "line",
                strokeWidth: 3,
              },
            ]}
            height={400}
          />
        </CardContent>
      </Card>

      {/* Summary Cards */}
      {summary && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Card>
            <CardContent className="pt-6">
              <p className="text-sm text-muted-foreground">Starting Net Worth</p>
              <p className="text-2xl font-bold">
                {formatPaiseCompact(summary.starting_net_worth_paise)}
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <p className="text-sm text-muted-foreground">Projected Ending</p>
              <p className="text-2xl font-bold text-primary">
                {formatPaiseCompact(summary.ending_net_worth_paise)}
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <p className="text-sm text-muted-foreground">Total Growth</p>
              <p
                className={`text-2xl font-bold ${
                  summary.net_worth_change_paise >= 0
                    ? "text-green-500"
                    : "text-red-500"
                }`}
              >
                {summary.net_worth_change_paise >= 0 ? "+" : ""}
                {formatPaiseCompact(summary.net_worth_change_paise)}
              </p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Assumptions */}
      {assumptions && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <Percent className="h-4 w-4" />
              Projection Assumptions
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
              <div>
                <p className="text-muted-foreground">Equity Return</p>
                <p className="font-medium">{assumptions.equity_return_percent}%</p>
              </div>
              <div>
                <p className="text-muted-foreground">Debt Return</p>
                <p className="font-medium">{assumptions.debt_return_percent}%</p>
              </div>
              <div>
                <p className="text-muted-foreground">Savings Basis</p>
                <p className="font-medium capitalize">{assumptions.savings_basis}</p>
              </div>
              <div>
                <p className="text-muted-foreground">Compounding</p>
                <p className="font-medium">
                  {assumptions.monthly_compounding ? "Monthly" : "Annual"}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
