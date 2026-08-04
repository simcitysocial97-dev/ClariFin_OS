/**
 * Runtime Event Bus Tests — Stage 9
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import {
  runtimeEventBus,
  resetRuntimeEventBus,
  SELECTION_CHANGED,
  TIMELINE_CHANGED,
  WORKSPACE_SWITCHED,
  NAVIGATION_COMPLETED,
  GRAPH_OVERLAY_OPENED,
  INSIGHT_GENERATED,
} from '../event-bus';

describe('RuntimeEventBus', () => {
  beforeEach(() => {
    resetRuntimeEventBus();
  });

  it('should publish and receive typed events', () => {
    const handler = vi.fn();
    runtimeEventBus.subscribe(SELECTION_CHANGED, handler);
    runtimeEventBus.publish({
      type: SELECTION_CHANGED,
      timestamp: Date.now(),
      source: 'SelectionRuntime',
      payload: { activeEntityId: 'tx-1', selectedIds: [], selectionRange: null },
    });
    expect(handler).toHaveBeenCalledTimes(1);
    expect(handler.mock.calls[0][0].payload.activeEntityId).toBe('tx-1');
  });

  it('should notify all-subscribers of any event', () => {
    const allHandler = vi.fn();
    runtimeEventBus.subscribeAll(allHandler);
    runtimeEventBus.publish({
      type: TIMELINE_CHANGED,
      timestamp: Date.now(),
      source: 'TimelineRuntime',
      payload: { activePeriod: { start: '', end: '', label: '' }, granularity: 'month', comparisonPeriod: null },
    });
    expect(allHandler).toHaveBeenCalledTimes(1);
  });

  it('should return unsubscribe function that removes subscriber', () => {
    const handler = vi.fn();
    const unsub = runtimeEventBus.subscribe(SELECTION_CHANGED, handler);
    unsub();
    runtimeEventBus.publish({
      type: SELECTION_CHANGED,
      timestamp: Date.now(),
      source: 'SelectionRuntime',
      payload: { activeEntityId: 'tx-1', selectedIds: [], selectionRange: null },
    });
    expect(handler).not.toHaveBeenCalled();
  });

  it('should isolate subscriber errors', () => {
    const goodHandler = vi.fn();
    const badHandler = vi.fn(() => { throw new Error('subscriber error'); });
    runtimeEventBus.subscribe(SELECTION_CHANGED, goodHandler);
    runtimeEventBus.subscribe(SELECTION_CHANGED, badHandler);

    // Should not throw
    expect(() => {
      runtimeEventBus.publish({
        type: SELECTION_CHANGED,
        timestamp: Date.now(),
        source: 'SelectionRuntime',
        payload: { activeEntityId: 'tx-1', selectedIds: [], selectionRange: null },
      });
    }).not.toThrow();

    expect(goodHandler).toHaveBeenCalledTimes(1);
    expect(badHandler).toHaveBeenCalledTimes(1);
  });

  it('should debounce high-frequency events', () => {
    vi.useFakeTimers();
    const handler = vi.fn();
    runtimeEventBus.subscribe(TIMELINE_CHANGED, handler);
    const debounced = runtimeEventBus.debouncedPublish(TIMELINE_CHANGED, 50);

    debounced({
      activePeriod: { start: '2024-01-01', end: '2024-01-31', label: 'Jan 2024' },
      granularity: 'month',
      comparisonPeriod: null,
    });
    debounced({
      activePeriod: { start: '2024-02-01', end: '2024-02-28', label: 'Feb 2024' },
      granularity: 'month',
      comparisonPeriod: null,
    });

    // Should not have fired yet (debounce delay)
    expect(handler).toHaveBeenCalledTimes(0);

    // Wait for debounce
    vi.advanceTimersByTime(100);
    expect(handler).toHaveBeenCalledTimes(1);
    vi.useRealTimers();
  });

  it('should handle multiple subscribers of same event type', () => {
    const handler1 = vi.fn();
    const handler2 = vi.fn();
    runtimeEventBus.subscribe(WORKSPACE_SWITCHED, handler1);
    runtimeEventBus.subscribe(WORKSPACE_SWITCHED, handler2);

    runtimeEventBus.publish({
      type: WORKSPACE_SWITCHED,
      timestamp: Date.now(),
      source: 'WorkspaceRuntime',
      payload: { fromWorkspaceId: 'dashboard', toWorkspaceId: 'transactions', transitionType: 'cached-restore' },
    });

    expect(handler1).toHaveBeenCalledTimes(1);
    expect(handler2).toHaveBeenCalledTimes(1);
  });

  it('should publish navigation completed event with correct payload', () => {
    const handler = vi.fn();
    runtimeEventBus.subscribe(NAVIGATION_COMPLETED, handler);

    runtimeEventBus.publish({
      type: NAVIGATION_COMPLETED,
      timestamp: Date.now(),
      source: 'NavigationRuntime',
      payload: { route: '/transactions', workspaceId: 'transactions' },
    });

    expect(handler).toHaveBeenCalledTimes(1);
    expect(handler.mock.calls[0][0].payload.route).toBe('/transactions');
  });

  it('should publish graph overlay opened event', () => {
    const handler = vi.fn();
    runtimeEventBus.subscribe(GRAPH_OVERLAY_OPENED, handler);

    runtimeEventBus.publish({
      type: GRAPH_OVERLAY_OPENED,
      timestamp: Date.now(),
      source: 'GraphRuntime',
      payload: { scope: { trigger: 'command', mode: 'overlay' }, layout: 'force-directed' },
    });

    expect(handler).toHaveBeenCalledTimes(1);
  });

  it('should publish insight generated event', () => {
    const handler = vi.fn();
    runtimeEventBus.subscribe(INSIGHT_GENERATED, handler);

    runtimeEventBus.publish({
      type: INSIGHT_GENERATED,
      timestamp: Date.now(),
      source: 'IntelligenceRuntime',
      payload: { insightId: 'ins-1', tier: 'investigative' },
    });

    expect(handler).toHaveBeenCalledTimes(1);
    expect(handler.mock.calls[0][0].payload.tier).toBe('investigative');
  });

  it('should reset clears all subscribers', () => {
    const handler = vi.fn();
    runtimeEventBus.subscribe(SELECTION_CHANGED, handler);
    resetRuntimeEventBus();

    runtimeEventBus.publish({
      type: SELECTION_CHANGED,
      timestamp: Date.now(),
      source: 'SelectionRuntime',
      payload: { activeEntityId: 'tx-1', selectedIds: [], selectionRange: null },
    });
    expect(handler).not.toHaveBeenCalled();
  });
});
