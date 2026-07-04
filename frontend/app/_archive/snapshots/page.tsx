"use client";

/**
 * Snapshots Page
 * ==============
 *
 * Modular, Suspense-driven architecture for the snapshot engine.
 * No data fetching in page.tsx - pure layout container.
 */

import { Suspense } from "react";
import { ErrorBoundary } from "@/components/error-boundary";
import { WidgetErrorFallback } from "@/components/dashboard/widget-error-fallback";

// Import modular components
import { SnapshotTriggerCard } from "@/components/snapshots/snapshot-trigger-card";
import { SnapshotHistoryTable } from "@/components/snapshots/snapshot-history-table";

// Import skeletons
import {
  SnapshotTriggerSkeleton,
  SnapshotHistorySkeleton,
} from "@/components/snapshots/snapshots-skeletons";

// ============================================================
// Component Wrappers with Error Boundaries
// ============================================================

function TriggerSection() {
  return (
    <ErrorBoundary
      fallback={
        <WidgetErrorFallback
          title="Snapshot Controls"
          error="Failed to load snapshot controls"
        />
      }
    >
      <Suspense fallback={<SnapshotTriggerSkeleton />}>
        <SnapshotTriggerCard />
      </Suspense>
    </ErrorBoundary>
  );
}

function HistorySection() {
  return (
    <ErrorBoundary
      fallback={
        <WidgetErrorFallback
          title="Snapshot History"
          error="Failed to load snapshot history"
        />
      }
    >
      <Suspense fallback={<SnapshotHistorySkeleton />}>
        <SnapshotHistoryTable />
      </Suspense>
    </ErrorBoundary>
  );
}

// ============================================================
// Main Page Component
// ============================================================

export default function SnapshotsPage() {
  return (
    <div className="container mx-auto py-6 space-y-6 max-w-7xl">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Monthly Snapshots</h1>
          <p className="text-sm text-muted-foreground mt-1">
            Capture and review historical financial states
          </p>
        </div>
      </div>

      {/* Snapshot Trigger Card */}
      <section className="max-w-2xl">
        <TriggerSection />
      </section>

      {/* Snapshot History Table */}
      <section>
        <HistorySection />
      </section>
    </div>
  );
}
