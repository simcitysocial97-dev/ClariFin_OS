"use client";

/**
 * Widget Skeletons
 * ================
 * 
 * Skeleton loading states for all dashboard widgets.
 * Matches exact dimensions to prevent layout shift (CLS).
 */

import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";

/**
 * Metric Card Skeleton - Small compact card for metrics
 */
export function MetricCardSkeleton() {
  return (
    <Card>
      <CardContent className="p-4">
        <div className="flex items-start justify-between">
          <div className="flex-1 space-y-2">
            <Skeleton className="h-3 w-20" />
            <Skeleton className="h-6 w-24" />
            <Skeleton className="h-3 w-16" />
          </div>
          <Skeleton className="h-8 w-8 rounded-md" />
        </div>
      </CardContent>
    </Card>
  );
}

/**
 * Metrics Row Skeleton - 4 metric cards in a row
 */
export function MetricsRowSkeleton() {
  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
      <MetricCardSkeleton />
      <MetricCardSkeleton />
      <MetricCardSkeleton />
      <MetricCardSkeleton />
    </div>
  );
}

/**
 * Chart Widget Skeleton - For bar, line, area charts
 */
export function ChartWidgetSkeleton() {
  return (
    <Card className="h-[320px]">
      <CardHeader className="pb-2">
        <Skeleton className="h-5 w-32" />
      </CardHeader>
      <CardContent className="h-[250px] flex items-end justify-center">
        <div className="w-full space-y-2">
          <div className="flex items-end justify-around h-[200px] gap-2">
            <Skeleton className="h-[40%] w-8" />
            <Skeleton className="h-[60%] w-8" />
            <Skeleton className="h-[80%] w-8" />
            <Skeleton className="h-[50%] w-8" />
            <Skeleton className="h-[70%] w-8" />
            <Skeleton className="h-[45%] w-8" />
          </div>
          <Skeleton className="h-4 w-full" />
        </div>
      </CardContent>
    </Card>
  );
}

/**
 * List Widget Skeleton - For lists with items
 */
export function ListWidgetSkeleton() {
  return (
    <Card className="h-[280px]">
      <CardHeader className="pb-2">
        <Skeleton className="h-5 w-32" />
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="flex items-center justify-between">
          <div className="space-y-1">
            <Skeleton className="h-4 w-32" />
            <Skeleton className="h-3 w-20" />
          </div>
          <Skeleton className="h-4 w-16" />
        </div>
        <Skeleton className="h-px w-full" />
        <div className="flex items-center justify-between">
          <div className="space-y-1">
            <Skeleton className="h-4 w-28" />
            <Skeleton className="h-3 w-24" />
          </div>
          <Skeleton className="h-4 w-16" />
        </div>
        <Skeleton className="h-px w-full" />
        <div className="flex items-center justify-between">
          <div className="space-y-1">
            <Skeleton className="h-4 w-36" />
            <Skeleton className="h-3 w-20" />
          </div>
          <Skeleton className="h-4 w-16" />
        </div>
        <Skeleton className="h-px w-full" />
        <div className="flex items-center justify-between">
          <div className="space-y-1">
            <Skeleton className="h-4 w-24" />
            <Skeleton className="h-3 w-28" />
          </div>
          <Skeleton className="h-4 w-16" />
        </div>
      </CardContent>
    </Card>
  );
}

/**
 * Donut Chart Widget Skeleton - For asset allocation
 */
export function DonutChartSkeleton() {
  return (
    <Card className="h-[320px]">
      <CardHeader className="pb-2">
        <Skeleton className="h-5 w-32" />
      </CardHeader>
      <CardContent className="flex flex-col items-center">
        <Skeleton className="h-[140px] w-[140px] rounded-full" />
        <div className="mt-4 grid grid-cols-2 gap-x-8 gap-y-2 w-full">
          <div className="flex items-center gap-2">
            <Skeleton className="h-3 w-3 rounded-full" />
            <Skeleton className="h-3 w-16" />
          </div>
          <div className="flex items-center gap-2">
            <Skeleton className="h-3 w-3 rounded-full" />
            <Skeleton className="h-3 w-16" />
          </div>
          <div className="flex items-center gap-2">
            <Skeleton className="h-3 w-3 rounded-full" />
            <Skeleton className="h-3 w-16" />
          </div>
          <div className="flex items-center gap-2">
            <Skeleton className="h-3 w-3 rounded-full" />
            <Skeleton className="h-3 w-16" />
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

/**
 * Area Chart Widget Skeleton - For net worth trend
 */
export function AreaChartSkeleton() {
  return (
    <Card className="h-[320px]">
      <CardHeader className="pb-2">
        <Skeleton className="h-5 w-32" />
      </CardHeader>
      <CardContent className="h-[250px]">
        <svg className="w-full h-full" viewBox="0 0 400 200">
          <Skeleton className="w-full h-full" />
        </svg>
      </CardContent>
    </Card>
  );
}
