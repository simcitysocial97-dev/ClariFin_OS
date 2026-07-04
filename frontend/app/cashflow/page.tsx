"use client";

/**
 * Cash Flow Page
 * ==============
 *
 * Modular, Suspense-driven architecture using the new cashflow components.
 * No data fetching in page.tsx - pure layout container.
 */

import { Suspense } from "react";
import { ErrorBoundary } from "@/components/error-boundary";
import { WidgetErrorFallback } from "@/components/dashboard/widget-error-fallback";

// Import new modular components
import { CashflowChart, CashflowSankeyView } from "@/components/cashflow";
import { MonthlyComparisonTable } from "@/components/cashflow/monthly-comparison-table";

// Import skeletons for loading states
import {
  CashflowChartSkeleton,
  MonthlyComparisonSkeleton,
} from "@/components/cashflow/cashflow-skeletons";

// ============================================================
// Component Wrappers with Error Boundaries
// ============================================================

function CashflowChartSection() {
  return (
    <ErrorBoundary
      fallback={
        <WidgetErrorFallback
          title="Cash Flow Chart"
          error="Failed to load cash flow visualization"
        />
      }
    >
      <Suspense fallback={<CashflowChartSkeleton />}>
        <CashflowChart months={12} />
      </Suspense>
    </ErrorBoundary>
  );
}

function SankeyViewSection() {
  return (
    <ErrorBoundary
      fallback={
        <WidgetErrorFallback
          title="Sankey View"
          error="Failed to load Sankey view"
        />
      }
    >
      <CashflowSankeyView />
    </ErrorBoundary>
  );
}

function MonthlyComparisonSection() {
  return (
    <ErrorBoundary
      fallback={
        <WidgetErrorFallback
          title="Monthly Comparison"
          error="Failed to load monthly comparison data"
        />
      }
    >
      <Suspense fallback={<MonthlyComparisonSkeleton />}>
        <MonthlyComparisonTable />
      </Suspense>
    </ErrorBoundary>
  );
}

// ============================================================
// Main Page Component
// ============================================================

export default function CashflowPage() {
  return (
    <div className="container mx-auto py-6 space-y-6 max-w-7xl">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Cash Flow Analysis</h1>
          <p className="text-sm text-muted-foreground">
            Understand your income, expenses, and savings patterns over time
          </p>
        </div>
      </div>

      {/* Cash Flow Visualization */}
      <section>
        <CashflowChartSection />
      </section>

      {/* Sankey View (Optional) - Not yet implemented */}
      <section>
        <SankeyViewSection />
      </section>

      {/* Monthly Comparison Table */}
      <section>
        <MonthlyComparisonSection />
      </section>
    </div>
  );
}
