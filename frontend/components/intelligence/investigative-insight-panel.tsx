/**
 * Investigative Insight Panel — Stage 8 Financial Operating System
 *
 * Displays user-initiated investigative insights with evidence trails,
 * related entities, and drill-down actions.
 *
 * Architecture: FINANCIAL_OS_SHELL_ARCHITECTURE.md §4.4
 */

'use client';

import { useEffect, useState, useCallback } from 'react';
import { cn } from '@/lib/utils';
import { investigativeInsightRuntime } from '@/lib/intelligence/investigative-runtime';
import type { InvestigativeInsight } from '@/lib/intelligence/types';
import {
  Search,
  X,
  ArrowRight,
  GitBranch,
  Link as LinkIcon,
  FileText,
  TrendingUp,
} from 'lucide-react';

// ─── Evidence Link Renderer ──────────────────────────────────────────────────

const evidenceIcons: Record<string, typeof Search> = {
  transaction: FileText,
  statement: FileText,
  reconciliation: GitBranch,
  forecast: TrendingUp,
};

function EvidenceLinkItem({ link }: { link: InvestigativeInsight['evidenceTrail'][number] }) {
  const Icon = evidenceIcons[link.sourceType] ?? Search;
  const confidenceColor = link.confidence >= 0.8
    ? 'text-[var(--color-positive-500)]'
    : link.confidence >= 0.5
      ? 'text-[var(--color-warning-500)]'
      : 'text-[var(--color-negative-500)]';

  return (
    <div className="flex items-center gap-1.5 fin-body-small text-[var(--text-secondary)]">
      <Icon className="h-2.5 w-2.5 shrink-0" />
      <span className="truncate">{link.label}</span>
      <span className={cn('ml-auto text-[10px]', confidenceColor)}>
        {(link.confidence * 100).toFixed(0)}%
      </span>
    </div>
  );
}

// ─── Entity Reference Renderer ───────────────────────────────────────────────

function EntityRefItem({ entity }: { entity: InvestigativeInsight['relatedEntities'][number] }) {
  return (
    <div className="flex items-center gap-1.5 fin-body-small text-[var(--text-link)] hover:underline cursor-pointer">
      <LinkIcon className="h-2.5 w-2.5 shrink-0" />
      <span className="truncate">{entity.label}</span>
      <span className="text-[var(--text-tertiary)] text-[10px] ml-auto shrink-0">
        {entity.relationshipType}
      </span>
    </div>
  );
}

// ─── Drill-Down Action Button ─────────────────────────────────────────────────

function DrillDownButton({
  action,
  index,
  insightId,
}: {
  action: InvestigativeInsight['drillDownActions'][number];
  index: number;
  insightId: string;
}) {
  const handleClick = () => {
    investigativeInsightRuntime.executeDrillDown(insightId, index);
  };

  return (
    <button
      onClick={handleClick}
      className="flex items-center gap-1 px-2 py-1 rounded-[var(--radius-sm)] bg-[var(--surface-interactive)] hover:bg-[var(--surface-selected)] fin-body-small text-[var(--text-primary)] transition-colors"
    >
      <span>{action.label}</span>
      <ArrowRight className="h-2.5 w-2.5" />
    </button>
  );
}

// ─── Insight Card ─────────────────────────────────────────────────────────────

interface InsightCardProps {
  insight: InvestigativeInsight;
  onDismiss: (id: string) => void;
}

function InsightCard({ insight, onDismiss }: InsightCardProps) {
  return (
    <div className="border border-[var(--border-default)] rounded-[var(--radius-md)] p-3 space-y-2.5">
      {/* Header */}
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0 flex-1">
          <h4 className="fin-label font-medium text-[var(--text-primary)] truncate">
            {insight.title}
          </h4>
          <p className="fin-body-small text-[var(--text-secondary)] mt-0.5">
            {insight.summary}
          </p>
        </div>
        <button
          onClick={() => onDismiss(insight.id)}
          className="shrink-0 h-5 w-5 rounded-full flex items-center justify-center hover:bg-[var(--surface-interactive)] text-[var(--text-tertiary)] transition-colors"
          aria-label="Dismiss insight"
        >
          <X className="h-2.5 w-2.5" />
        </button>
      </div>

      {/* Evidence Trail */}
      {insight.evidenceTrail.length > 0 && (
        <div className="space-y-0.5">
          <span className="fin-caption uppercase tracking-wider text-[var(--text-tertiary)]">
            Evidence
          </span>
          <div className="space-y-0.5">
            {insight.evidenceTrail.map((link, i) => (
              <EvidenceLinkItem key={i} link={link} />
            ))}
          </div>
        </div>
      )}

      {/* Related Entities */}
      {insight.relatedEntities.length > 0 && (
        <div className="space-y-0.5">
          <span className="fin-caption uppercase tracking-wider text-[var(--text-tertiary)]">
            Related
          </span>
          <div className="space-y-0.5">
            {insight.relatedEntities.slice(0, 5).map((entity, i) => (
              <EntityRefItem key={i} entity={entity} />
            ))}
          </div>
        </div>
      )}

      {/* Drill-Down Actions */}
      {insight.drillDownActions.length > 0 && (
        <div className="flex flex-wrap gap-1.5 pt-1">
          {insight.drillDownActions.map((action, i) => (
            <DrillDownButton
              key={i}
              action={action}
              index={i}
              insightId={insight.id}
            />
          ))}
        </div>
      )}
    </div>
  );
}

// ─── Panel Component ─────────────────────────────────────────────────────────

interface InvestigativeInsightPanelProps {
  className?: string;
}

export function InvestigativeInsightPanel({ className }: InvestigativeInsightPanelProps) {
  const [insights, setInsights] = useState<InvestigativeInsight[]>([]);

  useEffect(() => {
    setInsights(investigativeInsightRuntime.getInsights());
    const unsubscribe = investigativeInsightRuntime.subscribe(() => {
      setInsights(investigativeInsightRuntime.getInsights());
    });
    return unsubscribe;
  }, []);

  const handleDismiss = useCallback((id: string) => {
    investigativeInsightRuntime.dismiss(id);
  }, []);

  if (insights.length === 0) {
    return (
      <div className={cn('p-3 text-center', className)}>
        <span className="fin-body-small text-[var(--text-tertiary)]">
          No investigative insights. Select an entity or issue a command to explore relationships.
        </span>
      </div>
    );
  }

  return (
    <div className={cn('space-y-2 p-2', className)}>
      {insights.map((insight) => (
        <InsightCard key={insight.id} insight={insight} onDismiss={handleDismiss} />
      ))}
    </div>
  );
}
