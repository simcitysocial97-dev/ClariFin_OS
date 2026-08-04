/**
 * Executive Insight Runtime Tests — Stage 8
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import {
  executiveInsightRuntime,
  resetExecutiveInsightRuntime,
} from '../executive-runtime';
import type { ExecutiveSeverity } from '../types';

describe('ExecutiveInsightRuntime', () => {
  beforeEach(() => {
    resetExecutiveInsightRuntime();
  });

  const warningParams = {
    severity: 'warning' as ExecutiveSeverity,
    title: 'Subscription Growth Detected',
    summary: 'Your subscriptions increased by 25% this month',
    requiresAction: false,
    actionLabel: 'Review Subscriptions',
    thresholdPaise: 100000,
    actualValuePaise: 125000,
  };

  const criticalParams = {
    severity: 'critical' as ExecutiveSeverity,
    title: 'Account Balance Below Threshold',
    summary: 'Savings account balance is below the 3-month emergency fund target',
    requiresAction: true,
    actionLabel: 'Review Savings Plan',
    cancelLabel: 'Dismiss',
    thresholdPaise: 900000,
    actualValuePaise: 450000,
  };

  it('should generate a warning insight (toast queue)', () => {
    const insight = executiveInsightRuntime.generate(warningParams);
    expect(insight).toBeDefined();
    expect(insight.severity).toBe('warning');
    expect(insight.title).toBe('Subscription Growth Detected');
    expect(insight.requiresAction).toBe(false);
    expect(insight.auditTrail.detectedAt).toBeGreaterThan(0);
    expect(insight.auditTrail.threshold).toBe(100000);
    expect(insight.auditTrail.actualValue).toBe(125000);
  });

  it('should generate a critical insight (active modal)', () => {
    const insight = executiveInsightRuntime.generate(criticalParams);
    expect(insight).toBeDefined();
    expect(insight.severity).toBe('critical');
    expect(insight.requiresAction).toBe(true);
  });

  it('should have exactly one active critical insight at a time', () => {
    executiveInsightRuntime.generate(criticalParams);
    const first = executiveInsightRuntime.getActiveInsight();
    expect(first).not.toBeNull();

    const second = executiveInsightRuntime.generate({
      ...criticalParams,
      title: 'Second Critical Insight',
    });
    // Second replaces the first
    const active = executiveInsightRuntime.getActiveInsight();
    expect(active?.id).toBe(second.id);
    expect(active?.title).toBe('Second Critical Insight');
  });

  it('should queue multiple warning insights (max 3)', () => {
    executiveInsightRuntime.generate(warningParams);
    executiveInsightRuntime.generate({ ...warningParams, title: 'Warning 2' });
    executiveInsightRuntime.generate({ ...warningParams, title: 'Warning 3' });
    executiveInsightRuntime.generate({ ...warningParams, title: 'Warning 4' });

    const queue = executiveInsightRuntime.getToastQueue();
    expect(queue).toHaveLength(3);
    expect(queue[2].title).toBe('Warning 4'); // LRU eviction
  });

  it('should acknowledge and remove active critical insight', () => {
    const insight = executiveInsightRuntime.generate(criticalParams);
    executiveInsightRuntime.acknowledge(insight.id);
    expect(executiveInsightRuntime.getActiveInsight()).toBeNull();
  });

  it('should log decision on action execution', () => {
    const insight = executiveInsightRuntime.generate(criticalParams);
    executiveInsightRuntime.executeAction(insight.id);
    const log = executiveInsightRuntime.getAuditLog();
    expect(log).toHaveLength(1);
    expect(log[0].decision).toBe('action');
    expect(log[0].insightId).toBe(insight.id);
  });

  it('should log decision on cancel execution', () => {
    const insight = executiveInsightRuntime.generate(criticalParams);
    executiveInsightRuntime.executeCancel(insight.id);
    const log = executiveInsightRuntime.getAuditLog();
    expect(log).toHaveLength(1);
    expect(log[0].decision).toBe('cancel');
  });

  it('should dismiss toast from queue', () => {
    executiveInsightRuntime.generate(warningParams);
    const queueBefore = executiveInsightRuntime.getToastQueue();
    expect(queueBefore).toHaveLength(1);
    executiveInsightRuntime.dismissToast(queueBefore[0].id);
    expect(executiveInsightRuntime.getToastQueue()).toHaveLength(0);
  });

  it('should clear all toasts', () => {
    executiveInsightRuntime.generate(warningParams);
    executiveInsightRuntime.generate({ ...warningParams, title: 'Warning 2' });
    executiveInsightRuntime.clearAllToasts();
    expect(executiveInsightRuntime.getToastQueue()).toHaveLength(0);
  });

  it('should notify subscribers on changes', () => {
    const listener = vi.fn();
    executiveInsightRuntime.subscribe(listener);
    executiveInsightRuntime.generate(criticalParams);
    expect(listener).toHaveBeenCalledOnce();
  });

  it('should reset all state', () => {
    executiveInsightRuntime.generate(criticalParams);
    executiveInsightRuntime.generate(warningParams);
    resetExecutiveInsightRuntime();
    expect(executiveInsightRuntime.getActiveInsight()).toBeNull();
    expect(executiveInsightRuntime.getToastQueue()).toHaveLength(0);
    expect(executiveInsightRuntime.getAuditLog()).toHaveLength(0);
  });

  it('should enforce maximum 1 executive insight active at a time', () => {
    executiveInsightRuntime.generate(criticalParams);
    executiveInsightRuntime.generate({
      ...criticalParams,
      title: 'Another Critical',
    });
    // Only the latest critical insight is active
    expect(executiveInsightRuntime.getActiveInsight()?.title).toBe('Another Critical');
  });

  it('should not auto-dismiss critical insights', () => {
    const insight = executiveInsightRuntime.generate(criticalParams);
    // Critical insights persist until explicitly acknowledged
    expect(executiveInsightRuntime.getActiveInsight()?.id).toBe(insight.id);
  });
});
