/**
 * Notification Runtime — Stage 10 Financial Operating System
 *
 * Manages user-facing notifications: toasts, badges, notification center.
 * Maximum 3 visible toasts. Non-critical auto-dismiss after 5s.
 * Critical notifications persist until dismissed.
 *
 * Architecture: FINANCIAL_OS_SHELL_ARCHITECTURE.md §10.3 (Notification Runtime)
 */

// ─── Types ────────────────────────────────────────────────────────────────────

export type NotificationSeverity = 'info' | 'success' | 'warning' | 'error';

export interface Notification {
  id: string;
  severity: NotificationSeverity;
  title: string;
  message: string;
  duration: number; // ms, 0 = persistent (critical)
  actionLabel?: string;
  actionRoute?: string;
  source: string; // runtime name
  timestamp: number;
  acknowledged: boolean;
}

// ─── State ────────────────────────────────────────────────────────────────────

const MAX_VISIBLE = 3;
const AUTO_DISMISS_MS = 5000;

let _notifications: Notification[] = [];
const _listeners = new Set<() => void>();

function notify() {
  _listeners.forEach(fn => fn());
}

function generateId(): string {
  return `notif-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
}

// ─── Show / Dismiss ───────────────────────────────────────────────────────────

function show(params: {
  severity: NotificationSeverity;
  title: string;
  message: string;
  duration?: number;
  actionLabel?: string;
  actionRoute?: string;
  source?: string;
}): Notification {
  const notif: Notification = {
    id: generateId(),
    severity: params.severity,
    title: params.title,
    message: params.message,
    duration: params.duration ?? (params.severity === 'error' || params.severity === 'warning' ? 0 : AUTO_DISMISS_MS),
    actionLabel: params.actionLabel,
    actionRoute: params.actionRoute,
    source: params.source ?? 'unknown',
    timestamp: Date.now(),
    acknowledged: false,
  };

  _notifications.unshift(notif);
  if (_notifications.length > MAX_VISIBLE) {
    _notifications = _notifications.slice(0, MAX_VISIBLE);
  }
  notify();

  // Auto-dismiss non-persistent notifications
  if (notif.duration > 0) {
    setTimeout(() => {
      dismiss(notif.id);
    }, notif.duration);
  }

  return notif;
}

function dismiss(id: string): void {
  _notifications = _notifications.filter(n => n.id !== id);
  notify();
}

function acknowledge(id: string): void {
  const idx = _notifications.findIndex(n => n.id === id);
  if (idx >= 0) {
    _notifications[idx] = { ..._notifications[idx], acknowledged: true };
    notify();
  }
}

function clearAll(): void {
  _notifications = [];
  notify();
}

// ─── Query ────────────────────────────────────────────────────────────────────

function getActive(): Notification[] {
  return [..._notifications];
}

function getHistory(limit = 50): Notification[] {
  return [..._notifications].slice(0, limit);
}

function getBySource(source: string): Notification[] {
  return _notifications.filter(n => n.source === source);
}

// ─── Subscriptions ────────────────────────────────────────────────────────────

function subscribe(listener: () => void): () => void {
  _listeners.add(listener);
  return () => {
    _listeners.delete(listener);
  };
}

// ─── Reset ────────────────────────────────────────────────────────────────────

function reset(): void {
  _notifications = [];
  _listeners.clear();
}

// ─── Convenience Wrappers ─────────────────────────────────────────────────────

function showError(title: string, message: string, source = 'System'): Notification {
  return show({ severity: 'error', title, message, source });
}

function showWarning(title: string, message: string, source = 'System'): Notification {
  return show({ severity: 'warning', title, message, source });
}

function showSuccess(title: string, message: string, source = 'System'): Notification {
  return show({ severity: 'success', title, message, source });
}

function showInfo(title: string, message: string, source = 'System'): Notification {
  return show({ severity: 'info', title, message, source });
}

// ─── Singleton Export ──────────────────────────────────────────────────────────

export const notificationRuntime = {
  show,
  dismiss,
  acknowledge,
  clearAll,
  getActive,
  getHistory,
  getBySource,
  subscribe,
  reset,
  showError,
  showWarning,
  showSuccess,
  showInfo,
};

export function resetNotificationRuntime(): void {
  reset();
}
