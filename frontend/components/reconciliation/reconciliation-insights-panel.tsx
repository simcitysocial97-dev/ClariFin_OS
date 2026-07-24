/**
 * Reconciliation Insights Panel - Stage 4 Reconciliation Intelligence Workspace
 *
 * Displays actionable insights about reconciliation.
 *
 * Architecture Flow: Backend → API → DTO → Mapper → ViewModel → Capability → Workspace → Components → Page
 */

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { AlertCircle, Lightbulb, TrendingUp, TrendingDown, Info } from 'lucide-react';
import type { ReconciliationViewModel, ReconciliationInsightViewModel } from '@/types/reconciliation-view-model';

/**
 * Reconciliation Insights Panel Props
 */
interface InsightsPanelProps {
  reconciliation: ReconciliationViewModel | null;
  loading: boolean;
  error: Error | null;
}

/**
 * Insight Icon Component
 */
function InsightIcon({ type }: { type: string }) {
  switch (type) {
    case 'positive':
      return <TrendingUp className="h-4 w-4 text-green-500" />;
    case 'warning':
      return <TrendingDown className="h-4 w-4 text-yellow-500" />;
    case 'alert':
      return <AlertCircle className="h-4 w-4 text-red-500" />;
    default:
      return <Info className="h-4 w-4 text-blue-500" />;
  }
}

/**
 * Insight Card Component
 */
function InsightCard({ insight }: { insight: ReconciliationInsightViewModel }) {
  return (
    <div className="border-b pb-3 mb-3 last:border-0 last:pb-0 last:mb-0">
      <div className="flex items-start gap-3">
        <InsightIcon type={insight.type} />
        <div className="flex-1">
          <p className="text-sm">{insight.message}</p>
          {insight.action_url && (
            <a
              href={insight.action_url}
              className="text-xs text-blue-600 hover:underline mt-1 inline-block"
            >
              View details
            </a>
          )}
        </div>
      </div>
    </div>
  );
}

/**
 * Reconciliation Insights Panel Component
 */
export function InsightsPanel({ reconciliation, loading, error }: InsightsPanelProps) {
  // Loading state
  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>
            <Skeleton className="h-5 w-24" />
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-full" />
          </div>
        </CardContent>
      </Card>
    );
  }

  // Error state
  if (error) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Insights</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-2 text-red-600">
            <AlertCircle className="h-4 w-4" />
            <span className="text-sm">Failed to load insights</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  // Empty state
  if (!reconciliation || reconciliation.insights.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Insights</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-gray-500 text-sm">No insights available at this time</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Lightbulb className="h-5 w-5" />
          Insights
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          {reconciliation.insights.map((insight, index) => (
            <InsightCard key={index} insight={insight} />
          ))}
        </div>
      </CardContent>
    </Card>
  );
}