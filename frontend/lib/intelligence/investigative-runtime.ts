/**
 * Investigative Insight Runtime — Stage 8 Financial Operating System
 *
 * Generates and manages InvestigativeInsight objects on-demand (user-initiated).
 * Supports drill-down actions that navigate to workspaces with pre-selected entities.
 *
 * Architecture: FINANCIAL_OS_SHELL_ARCHITECTURE.md §4.4
 */

import type {
  InvestigativeInsight,
  InvestigativeTrigger,
  EvidenceLink,
  EntityReference,
  DrillDownAction,
} from './types';

// ─── State ───────────────────────────────────────────────────────────────────

const _insights: Map<string, InvestigativeInsight> = new Map();
const _listeners: Set<() => void> = new Set();

function notify() {
  _listeners.forEach(fn => fn());
}

// ─── ID Generator ─────────────────────────────────────────────────────────────

function generateId(): string {
  return `inv-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
}

// ─── Generation ──────────────────────────────────────────────────────────────

interface GenerateInvestigativeParams {
  trigger: InvestigativeTrigger;
  title: string;
  summary: string;
  evidenceTrail: EvidenceLink[];
  relatedEntities: EntityReference[];
  drillDownActions: DrillDownAction[];
}

function generate(params: GenerateInvestigativeParams): InvestigativeInsight {
  const insight: InvestigativeInsight = {
    id: generateId(),
    trigger: params.trigger,
    title: params.title,
    summary: params.summary,
    evidenceTrail: params.evidenceTrail,
    relatedEntities: params.relatedEntities,
    drillDownActions: params.drillDownActions,
    createdAt: Date.now(),
    dismissed: false,
  };

  _insights.set(insight.id, insight);
  notify();
  return insight;
}

// ─── Query ────────────────────────────────────────────────────────────────────

function getActiveInsights(): InvestigativeInsight[] {
  return Array.from(_insights.values())
    .filter(i => !i.dismissed)
    .sort((a, b) => b.createdAt - a.createdAt);
}

function getById(id: string): InvestigativeInsight | undefined {
  return _insights.get(id);
}

function getByTrigger(trigger: InvestigativeTrigger): InvestigativeInsight[] {
  return Array.from(_insights.values())
    .filter(i => !i.dismissed && i.trigger === trigger);
}

// ─── Dismissal ───────────────────────────────────────────────────────────────

function dismiss(id: string): void {
  const insight = _insights.get(id);
  if (insight) {
    _insights.set(id, { ...insight, dismissed: true });
    notify();
  }
}

function undismiss(id: string): void {
  const insight = _insights.get(id);
  if (insight) {
    _insights.set(id, { ...insight, dismissed: false });
    notify();
  }
}

function clearDismissed(): void {
  for (const id of _insights.keys()) {
    _insights.delete(id);
  }
  notify();
}

// ─── Drill-Down Execution ────────────────────────────────────────────────────

function executeDrillDown(insightId: string, actionIndex: number): boolean {
  const insight = _insights.get(insightId);
  if (!insight || actionIndex < 0 || actionIndex >= insight.drillDownActions.length) {
    return false;
  }

  const action = insight.drillDownActions[actionIndex];

  if (action.targetWorkspace || action.targetRoute) {
    const route = action.targetRoute ?? `/${action.targetWorkspace}`;
    window.location.href = route;
  }

  return true;
}

// ─── Subscriptions ───────────────────────────────────────────────────────────

function subscribe(listener: () => void): () => void {
  _listeners.add(listener);
  return () => {
    _listeners.delete(listener);
  };
}

// ─── Reset ───────────────────────────────────────────────────────────────────

function reset(): void {
  _insights.clear();
  _listeners.clear();
}

// ─── Singleton Export ─────────────────────────────────────────────────────────

export const investigativeInsightRuntime = {
  generate,
  getInsights: getActiveInsights,
  getById,
  getByTrigger,
  dismiss,
  undismiss,
  clearDismissed,
  executeDrillDown,
  subscribe,
  reset,
};

export function resetInvestigativeInsightRuntime(): void {
  reset();
}
