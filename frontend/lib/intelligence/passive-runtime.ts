/**
 * Passive Insight Runtime — Stage 6 Financial Operating System
 *
 * Converts IntelligenceRuntime Insights into PassiveInsight objects
 * with ranking, deduplication, and session-scoped dismissal.
 *
 * Architecture: FINANCIAL_OS_SHELL_ARCHITECTURE.md §4.3
 */

import type { Insight } from './types';
import { intelligenceRuntime } from './runtime';

// ─── Passive Insight Interface ──────────────────────────────────────────────

export type PassiveInsightCategory =
  | 'spending'
  | 'income'
  | 'cashflow'
  | 'forecast'
  | 'anomaly'
  | 'reminder'
  | 'positive';

export type PassiveSeverity = 'info' | 'positive' | 'warning' | 'critical';

export interface PassiveInsight {
  id: string;
  category: PassiveInsightCategory;
  title: string;
  summary: string;
  severity: PassiveSeverity;
  confidence: number; // 0.0–1.0
  relatedEntityId?: string;
  relatedEntityType?: string;
  actionLabel?: string;
  actionRoute?: string;
  dismissible: boolean;
  relevanceScore: number; // computed: recency*0.3 + severity*0.4 + impact*0.3
  createdAt: number; // timestamp in ms
}

// ─── Mapping: Insight → PassiveInsight ──────────────────────────────────────

const INSIGHT_TO_CATEGORY: Record<string, PassiveInsightCategory> = {
  health: 'cashflow',
  spending: 'spending',
  cashflow: 'cashflow',
  debt: 'reminder',
  investment: 'forecast',
  behaviour: 'anomaly',
  goal: 'reminder',
  risk: 'anomaly',
  opportunity: 'income',
  recommendation: 'reminder',
  alert: 'anomaly',
  anomaly: 'anomaly',
  milestone: 'positive',
  trend: 'forecast',
};

const SEVERITY_MAP: Record<string, PassiveSeverity> = {
  critical: 'critical',
  high: 'warning',
  medium: 'warning',
  low: 'info',
  info: 'info',
};

function mapInsightToPassive(insight: Insight, relevanceScore: number): PassiveInsight {
  return {
    id: insight.id,
    category: INSIGHT_TO_CATEGORY[insight.type] ?? 'reminder',
    title: insight.summary.split(':')[0]?.trim() ?? insight.summary.slice(0, 40),
    summary: insight.summary.length > 120
      ? `${insight.summary.slice(0, 117)}...`
      : insight.summary,
    severity: SEVERITY_MAP[insight.severity] ?? 'info',
    confidence: Math.max(0, Math.min(1, insight.confidence / 100)),
    relatedEntityId: insight.related_nodes?.[0],
    relatedEntityType: insight.related_nodes?.[1] ?? undefined,
    actionLabel: insight.recommended_actions?.[0]?.slice(0, 30),
    actionRoute: insight.deep_link,
    dismissible: true,
    relevanceScore,
    createdAt: Date.now(),
  };
}

// ─── Ranking ─────────────────────────────────────────────────────────────────

const SEVERITY_SCORES: Record<PassiveSeverity, number> = {
  critical: 1.0,
  warning: 0.75,
  info: 0.5,
  positive: 0.3,
};

function computeRelevanceScore(insight: Insight, now: number): number {
  // recency: how recent (normalized over last 24h window)
  const ageHours = (now - new Date(insight.evidence.source_references[0]?.timestamp ?? new Date().toISOString()).getTime()) / 3_600_000;
  const recency = Math.max(0, 1 - ageHours / 24);

  // severity: mapped from Insight.severity
  const severityScore = SEVERITY_SCORES[SEVERITY_MAP[insight.severity] ?? 'info'] ?? 0.5;

  // impact: derived from priority (1=highest) and value
  const priorityImpact = (5 - insight.priority + 1) / 5; // 0.2–1.0
  const monetaryImpact = insight.value_paise !== undefined && insight.value_paise > 0
    ? Math.min(1, Math.log10(insight.value_paise / 100 + 1) / 7)
    : 0.3;
  const impact = Math.max(priorityImpact, monetaryImpact);

  return recency * 0.3 + severityScore * 0.4 + impact * 0.3;
}

// ─── Deduplication ───────────────────────────────────────────────────────────

function deduplicateInsights(passiveInsights: PassiveInsight[]): PassiveInsight[] {
  const seen: Map<string, PassiveInsight> = new Map();

  for (const insight of passiveInsights) {
    // Dedup by category + similar title keyword overlap
    const keywords = insight.title.toLowerCase().split(/\s+/).filter(k => k.length > 3);
    const dedupKey = `${insight.category}:${keywords[0] ?? insight.id}`;

    const existing = seen.get(dedupKey);
    if (!existing || insight.relevanceScore > existing.relevanceScore) {
      seen.set(dedupKey, insight);
    }
  }

  return Array.from(seen.values());
}

// ─── Session State ───────────────────────────────────────────────────────────

let _dismissedIds: Set<string> = new Set();
const _listeners: Set<(insights: PassiveInsight[]) => void> = new Set();

function notify() {
  _listeners.forEach(fn => fn(getActiveInsights()));
}

// ─── Public API ──────────────────────────────────────────────────────────────

function getAllFromRuntime(): PassiveInsight[] {
  const insights = intelligenceRuntime.getInsights();
  const now = Date.now();
  const scored = insights.map(i => ({
    insight: i,
    score: computeRelevanceScore(i, now),
  }));
  scored.sort((a, b) => b.score - a.score);
  return scored.map(({ insight, score }) => mapInsightToPassive(insight, score));
}

function getActiveInsights(): PassiveInsight[] {
  let insights = getAllFromRuntime();
  insights = deduplicateInsights(insights);
  // Filter out dismissed
  insights = insights.filter(i => !_dismissedIds.has(i.id));
  // Enforce max 5
  insights = insights.slice(0, 5);
  return insights;
}

function dismiss(id: string): void {
  _dismissedIds.add(id);
  notify();
}

function undismiss(id: string): void {
  _dismissedIds.delete(id);
  notify();
}

function dismissAll(): void {
  const insights = getAllFromRuntime();
  insights.forEach(i => _dismissedIds.add(i.id));
  notify();
}

function subscribe(listener: (insights: PassiveInsight[]) => void): () => void {
  _listeners.add(listener);
  return () => {
    _listeners.delete(listener);
  };
}

function resetDismissals(): void {
  _dismissedIds.clear();
  notify();
}

// ─── Singleton Export ────────────────────────────────────────────────────────

export const passiveInsightRuntime = {
  getInsights: getActiveInsights,
  dismiss,
  undismiss,
  dismissAll,
  subscribe,
  resetDismissals,
  getAll: getAllFromRuntime,
};

export function resetPassiveInsightRuntime(): void {
  _dismissedIds.clear();
  _listeners.clear();
}
