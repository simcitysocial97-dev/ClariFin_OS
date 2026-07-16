/**
 * Financial Inbox Widget - Actionable items feed
 * 
 * Shows alerts, recommendations, and insights in a prioritized list.
 */

'use client';
import { AlertCircle, Lightbulb, BarChart3, ArrowRight } from 'lucide-react';
import { useBehaviorInsights } from '@/lib/hooks/use-behavior-insights';

interface InboxItem {
  id: string;
  type: 'action_required' | 'recommendation' | 'insight';
  priority: number;
  title: string;
  description: string;
}

function getItemIcon(type: InboxItem['type']) {
  switch (type) {
    case 'action_required':
      return <AlertCircle className="h-4 w-4 text-red-500" />;
    case 'recommendation':
      return <Lightbulb className="h-4 w-4 text-amber-500" />;
    case 'insight':
      return <BarChart3 className="h-4 w-4 text-blue-500" />;
  }
}

export function FinancialInboxWidget() {
  const { data, isLoading, error } = useBehaviorInsights();

  if (isLoading || error || !data) return null;

  const inboxItems: InboxItem[] = [
    ...data.nudges.slice(0, 2).map((nudge, i) => ({
      id: `nudge-${i}`,
      type: 'action_required' as const,
      priority: nudge.priority,
      title: nudge.title,
      description: nudge.message,
    })),
    ...data.insights.filter((i) => i.type === 'warning').slice(0, 1).map((insight, i) => ({
      id: `insight-${i}`,
      type: 'insight' as const,
      priority: 0,
      title: insight.title,
      description: insight.message,
    })),
  ].sort((a, b) => b.priority - a.priority).slice(0, 3);

  return (
    <div className="space-y-3">
      {inboxItems.map((item) => (
        <div key={item.id} className="flex items-start gap-3 pb-3 border-b last:border-0">
          <div className="mt-0.5">{getItemIcon(item.type)}</div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium">{item.title}</p>
            <p className="text-xs text-muted-foreground mt-1">{item.description}</p>
          </div>
        </div>
      ))}
      <a href="/dashboard/insights" className="flex items-center gap-1 text-xs text-primary hover:underline pt-2">
        View all
        <ArrowRight className="h-3 w-3" />
      </a>
    </div>
  );
}