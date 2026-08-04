/**
 * Executive Insight Runtime — Stage 8 Financial Operating System
 *
 * Manages executive-tier intelligence: threshold breach detection,
 * critical modals, warning toasts, and audit trails for all decisions.
 * Maximum 1 active executive insight at a time.
 *
 * Architecture: FINANCIAL_OS_SHELL_ARCHITECTURE.md §4.5
 */

import type { ExecutiveInsight, ExecutiveSeverity } from './types';

// ─── Audit Log ───────────────────────────────────────────────────────────────

interface AuditLogEntry {
  insightId: string;
  decision: 'action' | 'cancel' | null;
  timestamp: number;
  details?: Record<string, unknown>;
}

// ─── State ───────────────────────────────────────────────────────────────────

let _activeInsight: ExecutiveInsight | null = null;
const _auditLog: AuditLogEntry[] = [];
const _listeners: Set<() => void> = new Set();
const MAX_VISIBLE_TOASTS = 3;
let _toastQueue: ExecutiveInsight[] = [];

function notify() {
  _listeners.forEach(fn => fn());
}

// ─── ID Generator ─────────────────────────────────────────────────────────────

function generateId(): string {
  return `exec-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
}

// ─── Generation ──────────────────────────────────────────────────────────────

interface GenerateExecutiveParams {
  severity: ExecutiveSeverity;
  title: string;
  summary: string;
  requiresAction: boolean;
  actionLabel: string;
  cancelLabel?: string;
  thresholdPaise?: number;
  actualValuePaise?: number;
  onAction?: () => void;
  onCancel?: () => void;
}

function generate(params: GenerateExecutiveParams): ExecutiveInsight {
  const insight: ExecutiveInsight = {
    id: generateId(),
    severity: params.severity,
    title: params.title,
    summary: params.summary,
    requiresAction: params.requiresAction,
    actionLabel: params.actionLabel,
    cancelLabel: params.cancelLabel ?? 'Cancel',
    onAction: params.onAction,
    onCancel: params.onCancel,
    auditTrail: {
      detectedAt: Date.now(),
      ...(params.thresholdPaise !== undefined ? { threshold: params.thresholdPaise } : {}),
      ...(params.actualValuePaise !== undefined ? { actualValue: params.actualValuePaise } : {}),
    },
    acknowledged: false,
    decisions: [],
  };

  if (params.severity === 'critical') {
    // Critical insights replace any existing active insight (modal, blocks interaction)
    _activeInsight = insight;
  } else {
    // Warning insights go to toast queue (max visible = 3)
    _toastQueue.push(insight);
    if (_toastQueue.length > MAX_VISIBLE_TOASTS) {
      _toastQueue.shift();
    }
  }

  notify();
  return insight;
}

// ─── Query ────────────────────────────────────────────────────────────────────

function getActiveInsight(): ExecutiveInsight | null {
  return _activeInsight;
}

function getToastQueue(): ExecutiveInsight[] {
  return [..._toastQueue];
}

function getAuditLog(limit = 50): AuditLogEntry[] {
  return _auditLog.slice(-limit);
}

// ─── Acknowledgement & Decision Logging ───────────────────────────────────────

function acknowledge(id: string): void {
  if (_activeInsight?.id === id) {
    _activeInsight = null;
    notify();
  }
}

function logDecision(insightId: string, decision: 'action' | 'cancel', details?: Record<string, unknown>): void {
  _auditLog.push({
    insightId,
    decision,
    timestamp: Date.now(),
    ...(details ? { details } : {}),
  });
}

function executeAction(insightId: string): void {
  const insight = _activeInsight;
  if (insight?.id !== insightId) return;

  logDecision(insightId, 'action');
  insight.onAction?.();
  _activeInsight = null;
  notify();
}

function executeCancel(insightId: string): void {
  const insight = _activeInsight;
  if (insight?.id !== insightId) return;

  logDecision(insightId, 'cancel');
  insight.onCancel?.();
  _activeInsight = null;
  notify();
}

// ─── Toast Dismissal ─────────────────────────────────────────────────────────

function dismissToast(id: string): void {
  _toastQueue = _toastQueue.filter(t => t.id !== id);
  notify();
}

function clearAllToasts(): void {
  _toastQueue = [];
  notify();
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
  _activeInsight = null;
  _toastQueue = [];
  _auditLog.length = 0;
  _listeners.clear();
}

// ─── Singleton Export ─────────────────────────────────────────────────────────

export const executiveInsightRuntime = {
  generate,
  getActiveInsight,
  getToastQueue,
  getAuditLog,
  acknowledge,
  logDecision,
  executeAction,
  executeCancel,
  dismissToast,
  clearAllToasts,
  subscribe,
  reset,
};

export function resetExecutiveInsightRuntime(): void {
  reset();
}
