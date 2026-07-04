"use client";

/**
 * Net Worth Skeletons
 * ===================
 *
 * Loading states for Net Worth components.
 * Matches exact dimensions to prevent layout shift (CLS).
 */

import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";

/**
 * Header Skeleton - Large hero section placeholder
 */
export function NetWorthHeaderSkeleton() {
  return (
    <div className="text-center py-8 space-y-4">
      <Skeleton className="h-4 w-32 mx-auto" />
      <Skeleton className="h-16 w-64 mx-auto" />
      <div className="flex items-center justify-center gap-4">
        <Skeleton className="h-6 w-32" />
        <Skeleton className="h-6 w-4" />
        <Skeleton className="h-6 w-32" />
      </div>
    </div>
  );
}

/**
 * Assets/Liabilities Card Skeleton - Individual column placeholder
 */
function AssetsLiabilitiesCardSkeleton() {
  return (
    <Card className="h-full">
      <CardHeader className="pb-2">
        <Skeleton className="h-5 w-32" />
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex justify-between items-center">
          <Skeleton className="h-4 w-24" />
          <div className="flex items-center gap-2">
            <Skeleton className="h-4 w-20" />
            <Skeleton className="h-3 w-12" />
          </div>
        </div>
        <Skeleton className="h-px w-full" />
        <div className="flex justify-between items-center">
          <Skeleton className="h-4 w-20" />
          <div className="flex items-center gap-2">
            <Skeleton className="h-4 w-20" />
            <Skeleton className="h-3 w-12" />
          </div>
        </div>
        <Skeleton className="h-px w-full" />
        <div className="flex justify-between items-center">
          <Skeleton className="h-4 w-28" />
          <div className="flex items-center gap-2">
            <Skeleton className="h-4 w-20" />
            <Skeleton className="h-3 w-12" />
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

/**
 * Assets & Liabilities Columns Skeleton - Two-column layout
 */
export function AssetsLiabilitiesSkeleton() {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
      <AssetsLiabilitiesCardSkeleton />
      <AssetsLiabilitiesCardSkeleton />
    </div>
  );
}

/**
 * History Chart Skeleton - Area chart placeholder
 */
export function NetWorthHistorySkeleton() {
  return (
    <Card className="h-[400px]">
      <CardHeader className="pb-2">
        <Skeleton className="h-5 w-40" />
      </CardHeader>
      <CardContent className="h-[320px] flex items-end justify-center">
        <div className="w-full space-y-2">
          {/* Simulated area chart */}
          <svg className="w-full h-[250px]" viewBox="0 0 400 200">
            <defs>
              <linearGradient id="skeletonGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="hsl(var(--muted))" stopOpacity="0.3" />
                <stop offset="100%" stopColor="hsl(var(--muted))" stopOpacity="0" />
              </linearGradient>
            </defs>
            <path
              d="M0,150 Q50,120 100,130 T200,100 T300,80 T400,60 L400,200 L0,200 Z"
              fill="url(#skeletonGradient)"
            />
            <path
              d="M0,150 Q50,120 100,130 T200,100 T300,80 T400,60"
              fill="none"
              stroke="hsl(var(--muted))"
              strokeWidth="2"
              strokeDasharray="5,5"
            />
          </svg>
          <Skeleton className="h-4 w-full" />
        </div>
      </CardContent>
    </Card>
  );
}

/**
 * Asset Allocation Skeleton - Donut chart placeholder
 */
export function AssetAllocationSkeleton() {
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
