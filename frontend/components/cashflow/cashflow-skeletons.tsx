"use client";

/**
 * Cash Flow Skeletons
 * ===================
 *
 * Loading states for Cash Flow components.
 * Matches exact dimensions to prevent layout shift (CLS).
 */

import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";

/**
 * Summary Cards Skeleton - Four metric cards
 */
export function CashflowSummarySkeleton() {
  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
      {[1, 2, 3, 4].map((i) => (
        <Card key={i}>
          <CardContent className="p-4 space-y-2">
            <Skeleton className="h-3 w-24" />
            <Skeleton className="h-8 w-28" />
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

/**
 * Best/Worst Month Cards Skeleton
 */
export function BestWorstMonthSkeleton() {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      <Card>
        <CardContent className="p-4 flex items-center justify-between">
          <div className="space-y-2">
            <Skeleton className="h-3 w-20" />
            <Skeleton className="h-6 w-24" />
          </div>
          <Skeleton className="h-8 w-8 rounded" />
        </CardContent>
      </Card>
      <Card>
        <CardContent className="p-4 flex items-center justify-between">
          <div className="space-y-2">
            <Skeleton className="h-3 w-20" />
            <Skeleton className="h-6 w-24" />
          </div>
          <Skeleton className="h-8 w-8 rounded" />
        </CardContent>
      </Card>
    </div>
  );
}

/**
 * Chart Skeleton - For cash flow visualization
 */
export function CashflowChartSkeleton() {
  return (
    <Card className="h-[400px]">
      <CardHeader className="pb-2">
        <Skeleton className="h-5 w-48" />
      </CardHeader>
      <CardContent className="h-[320px] flex items-end justify-center">
        <div className="w-full space-y-2">
          {/* Simulated bar chart */}
          <div className="flex items-end justify-around h-[250px] gap-2">
            <div className="flex flex-col items-center gap-2">
              <Skeleton className="h-[60%] w-8 bg-green-200 dark:bg-green-900/30" />
              <Skeleton className="h-[40%] w-8 bg-red-200 dark:bg-red-900/30" />
            </div>
            <div className="flex flex-col items-center gap-2">
              <Skeleton className="h-[70%] w-8 bg-green-200 dark:bg-green-900/30" />
              <Skeleton className="h-[45%] w-8 bg-red-200 dark:bg-red-900/30" />
            </div>
            <div className="flex flex-col items-center gap-2">
              <Skeleton className="h-[55%] w-8 bg-green-200 dark:bg-green-900/30" />
              <Skeleton className="h-[50%] w-8 bg-red-200 dark:bg-red-900/30" />
            </div>
            <div className="flex flex-col items-center gap-2">
              <Skeleton className="h-[80%] w-8 bg-green-200 dark:bg-green-900/30" />
              <Skeleton className="h-[35%] w-8 bg-red-200 dark:bg-red-900/30" />
            </div>
            <div className="flex flex-col items-center gap-2">
              <Skeleton className="h-[65%] w-8 bg-green-200 dark:bg-green-900/30" />
              <Skeleton className="h-[55%] w-8 bg-red-200 dark:bg-red-900/30" />
            </div>
            <div className="flex flex-col items-center gap-2">
              <Skeleton className="h-[75%] w-8 bg-green-200 dark:bg-green-900/30" />
              <Skeleton className="h-[42%] w-8 bg-red-200 dark:bg-red-900/30" />
            </div>
          </div>
          <Skeleton className="h-4 w-full" />
        </div>
      </CardContent>
    </Card>
  );
}

/**
 * Monthly Breakdown Skeleton - For income/expense breakdown
 */
export function MonthlyBreakdownSkeleton() {
  return (
    <Card className="h-[400px]">
      <CardHeader className="pb-2 flex flex-row items-center justify-between">
        <Skeleton className="h-5 w-32" />
        <Skeleton className="h-9 w-32" />
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Income Column */}
          <div className="space-y-3">
            <Skeleton className="h-4 w-24" />
            <div className="space-y-2">
              {[1, 2, 3, 4].map((i) => (
                <div key={i} className="flex justify-between items-center">
                  <Skeleton className="h-4 w-24" />
                  <Skeleton className="h-4 w-20" />
                </div>
              ))}
            </div>
          </div>
          {/* Expense Column */}
          <div className="space-y-3">
            <Skeleton className="h-4 w-24" />
            <div className="space-y-2">
              {[1, 2, 3, 4].map((i) => (
                <div key={i} className="flex justify-between items-center">
                  <Skeleton className="h-4 w-24" />
                  <Skeleton className="h-4 w-20" />
                </div>
              ))}
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

/**
 * Monthly Comparison Table Skeleton
 */
export function MonthlyComparisonSkeleton() {
  return (
    <Card>
      <CardHeader className="pb-2">
        <Skeleton className="h-5 w-48" />
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {/* Header */}
          <div className="flex justify-between items-center pb-2 border-b">
            <Skeleton className="h-4 w-24" />
            <div className="flex gap-8">
              <Skeleton className="h-4 w-20" />
              <Skeleton className="h-4 w-20" />
              <Skeleton className="h-4 w-16" />
            </div>
          </div>
          {/* Rows */}
          {[1, 2, 3, 4, 5].map((i) => (
            <div key={i} className="flex justify-between items-center py-2">
              <Skeleton className="h-4 w-28" />
              <div className="flex gap-8">
                <Skeleton className="h-4 w-20" />
                <Skeleton className="h-4 w-20" />
                <Skeleton className="h-4 w-16" />
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
