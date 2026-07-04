"use client";

/**
 * Income Page
 * ===========
 *
 * Modular, Suspense-driven architecture for managing income sources.
 * No data fetching in page.tsx - pure layout container.
 */

import { Suspense } from "react";
import { ErrorBoundary } from "@/components/error-boundary";
import { WidgetErrorFallback } from "@/components/dashboard/widget-error-fallback";

// Import modular components
import { IncomeSummaryCards } from "@/components/income/income-summary-cards";
import { IncomeStreamsTable } from "@/components/income/income-streams-table";
import { IncomeTrendChart } from "@/components/income/income-trend-chart";

// Import skeletons
import {
  IncomeSummarySkeleton,
  IncomeStreamsSkeleton,
  IncomeTrendSkeleton,
} from "@/components/income/income-skeletons";

// ============================================================
// Component Wrappers with Error Boundaries
// ============================================================

function SummarySection() {
  return (
    <ErrorBoundary
      fallback={
        <WidgetErrorFallback
          title="Income Summary"
          error="Failed to load income summary"
        />
      }
    >
      <Suspense fallback={<IncomeSummarySkeleton />}>
        <IncomeSummaryCards />
      </Suspense>
    </ErrorBoundary>
  );
}

function TrendSection() {
  return (
    <ErrorBoundary
      fallback={
        <WidgetErrorFallback
          title="Income Trend"
          error="Failed to load income trend"
        />
      }
    >
      <Suspense fallback={<IncomeTrendSkeleton />}>
        <IncomeTrendChart />
      </Suspense>
    </ErrorBoundary>
  );
}

function StreamsSection() {
  return (
    <ErrorBoundary
      fallback={
        <WidgetErrorFallback
          title="Income Streams"
          error="Failed to load income streams"
        />
      }
    >
      <Suspense fallback={<IncomeStreamsSkeleton />}>
        <IncomeStreamsTable />
      </Suspense>
    </ErrorBoundary>
  );
}

// ============================================================
// Main Page Component
// ============================================================

export default function IncomePage() {
  return (
    <div className="container mx-auto py-6 space-y-6 max-w-7xl">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Income Sources</h1>
          <p className="text-sm text-muted-foreground mt-1">
            Track and analyze your income streams
          </p>
        </div>
      </div>

      {/* Income Summary Cards */}
      <section>
        <SummarySection />
      </section>

      {/* Charts Row */}
      <section className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <TrendSection />
      </section>

      {/* Income Streams Table */}
      <section>
        <StreamsSection />
      </section>
    </div>
  );
}
