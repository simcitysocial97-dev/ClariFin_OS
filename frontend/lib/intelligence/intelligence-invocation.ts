/**
 * Intelligence Invocation Layer — Stage 8 Financial Operating System
 *
 * Connects CommandRuntime, SelectionRuntime, and PassiveInsightRuntime
 * to the InvestigativeInsightRuntime as user-initiated drill-down triggers.
 *
 * Architecture: FINANCIAL_OS_SHELL_ARCHITECTURE.md §4.4
 */

import { investigativeInsightRuntime } from './investigative-runtime';
import { selectionRuntime } from '../runtime/selection-runtime';
import { passiveInsightRuntime } from './passive-runtime';
import type { InvestigativeTrigger } from './types';
import { runtimeEventBus, INSIGHT_GENERATED, INSIGHT_DISMISSED } from '../event-bus';

// ===== State ────────────────────────────────────────────────────────────────

const _listeners = new Set<() => void>();

function notify() {
  _listeners.forEach(fn => fn());
}

// ===== Generate Investigative Insight ───────────────────────────────────────

function generateFromSelection(trigger: InvestigativeTrigger, entityId?: string): void {
  investigativeInsightRuntime.generate({
    trigger,
    title: entityId ? `Investigation: ${entityId.slice(0, 12)}` : 'Entity Investigation',
    summary: entityId
      ? `Exploring relationships and patterns for entity ${entityId}. Review evidence trails and drill-down actions below.`
      : 'No entity selected. Select an entity to investigate its relationships.',
    evidenceTrail: entityId
      ? [
          {
            label: `Transaction linked to ${entityId}`,
            sourceType: 'transaction',
            sourceId: entityId,
            confidence: 0.92,
          },
        ]
      : [],
    relatedEntities: entityId
      ? [
          {
            entityId,
            entityType: 'transaction',
            label: `Entity ${entityId.slice(0, 8)}`,
            relationshipType: 'SOURCE',
          },
        ]
      : [],
    drillDownActions: entityId
      ? [
          {
            label: 'View in Transactions',
            targetWorkspace: 'transactions',
            contextPayload: { preselect: entityId },
          },
          {
            label: 'View in Graph',
            targetRoute: '/graph',
          },
        ]
      : [
          {
            label: 'Open Transactions Workspace',
            targetWorkspace: 'transactions',
          },
        ],
  });
  notify();
  runtimeEventBus.publish({
    type: INSIGHT_GENERATED,
    timestamp: Date.now(),
    source: 'IntelligenceRuntime',
    payload: { insightId: '', tier: 'investigative' },
  });
}

function handlePassiveInsightClick(passiveInsightId: string): void {
  const passiveInsight = passiveInsightRuntime.getAll().find(i => i.id === passiveInsightId);
  if (!passiveInsight) return;

  const trigger: InvestigativeTrigger = 'insight-clicked';
  investigativeInsightRuntime.generate({
    trigger,
    title: `Drill-down: ${passiveInsight.title}`,
    summary: passiveInsight.summary,
    evidenceTrail: passiveInsight.relatedEntityId
      ? [
          {
            label: `Source: ${passiveInsight.relatedEntityType ?? 'entity'}`,
            sourceType: 'transaction',
            sourceId: passiveInsight.relatedEntityId,
            confidence: passiveInsight.confidence,
          },
        ]
      : [],
    relatedEntities: passiveInsight.relatedEntityId
      ? [
          {
            entityId: passiveInsight.relatedEntityId,
            entityType: passiveInsight.relatedEntityType ?? 'unknown',
            label: passiveInsight.title,
            relationshipType: 'RELATED_TO',
          },
        ]
      : [],
    drillDownActions: [
      ...(passiveInsight.actionRoute
        ? [{ label: passiveInsight.actionLabel ?? 'Navigate', targetRoute: passiveInsight.actionRoute }]
        : []),
      { label: 'View in Workspace', targetWorkspace: 'transactions' },
    ],
  });
  notify();
  runtimeEventBus.publish({
    type: INSIGHT_GENERATED,
    timestamp: Date.now(),
    source: 'IntelligenceRuntime',
    payload: { insightId: passiveInsightId, tier: 'investigative' },
  });
}

// ===== Public API ────────────────────────────────────────────────────────────

export const intelligenceInvocation = {
  generateFromSelection,
  handlePassiveInsightClick,
  subscribe: (fn: () => void) => {
    _listeners.add(fn);
    return () => { _listeners.delete(fn); };
  },
};

// ===== Runtime Integration — Command Events ──────────────────────────────────

function initCommandEventHandlers() {
  const investigateHandler = () => {
    const entity = selectionRuntime.state.active;
    const entityId = entity?.id ? String(entity.id) : undefined;
    investigativeInsightRuntime.generate({
      trigger: 'command-issued',
      title: 'Entity Investigation',
      summary: entityId
        ? `Investigating entity ${entityId}. Review evidence and drill-down options.`
        : 'Select an entity first, then use the investigate command to explore relationships.',
      evidenceTrail: [],
      relatedEntities: [],
      drillDownActions: entityId
        ? [
            { label: 'View Details', targetWorkspace: 'transactions', contextPayload: { preselect: entityId } },
            { label: 'Explore in Graph', targetWorkspace: 'graph' },
          ]
        : [
            { label: 'Open Transactions', targetWorkspace: 'transactions' },
          ],
    });
    notify();
    runtimeEventBus.publish({
      type: INSIGHT_GENERATED,
      timestamp: Date.now(),
      source: 'IntelligenceRuntime',
      payload: { insightId: '', tier: 'investigative' },
    });
  };

  const clearHandler = () => {
    investigativeInsightRuntime.clearDismissed();
    notify();
    runtimeEventBus.publish({
      type: INSIGHT_DISMISSED,
      timestamp: Date.now(),
      source: 'IntelligenceRuntime',
      payload: { insightId: 'all', reason: 'command-clear' },
    });
  };

  window.addEventListener('os-intelligence-investigate', investigateHandler);
  window.addEventListener('os-intelligence-clear', clearHandler);

  return () => {
    window.removeEventListener('os-intelligence-investigate', investigateHandler);
    window.removeEventListener('os-intelligence-clear', clearHandler);
  };
}

// ===== Runtime Integration — Keyboard Shortcut (Cmd/Ctrl+I) ─────────────────

function initKeyboardShortcut() {
  const handler = (e: KeyboardEvent) => {
    if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'i' && !e.shiftKey && !e.altKey) {
      e.preventDefault();
      window.dispatchEvent(new CustomEvent('os-intelligence-investigate'));
    }
  };
  window.addEventListener('keydown', handler);
  return () => window.removeEventListener('keydown', handler);
}

// ===== Init ──────────────────────────────────────────────────────────────────

// These installers attach `window` event listeners, so they must not run during
// server-side rendering / static prerendering, where `window` is undefined.
// Guarding at the single module-level call site keeps the browser behaviour
// identical while making the module safe to import from a server context.
if (typeof window !== 'undefined') {
  initCommandEventHandlers();
  initKeyboardShortcut();
}

export function resetIntelligenceInvocation() {
  investigativeInsightRuntime.clearDismissed();
}
