"use client";

/**
 * Alerts Center Widget
 * ====================
 * 
 * Shows actionable alerts requiring user attention:
 * - NEEDS_REVIEW imports (missing balances or bbox required)
 * 
 * Provides quick-action buttons to navigate to resolution pages.
 */

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useImportsQuery } from "@/lib/hooks/use-queries";
import { ListWidgetSkeleton } from "./skeletons";
import { WidgetErrorFallback } from "./widget-error-fallback";
import { AlertTriangle, FileWarning, ArrowRight, CheckCircle2 } from "lucide-react";
import Link from "next/link";

interface AlertsCenterWidgetProps {
  mode?: "personal" | "family";
}

export function AlertsCenterWidget({ mode = "personal" }: AlertsCenterWidgetProps) {
  // Fetch imports needing review
  const {
    data: importsData,
    isLoading: importsLoading,
    error: importsError,
    refetch: refetchImports,
  } = useImportsQuery({ status: "NEEDS_REVIEW", page: 1, per_page: 100 });

  const needsReviewCount = importsData?.total || 0;

  // Loading state
  if (importsLoading) {
    return <ListWidgetSkeleton />;
  }

  // Error state
  if (importsError) {
    return (
      <WidgetErrorFallback
        title="Alerts Center"
        error={importsError?.message || "Failed to load alerts"}
        onRetry={() => {
          refetchImports();
        }}
      />
    );
  }

  // Clean state - no alerts
  if (needsReviewCount === 0) {
    return (
      <Card className="h-[180px]">
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-semibold flex items-center gap-2">
            <CheckCircle2 className="h-4 w-4 text-green-500" />
            All Clear
          </CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col items-center justify-center h-[100px] text-center px-6">
          <p className="text-muted-foreground text-sm">No issues requiring attention</p>
          <p className="text-muted-foreground text-xs mt-1">
            All imports are resolved
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="h-[180px]">
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-semibold flex items-center gap-2">
          <AlertTriangle className="h-4 w-4 text-amber-500" />
          Alerts Center
          {mode === "family" && <span className="text-muted-foreground ml-2">· Family</span>}
          <Badge variant="destructive" className="ml-auto text-xs">
            {needsReviewCount}
          </Badge>
        </CardTitle>
      </CardHeader>
      <CardContent className="px-6">
        <div className="flex items-center gap-3 p-3 bg-amber-50 dark:bg-amber-950/20 rounded-lg mb-4">
          <div className="p-2 bg-amber-100 dark:bg-amber-900/30 rounded-full">
            <FileWarning className="h-4 w-4 text-amber-600 dark:text-amber-400" />
          </div>
          <div>
            <p className="text-lg font-semibold">{needsReviewCount}</p>
            <p className="text-xs text-muted-foreground">Need Review</p>
          </div>
        </div>

        {/* Action Button */}
        <Link href="/imports" className="block">
          <Button 
            variant="outline" 
            size="sm" 
            className="w-full"
            disabled={needsReviewCount === 0}
          >
            Review Imports
            <ArrowRight className="h-3 w-3 ml-1" />
          </Button>
        </Link>
      </CardContent>
    </Card>
  );
}
