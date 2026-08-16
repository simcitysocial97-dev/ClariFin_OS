/**
 * Context Runtime Tests — Stage 10
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import {
  contextRuntime,
  resetContextRuntime,
} from '../context/runtime';
import { selectionRuntime, resetSelectionRuntime } from '../runtime/selection-runtime';
import { timelineRuntime, resetTimelineRuntime } from '../runtime/timeline-runtime';

describe('ContextRuntime', () => {
  beforeEach(() => {
    resetContextRuntime();
    resetSelectionRuntime();
    resetTimelineRuntime();
  });

  it('should compose a valid ContextObject from runtime states', () => {
    const ctx = contextRuntime.getContext();
    expect(ctx).toBeDefined();
    expect(ctx.selection).toBeDefined();
    expect(ctx.timeline).toBeDefined();
    expect(ctx.workspace).toBeDefined();
    expect(ctx.scenario).toBeDefined();
    expect(ctx.filters).toBeDefined();
    expect(ctx.household).toBeDefined();
    expect(ctx.metadata).toBeDefined();
    expect(typeof ctx.metadata.timestamp).toBe('number');
    expect(typeof ctx.metadata.version).toBe('string');
    expect(typeof ctx.metadata.sessionId).toBe('string');
  });

  it('should reflect selection state changes', () => {
    selectionRuntime.selectEntity({ type: 'transaction', id: 'tx-42' });
    const ctx = contextRuntime.getContext();
    expect(ctx.selection.activeEntityId).toBe('tx-42');
    expect(ctx.selection.activeEntityType).toBe('transaction');
  });

  it('should reflect timeline state changes', () => {
    timelineRuntime.setPosition('2024-06-15');
    timelineRuntime.setGranularity('quarter');
    const ctx = contextRuntime.getContext();
    expect(ctx.timeline.activePeriod.start).toBe('2024-06-15');
    expect(ctx.timeline.granularity).toBe('quarter');
  });

  it('should subscribe to context changes', () => {
    const listener = vi.fn();
    contextRuntime.subscribe(listener);
    selectionRuntime.selectEntity({ type: 'loan', id: 'ln-1' });
    expect(listener).toHaveBeenCalledOnce();
  });

  it('should return selector results from context', () => {
    selectionRuntime.selectEntity({ type: 'account', id: 'acc-1' });
    const workspaceId = contextRuntime.select(ctx => ctx.workspace.activeWorkspaceId);
    expect(typeof workspaceId).toBe('string');
  });

  it('should reset all composed state', () => {
    selectionRuntime.selectEntity({ type: 'transaction', id: 'tx-1' });
    resetContextRuntime();
    const ctx = contextRuntime.getContext();
    expect(ctx.selection.activeEntityId).toBeNull();
  });
});
