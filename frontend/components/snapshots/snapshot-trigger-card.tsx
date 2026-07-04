"use client";

import { useState } from "react";
import { useSnapshots, useGenerateSnapshot, useBackfillSnapshots } from "@/lib/hooks/use-finance-data";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { WidgetErrorFallback } from "@/components/dashboard/widget-error-fallback";
import { useToast } from "@/hooks/use-toast";
import { Camera, History, Loader2, CheckCircle } from "lucide-react";
import { cn } from "@/lib/utils";

export function SnapshotTriggerCard({ className }: { className?: string }) {
  const { snapshots, loading, error, refetch } = useSnapshots();
  const { generating, generateSnapshot } = useGenerateSnapshot();
  const { backfilling, backfillSnapshots } = useBackfillSnapshots();
  const { toast } = useToast();
  const [lastGenerated, setLastGenerated] = useState<string | null>(null);

  if (loading) {
    return (
      <Card className={cn("animate-pulse", className)}>
        <CardHeader className="pb-2">
          <div className="h-5 w-40 bg-muted rounded" />
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="h-4 w-full bg-muted rounded" />
          <div className="h-10 w-40 bg-muted rounded" />
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className={className}>
        <CardContent className="py-6">
          <WidgetErrorFallback title="Snapshot Controls" error={error.message} onRetry={refetch} />
        </CardContent>
      </Card>
    );
  }

  const latestSnapshot = snapshots?.[0];
  const hasRecentSnapshot = latestSnapshot && 
    new Date(latestSnapshot.month).getMonth() === new Date().getMonth() &&
    new Date(latestSnapshot.month).getFullYear() === new Date().getFullYear();

  const handleGenerate = async () => {
    try {
      await generateSnapshot(undefined);
      setLastGenerated(new Date().toLocaleString());
      toast({
        title: "Snapshot Generated",
        description: `Monthly snapshot has been created successfully.`,
      });
      refetch();
    } catch {
      toast({
        title: "Generation Failed",
        description: "Failed to generate snapshot. Please try again.",
        variant: "destructive",
      });
    }
  };

  const handleBackfill = async () => {
    try {
      await backfillSnapshots({ start: "", end: "" });
      toast({
        title: "Snapshots Backfilled",
        description: `Historical snapshots have been generated.`,
      });
      refetch();
    } catch {
      toast({
        title: "Backfill Failed",
        description: "Failed to backfill snapshots. Please try again.",
        variant: "destructive",
      });
    }
  };

  return (
    <Card className={className}>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-semibold flex items-center gap-2">
          <Camera className="h-4 w-4" />
          Snapshot Engine
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <p className="text-sm text-muted-foreground">
          Snapshots freeze your monthly financial state for historical tracking.
          {hasRecentSnapshot && (
            <span className="block mt-1 text-green-600 flex items-center gap-1">
              <CheckCircle className="h-3 w-3" />
              Snapshot already generated for this month
            </span>
          )}
        </p>
        
        <div className="flex flex-wrap gap-3">
          <Button 
            onClick={handleGenerate} 
            disabled={generating || hasRecentSnapshot}
            className="flex items-center gap-2"
          >
            {generating ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Camera className="h-4 w-4" />
            )}
            {generating ? "Generating..." : "Generate Monthly Snapshot"}
          </Button>
          
          <Button 
            variant="outline" 
            onClick={handleBackfill} 
            disabled={backfilling}
            className="flex items-center gap-2"
          >
            {backfilling ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <History className="h-4 w-4" />
            )}
            {backfilling ? "Backfilling..." : "Backfill History"}
          </Button>
        </div>

        {lastGenerated && (
          <p className="text-xs text-muted-foreground">
            Last generated: {lastGenerated}
          </p>
        )}
      </CardContent>
    </Card>
  );
}
