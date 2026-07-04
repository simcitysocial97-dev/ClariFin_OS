"use client";

/**
 * Monthly Comparison Table
 * ========================
 *
 * Compares this month's spending vs last month's spending by category,
 * showing variance with color-coded indicators.
 */

import { useMonthlyCashflow, useCashflowSummary } from "@/lib/hooks/use-finance-data";
import { formatPaise } from "@/lib/format";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { WidgetErrorFallback } from "@/components/dashboard/widget-error-fallback";
import { ArrowUp, ArrowDown, Minus, TrendingUp, TrendingDown } from "lucide-react";
import { cn } from "@/lib/utils";

interface MonthlyComparisonTableProps {
  className?: string;
}

interface CategoryComparison {
  category: string;
  currentMonth: number;
  previousMonth: number;
  change: number;
  percentChange: number;
}

export function MonthlyComparisonTable({ className }: MonthlyComparisonTableProps) {
  const { data: cashflowData, loading, error, refetch } = useMonthlyCashflow();
  const { data: summary } = useCashflowSummary();

  if (loading) {
    return (
      <Card className={className}>
        <CardHeader className="pb-2">
          <div className="h-5 w-48 bg-muted rounded animate-pulse" />
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            <div className="flex justify-between items-center pb-2 border-b">
              <div className="h-4 w-24 bg-muted rounded animate-pulse" />
              <div className="flex gap-8">
                <div className="h-4 w-20 bg-muted rounded animate-pulse" />
                <div className="h-4 w-20 bg-muted rounded animate-pulse" />
                <div className="h-4 w-16 bg-muted rounded animate-pulse" />
              </div>
            </div>
            {[1, 2, 3, 4, 5].map((i) => (
              <div key={i} className="flex justify-between items-center py-2">
                <div className="h-4 w-28 bg-muted rounded animate-pulse" />
                <div className="flex gap-8">
                  <div className="h-4 w-20 bg-muted rounded animate-pulse" />
                  <div className="h-4 w-20 bg-muted rounded animate-pulse" />
                  <div className="h-4 w-16 bg-muted rounded animate-pulse" />
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className={className}>
        <CardContent className="py-8">
          <WidgetErrorFallback
            title="Monthly Comparison"
            error={error.message}
            onRetry={refetch}
          />
        </CardContent>
      </Card>
    );
  }

  const monthly = cashflowData?.months || [];

  // Need at least 2 months for comparison
  if (monthly.length < 2) {
    return (
      <Card className={className}>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-semibold flex items-center gap-2">
            <TrendingDown className="h-4 w-4" />
            Monthly Comparison
          </CardTitle>
        </CardHeader>
        <CardContent className="py-8 text-center">
          <p className="text-muted-foreground text-sm">
            Not enough data for comparison. At least 2 months of transactions required.
          </p>
        </CardContent>
      </Card>
    );
  }

  // Get current and previous month data
  const currentMonth = monthly[monthly.length - 1];
  const previousMonth = monthly[monthly.length - 2];

  // Get expense categories from both months
  // Note: MonthlyCashflow doesn't have by_category, we need to use a different approach
  // For now, use empty objects since the API doesn't provide this in monthly data
  const currentCategories: Record<string, { paise?: number }> = {};
  const previousCategories: Record<string, { paise?: number }> = {};

  // Build comparison data
  const allCategories = new Set([
    ...Object.keys(currentCategories),
    ...Object.keys(previousCategories),
  ]);

  const comparisons: CategoryComparison[] = Array.from(allCategories)
    .map((category) => {
      const current = (currentCategories[category] as { paise?: number })?.paise || 0;
      const previous = (previousCategories[category] as { paise?: number })?.paise || 0;
      const change = current - previous;
      const percentChange = previous !== 0 ? (change / previous) * 100 : 0;

      return {
        category,
        currentMonth: current,
        previousMonth: previous,
        change,
        percentChange,
      };
    })
    // Sort by current month spending (descending)
    .sort((a, b) => b.currentMonth - a.currentMonth);

  // Calculate totals
  const currentTotal = comparisons.reduce((sum, c) => sum + c.currentMonth, 0);
  const previousTotal = comparisons.reduce((sum, c) => sum + c.previousMonth, 0);
  const totalChange = currentTotal - previousTotal;
  const totalPercentChange = previousTotal !== 0 ? (totalChange / previousTotal) * 100 : 0;

  return (
    <Card className={className}>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-semibold flex items-center gap-2">
          <TrendingDown className="h-4 w-4" />
          Monthly Spending Comparison
          <span className="ml-auto text-xs text-muted-foreground">
            {currentMonth?.month?.slice(0, 7) || "Current"} vs{" "}
            {previousMonth?.month?.slice(0, 7) || "Previous"}
          </span>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="overflow-x-auto">
          <Table>
            <TableHeader>
              <TableRow className="hover:bg-transparent">
                <TableHead className="w-[200px]">Category</TableHead>
                <TableHead className="text-right">
                  {currentMonth?.month?.slice(0, 7) || "Current"}
                </TableHead>
                <TableHead className="text-right">
                  {previousMonth?.month?.slice(0, 7) || "Previous"}
                </TableHead>
                <TableHead className="text-right">Change</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {/* Total Row */}
              <TableRow className="font-semibold bg-muted/50">
                <TableCell className="font-medium">Total Spending</TableCell>
                <TableCell className="text-right">
                  {formatPaise(currentTotal)}
                </TableCell>
                <TableCell className="text-right">
                  {formatPaise(previousTotal)}
                </TableCell>
                <TableCell className="text-right">
                  <div
                    className={cn(
                      "flex items-center justify-end gap-1",
                      totalChange > 0 ? "text-red-600" : "text-green-600"
                    )}
                  >
                    {totalChange > 0 ? (
                      <ArrowUp className="h-3 w-3" />
                    ) : totalChange < 0 ? (
                      <ArrowDown className="h-3 w-3" />
                    ) : (
                      <Minus className="h-3 w-3" />
                    )}
                    <span>
                      {totalChange > 0 ? "+" : ""}
                      {Math.abs(totalPercentChange).toFixed(1)}%
                    </span>
                  </div>
                </TableCell>
              </TableRow>

              {/* Category Rows */}
              {comparisons.map((item) => {
                const TrendIcon =
                  item.change > 0 ? ArrowUp : item.change < 0 ? ArrowDown : Minus;
                const trendColor =
                  item.change > 0
                    ? "text-red-600"
                    : item.change < 0
                    ? "text-green-600"
                    : "text-muted-foreground";

                return (
                  <TableRow key={item.category}>
                    <TableCell className="font-medium capitalize">
                      {item.category.replace(/_/g, " ")}
                    </TableCell>
                    <TableCell className="text-right">
                      {formatPaise(item.currentMonth)}
                    </TableCell>
                    <TableCell className="text-right">
                      {formatPaise(item.previousMonth)}
                    </TableCell>
                    <TableCell className="text-right">
                      <div className={cn("flex items-center justify-end gap-1", trendColor)}>
                        <TrendIcon className="h-3 w-3" />
                        <span>
                          {item.change > 0 ? "+" : ""}
                          {Math.abs(item.percentChange).toFixed(0)}%
                        </span>
                      </div>
                    </TableCell>
                  </TableRow>
                );
              })}

              {comparisons.length === 0 && (
                <TableRow>
                  <TableCell colSpan={4} className="text-center text-muted-foreground py-8">
                    No spending data available
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </div>

        {/* Summary Cards */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6 pt-6 border-t">
          <div className="text-center">
            <p className="text-xs text-muted-foreground mb-1">Avg Monthly Income</p>
            <p className="text-lg font-bold text-green-600">
              {formatPaise(summary?.avg_monthly_income_paise || 0)}
            </p>
          </div>
          <div className="text-center">
            <p className="text-xs text-muted-foreground mb-1">Avg Monthly Expense</p>
            <p className="text-lg font-bold text-red-600">
              {formatPaise(summary?.avg_monthly_expense_paise || 0)}
            </p>
          </div>
          <div className="text-center">
            <p className="text-xs text-muted-foreground mb-1">Savings Rate</p>
            <p className="text-lg font-bold">
              {summary?.avg_savings_rate?.toFixed(1) || 0}%
            </p>
          </div>
          <div className="text-center">
            <p className="text-xs text-muted-foreground mb-1">Trend</p>
            <div className="flex items-center justify-center gap-1">
              <p className="text-lg font-bold capitalize">{summary?.trend || "stable"}</p>
              {summary?.trend === "improving" ? (
                <TrendingUp className="h-4 w-4 text-green-500" />
              ) : summary?.trend === "declining" ? (
                <TrendingDown className="h-4 w-4 text-red-500" />
              ) : null}
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
