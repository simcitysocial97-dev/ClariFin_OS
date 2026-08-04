/**
 * Bottom Intelligence Shelf - Stage 8A Financial Operating System Shell
 *
 * Passive intelligence surface (88px collapsed, up to 240px expanded).
 * Displays insights, timeline scrubber, temporal navigation.
 * Driven by passiveInsightRuntime — no business logic.
 * Collapsed state shows only the scrubber strip.
 */

'use client';

import { useState, useMemo, useEffect } from 'react';
import { cn } from '@/lib/utils';
import { ChevronUp, ChevronDown, Lightbulb, TrendingUp, AlertCircle, CheckCircle2 } from 'lucide-react';
import { passiveInsightRuntime } from '@/lib/intelligence/passive-runtime';
import type { PassiveInsight } from '@/lib/intelligence/passive-runtime';
import { intelligenceInvocation } from '@/lib/intelligence/intelligence-invocation';

// ===== Insight Severity Colors =====
const severityColors: Record<string, string> = {
  info: 'text-[var(--color-info-500)]',
  warning: 'text-[var(--color-warning-500)]',
  critical: 'text-[var(--color-negative-500)]',
  positive: 'text-[var(--color-positive-500)]',
};

const severityBg: Record<string, string> = {
  info: 'bg-[var(--color-info-50)] dark:bg-[var(--color-info-950)]',
  warning: 'bg-[var(--color-warning-50)] dark:bg-[var(--color-warning-950)]',
  critical: 'bg-[var(--color-negative-50)] dark:bg-[var(--color-negative-950)]',
  positive: 'bg-[var(--color-positive-50)] dark:bg-[var(--color-positive-950)]',
};

// ===== Insight Card =====
interface InsightCardProps {
  insight: PassiveInsight;
  compact?: boolean;
  onDismiss?: (id: string) => void;
  onInvestigate?: (id: string) => void;
}

function InsightCard({ insight, compact, onDismiss, onInvestigate }: InsightCardProps) {
  const Icon = insight.severity === 'positive' ? CheckCircle2
    : insight.severity === 'warning' ? AlertCircle
    : insight.severity === 'critical' ? AlertCircle
    : TrendingUp;

  return (
    <div
      className={cn(
        'flex items-center gap-2 px-2 py-1.5 rounded-[var(--radius-sm)]',
        compact ? 'min-w-max' : 'flex-1',
        severityBg[insight.severity] ?? 'bg-[var(--surface-raised)]',
      )}
    >
      <Icon className={cn('h-3 w-3 shrink-0', severityColors[insight.severity] ?? 'text-[var(--text-tertiary)]')} />
      <div className="min-w-0 flex-1">
        <span className="fin-caption font-medium text-[var(--text-primary)]">{insight.title}</span>
        {!compact && (
          <span className="fin-caption text-[var(--text-secondary)] block truncate">{insight.summary}</span>
        )}
      </div>
      <div className="flex items-center gap-0.5 shrink-0">
        {onInvestigate && (
          <button
            onClick={(e) => { e.stopPropagation(); onInvestigate(insight.id); }}
            className="shrink-0 h-4 w-4 rounded-full flex items-center justify-center hover:bg-[var(--surface-interactive)] text-[var(--text-tertiary)] opacity-0 group-hover:opacity-100 transition-opacity"
            aria-label="Investigate insight"
          >
            <svg className="h-2.5 w-2.5" viewBox="0 0 10 10" fill="none">
              <circle cx="4" cy="4" r="3" stroke="currentColor" strokeWidth="1.2" />
              <path d="M6.5 6.5L9 9" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" />
            </svg>
          </button>
        )}
        {onDismiss && insight.dismissible && (
          <button
            onClick={(e) => { e.stopPropagation(); onDismiss(insight.id); }}
            className="shrink-0 h-4 w-4 rounded-full flex items-center justify-center hover:bg-[var(--surface-interactive)] text-[var(--text-tertiary)] opacity-0 group-hover:opacity-100 transition-opacity"
            aria-label="Dismiss insight"
          >
            <span className="text-[8px] leading-none">×</span>
          </button>
        )}
      </div>
    </div>
  );
}

// ===== Bottom Intelligence Shelf Component =====
interface BottomIntelligenceShelfProps {
  className?: string;
}

export function BottomIntelligenceShelf({ className }: BottomIntelligenceShelfProps) {
  const [expanded, setExpanded] = useState(false);
  const [insights, setInsights] = useState<PassiveInsight[]>([]);

  // Subscribe to passive insight changes
  useEffect(() => {
    setInsights(passiveInsightRuntime.getInsights());
    const unsubscribe = passiveInsightRuntime.subscribe((updated) => {
      setInsights(updated);
    });
    return unsubscribe;
  }, []);

  const handleDismiss = useMemo(() => {
    return (id: string) => {
      passiveInsightRuntime.dismiss(id);
    };
  }, []);

  const handleInvestigate = useMemo(() => {
    return (id: string) => {
      intelligenceInvocation.handlePassiveInsightClick(id);
    };
  }, []);

  return (
    <footer
      className={cn(
        'fixed bottom-6 left-[180px] right-0 z-20',
        'border-t border-[var(--border-default)]',
        'bg-[var(--surface-timeline)]',
        className,
      )}
      style={{ height: expanded ? '240px' : '88px' }}
    >
      {/* Header / Toggle bar */}
      <div className="flex items-center justify-between h-7 px-3 border-b border-[var(--border-default)] shrink-0">
        <div className="flex items-center gap-1.5">
          <Lightbulb className="h-3.5 w-3.5 text-[var(--text-tertiary)]" />
          <span className="fin-caption font-semibold uppercase tracking-wider text-[var(--text-secondary)]">
            Intelligence
          </span>
          <span className="fin-caption text-[var(--text-tertiary)]">
            · {insights.length} insight{insights.length !== 1 ? 's' : ''}
          </span>
        </div>
        <button
          onClick={() => setExpanded(!expanded)}
          className="flex items-center justify-center h-5 w-5 rounded-[var(--radius-sm)] hover:bg-[var(--surface-interactive)] text-[var(--text-tertiary)] transition-colors"
          aria-label={expanded ? 'Collapse intelligence shelf' : 'Expand intelligence shelf'}
        >
          {expanded ? (
            <ChevronDown className="h-2.5 w-2.5" />
          ) : (
            <ChevronUp className="h-2.5 w-2.5" />
          )}
        </button>
      </div>

      {/* Content area */}
      <div className="overflow-hidden">
        {expanded ? (
          /* Expanded: show all insights with details */
          <div className="p-2 space-y-1.5">
            {insights.map((insight) => (
              <div key={insight.id} className="group">
                <InsightCard
                  insight={insight}
                  compact={false}
                  onDismiss={handleDismiss}
                  onInvestigate={handleInvestigate}
                />
              </div>
            ))}
            {insights.length === 0 && (
              <div className="px-2 py-3 text-center">
                <span className="fin-caption text-[var(--text-tertiary)]">No insights for this period</span>
              </div>
            )}
          </div>
        ) : (
          /* Collapsed: show compact insight strip */
          <div className="flex items-center gap-1 px-2 py-1.5 overflow-x-auto">
            {insights.slice(0, 5).map((insight) => (
              <InsightCard key={insight.id} insight={insight} compact onDismiss={handleDismiss} onInvestigate={handleInvestigate} />
            ))}
            {insights.length === 0 && (
              <div className="px-2 py-1 text-[var(--text-tertiary)]">
                <span className="fin-caption">No active insights</span>
              </div>
            )}
          </div>
        )}
      </div>
    </footer>
  );
}
