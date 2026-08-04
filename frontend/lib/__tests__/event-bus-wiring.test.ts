/**
 * Runtime Event Bus Wiring Tests — Stage 9
 *
 * Verifies that each frozen runtime publishes events through the event bus
 * when its state changes.
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { runtimeEventBus, resetRuntimeEventBus } from '../event-bus';
import { selectionRuntime, resetSelectionRuntime } from '../runtime/selection-runtime';
import { timelineRuntime, resetTimelineRuntime } from '../runtime/timeline-runtime';
import { navigationRuntime, resetNavigationRuntime } from '../runtime/navigation-runtime';
import {
  SELECTION_CHANGED,
  SELECTION_CLEARED,
  TIMELINE_CHANGED,
  TIMELINE_GRANULARITY_CHANGED,
  NAVIGATION_COMPLETED,
  NAVIGATION_BACK,
} from '../event-bus';

describe('Runtime Event Bus Wiring', () => {
  beforeEach(() => {
    resetRuntimeEventBus();
    resetSelectionRuntime();
    resetTimelineRuntime();
    resetNavigationRuntime();
  });

  describe('SelectionRuntime', () => {
    it('should publish SelectionChanged when entity is selected', () => {
      const handler = vi.fn();
      runtimeEventBus.subscribe(SELECTION_CHANGED, handler);
      selectionRuntime.selectEntity({ type: 'transaction', id: 'tx-1' });
      expect(handler).toHaveBeenCalledTimes(1);
      expect(handler.mock.calls[0][0].payload.activeEntityId).toBe('tx-1');
    });

    it('should publish SelectionCleared when selection is cleared', () => {
      const handler = vi.fn();
      runtimeEventBus.subscribe(SELECTION_CLEARED, handler);
      selectionRuntime.selectEntity({ type: 'transaction', id: 'tx-1' });
      selectionRuntime.clearSelection();
      expect(handler).toHaveBeenCalledTimes(1);
      expect(handler.mock.calls[0][0].payload.previousEntityId).toBe('tx-1');
    });
  });

  describe('TimelineRuntime', () => {
    it('should publish TimelineChanged when position is set', () => {
      const handler = vi.fn();
      runtimeEventBus.subscribe(TIMELINE_CHANGED, handler);
      timelineRuntime.setPosition('2024-06-15');
      expect(handler).toHaveBeenCalledTimes(1);
    });

    it('should publish TimelineGranularityChanged when granularity changes', () => {
      const handler = vi.fn();
      runtimeEventBus.subscribe(TIMELINE_GRANULARITY_CHANGED, handler);
      timelineRuntime.setGranularity('quarter');
      expect(handler).toHaveBeenCalledTimes(1);
      expect(handler.mock.calls[0][0].payload.granularity).toBe('quarter');
    });
  });

  describe('NavigationRuntime', () => {
    it('should publish NavigationCompleted when pushing a path', () => {
      const handler = vi.fn();
      runtimeEventBus.subscribe(NAVIGATION_COMPLETED, handler);
      navigationRuntime.pushPath('/transactions', 'transactions');
      expect(handler).toHaveBeenCalledTimes(1);
      expect(handler.mock.calls[0][0].payload.route).toBe('/transactions');
    });

    it('should publish NavigationBack when going back', () => {
      const handler = vi.fn();
      runtimeEventBus.subscribe(NAVIGATION_BACK, handler);
      navigationRuntime.pushPath('/dashboard');
      navigationRuntime.pushPath('/transactions');
      navigationRuntime.goBack();
      expect(handler).toHaveBeenCalledTimes(1);
    });
  });
});

