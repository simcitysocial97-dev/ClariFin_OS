/**
 * Notification Runtime — Public API
 *
 * Manages user-facing notifications (toasts, badges).
 * Maximum 3 visible. Non-critical auto-dismiss after 5s.
 * Architecture: FINANCIAL_OS_SHELL_ARCHITECTURE.md §10.3
 */

export type { Notification, NotificationSeverity } from './runtime';

export {
  notificationRuntime,
  resetNotificationRuntime,
} from './runtime';
