"use client";

/**
 * Recurring Page
 * ==============
 *
 * Modular, Suspense-driven architecture for managing recurring transactions.
 * No data fetching in page.tsx - pure layout container.
 */

import { Suspense } from "react";
import { ErrorBoundary } from "@/components/error-boundary";
import { WidgetErrorFallback } from "@/components/dashboard/widget-error-fallback";

// Import modular components
import { MonthlyObligationsSummary } from "@/components/recurring/monthly-obligations-summary";
import { UpcomingBillsTimeline } from "@/components/recurring/upcoming-bills-timeline";
import { SubscriptionsTable } from "@/components/recurring/subscriptions-table";

// Import skeletons
import {
  ObligationsSummarySkeleton,
  TimelineSkeleton,
  SubscriptionsTableSkeleton,
} from "@/components/recurring/recurring-skeletons";

// ============================================================
// Component Wrappers with Error Boundaries
// ============================================================

function ObligationsSection() {
  return (
    <ErrorBoundary
      fallback={
        <WidgetErrorFallback
          title="Monthly Obligations"
          error="Failed to load obligations data"
        />
      }
    >
      <Suspense fallback={<ObligationsSummarySkeleton />}>
        <MonthlyObligationsSummary />
      </Suspense>
    </ErrorBoundary>
  );
}

function TimelineSection() {
  return (
    <ErrorBoundary
      fallback={
        <WidgetErrorFallback
          title="Upcoming Bills"
          error="Failed to load upcoming bills"
        />
      }
    >
      <Suspense fallback={<TimelineSkeleton />}>
        <UpcomingBillsTimeline />
      </Suspense>
    </ErrorBoundary>
  );
}

function SubscriptionsSection() {
  return (
    <ErrorBoundary
      fallback={
        <WidgetErrorFallback
          title="Subscriptions"
          error="Failed to load subscriptions"
        />
      }
    >
      <Suspense fallback={<SubscriptionsTableSkeleton />}>
        <SubscriptionsTable />
      </Suspense>
    </ErrorBoundary>
  );
}

// ============================================================
// Main Page Component
// ============================================================

export default function RecurringPage() {
  return (
    <div className="container mx-auto py-6 space-y-6 max-w-7xl">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Recurring Obligations</h1>
          <p className="text-sm text-muted-foreground mt-1">
            Track subscriptions, bills, and recurring payments
          </p>
        </div>
      </div>

      {/* Monthly Obligations Summary */}
      <section>
        <ObligationsSection />
      </section>

      {/* Upcoming Bills Timeline */}
      <section>
        <TimelineSection />
      </section>

      {/* All Subscriptions Table */}
      <section>
        <SubscriptionsSection />
      </section>
    </div>
  );
}
