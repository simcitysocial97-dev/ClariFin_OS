"use client";

/**
 * Health Score Widget
 * ===================
 *
 * Shows behavior score with ring visualization and key insights.
 * Uses React Query for data fetching (self-contained, no prop drilling).
 */

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useBehaviorScoreQuery } from "@/lib/hooks/use-query-finance";
import { useOverviewQuery } from "@/lib/hooks/use-query-finance";
import { WidgetErrorFallback } from "./widget-error-fallback";
import { Skeleton } from "@/components/ui/skeleton";
import { AlertCircle, CheckCircle2, AlertTriangle, Info } from "lucide-react";
import { cn } from "@/lib/utils";

interface HealthScoreWidgetProps {
  mode?: "personal" | "family";
}

export function HealthScoreSkeleton() {
  return (
    <Card className="h-[280px]">
      <CardHeader className="pb-2">
        <Skeleton className="h-5 w-28" />
      </CardHeader>
      <CardContent className="flex items-center gap-4">
        <Skeleton className="w-20 h-20 rounded-full" />
        <div className="space-y-2 flex-1">
          <Skeleton className="h-4 w-32" />
          <Skeleton className="h-3 w-24" />
          <Skeleton className="h-8 w-full" />
        </div>
      </CardContent>
    </Card>
  );
}

function ScoreRing({ score }: { score: number }) {
  const getColor = (s: number) => {
    if (s >= 70) return "text-green-500 stroke-green-500";
    if (s >= 40) return "text-amber-500 stroke-amber-500";
    return "text-red-500 stroke-red-500";
  };

  const circumference = 2 * Math.PI * 36;
  const strokeDashoffset = circumference - (score / 100) * circumference;

  return (
    <div className="relative w-20 h-20 flex-shrink-0">
      <svg className="w-full h-full -rotate-90" viewBox="0 0 80 80">
        <circle
          cx="40"
          cy="40"
          r="36"
          fill="none"
          stroke="currentColor"
          strokeWidth="8"
          className="text-muted/20"
        />
        <circle
          cx="40"
          cy="40"
          r="36"
          fill="none"
          stroke="currentColor"
          strokeWidth="8"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={strokeDashoffset}
          className={cn("transition-all duration-1000", getColor(score))}
        />
      </svg>
      <div className="absolute inset-0 flex items-center justify-center">
        <span className={cn("text-lg font-bold", getColor(score).split(" ")[0])}>
          {score.toFixed(0)}
        </span>
      </div>
    </div>
  );
}

function InsightCard({ title, description, severity }: { title: string; description: string; severity: string }) {
  const severityConfig = {
    positive: { icon: CheckCircle2, color: "text-green-600 bg-green-50 dark:bg-green-950/20" },
    warning: { icon: AlertTriangle, color: "text-amber-600 bg-amber-50 dark:bg-amber-950/20" },
    alert: { icon: AlertCircle, color: "text-red-600 bg-red-50 dark:bg-red-950/20" },
    info: { icon: Info, color: "text-blue-600 bg-blue-50 dark:bg-blue-950/20" },
  };

  const config = severityConfig[severity as keyof typeof severityConfig] || severityConfig.info;
  const Icon = config.icon;

  return (
    <div className={cn("flex items-start gap-2 p-2 rounded-lg", config.color)}>
      <Icon className={cn("h-4 w-4 mt-0.5 flex-shrink-0", config.color.split(" ")[0])} />
      <div className="min-w-0">
        <p className="text-xs font-medium truncate">{title}</p>
        <p className="text-[10px] text-muted-foreground line-clamp-2">{description}</p>
      </div>
    </div>
  );
}

export function HealthScoreWidget({ mode = "personal" }: HealthScoreWidgetProps) {
  // Use React Query hooks - self-contained, no prop drilling
  const {
    data: behaviorData,
    loading: behaviorLoading,
    error: behaviorError,
    refetch: refetchBehavior,
  } = useBehaviorScoreQuery();

  const {
    data: overviewData,
    loading: overviewLoading,
  } = useOverviewQuery();

  const loading = behaviorLoading || overviewLoading;
  const error = behaviorError;

  if (loading) {
    return <HealthScoreSkeleton />;
  }

  if (error) {
    return (
      <WidgetErrorFallback
        title="Health Score"
        error={error.message}
        onRetry={refetchBehavior}
      />
    );
  }

  const score = behaviorData?.score ?? null;
  const grade = behaviorData?.grade ?? "N/A";
  const factors = behaviorData?.factors ?? [];

  // Get insights from overview behavioral_insights
  const insights = overviewData?.behavioral_insights?.slice(0, 2) ?? [];

  // Empty state - no score yet
  if (score === null) {
    return (
      <Card className="h-[280px]">
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-semibold">
            Health Score
            {mode === "family" && <span className="text-muted-foreground ml-2">· Family</span>}
          </CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col items-center justify-center h-[200px] text-center">
          <div className="w-16 h-16 rounded-full bg-muted flex items-center justify-center mb-3">
            <span className="text-2xl text-muted-foreground">—</span>
          </div>
          <p className="text-muted-foreground text-sm">No health score yet</p>
          <p className="text-muted-foreground text-xs mt-1">
            Upload transactions to see your score
          </p>
        </CardContent>
      </Card>
    );
  }

  const getGradeLabel = (s: number) => {
    if (s >= 80) return "Excellent";
    if (s >= 60) return "Good";
    if (s >= 40) return "Fair";
    return "Needs Work";
  };

  return (
    <Card className="h-[280px]">
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-semibold">
          Health Score
          {mode === "family" && <span className="text-muted-foreground ml-2">· Family</span>}
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {/* Score Ring and Grade */}
        <div className="flex items-center gap-4">
          <ScoreRing score={score} />
          <div className="flex-1 min-w-0">
            <p className="text-lg font-semibold">{getGradeLabel(score)}</p>
            <p className="text-xs text-muted-foreground">Grade: {grade}</p>
            {factors.length > 0 && (
              <p className="text-[10px] text-muted-foreground mt-1 truncate">
                Based on {factors.length} factor{factors.length !== 1 ? "s" : ""}
              </p>
            )}
          </div>
        </div>

        {/* Insights */}
        {insights.length > 0 ? (
          <div className="space-y-2">
            {insights.map((insight, idx) => (
              <InsightCard
                key={idx}
                title={insight.title}
                description={insight.description}
                severity={insight.severity}
              />
            ))}
          </div>
        ) : factors.length > 0 ? (
          <div className="p-2 bg-muted/50 rounded-lg">
            <p className="text-xs font-medium mb-1">Key Factors</p>
            <ul className="space-y-1">
              {factors.slice(0, 2).map((factor, idx) => (
                <li key={idx} className="text-[10px] text-muted-foreground flex items-start gap-1">
                  <span className="text-primary">•</span>
                  <span className="line-clamp-1">{factor}</span>
                </li>
              ))}
            </ul>
          </div>
        ) : null}
      </CardContent>
    </Card>
  );
}
