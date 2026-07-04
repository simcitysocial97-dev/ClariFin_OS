"use client";

/**
 * Recent Imports Widget
 * =====================
 * 
 * Shows the last 5 imports with status pills (COMMITTED/NEEDS_REVIEW/STAGED/FAILED).
 * Uses the V2 imports API.
 */

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { useImportsQuery } from "@/lib/hooks/use-query-finance";
import { ListWidgetSkeleton } from "./skeletons";
import { WidgetErrorFallback } from "./widget-error-fallback";
import { FileText, ArrowRight } from "lucide-react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import type { ImportStatus } from "@/types/v2";

interface RecentImportsWidgetProps {
  mode?: "personal" | "family";
}

const statusConfig: Record<ImportStatus, { label: string; variant: "default" | "secondary" | "destructive" | "outline" }> = {
  COMMITTED: { label: "Committed", variant: "default" },
  NEEDS_REVIEW: { label: "Needs Review", variant: "secondary" },
  STAGED: { label: "Staged", variant: "outline" },
  FAILED: { label: "Failed", variant: "destructive" },
};

function getStatusBadge(status: ImportStatus) {
  const config = statusConfig[status];
  return (
    <Badge variant={config.variant} className="text-[10px] px-1.5 py-0">
      {config.label}
    </Badge>
  );
}

function formatDate(dateString: string): string {
  const date = new Date(dateString);
  return date.toLocaleDateString("en-IN", {
    day: "numeric",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function truncateFilename(filename: string, maxLength: number = 25): string {
  if (filename.length <= maxLength) return filename;
  const ext = filename.split(".").pop();
  const name = filename.substring(0, maxLength - 4);
  return `${name}...${ext ? `.${ext}` : ""}`;
}

export function RecentImportsWidget({ mode = "personal" }: RecentImportsWidgetProps) {
  const { data, loading: loading, error, refetch } = useImportsQuery({ page: 1, per_page: 5 });

  if (loading) {
    return <ListWidgetSkeleton />;
  }

  if (error) {
    return (
      <WidgetErrorFallback
        title="Recent Imports"
        error={error.message}
        onRetry={refetch}
      />
    );
  }

  const imports = data?.items || [];

  // Empty state
  if (imports.length === 0) {
    return (
      <Card className="h-[320px]">
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-semibold">Recent Imports</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col items-center justify-center h-[250px] text-center px-6">
          <FileText className="h-10 w-10 text-muted-foreground/50 mb-3" />
          <p className="text-muted-foreground text-sm">No imports yet</p>
          <p className="text-muted-foreground text-xs mt-1">
            Upload PDF statements to see your import history
          </p>
          <Link href="/import" className="mt-4">
            <Button variant="outline" size="sm">
              Import Statement
              <ArrowRight className="h-4 w-4 ml-2" />
            </Button>
          </Link>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="h-[320px]">
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-semibold">
          Recent Imports
          {mode === "family" && <span className="text-muted-foreground ml-2">· Family</span>}
        </CardTitle>
      </CardHeader>
      <CardContent className="p-0">
        <ScrollArea className="h-[250px] px-6">
          <div className="space-y-3 py-2">
            {imports.map((importItem) => (
              <div
                key={importItem.id}
                className="flex items-center justify-between py-2 border-b border-border/50 last:border-0"
              >
                <div className="flex-1 min-w-0 mr-3">
                  <p className="text-sm font-medium truncate" title={importItem.source_filename}>
                    {truncateFilename(importItem.source_filename)}
                  </p>
                  <div className="flex items-center gap-2 mt-0.5">
                    <p className="text-xs text-muted-foreground">
                      {importItem.bank}
                    </p>
                    <span className="text-xs text-muted-foreground">·</span>
                    <p className="text-xs text-muted-foreground">
                      {formatDate(importItem.created_at)}
                    </p>
                  </div>
                </div>
                <div className="flex flex-col items-end gap-1">
                  {getStatusBadge(importItem.status)}
                  <span className="text-[10px] text-muted-foreground">
                    {importItem.transaction_count} txns
                  </span>
                </div>
              </div>
            ))}
          </div>
        </ScrollArea>
        <div className="px-6 pb-4 pt-2">
          <Link href="/import">
            <Button variant="ghost" size="sm" className="w-full">
              View all imports
              <ArrowRight className="h-4 w-4 ml-2" />
            </Button>
          </Link>
        </div>
      </CardContent>
    </Card>
  );
}
