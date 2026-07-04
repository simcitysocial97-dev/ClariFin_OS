"use client";

/**
 * Net Worth Page
 * ==============
 *
 * Modular, Suspense-driven architecture using the new networth components.
 * No data fetching in page.tsx - pure layout container.
 */

import { Suspense } from "react";
import { ErrorBoundary } from "@/components/error-boundary";
import { WidgetErrorFallback } from "@/components/dashboard/widget-error-fallback";

// Import new modular components
import { NetWorthHeader } from "@/components/networth/networth-header";
import { AssetsLiabilitiesColumns } from "@/components/networth/assets-liabilities-columns";
import { NetWorthHistoryChart } from "@/components/networth/networth-history-chart";

// Import skeletons for loading states
import {
  NetWorthHeaderSkeleton,
  AssetsLiabilitiesSkeleton,
  NetWorthHistorySkeleton,
  AssetAllocationSkeleton,
} from "@/components/networth/networth-skeletons";

// Import Asset Allocation from dashboard (reused component)
import { AssetAllocationWidget } from "@/components/dashboard/asset-allocation-widget";

// ============================================================
// Component Wrappers with Error Boundaries
// ============================================================

function HeaderSection() {
  return (
    <ErrorBoundary
      fallback={
        <WidgetErrorFallback
          title="Net Worth Summary"
          error="Failed to load net worth data"
        />
      }
    >
      <Suspense fallback={<NetWorthHeaderSkeleton />}>
        <NetWorthHeader />
      </Suspense>
    </ErrorBoundary>
  );
}

function AssetsLiabilitiesSection() {
  return (
    <ErrorBoundary
      fallback={
        <WidgetErrorFallback
          title="Assets & Liabilities"
          error="Failed to load account details"
        />
      }
    >
      <Suspense fallback={<AssetsLiabilitiesSkeleton />}>
        <AssetsLiabilitiesColumns />
      </Suspense>
    </ErrorBoundary>
  );
}

function HistoryChartSection() {
  return (
    <ErrorBoundary
      fallback={
        <WidgetErrorFallback
          title="Net Worth History"
          error="Failed to load historical data"
        />
      }
    >
      <Suspense fallback={<NetWorthHistorySkeleton />}>
        <NetWorthHistoryChart months={24} />
      </Suspense>
    </ErrorBoundary>
  );
}

function AssetAllocationSection() {
  return (
    <ErrorBoundary
      fallback={
        <WidgetErrorFallback
          title="Asset Allocation"
          error="Failed to load allocation data"
        />
      }
    >
      <Suspense fallback={<AssetAllocationSkeleton />}>
        <AssetAllocationWidget />
      </Suspense>
    </ErrorBoundary>
  );
}

// ============================================================
// Main Page Component
// ============================================================

export default function NetWorthPage() {
  return (
    <div className="container mx-auto py-6 space-y-6 max-w-7xl">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Net Worth</h1>
          <p className="text-sm text-muted-foreground">
            Track your assets, liabilities, and overall financial position
          </p>
        </div>
      </div>

      {/* Hero Section: Net Worth Summary */}
      <section>
        <HeaderSection />
      </section>

      {/* Assets & Liabilities Breakdown */}
      <section>
        <AssetsLiabilitiesSection />
      </section>

      {/* Charts Row: History + Allocation */}
      <section className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Net Worth History Chart (takes 2/3 on large screens) */}
        <div className="lg:col-span-2">
          <HistoryChartSection />
        </div>

        {/* Asset Allocation (takes 1/3 on large screens) */}
        <div className="lg:col-span-1">
          <AssetAllocationSection />
        </div>
      </section>
    </div>
  );
}
