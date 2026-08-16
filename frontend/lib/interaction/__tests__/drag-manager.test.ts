/**
 * Drag Manager Tests - Milestone 9 Interaction Polish
 *
 * Tests for drag session lifecycle, drop target registration,
 * position tracking, and subscription behavior.
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { dragManager } from '../drag-manager';

describe('DragManager — Milestone 9', () => {
  beforeEach(() => {
    dragManager.reset();
  });

  describe('Drag Session Lifecycle', () => {
    it('starts a drag session and returns session ID', () => {
      const id = dragManager.startDrag({ type: 'transaction', id: 'tx-1' });
      expect(id).toMatch(/^drag-/);
      const state = dragManager.getState();
      expect(state.isDragging).toBe(true);
      expect(state.activeType).toBe('transaction');
    });

    it('updates drag position', () => {
      const sessionId = dragManager.startDrag({ type: 'transaction', id: 'tx-1' });
      dragManager.updatePosition(sessionId, 100, 200);
      const state = dragManager.getState();
      expect(state.position).toEqual({ x: 100, y: 200 });
    });

    it('updates position for wrong session ID does nothing', () => {
      dragManager.startDrag({ type: 'transaction', id: 'tx-1' });
      dragManager.updatePosition('wrong-session', 100, 200);
      expect(dragManager.getState().position).toBeNull();
    });

    it('ends drag and returns data', () => {
      dragManager.startDrag({ type: 'transaction', id: 'tx-1' });
      const { data, targetId } = dragManager.endDrag('target-1');
      expect(data).not.toBeNull();
      expect(data?.type).toBe('transaction');
      expect(targetId).toBe('target-1');

      const state = dragManager.getState();
      expect(state.isDragging).toBe(false);
    });

    it('cancelDrag clears session', () => {
      dragManager.startDrag({ type: 'transaction', id: 'tx-1' });
      dragManager.cancelDrag();
      const state = dragManager.getState();
      expect(state.isDragging).toBe(false);
      expect(state.activeType).toBeNull();
    });

    it('drop returns data and clears dragging state', () => {
      dragManager.startDrag({ type: 'account', id: 'acc-1' });
      const data = dragManager.drop('target-2');
      expect(data?.type).toBe('account');
      expect(dragManager.getState().isDragging).toBe(false);
    });

    it('drop without active session returns null', () => {
      expect(dragManager.drop('target')).toBeNull();
    });
  });

  describe('Drop Target Management', () => {
    const mockEl = { id: 'mock' } as unknown as HTMLElement;

    beforeEach(() => {
      dragManager.startDrag({ type: 'transaction', id: 'tx-1' });
    });

    it('registers a drop target', () => {
      dragManager.registerDropTarget({ id: 'target-1', type: 'table', accepts: ['transaction'], element: mockEl });
      expect(dragManager.getDropTargets().length).toBe(1);
    });

    it('unregisters a drop target', () => {
      dragManager.registerDropTarget({ id: 'target-1', type: 'table', accepts: ['transaction'], element: mockEl });
      expect(dragManager.unregisterDropTarget('target-1')).toBe(true);
      expect(dragManager.getDropTargets().length).toBe(0);
    });

    it('returns false when unregistering non-existent target', () => {
      expect(dragManager.unregisterDropTarget('nonexistent')).toBe(false);
    });

    it('gets a specific drop target', () => {
      dragManager.registerDropTarget({ id: 'target-1', type: 'table', accepts: ['transaction'], element: mockEl });
      expect(dragManager.getDropTarget('target-1')?.type).toBe('table');
    });

    it('filters acceptable targets by data type', () => {
      dragManager.registerDropTarget({ id: 't1', type: 'table', accepts: ['transaction'], element: mockEl });
      dragManager.registerDropTarget({ id: 't2', type: 'account', accepts: ['account'], element: mockEl });
      const acceptable = dragManager.getAcceptableTargets('transaction');
      expect(acceptable.length).toBe(1);
      expect(acceptable[0].id).toBe('t1');
    });

    it('accepts wildcard drop targets', () => {
      dragManager.registerDropTarget({ id: 't1', type: 'any', accepts: ['*'], element: mockEl });
      const acceptable = dragManager.getAcceptableTargets('transaction');
      expect(acceptable.length).toBe(1);
    });

    it('tracks hovered target', () => {
      dragManager.registerDropTarget({ id: 'target-1', type: 'table', accepts: ['transaction'], element: mockEl });
      dragManager.hoverTarget('target-1');
      const session = dragManager.getActiveSession();
      expect(session?.hoveredTarget).toBe('target-1');
    });
  });

  describe('Source Workspace', () => {
    it('tracks source workspace on drag start', () => {
      dragManager.startDrag({ type: 'transaction', id: 'tx-1' }, 'transactions');
      expect(dragManager.getState().sourceWorkspace).toBe('transactions');
    });
  });

  describe('Get Active Session', () => {
    it('returns null when no drag is active', () => {
      expect(dragManager.getActiveSession()).toBeNull();
    });

    it('returns session when drag is active', () => {
      dragManager.startDrag({ type: 'transaction', id: 'tx-1' });
      expect(dragManager.getActiveSession()).not.toBeNull();
    });
  });

  describe('Get State', () => {
    it('returns default state when no drag', () => {
      const state = dragManager.getState();
      expect(state.isDragging).toBe(false);
      expect(state.activeId).toBeNull();
      expect(state.data).toBeNull();
      expect(state.position).toBeNull();
    });

    it('returns dragging state with data', () => {
      dragManager.startDrag({ type: 'transaction', id: 'tx-1', label: 'Test' });
      const state = dragManager.getState();
      expect(state.isDragging).toBe(true);
      expect(state.activeId).toBe('tx-1');
      expect(state.activeType).toBe('transaction');
    });
  });

  describe('Subscription', () => {
    it('subscribes to drag state changes', () => {
      const listener = vi.fn();
      const sessionId = dragManager.startDrag({ type: 'transaction', id: 'tx-1' });
      const unsub = dragManager.subscribe(listener);
      dragManager.updatePosition(sessionId, 10, 20);
      expect(listener).toHaveBeenCalled();
      unsub();
    });

    it('unsubscribe stops receiving events', () => {
      const sessionId = dragManager.startDrag({ type: 'transaction', id: 'tx-1' });
      const listener = vi.fn();
      const unsub = dragManager.subscribe(listener);
      unsub();
      dragManager.updatePosition(sessionId, 10, 20);
      expect(listener).not.toHaveBeenCalled();
    });
  });

  describe('Reset', () => {
    it('clears all sessions', () => {
      dragManager.startDrag({ type: 'transaction', id: 'tx-1' });
      dragManager.reset();
      expect(dragManager.getState().isDragging).toBe(false);
      expect(dragManager.getActiveSession()).toBeNull();
    });
  });
});
