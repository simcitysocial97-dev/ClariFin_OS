'use client';

import { useState } from 'react';
import { ChartContainer } from '@/components/ui/chart-container';
import { useOverview } from '@/lib/hooks/use-overview';
import { TrendingUp, TrendingDown, AlertTriangle, CheckCircle, Info } from 'lucide-react';
import { cn } from '@/lib/utils';

interface BehavioralInsight {
  title: string;
  description: string;
  severity: 'warning' | 'positive' | 'neutral';
  icon: string;
}

const getSeverityStyles = (severity: string) => {
  switch (severity) {
    case 'warning':
      return 'bg-amber-50 border-amber-200 text-amber-800';
    case 'positive':
      return 'bg-green-50 border-green-200 text-green-800';
    default:
      return 'bg-slate-50 border-slate-200 text-slate-800';
  }
};

const getIcon = (iconName: string, severity: string) => {
  const iconClass = "h-4 w-4";
  
  if (iconName === 'trending-up' || severity === 'warning') {
    return <TrendingUp className={cn(iconClass, "text-amber-600")} />;
  }
  if (iconName === 'trending-down' || severity === 'positive') {
    return <TrendingDown className={cn(iconClass, "text-green-600")} />;
  }
  if (iconName === 'alert-triangle') {
    return <AlertTriangle className={cn(iconClass, "text-amber-600")} />;
  }
  if (iconName === 'check-circle') {
    return <CheckCircle className={cn(iconClass, "text-green-600")} />;
  }
  return <Info className={cn(iconClass, "text-slate-600")} />;
};

export function InsightsPanel() {
  const { data, isLoading, isError, refetch } = useOverview();
  const [showAll, setShowAll] = useState(false);

  const insights = data?.behavioral_insights || [];
  const displayedInsights = showAll ? insights : insights.slice(0, 6);
  const hasMore = insights.length > 6;

  const isEmpty = !isLoading && !isError && insights.length === 0;

  return (
    <ChartContainer
      isLoading={isLoading}
      isError={isError}
      isEmpty={isEmpty}
      emptyMessage="No insights available for this period"
      onRetry={refetch}
      title="Behavioral Insights"
    >
      {insights.length > 0 && (
        <div className="space-y-2">
          {displayedInsights.map((insight, index) => (
            <div
              key={index}
              className={cn(
                "flex items-start gap-2 p-2 rounded-md border text-xs",
                getSeverityStyles(insight.severity)
              )}
            >
              <div className="mt-0.5">
                {getIcon(insight.icon, insight.severity)}
              </div>
              <div className="flex-1 min-w-0">
                <p className="font-medium">{insight.title}</p>
                <p className="mt-0.5 opacity-80">{insight.description}</p>
              </div>
            </div>
          ))}
          
          {hasMore && (
            <button
              onClick={() => setShowAll(!showAll)}
              className="text-xs text-primary hover:underline mt-1"
            >
              {showAll ? 'Show less' : `Show ${insights.length - 6} more`}
            </button>
          )}
        </div>
      )}
    </ChartContainer>
  );
}