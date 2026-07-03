"use client";

/**
 * Template Coverage Widget
 * ========================
 * 
 * Shows the percentage of imports where template_applied=true.
 * Computed from recent import records (template_id !== null).
 */

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useImportsQuery } from "@/lib/hooks/use-queries";
import { ListWidgetSkeleton } from "./skeletons";
import { WidgetErrorFallback } from "./widget-error-fallback";
import { LayoutTemplate, CheckCircle2, XCircle } from "lucide-react";
import { cn } from "@/lib/utils";

interface TemplateCoverageWidgetProps {
  mode?: "personal" | "family";
}

export function TemplateCoverageWidget({ mode = "personal" }: TemplateCoverageWidgetProps) {
  // Get more imports for better coverage stats (last 20)
  const { data, isLoading: loading, error, refetch } = useImportsQuery({ page: 1, per_page: 20 });

  if (loading) {
    return <ListWidgetSkeleton />;
  }

  if (error) {
    return (
      <WidgetErrorFallback
        title="Template Coverage"
        error={error.message}
        onRetry={refetch}
      />
    );
  }

  const imports = data?.items || [];

  // Calculate template coverage
  // template_id !== null means a template was applied
  const totalImports = imports.length;
  const templatedImports = imports.filter((item) => item.template_id !== null).length;
  const coveragePercentage = totalImports > 0 ? Math.round((templatedImports / totalImports) * 100) : 0;

  // Empty state
  if (totalImports === 0) {
    return (
      <Card className="h-[320px]">
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-semibold">Template Coverage</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col items-center justify-center h-[250px] text-center px-6">
          <LayoutTemplate className="h-10 w-10 text-muted-foreground/50 mb-3" />
          <p className="text-muted-foreground text-sm">No imports yet</p>
          <p className="text-muted-foreground text-xs mt-1">
            Upload statements to see template coverage
          </p>
        </CardContent>
      </Card>
    );
  }

  // Determine color based on coverage
  const getCoverageColor = (pct: number) => {
    if (pct >= 80) return "text-green-500";
    if (pct >= 50) return "text-amber-500";
    return "text-red-500";
  };

  const getCoverageBg = (pct: number) => {
    if (pct >= 80) return "bg-green-500";
    if (pct >= 50) return "bg-amber-500";
    return "bg-red-500";
  };

  const getCoverageMessage = (pct: number) => {
    if (pct >= 80) return "Excellent coverage";
    if (pct >= 50) return "Good coverage";
    return "Low coverage";
  };

  return (
    <Card className="h-[320px]">
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-semibold">
          Template Coverage
          {mode === "family" && <span className="text-muted-foreground ml-2">· Family</span>}
        </CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col items-center justify-center h-[250px] px-6">
        {/* Large percentage display */}
        <div className="text-center">
          <div className={cn("text-5xl font-bold", getCoverageColor(coveragePercentage))}>
            {coveragePercentage}%
          </div>
          <p className="text-sm text-muted-foreground mt-1">
            {getCoverageMessage(coveragePercentage)}
          </p>
        </div>

        {/* Progress bar */}
        <div className="w-full mt-6">
          <div className="h-2 w-full bg-muted rounded-full overflow-hidden">
            <div
              className={cn("h-full transition-all duration-500", getCoverageBg(coveragePercentage))}
              style={{ width: `${coveragePercentage}%` }}
            />
          </div>
        </div>

        {/* Stats breakdown */}
        <div className="grid grid-cols-2 gap-4 w-full mt-6">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="h-4 w-4 text-green-500" />
            <div>
              <p className="text-sm font-medium">{templatedImports}</p>
              <p className="text-[10px] text-muted-foreground">With template</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <XCircle className="h-4 w-4 text-muted-foreground" />
            <div>
              <p className="text-sm font-medium">{totalImports - templatedImports}</p>
              <p className="text-[10px] text-muted-foreground">Without template</p>
            </div>
          </div>
        </div>

        {/* Total count */}
        <p className="text-xs text-muted-foreground mt-4">
          Based on last {totalImports} import{totalImports !== 1 ? "s" : ""}
        </p>
      </CardContent>
    </Card>
  );
}
