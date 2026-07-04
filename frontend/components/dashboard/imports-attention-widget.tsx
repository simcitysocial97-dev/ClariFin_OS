"use client";

/**
 * Imports Attention Widget
 * ========================
 * 
 * Shows imports requiring attention with counts and CTAs:
 * - NEEDS_REVIEW count (missing balances or bbox required)
 * - FAILED count (extraction failures)
 * 
 * Provides quick-action buttons:
 * - "Open Imports Inbox" → /imports
 * - "Import PDF" → /import
 * 
 * Polling: Enabled (60s interval) for real-time attention updates
 */

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useImportsQuery } from "@/lib/hooks/use-query-finance";
import { ListWidgetSkeleton } from "./skeletons";
import { WidgetErrorFallback } from "./widget-error-fallback";
import { AlertTriangle, FileWarning, ArrowRight, Upload, CheckCircle2 } from "lucide-react";
import Link from "next/link";

interface ImportsAttentionWidgetProps {
  mode?: "personal" | "family";
}

export function ImportsAttentionWidget({ mode = "personal" }: ImportsAttentionWidgetProps) {
  // Fetch imports needing review with polling for real-time updates
  const {
    data: needsReviewData,
    loading: needsReviewLoading,
    error: needsReviewError,
    refetch: refetchNeedsReview,
  } = useImportsQuery({ 
    status: "NEEDS_REVIEW", 
    page: 1, 
    per_page: 100,
  });

  // Fetch failed imports with polling for real-time updates
  const {
    data: failedData,
    loading: failedLoading,
    error: failedError,
    refetch: refetchFailed,
  } = useImportsQuery({ 
    status: "FAILED", 
    page: 1, 
    per_page: 100,
  });

  const needsReviewCount = needsReviewData?.total || 0;
  const failedCount = failedData?.total || 0;
  const totalAttentionNeeded = needsReviewCount + failedCount;

  const loading = needsReviewLoading || failedLoading;
  const error = needsReviewError || failedError;

  const handleRetry = () => {
    refetchNeedsReview();
    refetchFailed();
  };

  // Loading state
  if (loading) {
    return <ListWidgetSkeleton />;
  }

  // Error state
  if (error) {
    return (
      <WidgetErrorFallback
        title="Imports Attention"
        error={error?.message || "Failed to load import status"}
        onRetry={handleRetry}
      />
    );
  }

  // Clean state - no attention needed
  if (totalAttentionNeeded === 0) {
    return (
      <Card className="h-[280px]">
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-semibold flex items-center gap-2">
            <CheckCircle2 className="h-4 w-4 text-green-500" />
            Imports
            {mode === "family" && <span className="text-muted-foreground ml-2">· Family</span>}
          </CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col items-center justify-center h-[200px] text-center px-6">
          <p className="text-muted-foreground text-sm">All imports are resolved</p>
          <p className="text-muted-foreground text-xs mt-1 mb-4">
            No issues requiring attention
          </p>
          <Link href="/import" className="block w-full">
            <Button variant="outline" size="sm" className="w-full">
              <Upload className="h-3 w-3 mr-2" />
              Import PDF
            </Button>
          </Link>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="h-[280px]">
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-semibold flex items-center gap-2">
          <AlertTriangle className="h-4 w-4 text-amber-500" />
          Imports Attention
          {mode === "family" && <span className="text-muted-foreground ml-2">· Family</span>}
          <Badge variant="destructive" className="ml-auto text-xs">
            {totalAttentionNeeded}
          </Badge>
        </CardTitle>
      </CardHeader>
      <CardContent className="px-6 space-y-3">
        {/* NEEDS_REVIEW Alert */}
        {needsReviewCount > 0 && (
          <div className="flex items-center gap-3 p-2 bg-amber-50 dark:bg-amber-950/20 rounded-lg">
            <div className="p-2 bg-amber-100 dark:bg-amber-900/30 rounded-full">
              <FileWarning className="h-4 w-4 text-amber-600 dark:text-amber-400" />
            </div>
            <div className="flex-1">
              <p className="text-lg font-semibold">{needsReviewCount}</p>
              <p className="text-xs text-muted-foreground">Need Review</p>
            </div>
          </div>
        )}

        {/* FAILED Alert */}
        {failedCount > 0 && (
          <div className="flex items-center gap-3 p-2 bg-red-50 dark:bg-red-950/20 rounded-lg">
            <div className="p-2 bg-red-100 dark:bg-red-900/30 rounded-full">
              <AlertTriangle className="h-4 w-4 text-red-600 dark:text-red-400" />
            </div>
            <div className="flex-1">
              <p className="text-lg font-semibold">{failedCount}</p>
              <p className="text-xs text-muted-foreground">Failed</p>
            </div>
          </div>
        )}

        {/* Action Buttons */}
        <div className="grid grid-cols-2 gap-2 pt-1">
          <Link href="/imports" className="block">
            <Button 
              variant="outline" 
              size="sm" 
              className="w-full"
            >
              Open Inbox
              <ArrowRight className="h-3 w-3 ml-1" />
            </Button>
          </Link>
          <Link href="/import" className="block">
            <Button 
              variant="default" 
              size="sm" 
              className="w-full"
            >
              <Upload className="h-3 w-3 mr-1" />
              Import PDF
            </Button>
          </Link>
        </div>
      </CardContent>
    </Card>
  );
}
