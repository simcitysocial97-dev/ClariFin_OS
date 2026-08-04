/**
 * Notification Runtime Tests — Stage 10
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import {
  notificationRuntime,
  resetNotificationRuntime,
} from '../notification/runtime';

describe('NotificationRuntime', () => {
  beforeEach(() => {
    resetNotificationRuntime();
  });

  it('should show a notification', () => {
    const notif = notificationRuntime.show({
      severity: 'info',
      title: 'Test',
      message: 'Hello',
      source: 'test',
    });
    expect(notif).toBeDefined();
    expect(notif.title).toBe('Test');
    expect(notif.severity).toBe('info');
  });

  it('should enforce max 3 visible notifications', () => {
    notificationRuntime.show({ severity: 'info', title: 'N1', message: 'm', source: 't' });
    notificationRuntime.show({ severity: 'warning', title: 'N2', message: 'm', source: 't' });
    notificationRuntime.show({ severity: 'error', title: 'N3', message: 'm', source: 't' });
    notificationRuntime.show({ severity: 'success', title: 'N4', message: 'm', source: 't' });

    const active = notificationRuntime.getActive();
    expect(active).toHaveLength(3);
    expect(active[0].title).toBe('N4'); // newest first
  });

  it('should dismiss a notification', () => {
    const n1 = notificationRuntime.show({ severity: 'info', title: 'N1', message: 'm', source: 't' });
    notificationRuntime.dismiss(n1.id);
    expect(notificationRuntime.getActive()).toHaveLength(0);
  });

  it('should acknowledge a notification', () => {
    const n1 = notificationRuntime.show({ severity: 'info', title: 'N1', message: 'm', source: 't' });
    notificationRuntime.acknowledge(n1.id);
    const active = notificationRuntime.getActive();
    expect(active[0].acknowledged).toBe(true);
  });

  it('should clear all notifications', () => {
    notificationRuntime.show({ severity: 'info', title: 'N1', message: 'm', source: 't' });
    notificationRuntime.show({ severity: 'warning', title: 'N2', message: 'm', source: 't' });
    notificationRuntime.clearAll();
    expect(notificationRuntime.getActive()).toHaveLength(0);
  });

  it('should subscribe to changes', () => {
    const listener = vi.fn();
    notificationRuntime.subscribe(listener);
    notificationRuntime.show({ severity: 'info', title: 'N1', message: 'm', source: 't' });
    expect(listener).toHaveBeenCalledOnce();
  });

  it('should set persistent duration for error/warning', () => {
    const errorNotif = notificationRuntime.show({ severity: 'error', title: 'Err', message: 'm', source: 't' });
    const warnNotif = notificationRuntime.show({ severity: 'warning', title: 'Warn', message: 'm', source: 't' });
    expect(errorNotif.duration).toBe(0);
    expect(warnNotif.duration).toBe(0);
  });

  it('should auto-dismiss info/success notifications', () => {
    const infoNotif = notificationRuntime.show({ severity: 'info', title: 'Info', message: 'm', source: 't' });
    expect(infoNotif.duration).toBe(5000);
  });

  it('should get history', () => {
    notificationRuntime.show({ severity: 'info', title: 'N1', message: 'm', source: 't' });
    notificationRuntime.show({ severity: 'warning', title: 'N2', message: 'm', source: 't' });
    const history = notificationRuntime.getHistory();
    expect(history).toHaveLength(2);
  });

  it('should filter by source', () => {
    notificationRuntime.show({ severity: 'info', title: 'N1', message: 'm', source: 'auth' });
    notificationRuntime.show({ severity: 'warning', title: 'N2', message: 'm', source: 'graph' });
    const authNotifications = notificationRuntime.getBySource('auth');
    expect(authNotifications).toHaveLength(1);
    expect(authNotifications[0].title).toBe('N1');
  });

  it('should reset all state', () => {
    notificationRuntime.show({ severity: 'info', title: 'N1', message: 'm', source: 't' });
    resetNotificationRuntime();
    expect(notificationRuntime.getActive()).toHaveLength(0);
  });
});
