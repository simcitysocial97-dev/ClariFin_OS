/**
 * Insights Panel - Stage 4 Cashflow Truth Workspace
 *
 * Displays insights and recommendations for cashflow analysis.
 *
 * Architecture Flow: Backend → API → DTO → Mapper → ViewModel → Capability → Workspace → Components → Page
 */

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { AlertCircle, Info, CheckCircle, AlertTriangle } from 'lucide-react';
import type { CashflowInsightViewModel } from '@/types/cashflow-view-model';

/**
 * Insights Panel Props
 */
interface InsightsPanelProps {
  insights: CashflowInsightViewModel[];
  loading: boolean;
  error: Error | null;
}

/**
 * Insight Icon Component
 * Displays the appropriate icon based on insight type
 */
function InsightIcon({ type }: { type: string }) {
  const iconClass = "h-4 w-4";
  
  switch (type) {
    case 'positive':
      return <CheckCircle className={`${iconClass} text-green-500`} />;
    case 'warning':
      return <AlertTriangle className={`${iconClass} text-amber-500`} />;
    case 'alert':
      return <AlertCircle className={`${iconClass} text-red-500`} />;
    default:
      return <Info className={`${iconClass} text-blue-500`} />;
  }
}

/**
 * Insights Panel Component
 *
 * Shows a list of insights about cashflow patterns.
 */
export function InsightsPanel({ insights, loading, error }: InsightsPanelProps) {
  // Loading state
  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Insights</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-gray-500 text-sm">Loading insights...</p>
        </CardContent>
      </Card>
    );
  }

  // Error state
  if (error) {
    return (
      <Card>
        <CardContent className="p-6">
          <div className="flex items-center gap-2 text-red-600">
            <AlertCircle className="h-4 w-4" />
            <span className="text-sm">Failed to load insights</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  // Empty state
  if (!insights || insights.length === 0) {
    return (
      <Card>
        <CardContent className="p-6">
          <p className="text-gray-500 text-sm">No insights available</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Insights</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {insights.map((insight, index) => (
            <div
              key={index}
              className="flex items-start gap-3 p-3 border rounded-lg"
            >
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
          ))}
        </div>
      </CardContent>
    </Card>
  );
}